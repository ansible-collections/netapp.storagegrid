#!/usr/bin/python

# (c) 2025, NetApp Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""NetApp StorageGRID - Generate auth token to Login into grid/tenant module"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.0",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
module: na_sg_grid_login
short_description: Login to StorageGRID grid/tenant.
version_added: '21.16.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
  - This module generates authentication token to get login into grid/tenant module.
options:
  validate_certs:
    required: false
    default: true
    description:
    - Should https certificates be validated?
    type: bool
  hostname:
    description:
    - The ip or fqdn of the admin node for the grid.
    type: str
    required: true
  username:
    description:
    - The username of the user authenticating.
    type: str
    required: true
  password:
    description:
    - The password of the user authenticating.
    type: str
    required: true
  tenant_id:
    description:
    - The uuid of the tenant to log into tenant manager.
    type: str
"""

EXAMPLES = """
- name: generate auth token for grid module on StorageGRID
  netapp.storagegrid.na_sg_grid_login:
    hostname: 1.2.3.4
    username: root
    password: admin123
    validate_certs: false
  register: auth

- name: generate auth token for org module on StorageGRID
  netapp.storagegrid.na_sg_grid_login:
    hostname: 1.2.3.4
    username: tenant_username
    password: tenant_password
    tenant_id: 24240721088016532652
    validate_certs: false
  register: auth
"""

RETURN = """
resp:
    description: Returns information about the authentication token.
    returned: success
    type: str
    sample: "24263715-99c1-4d32-8c7f-e21cd0f6a731"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import SGAuthGenRestAPI


class SgLogin(object):
    """
    Class to generate auth token for StorageGRID grid/tenant
    """

    def __init__(self):
        """
        Parse arguments, setup state variables,
        check parameters and ensure request module is installed
        """
        self.argument_spec = (
            dict(
                hostname=dict(type="str", required=True),
                username=dict(type="str", required=True),
                password=dict(type="str", required=True, no_log=True),
                tenant_id=dict(type="str", required=False),
                validate_certs=dict(type="bool", default=True, required=False)
            )
        )
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()

        # set up state variables
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # Calling generic SG auth rest_api class
        self.rest_api = SGAuthGenRestAPI(self.module)

    def generate_auth_token(self):
        """Generate auth token using username and password"""
        api = "api/v3/authorize"
        body = {
            "username": self.parameters["username"],
            "password": self.parameters["password"],
            "cookie": False,
            "csrfToken": False,
        }
        if self.parameters.get("tenant_id"):
            body["accountId"] = self.parameters["tenant_id"]

        response, error = self.rest_api.post(api, body)
        if error:
            self.module.fail_json(msg=error)
        return response["data"]

    def apply(self):
        ''' Apply login changes '''

        resp_data = self.generate_auth_token()
        result_message = "authentication token generated successfully."
        self.na_helper.changed = True

        self.module.exit_json(changed=self.na_helper.changed, msg=result_message, na_sa_token=resp_data)


def main():
    """
    Main function
    """
    na_sg_grid_login = SgLogin()
    na_sg_grid_login.apply()


if __name__ == "__main__":
    main()
