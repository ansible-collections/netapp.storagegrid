#!/usr/bin/python

# (c) 2026, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""NetApp StorageGRID - Cluster configuration via install API"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
module: na_sg_grid_cluster_config
short_description: NetApp StorageGRID cluster configuration via install API.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg_pge
version_added: '21.17.0'
author: NetApp Ansible Team (@jayaramp) <ng-ansibleteam@netapp.com>
description:
  - Configure a NetApp StorageGRID cluster via the pre-authentication install API.
  - Covers grid details (name and license), DNS servers, NTP servers, grid networks,
    site creation, provisioning passwords, node approval, and provisioning start.
  - Each configuration area is applied only when its corresponding parameter is
    provided, making all parameters optional and the module fully idempotent.
options:
  state:
    description:
      - Desired state of the cluster configuration.
    type: str
    choices: ['present']
    default: present
  grid_name:
    description:
      - Name to assign to the StorageGRID grid.
    type: str
  license:
    description:
      - StorageGRID license key (base64-encoded JSON string).
    type: str
  dns_servers:
    description:
      - List of DNS server IP addresses for the grid.
    type: list
    elements: str
  ntp_servers:
    description:
      - List of NTP server addresses for the grid.
    type: list
    elements: str
  grid_networks:
    description:
      - List of grid network CIDR ranges.
    type: list
    elements: str
  site_name:
    description:
            - Name of the primary site to create. Skipped if a site with this name
                already exists.
    type: str
  provision_passphrase:
    description:
      - Provisioning passphrase for the grid.
    type: str
  management_passphrase:
    description:
      - Management (root) password for the grid admin interface.
    type: str
  use_random_passwords:
    description:
      - Use randomly generated passwords instead of the supplied ones.
    type: bool
    default: false
  approve_nodes:
    description:
      - Auto-approve all pending (unconfigured) nodes discovered by the install API.
      - Nodes already marked as configured are skipped.
      - A site must exist (or C(site_name) must be provided) before approving nodes.
    type: bool
    default: false
  start_provisioning:
    description:
      - Trigger the grid provisioning process after all other configuration steps.
    type: bool
    default: false
  recovery_package_path:
    description:
      - Local filesystem path where the Recovery Package ZIP file will be saved.
    type: str
    required: false
  recovery_package_set_cookie:
    description:
      - Integer cookie value passed as the C(setCookie) query parameter when
        downloading the Recovery Package.
            - When provided, a cookie named
                C(recovery-package-download-started-{value}) is set on a successful
                download response.
    type: int
    required: false
  recovery_package_wait_timeout:
    description:
            - Seconds to wait for the Recovery Package to become available after
                provisioning starts.
    type: int
    default: 1800
"""

EXAMPLES = """
- name: Configure StorageGRID cluster
  netapp.storagegrid.na_sg_grid_cluster_config:
    api_url: "<storage_endpoint>"
    validate_certs: false
    state: present
    grid_name: "my-grid"
    license: "<base64-encoded-license>"
    dns_servers:
      - "10.224.223.130"
    ntp_servers:
      - "10.235.48.111"
    grid_networks:
      - "172.16.160.0/19"
    site_name: "gdl"
    provision_passphrase: "{{ provision_pass }}"
    management_passphrase: "{{ mgmt_pass }}"
    approve_nodes: true
    start_provisioning: true

- name: Update DNS and NTP servers only
  netapp.storagegrid.na_sg_grid_cluster_config:
    api_url: "<storage_endpoint>"
    validate_certs: false
    dns_servers:
      - "8.8.8.8"
      - "8.8.4.4"
    ntp_servers:
      - "pool.ntp.org"
"""

RETURN = """
resp:
    description: Results of each configuration step that was applied.
    returned: success
    type: dict
    sample: {
        "grid_details": {"name": "my-grid"},
        "dns_servers": ["10.224.223.130"],
        "ntp_servers": ["10.235.48.111"],
        "grid_networks": ["172.16.160.0/19"],
        "site": {"id": "abc123", "name": "gdl"},
        "passwords_set": true,
        "nodes_approved": 3,
        "provisioning_started": true,
        "recovery_package_url": "https://10.224.176.67/api/v4/install/recovery-package",
        "recovery_package_msg": "Visit the recovery package URL",
        "recovery_package_path": "/tmp/storagegrid-recovery.zip",
        "recovery_package_confirm": {"status": "success"}
    }
"""

import os
import time

from ansible.module_utils.basic import AnsibleModule
import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import PgeRestAPI


class SgGridClusterConfig(object):
    """Configure StorageGRID cluster settings via the install API."""

    INSTALL_API_VERSION = "v4"

    def __init__(self):
        self.argument_spec = netapp_utils.na_storagegrid_pge_argument_spec()
        self.argument_spec.update(
            dict(
                state=dict(
                    required=False,
                    type="str",
                    choices=["present"],
                    default="present",
                ),
                grid_name=dict(required=False, type="str"),
                license=dict(required=False, type="str", no_log=True),
                dns_servers=dict(required=False, type="list", elements="str"),
                ntp_servers=dict(required=False, type="list", elements="str"),
                grid_networks=dict(required=False, type="list", elements="str"),
                site_name=dict(required=False, type="str"),
                provision_passphrase=dict(required=False, type="str", no_log=True),
                management_passphrase=dict(required=False, type="str", no_log=True),
                use_random_passwords=dict(required=False, type="bool", default=False),
                approve_nodes=dict(required=False, type="bool", default=False),
                start_provisioning=dict(required=False, type="bool", default=False),
                recovery_package_path=dict(required=False, type="str"),
                recovery_package_set_cookie=dict(required=False, type="int"),
                recovery_package_wait_timeout=dict(
                    required=False, type="int", default=1800
                ),
            )
        )

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True,
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.rest_api = PgeRestAPI(self.module)

    def _install_api(self, path):
        """Build an install API path."""
        return "api/%s/install/%s" % (self.INSTALL_API_VERSION, path)

    def get_grid_details(self):
        response, error = self.rest_api.get(self._install_api("grid-details"))
        if error:
            self.module.fail_json(msg="Failed to get grid-details: %s" % error)
        return response.get("data", {})

    def update_grid_details(self, payload):
        response, error = self.rest_api.put(self._install_api("grid-details"), payload)
        if error:
            self.module.fail_json(msg="Failed to update grid-details: %s" % error)
        return response.get("data", {})

    def get_dns_servers(self):
        response, error = self.rest_api.get(self._install_api("dns-servers"))
        if error:
            self.module.fail_json(msg="Failed to get dns-servers: %s" % error)
        return response.get("data", [])

    def update_dns_servers(self, servers):
        response, error = self.rest_api.put(self._install_api("dns-servers"), servers)
        if error:
            self.module.fail_json(msg="Failed to update dns-servers: %s" % error)
        return response.get("data", [])

    def get_ntp_servers(self):
        response, error = self.rest_api.get(self._install_api("ntp-servers"))
        if error:
            self.module.fail_json(msg="Failed to get ntp-servers: %s" % error)
        return response.get("data", [])

    def update_ntp_servers(self, servers):
        response, error = self.rest_api.put(self._install_api("ntp-servers"), servers)
        if error:
            self.module.fail_json(msg="Failed to update ntp-servers: %s" % error)
        return response.get("data", [])

    def get_grid_networks(self):
        response, error = self.rest_api.get(self._install_api("grid-networks"))
        if error:
            self.module.fail_json(msg="Failed to get grid-networks: %s" % error)
        return response.get("data", [])

    def update_grid_networks(self, networks):
        response, error = self.rest_api.put(
            self._install_api("grid-networks"), networks
        )
        if error:
            self.module.fail_json(msg="Failed to update grid-networks: %s" % error)
        return response.get("data", [])

    def get_sites(self):
        response, error = self.rest_api.get(self._install_api("sites"))
        if error:
            self.module.fail_json(msg="Failed to get sites: %s" % error)
        return response.get("data", [])

    def create_site(self, name):
        response, error = self.rest_api.post(self._install_api("sites"), {"name": name})
        if error:
            self.module.fail_json(msg="Failed to create site '%s': %s" % (name, error))
        return response.get("data", {})

    def set_passwords(self):
        payload = {
            "provision": self.parameters.get("provision_passphrase", ""),
            "management": self.parameters.get("management_passphrase", ""),
            "useRandom": self.parameters.get("use_random_passwords", False),
        }
        error = self.rest_api.put(self._install_api("passwords"), payload)[1]
        if error:
            self.module.fail_json(msg="Failed to set passwords: %s" % error)

    def get_nodes(self):
        response, error = self.rest_api.get(self._install_api("nodes"))
        if error:
            self.module.fail_json(msg="Failed to get nodes: %s" % error)
        return response.get("data", [])

    def get_node(self, node_id):
        response, error = self.rest_api.get(self._install_api("nodes/%s" % node_id))
        if error:
            self.module.fail_json(msg="Failed to get node '%s': %s" % (node_id, error))
        return response.get("data", {})

    def approve_node(self, node, site_id):
        # Carry through existing network info and ensure each interface is static
        networks = {}
        for iface, info in node.get("networks", {}).items():
            networks[iface] = dict(info)
            networks[iface]["config"] = "static"

        payload = {
            "id": node["id"],
            "site": site_id,
            "name": node["name"],
            "type": node["type"],
            # isPrimaryAdmin comes from the node data — not derived from the type string
            # (real API type is "adminNode", not "primary_admin")
            "isPrimaryAdmin": node.get("isPrimaryAdmin", False),
            "configured": True,
            "hardware": node.get("hardware", ""),
            "networks": networks,
        }
        # Pass through optional fields if the node data includes them
        for opt_field in ("ntpRole", "storageType", "hasAdc", "storageGrade"):
            if opt_field in node:
                payload[opt_field] = node[opt_field]

        error = self.rest_api.put(
            self._install_api("nodes/%s" % node["id"]), payload)[1]
        if error:
            self.module.fail_json(
                msg="Failed to approve node '%s': %s"
                % (node.get("name", node["id"]), error)
            )

    def start_provision(self):
        error = self.rest_api.post(self._install_api("start"), None)[1]
        if error:
            self.module.fail_json(msg="Failed to start provisioning: %s" % error)

    def get_install_progress(self):
        response, error = self.rest_api.get(self._install_api("progress"))
        if error:
            return None  # progress endpoint may not exist in all versions
        return response.get("data", {}) if response else None

    def get_recovery_package(self, dest_path, set_cookie=None):
        # The endpoint returns application/zip and requires an explicit Accept header.
        try:
            import requests
        except ImportError:
            self.module.fail_json(
                msg=(
                    "The 'requests' library is required to download the "
                    "recovery package."
                )
            )

        endpoint = self._install_api("recovery-package")
        url = "%s/%s" % (self.rest_api.api_url, endpoint)
        params = {}
        if set_cookie is not None:
            params["setCookie"] = set_cookie
        headers = {"Accept": "application/zip"}
        wait_timeout = self.parameters.get("recovery_package_wait_timeout", 1800)
        deadline = time.time() + wait_timeout if wait_timeout > 0 else 0

        while True:
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    verify=self.rest_api.verify,
                    timeout=self.rest_api.timeout,
                )
            except Exception as err:
                self.module.fail_json(
                    msg="Failed to download recovery package from '%s': %s"
                    % (url, str(err))
                )

            # 500 means the package is not ready yet — retry until deadline
            if response.status_code == 500:
                if wait_timeout > 0 and time.time() < deadline:
                    time.sleep(30)
                    continue
                # Timeout exceeded; return None so caller can decide whether
                # to warn or fail.
                return None

            try:
                response.raise_for_status()
            except Exception as err:
                self.module.fail_json(
                    msg="Failed to download recovery package from '%s': %s"
                    % (url, str(err))
                )
            break

        dest_dir = os.path.dirname(os.path.abspath(dest_path))
        if not os.path.exists(dest_dir):
            try:
                os.makedirs(dest_dir)
            except OSError as err:
                self.module.fail_json(
                    msg="Failed to create directory '%s': %s" % (dest_dir, str(err))
                )

        try:
            with open(dest_path, "wb") as fh:
                fh.write(response.content)
        except IOError as err:
            self.module.fail_json(
                msg="Failed to write recovery package to '%s': %s"
                % (dest_path, str(err))
            )
        return True

    def get_recovery_package_confirm(self):
        response, error = self.rest_api.get(
            self._install_api("recovery-package-confirm")
        )
        if error:
            self.module.fail_json(
                msg="Failed to get recovery-package-confirm status: %s" % error
            )
        return response.get("data", {})

    def post_recovery_package_confirm(self):
        response, error = self.rest_api.post(
            self._install_api("recovery-package-confirm"), None
        )
        if error:
            self.module.fail_json(
                msg="Failed to confirm recovery package download: %s" % error
            )
        return response.get("data", {}) if response else {}

    def apply(self):
        changed = False
        resp_data = {}

        # grid details
        if self.parameters.get("grid_name") or self.parameters.get("license"):
            current = self.get_grid_details()
            payload = {}
            if self.parameters.get("grid_name"):
                payload["name"] = self.parameters["grid_name"]
            if self.parameters.get("license"):
                payload["license"] = self.parameters["license"]

            name_changed = (
                payload.get("name") and payload["name"] != current.get("name")
            )
            # License content cannot be read back; always apply when provided
            license_provided = bool(payload.get("license"))

            if name_changed or license_provided:
                changed = True
                if not self.module.check_mode:
                    resp_data["grid_details"] = self.update_grid_details(payload)

        # DNS servers
        if self.parameters.get("dns_servers") is not None:
            desired = self.parameters["dns_servers"]
            current = self.get_dns_servers()
            if sorted(desired) != sorted(current):
                changed = True
                if not self.module.check_mode:
                    resp_data["dns_servers"] = self.update_dns_servers(desired)

        # NTP servers
        if self.parameters.get("ntp_servers") is not None:
            desired = self.parameters["ntp_servers"]
            current = self.get_ntp_servers()
            if sorted(desired) != sorted(current):
                changed = True
                if not self.module.check_mode:
                    resp_data["ntp_servers"] = self.update_ntp_servers(desired)

        # grid networks
        if self.parameters.get("grid_networks") is not None:
            desired = self.parameters["grid_networks"]
            current = self.get_grid_networks()
            if sorted(desired) != sorted(current):
                changed = True
                if not self.module.check_mode:
                    resp_data["grid_networks"] = self.update_grid_networks(desired)

        # site
        site_id = None
        if self.parameters.get("site_name"):
            sites = self.get_sites()
            existing = next(
                (
                    s for s in sites
                    if s.get("name") == self.parameters["site_name"]
                ),
                None,
            )
            if existing is None:
                changed = True
                if not self.module.check_mode:
                    site_data = self.create_site(self.parameters["site_name"])
                    resp_data["site"] = site_data
                    site_id = site_data.get("id")
            else:
                site_id = existing.get("id")
                resp_data["site"] = existing

        # passwords
        # Both passphrases must be supplied together when not using random passwords.
        if self.parameters.get("provision_passphrase") or self.parameters.get(
            "management_passphrase"
        ):
            if not self.parameters.get("use_random_passwords", False):
                provision = self.parameters.get("provision_passphrase")
                management = self.parameters.get("management_passphrase")
                if bool(provision) != bool(management):
                    self.module.fail_json(
                        msg=(
                            "Both 'provision_passphrase' and "
                            "'management_passphrase' must be provided "
                            "when 'use_random_passwords' is false."
                        )
                    )
            changed = True
            if not self.module.check_mode:
                self.set_passwords()
                resp_data["passwords_set"] = True

        # node approval
        all_nodes = None
        if self.parameters.get("approve_nodes"):
            all_nodes = self.get_nodes()
            pending = [n for n in all_nodes if not n.get("configured", False)]

            if all_nodes:
                if site_id is None:
                    sites = self.get_sites()
                    if not sites:
                        self.module.fail_json(
                            msg=(
                                "No site found. Provide 'site_name' or create a "
                                "site before approving nodes."
                            )
                        )
                    site_id = sites[0].get("id")

                if not self.module.check_mode:
                    # Always re-approve ALL nodes — prevents stale configured=True state
                    # from blocking provisioning after a PGE reboot or partial reset.
                    for node in all_nodes:
                        self.approve_node(node, site_id)

                # changed and nodes_approved reflect only genuinely unconfigured nodes
                if pending:
                    changed = True
                resp_data["nodes_approved"] = len(pending)

        # start provisioning
        if self.parameters.get("start_provisioning"):
            # Only validate primary admin state when approve_nodes was NOT used in this
            if not self.parameters.get("approve_nodes"):
                check_nodes = all_nodes if all_nodes is not None else self.get_nodes()
                primary_configured = any(
                    n.get("configured", False) and n.get("isPrimaryAdmin", False)
                    for n in check_nodes
                )
                if not primary_configured:
                    self.module.fail_json(
                        msg=(
                            "Cannot start provisioning: no Primary Admin Node "
                            "is configured. "
                            "Set 'approve_nodes: true' and ensure the Primary "
                            "Admin Node is "
                            "visible in GET /nodes with isPrimaryAdmin=true."
                        )
                    )
            changed = True
            if not self.module.check_mode:
                self.start_provision()
                resp_data["provisioning_started"] = True

        # recovery package
        # Always providing the download URL so the user knows where to get the file.
        recovery_pkg_url = "%s/%s" % (
            self.rest_api.api_url, self._install_api("recovery-package")
        )
        resp_data["recovery_package_url"] = recovery_pkg_url
        resp_data["recovery_package_msg"] = (
            "Visit %s to download the recovery package to finish pre-setup steps"
            % recovery_pkg_url
        )

        recovery_pkg_path = self.parameters.get("recovery_package_path")
        if recovery_pkg_path and not self.module.check_mode:
            set_cookie = self.parameters.get("recovery_package_set_cookie")
            downloaded = self.get_recovery_package(
                recovery_pkg_path, set_cookie=set_cookie
            )
            if downloaded:
                resp_data["recovery_package_path"] = recovery_pkg_path
                resp_data["recovery_package_confirm"] = (
                    self.post_recovery_package_confirm()
                )
                changed = True
            else:
                # Package not yet available — provisioning may still be in progress.
                progress = self.get_install_progress()
                warn = (
                    "Recovery package not yet available after %d seconds. "
                    "Re-run with only 'recovery_package_path' set once "
                    "installation progresses."
                    % self.parameters.get("recovery_package_wait_timeout", 1800)
                )
                if progress:
                    warn += " Install progress: %s" % progress
                resp_data["recovery_package_warning"] = warn

        self.na_helper.changed = changed
        result_message = (
            "Cluster configuration applied." if changed else "No changes required."
        )
        self.module.exit_json(
            changed=self.na_helper.changed, msg=result_message, resp=resp_data
        )


def main():
    """Main function"""
    obj = SgGridClusterConfig()
    obj.apply()


if __name__ == "__main__":
    main()
