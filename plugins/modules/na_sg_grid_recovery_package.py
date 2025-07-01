#!/usr/bin/python

# (c) 2025, NetApp Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""NetApp StorageGRID - Recovery Packages"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
module: na_sg_grid_recovery_package
short_description: Retrieve the recovery package from StorageGRID
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg
version_added: '21.16.0'
author: NetApp Ansible Team (@aamirs) <ng-ansibleteam@netapp.com>
description:
  - Create recovery package on NetApp StorageGRID.
options:
  state:
    description:
    - Whether the recovery package should be present or absent.
    choices: ['present', 'absent']
    default: 'present'
    type: str
  passphrase:
    description:
    - the password used during maintenance procedures to make changes to the grid topology.
    type: str
"""

EXAMPLES = """
- name: Create StorageGRID recovery package
  netapp.storagegrid.na_sg_grid_recovery_package:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    state: present
    passphrase: "{{ storagegrid_passphrase }}"
"""

RETURN = """
resp:
    description: Returns information about the StorageGRID recovery package.
    returned: success
    type: dict
    sample: {
        "file_saved": "sgws-recovery-package-431636-rev1.zip"
    }
"""

import re
import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import SGRestAPI


class SgGridRecoveryPackage:
    """
    Download StorageGRID Recovery package
    """

    def __init__(self):
        """
        Parse arguments, setup state variables,
        check parameters and ensure request module is installed
        """
        self.argument_spec = netapp_utils.na_storagegrid_host_argument_spec()
        self.argument_spec.update(
            dict(
                state=dict(required=False, type="str", choices=["present", "absent"], default="present"),
                passphrase=dict(type='str', required=False, no_log=True),
            )
        )

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[("state", "present", ["passphrase"])],
            supports_check_mode=True,
        )

        self.na_helper = NetAppModule()

        # set up state variables
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # Calling generic SG rest_api class
        self.rest_api = SGRestAPI(self.module)
        # Get API version
        self.rest_api.get_sg_product_version(api_root="grid")

        # Checking for the parameters passed and create new parameters list
        self.data = {}
        self.data["passphrase"] = self.parameters["passphrase"]

    def create_recovery_package(self):
        # Create recovery package
        api = "api/v3/grid/recovery-package"

        response, error = self.rest_api.post(api, self.data)

        if error:
            self.module.fail_json(msg=error)

        if not response:
            self.module.fail_json(msg="ERROR: Received empty response from API.")

        content_disposition = response.headers.get("Content-Disposition", "")
        match = re.search(r'filename="?([^"]+)"?', content_disposition)
        if match:
            file_name = match.group(1)

        with open(file_name, "wb") as f:
            f.write(response.content)

        return {"file_saved", file_name}, None

    def apply(self):
        """
        Perform pre-checks, call functions and exit
        """
        recovery_package = None

        cd_action = self.na_helper.get_cd_action(recovery_package, self.parameters)

        result_message = ""
        resp_data = None
        if self.na_helper.changed:
            if self.module.check_mode:
                pass

            if cd_action == "create":
                resp_data = self.create_recovery_package()
                result_message = "recovery package downloaded successfully"

        self.module.exit_json(changed=self.na_helper.changed, resp=resp_data, msg=result_message)


def main():
    """
    Main function
    """
    na_sg_grid_recovery_package = SgGridRecoveryPackage()
    na_sg_grid_recovery_package.apply()


if __name__ == '__main__':
    main()
