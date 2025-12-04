#!/usr/bin/python

# (c) 2025, NetApp Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""NetApp StorageGRID - Manage SSH Security configuration"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.0",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
module: na_sg_grid_ssh_security
short_description: Configure ssh security on StorageGRID.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg
version_added: '21.16.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
  - Configure ssh security on NetApp StorageGRID.
options:
  state:
    description:
    - The ssh security should be present.
    choices: ['present']
    default: 'present'
    type: str
  allow_external_access:
    description:
    - Whether external SSH access to the grid is allowed.
    type: bool
    required: true
"""

EXAMPLES = """
- name: configure ssh security setting
  netapp.storagegrid.na_sg_grid_ssh_security:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    state: present
    allow_external_access: true
"""

RETURN = """
resp:
    description: Returns information about the StorageGRID ssh security.
    returned: If state is 'present'.
    type: dict
    sample: {
        "allowExternalAccess": true
    }
"""

import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import SGRestAPI


class SgSSHsecurity:
    """
    Configure ssh security for StorageGRID
    """

    def __init__(self):
        """
        Parse arguments, setup state variables,
        check parameters and ensure request module is installed
        """
        self.argument_spec = netapp_utils.na_storagegrid_host_argument_spec()
        self.argument_spec.update(
            dict(
                state=dict(type="str", choices=["present"], default="present"),
                allow_external_access=dict(required=True, type="bool"),
            )
        )
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()

        # set up state variables
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # Calling generic SG rest_api class
        self.rest_api = SGRestAPI(self.module)
        # Get API version
        self.rest_api.get_sg_product_version()
        self.api_version = self.rest_api.get_api_version()

        # Create new parameters list
        self.data = {}

        self.data["allowExternalAccess"] = self.parameters["allow_external_access"]

    def get_ssh_security_setting(self):
        """ Get ssh security setting """
        api = "api/v4/grid/ssh-security-setting"
        response, error = self.rest_api.get(api)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def update_ssh_security_setting(self):
        """ Update ssh security setting """
        api = "api/v4/grid/ssh-security-setting"
        response, error = self.rest_api.put(api, self.data)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def apply(self):
        ''' Apply ssh security changes '''

        current_ssh_security = self.get_ssh_security_setting()

        if self.parameters["state"] == "present":
            # let's see if we need to update parameters
            modify = self.na_helper.get_modified_attributes(current_ssh_security, self.data)

        result_message = ""
        resp_data = current_ssh_security
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            elif modify:
                resp_data = self.update_ssh_security_setting()
                result_message = "SSH security setting updated successfully."

        self.module.exit_json(changed=self.na_helper.changed, msg=result_message, resp=resp_data)


def main():
    """
    Main function
    """
    na_sg_grid_ssh_security = SgSSHsecurity()
    na_sg_grid_ssh_security.apply()


if __name__ == "__main__":
    main()
