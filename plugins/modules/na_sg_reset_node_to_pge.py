#!/usr/bin/python

# (c) 2026, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" NetApp StorageGRID PGE Primary admin node reset over SSH """


from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: na_sg_reset_node_to_pge
short_description: NetApp StorageGRID PGE Primary admin node reset.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg_pge
version_added: '21.17.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
  - Reset a StorageGRID Pre-Grid Environment (PGE) appliance by SSHing to the
    primary admin node (as the C(admin) user by default) and running C(sgareinstall).
options:
  ssh_password:
    description:
      - Password to use when SSHing to the appliance.
    required: true
    type: str
"""

EXAMPLES = """
- name: Reset StorageGRID PGE appliance
  netapp.storagegrid.na_sg_reset_node_to_pge:
    api_url: "https://<storagegrid-node-pge-endpoint>"
    validate_certs: false
    ssh_password: "{{ sg_ssh_password }}"
"""

RETURN = """
resp:
    description: Result of the reset command.
    returned: success
    type: dict
    sample: {
        "host": "10.10.10.10",
        "command": "sudo -S -p '' bash -lc 'yes | sgareinstall'",
        "exit_status": 255,
        "stdout": "",
        "stderr": "",
        "rebooted": true
    }
"""

from urllib.parse import urlparse
from shlex import quote as shell_quote

from ansible.module_utils.basic import AnsibleModule
import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import PgeRestAPI


SGAREINSTALL_CMD = "yes | sgareinstall"


class PgeSSH(object):
    """
    Thin SSH wrapper around ``module.run_command()`` (the same primitive used
    by Ansible's ``shell`` / ``command`` modules).

    It shells out to the system ``ssh`` binary against a StorageGRID node,
    authenticating with a password via ``sshpass``. ``run()`` can wrap the
    remote command in ``sudo -S`` and tolerate the session being torn down
    when the command reboots the node.
    """

    DEFAULT_SSH_OPTS = [
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=30",
    ]

    def __init__(self, module):
        self.module = module
        params = self.module.params

        self.host = self._host_from_api_url(params.get("api_url"))
        self.port = 8022
        self.username = "admin"
        self.password = params["ssh_password"]
        self.become_password = self.password

        self.ssh_bin = self.module.get_bin_path("ssh", required=True)
        self.sshpass_bin = self.module.get_bin_path("sshpass", required=False)

    @staticmethod
    def _host_from_api_url(api_url):
        if not api_url:
            return None
        parsed = urlparse(api_url if "://" in api_url else "https://" + api_url)
        return parsed.hostname

    def _build_argv(self, remote_cmd):
        argv = [self.sshpass_bin, "-e", self.ssh_bin, "-p", str(self.port)]
        argv += list(self.DEFAULT_SSH_OPTS)
        argv += ["%s@%s" % (self.username, self.host), remote_cmd]
        return argv

    def run(self, cmd, use_sudo=False, expect_reboot=False):
        """ Execute a shell command on the appliance via the ssh binary. """
        if use_sudo:
            # Run the whole pipeline as root via a login shell so PATH is set
            remote_cmd = "sudo -S -p '' bash -lc %s" % shell_quote(cmd)
        else:
            remote_cmd = cmd
        argv = self._build_argv(remote_cmd)

        # The sudo password is forwarded over ssh stdin to the remote sudo -S.
        stdin_data = (self.become_password + "\n") if use_sudo else None

        rc, stdout, stderr = self.module.run_command(
            argv,
            data=stdin_data,
            binary_data=False,
            use_unsafe_shell=False,
            environ_update={"SSHPASS": self.password},
        )

        rebooted = False
        # ssh exits 255 when the connection drops, which is expected when the
        # remote command reboots the node.
        if expect_reboot and rc == 255:
            rebooted = True

        return {
            "host": self.host,
            "command": remote_cmd,
            "exit_status": rc,
            "stdout": stdout,
            "stderr": stderr,
            "rebooted": rebooted,
        }


class NetAppSgPgeReset(object):
    """ Class to reset a StorageGRID PGE node over SSH """

    def __init__(self):
        self.argument_spec = netapp_utils.na_storagegrid_pge_argument_spec()
        self.argument_spec.update(
            dict(
                ssh_password=dict(type='str', required=True, no_log=True),
            )
        )

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True,
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.rest_api = PgeRestAPI(self.module)
        self.ssh = PgeSSH(self.module)

    def get_install_status(self):
        """ Return (install_status, error) from the PGE install-status API. """
        response, error = self.rest_api.get("api/v2/install-status")
        if error:
            return None, error
        return response.get("data"), None

    def _already_reset(self):
        """
        True when the node is reachable on the PGE API and sitting in a fresh
        pre-grid state (install not started/running/complete), i.e. it has
        already been reset and re-running sgareinstall would change nothing.
        """
        status, error = self.get_install_status()
        if error or status is None:
            # PGE API not answering (likely an installed/running grid)
            return False, None
        is_fresh = (
            not status.get("started")
            and not status.get("running")
            and not status.get("complete")
        )
        return is_fresh, status

    def apply(self):
        """ Perform the reset and exit. """
        already_reset, install_status = self._already_reset()
        if already_reset:
            self.module.exit_json(
                changed=False,
                msg="StorageGRID node on %s is already in a reset (PGE) state." % self.ssh.host,
                resp={"host": self.ssh.host, "install_status": install_status},
            )

        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                msg="Would run 'sudo %s' on %s" % (SGAREINSTALL_CMD, self.ssh.host),
                resp={"host": self.ssh.host, "command": SGAREINSTALL_CMD},
            )

        resp = self.ssh.run(SGAREINSTALL_CMD, use_sudo=True, expect_reboot=True)

        # If the command returned a non-zero status without a session drop,
        # surface the failure to the user.
        if not resp["rebooted"] and resp["exit_status"] not in (0, None):
            self.module.fail_json(
                msg="sgareinstall failed on %s (rc=%s): %s"
                    % (resp["host"], resp["exit_status"],
                       (resp["stderr"] or resp["stdout"]).strip()),
                resp=resp,
            )

        self.module.exit_json(
            changed=True,
            msg="StorageGRID PGE reset triggered on %s; node is rebooting." % resp["host"],
            resp=resp,
        )


def main():
    """ Main function """
    obj = NetAppSgPgeReset()
    obj.apply()


if __name__ == '__main__':
    main()
