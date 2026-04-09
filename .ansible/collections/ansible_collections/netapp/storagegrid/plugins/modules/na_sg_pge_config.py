#!/usr/bin/python

# (c) 2026, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" NetApp StorageGRID pge configuration using REST APIs """


from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: na_sg_pge_config
short_description: NetApp StorageGRID node PGE configuration.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg_pge
version_added: '21.17.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
  - update configuration for StorageGRID node Pre-Grid Environment (PGE).
options:
  reset_config:
    description:
      - Reset the PGE configuration update fields to default values.
    type: bool
    required: false
    default: false
  file_path:
    description:
      - Path of the StorageGRID Appliance configuration file to be uploaded.
    type: str
    required: false
  selected_node:
    description:
      - The node on which the uploaded PGE configuration will be applied.
    type: str
    required: false
"""

EXAMPLES = """
- name: Upload and apply configuration on StorageGRID Appliance
  netapp.storagegrid.na_sg_pge_config:
    api_url: "https://<storagegrid-endpoint-url>"
    validate_certs: false
    file_path: "/path/to/configuration/file.json"
    selected_node: "node-name"

- name: Reset configuration update fields to default
  netapp.storagegrid.na_sg_pge_config:
    api_url: "https://<storagegrid-endpoint-url>"
    validate_certs: false
    reset_config: true
"""

RETURN = """
resp:
    description: Returns information about the StorageGRID PGE configuration.
    returned: success
    type: dict
    sample: {
        "jsonFileName": "config.json",
        "logMessages": null,
        "nodeNames": ["node1"],
        "selectedNode": null,
        "updateConfigStatus": "ready"
    }
"""

import time
from ansible.module_utils.basic import AnsibleModule
import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import PgeRestAPI


class NetAppSgPgeConfig(object):
    """ Class with update pge configuration """

    def __init__(self):
        """
        Parse arguments, setup variables, check parameters and ensure
        request module is installed.
        """
        self.argument_spec = netapp_utils.na_storagegrid_pge_argument_spec()
        self.argument_spec.update(dict(
            reset_config=dict(type='bool', required=False, default=False),
            file_path=dict(type='str', required=False),
            selected_node=dict(type='str', required=False),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        # set up variables
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.rest_api = PgeRestAPI(self.module)

    def get_update_config_status(self):
        """ Get the status of pge configuration update"""
        api = "api/v2/update-config/status"
        response, error = self.rest_api.get(api)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def reset_update_config(self):
        """ Reset the pge configuration update fields to default values """
        api = "api/v2/update-config/reset"
        response, error = self.rest_api.put(api, data=None)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def upload_update_config_file(self, file_path):
        """ Upload the pge configuration update file to storagegrid node """
        api = "api/v2/update-config/upload"
        try:
            with open(file_path, 'rb') as f:
                file_name = file_path.split('/')[-1]
                upfile = {'upfile': (file_name, f)}
                response, error = self.rest_api.post(api, files=upfile)

                if response and response["data"].get('updateConfigStatus') == 'json-error':
                    self.module.fail_json(msg=f"uploaded config file has JSON error: {response.get('data', {}).get('logMessages')}")
                if error:
                    self.module.fail_json(msg=error)
                else:
                    return response["data"]

        except FileNotFoundError:
            self.module.fail_json(msg=f"Configuration file not found: {file_path}")

    def apply_uploaded_update_config(self):
        """ Apply the uploaded pge configuration update file to storagegrid node """
        api = "api/v2/update-config/apply"
        data = {
            "selectedNode": self.parameters['selected_node']
        }
        response, error = self.rest_api.post(api, data)

        if response["data"].get("updateConfigStatus") == "error":
            self.module.fail_json(msg=f"uploaded config file has JSON error: {response.get('data', {}).get('logMessages')}")
        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def apply(self):
        """ Perform pre-checks, call functions and exit """
        config_status = self.get_update_config_status()
        result_message = ""

        if self.parameters.get('reset_config'):
            # Only reset if not already in awaiting-upload status
            if config_status.get("updateConfigStatus") == "awaiting-upload":
                self.na_helper.changed = False
            else:
                config_status = self.reset_update_config()
                result_message = "Config reset successfully"
                self.na_helper.changed = True

        elif self.parameters.get('file_path'):
            # Check if config already uploaded
            file_name = self.parameters['file_path'].split('/')[-1]
            uploaded_filename = config_status.get('jsonFileName')
            update_config_status = config_status.get('updateConfigStatus')

            if uploaded_filename != file_name or update_config_status not in ['ready', 'applying']:
                config_status = self.upload_update_config_file(self.parameters['file_path'])
                self.na_helper.changed = True
                file_uploaded = True
            else:
                file_uploaded = False

            # If selected_node is provided and status is ready, apply the config
            if config_status.get("updateConfigStatus") == "ready" and self.parameters.get("selected_node"):
                self.apply_uploaded_update_config()
                time.sleep(5)  # Wait for a few seconds before checking the status again
                config_status = self.get_update_config_status()  # Refresh the status after applying
                if config_status.get("updateConfigStatus") == "complete":
                    if file_uploaded:
                        result_message = "Config file uploaded and applied successfully"
                    else:
                        result_message = "Config applied successfully"
                    self.na_helper.changed = True
                else:
                    self.module.fail_json(msg=f"Config apply failed with error: {config_status.get('logMessages')}")
            else:
                if file_uploaded:
                    result_message = "Config file uploaded successfully"

        elif self.parameters.get('selected_node'):
            self.apply_uploaded_update_config()
            time.sleep(5)  # Wait for a few seconds before checking the status again
            config_status = self.get_update_config_status()  # Refresh the status after applying
            if config_status.get("updateConfigStatus") == "complete":
                result_message = "Config applied successfully"
                self.na_helper.changed = True
        else:
            result_message = config_status
            self.na_helper.changed = False

        resp_data = config_status
        self.module.exit_json(changed=self.na_helper.changed, msg=result_message, resp=resp_data)


def main():
    """ Main function """
    obj = NetAppSgPgeConfig()
    obj.apply()


if __name__ == '__main__':
    main()
