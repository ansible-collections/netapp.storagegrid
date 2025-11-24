#!/usr/bin/python

# (c) 2025, NetApp Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""NetApp StorageGRID - Manage untrusted Client Network configuration"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.0",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
module: na_sg_grid_untrusted_client_network
short_description: Configure untrusted Client Network on StorageGRID.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg
version_added: '21.16.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
  - Configure untrusted Client Network on NetApp StorageGRID.
options:
  state:
    description:
    - The untrusted Client Network should be present.
    choices: ['present']
    default: 'present'
    type: str
  default_node:
    description:
    - The default setting for the Client Network on nodes added to the grid.
    choices: ['trusted', 'untrusted']
    default: 'trusted'
    type: str
  untrusted_nodes_id:
    description:
    - List of nodes IDs that have untrusted Client Networks.
    type: list
    elements: str
  untrusted_nodes_name:
    description:
    - List of nodes name that have untrusted Client Networks.
    type: list
    elements: str
"""

EXAMPLES = """
- name: Configure untrusted Client Network
  netapp.storagegrid.na_sg_grid_untrusted_client_network:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    state: present
    default_node: trusted
    untrusted_nodes_name:
      - SITE1-SN1
      - SITE1-SN2
"""

RETURN = """
resp:
    description: Returns information about the StorageGRID untrusted Client Network.
    returned: If state is 'present'.
    type: dict
    sample: {
        "default": "untrusted",
        "untrustedNodes": [
            "658a91d7-d6f4-4d8e-a8ba-e15e6408b604",
            "f02ab622-e2f6-4bfe-b14b-0fa472db756f"
        ]
    }
"""

import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import SGRestAPI


class SguntrustedClientNetwork:
    """
    Configure untrusted Client Network for StorageGRID
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
                default_node=dict(type="str", choices=["trusted", "untrusted"], default="trusted"),
                untrusted_nodes_id=dict(type="list", elements="str"),
                untrusted_nodes_name=dict(required=False, type="list", elements="str"),
            )
        )
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            mutually_exclusive=[["untrusted_nodes_id", "untrusted_nodes_name"]],
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()

        # set up state variables
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # Calling generic SG rest_api class
        self.rest_api = SGRestAPI(self.module)
        # Get API version
        self.rest_api.get_sg_product_version()

        # Checking for the parameters passed and create new parameters list
        self.data = {}
        self.data["untrustedNodes"] = []

        if self.parameters.get("default_node") is not None:
            self.data["default"] = self.parameters["default_node"]

        if self.parameters.get("untrusted_nodes_name") is not None:
            nodes_details = self.get_all_node_details()
            for node_details in nodes_details:
                for node_name in self.parameters["untrusted_nodes_name"]:
                    if node_name == node_details["name"]:
                        self.data["untrustedNodes"].append(node_details["id"])

        elif self.parameters.get("untrusted_nodes_id") is not None:
            self.data["untrustedNodes"] = self.parameters["untrusted_nodes_id"]

    def get_untrusted_client_network(self):
        """ Get untrusted Client Network configuration """
        api = "api/v4/grid/untrusted-client-network"
        response, error = self.rest_api.get(api)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def get_all_node_details(self):
        """ Get all node details """
        api = "api/v4/grid/node-health"
        response, error = self.rest_api.get(api)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def update_untrusted_client_network(self):
        """ Update untrusted Client Network configuration """
        api = "api/v4/grid/untrusted-client-network"
        response, error = self.rest_api.put(api, self.data)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def apply(self):
        ''' Apply untrusted Client Network configuration '''

        current_untrusted_client_network = self.get_untrusted_client_network()

        if self.parameters["state"] == "present":
            # let's see if we need to update parameters
            modify = self.na_helper.get_modified_attributes(current_untrusted_client_network, self.data)

        result_message = ""
        resp_data = current_untrusted_client_network
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            elif modify:
                resp_data = self.update_untrusted_client_network()
                result_message = "Untrusted Client Network configuration updated successfully."

        self.module.exit_json(changed=self.na_helper.changed, msg=result_message, resp=resp_data)


def main():
    """
    Main function
    """
    na_sg_grid_untrusted_client_network = SguntrustedClientNetwork()
    na_sg_grid_untrusted_client_network.apply()


if __name__ == "__main__":
    main()
