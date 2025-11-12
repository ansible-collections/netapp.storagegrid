#!/usr/bin/python

""" NetApp StorageGRID User S3 Keys Info """


from __future__ import absolute_import, division, print_function


__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: na_sg_org_user_s3_key_info
author: Robin Elfrink <robin.elfrink@eu.equinix.com>
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg
short_description: NetApp StorageGRID Org User S3 Keys information gatherer.
description:
    - This module allows you to gather various information about a StorageGRID Org User's S3 keys.
version_added: 21.16.0
options:
  unique_user_name:
    description:
    - Unique user name owning the S3 Key.
    required: true
    type: str
"""

EXAMPLES = """
- name: fetch user's s3 key info
  netapp.storagegrid.na_sg_org_user_s3_key_info:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    unique_user_name: user/ansibleuser1
"""
RETURN = """
sg_user_s3_keys:
    description: Returns information about S3 access keys for the user.
    returned: always
    type: list
    sample: [
        {
            "id": "abcABC_01234-0123456789abcABCabc0123456789==",
            "accountId": 12345678901234567000,
            "displayName": "****************AB12",
            "userURN": "urn:sgws:identity::12345678901234567000:root",
            "userUUID": "00000000-0000-0000-0000-000000000000",
            "expires": "2020-09-04T00:00:00.000Z"
        },
    ]
"""

from ansible.module_utils.basic import AnsibleModule
import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import SGRestAPI


class SgOrgUserS3KeyInfo(object):
    """ Class with gather info methods """

    def __init__(self):
        """
        Parse arguments, setup variables, check parameters and ensure
        request module is installed.
        """
        self.argument_spec = netapp_utils.na_storagegrid_host_argument_spec()
        self.argument_spec.update(dict(
            unique_user_name=dict(required=True, type="str"),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        # set up variables
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.rest_api = SGRestAPI(self.module)


    def get_org_user_id(self, unique_user_name):
        # Use the unique name to check if the user exists
        api = "api/v3/org/users/%s" % unique_user_name
        response, error = self.rest_api.get(api)
        if error:
            if response["code"] != 404:
                self.module.fail_json(msg=error)
        else:
            return response["data"]["id"]
        return None

    def get_org_user_s3_keys(self, user_id):
        # Use the unique name to check if the user exists
        api = "api/v3/org/users/current-user/s3-access-keys"

        if user_id:
            api = "api/v3/org/users/%s/s3-access-keys" % (
                user_id,
            )

        response, error = self.rest_api.get(api)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]
        return None
    
    def apply(self):
        """
        Perform pre-checks, call functions and exit
        """
        result_message = ""
        resp_data = {}
        user_id = None

        if self.parameters.get("unique_user_name"):
            user_id = self.get_org_user_id(self.parameters["unique_user_name"])

        resp_data = self.get_org_user_s3_keys(user_id)
        self.module.exit_json(changed=False, sg_user_s3_keys=resp_data)

def main():
    """ Main function """
    na_sg_org_user_s3_key_info = SgOrgUserS3KeyInfo()
    na_sg_org_user_s3_key_info.apply()


if __name__ == '__main__':
    main()
