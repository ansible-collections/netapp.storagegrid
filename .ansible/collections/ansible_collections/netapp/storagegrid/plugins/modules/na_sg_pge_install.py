#!/usr/bin/python

# (c) 2026, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" NetApp StorageGRID pge install using REST APIs """


from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: na_sg_pge_install
short_description: NetApp StorageGRID PGE load install.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg_pge
version_added: '21.17.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
  - Start loading installation for StorageGRID Pre-Grid Environment (PGE).
options:
  start_install:
    description:
      - Trigger the storagegrid installation.
    type: bool
    required: true
"""

EXAMPLES = """
- name: Trigger installation for StorageGRID Appliance
  netapp.storagegrid.na_sg_pge_install:
    api_url: "https://<storagegrid-endpoint-url>"
    validate_certs: false
    start_install: true
"""

RETURN = """
resp:
    description: Returns information about the StorageGRID PGE install.
    returned: success
    type: dict
    sample: {
        "complete": False,
        "failed": False,
        "okToRedirect": True,
        "running": True,
        "started": True,
        "status": [
            {
                "errors": [],
                "name": "Configure storage",
                "state": "complete",
                "steps": [
                    {
                        "name": "Evaluate local node storage",
                        "progress": 100,
                        "state": "complete"
                    },
                    {
                        "name": "Create local node storage",
                        "progress": 100,
                        "state": "skipped"
                    },
                    {
                        "name": "Map local node storage",
                        "progress": 100,
                        "state": "complete"
                    }
                ]
            },
            {
                "errors": [],
                "name": "Install OS",
                "state": "complete",
                "steps": [
                    {
                        "name": "Obtain installer binaries",
                        "progress": 100,
                        "state": "complete"
                    },
                    {
                        "name": "Configure installer",
                        "progress": 100,
                        "state": "complete"
                    },
                    {
                        "name": "Install OS",
                        "progress": 100,
                        "state": "complete"
                    }
                ]
            },
            {
                "errors": [],
                "name": "Install StorageGRID",
                "state": "complete",
                "steps": [
                    {
                        "name": "Install StorageGRID",
                        "progress": 100,
                        "state": "complete"
                    }
                ]
            },
            {
                "errors": [],
                "name": "Finalize installation",
                "state": "complete",
                "steps": [
                    {
                        "name": "Prepare for bare metal",
                        "progress": 100,
                        "state": "complete"
                    },
                    {
                        "name": "Initiate bare metal reboot",
                        "progress": 100,
                        "state": "complete"
                    }
                ]
            },
            {
                "errors": [],
                "name": "Load StorageGRID Installer",
                "state": "running",
                "steps": [
                    {
                        "endTime": None,
                        "message": "Do not refresh. You will be redirected when the installer is ready",
                        "name": "Starting StorageGRID Installer",
                        "progress": 50,
                        "state": "running"
                    }
                ]
            }
        ]
    }
"""

import time
from ansible.module_utils.basic import AnsibleModule
import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import PgeRestAPI


class NetAppSgPgeInstall(object):
    """ Class with install pge system """

    def __init__(self):
        """
        Parse arguments, setup variables, check parameters and ensure
        request module is installed.
        """
        self.argument_spec = netapp_utils.na_storagegrid_pge_argument_spec()
        self.argument_spec.update(dict(
            start_install=dict(type='bool', required=True),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        # set up variables
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.rest_api = PgeRestAPI(self.module)

    def get_current_install_status_info(self):
        """ Get the current install status information for the storagegrid """
        api = "api/v2/install-status"
        response, error = self.rest_api.get(api)

        if error:
            return None, error
        return response["data"], None

    def get_node_type(self):
        """ Get the appliance node type from system-config """
        api = "api/v2/system-config"
        response, error = self.rest_api.get(api)
        if error:
            self.module.fail_json(msg=error)

        return response["data"].get("nodeType")

    @staticmethod
    def _awaiting_node_approval(install_status):
        """Return True when the node is waiting for
        approval on the primary admin GMI."""
        for line in install_status.get("logLines"):
            if "Approve this node" in line:
                return True
        return False

    def execute_install(self):
        """ Execute the install for the storagegrid """
        api = "api/v2/start-install"
        response, error = self.rest_api.post(api, data=None)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def apply(self):
        """ Perform pre-checks, call functions and exit """
        current_install_status, error = self.get_current_install_status_info()
        if error:
            self.module.fail_json(msg=error)

        if current_install_status.get("complete"):
            self.module.exit_json(changed=False, msg="Installation already complete.", resp=current_install_status)

        if current_install_status.get("failed"):
            self.module.fail_json(msg="Installation has failed.", resp=current_install_status)

        if self._awaiting_node_approval(current_install_status):
            node_type = self.get_node_type()
            self.module.exit_json(
                changed=False,
                msg=("StorageGRID node already installed and waiting for approval. "
                     "Approve node type '%s' on the primary admin GMI to proceed." % node_type),
                resp={
                    "install_status": current_install_status,
                    "node_type": node_type,
                    "next_step_url": None,
                },
            )

        if self.module.check_mode:
            if current_install_status.get("running"):
                self.module.exit_json(changed=False, msg="Installation already in progress.", resp=current_install_status)
            self.module.exit_json(changed=True, msg="Installation would be triggered.")

        # Trigger the install if it has not been started yet
        if not current_install_status.get("started") and not current_install_status.get("running"):
            self.execute_install()

        node_type = self.get_node_type()
        is_primary_admin = node_type == "primary_admin"
        # we can expect welcome_url if installer succesfully loaded
        welcome_url = "%s/install/#/install/welcome" % self.parameters["api_url"].rstrip("/")

        poll_interval = 3
        max_wait = 3600
        elapsed = 0
        changed = False
        install_status = current_install_status

        while elapsed < max_wait:
            status, err = self.get_current_install_status_info()

            if err is None:
                install_status = status
                if install_status.get("failed"):
                    self.module.fail_json(msg="Installation failed.", resp=install_status)
                if install_status.get("complete"):
                    changed = True
                    break
                # Non-primary-admin nodes will wait for approval on the Admin Node GMI.
                if not is_primary_admin and self._awaiting_node_approval(install_status):
                    changed = True
                    break
            elif is_primary_admin:
                resp_body, probe_err = self.rest_api.get("install/")
                if probe_err is None:
                    changed = True
                    break

            time.sleep(poll_interval)
            elapsed += poll_interval

        if not changed and not install_status.get("complete"):
            self.module.fail_json(
                msg="Installation did not complete within %d seconds." % max_wait,
                resp=install_status,
            )

        if install_status.get("complete"):
            msg = "Installation completed successfully."
        elif is_primary_admin:
            msg = "StorageGRID installer ready. Continue at: %s" % welcome_url
        else:
            msg = ("StorageGRID node installed and waiting for approval. "
                   "Approve node type '%s' on the primary admin GMI to proceed." % node_type)

        self.module.exit_json(
            changed=changed,
            msg=msg,
            resp={
                "install_status": install_status,
                "node_type": node_type,
                "next_step_url": welcome_url if is_primary_admin else None,
            },
        )


def main():
    """ Main function """
    obj = NetAppSgPgeInstall()
    obj.apply()


if __name__ == '__main__':
    main()
