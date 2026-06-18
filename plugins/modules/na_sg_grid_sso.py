#!/usr/bin/python

# (c) 2026, NetApp Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""NetApp StorageGRID - Operations on single sign-on"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.0",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
module: na_sg_grid_sso
short_description: Manage single sign-on (SSO) configuration on StorageGRID.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg
version_added: '21.17.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
  - Manage single sign-on (SSO) configuration on NetApp StorageGRID.
options:
  state:
    description:
    - The desired state of the SSO configuration.
    choices: ['present']
    default: 'present'
    type: str
  disable:
    description:
    - Whether single sign-on is enabled for the grid.
    required: true
    type: bool
  sandbox:
    description:
    - Whether single sign-on sandbox mode is enabled for SSO configuration testing.
    required: true
    type: bool
  identity_provider:
    description:
    - Configuration for the identity provider (IdP) used for single sign-on.
    type: dict
    required: true
    suboptions:
      idp_type:
        description:
        - The type of identity provider service. Default is Active Directory.
        type: str
      federation_service_name:
        description:
        - The name of the identity provider service, required for Active Directory and ignored for other types.
        type: str
      relying_party_identifier:
        description:
        - The relying party unique identification string.
        required: true
        type: str
      admin_nodes:
        description:
        - Single sign-on settings for each Admin Node. Required for Azure and Ping Federate. Optional for Active Directory.
        type: list
        elements: dict
        suboptions:
          name:
            description:
            - The name of the admin node.
            type: str
          federation_metadata_url:
            description:
            - The URL for retrieving federation metadata from the admin node.
            type: str
  disable_tls:
    description:
    - Whether to disable TLS for securing the connection when the idp sends SSO configuration information in response to StorageGRID requests.
    type: bool
    default: False
  ca_cert:
    description:
    - Custom certificate for securing the TLS connection between StorageGRID and the identity provider.
    - If no custom certificate is supplied and TLS is enabled, the OS CA certificate will be used.
    type: str
"""

EXAMPLES = """
- name: Configure SSO with Azure identity provider
  netapp.storagegrid.na_sg_grid_sso:
    api_url: gmi.example.com
    auth_token: "storagegrid-auth-token"
    disable: false
    sandbox: true
    identity_provider:
      idp_type: Azure
      federation_service_name: ansible_test_federation
      relying_party_identifier: ansible_test_relying_party
      admin_nodes:
        - name: admin-node-1
          federation_metadata_url: https://admin-node-1.example.com/metadata
    disable_tls: true
    ca_cert: -----BEGIN CERTIFICATE----- abcdefghijkl1234FabcdefghijklABCD -----END CERTIFICATE----
"""

RETURN = """
resp:
    description: Returns information about the StorageGRID single sign-on configuration.
    returned: If state is 'present'.
    type: dict
    sample: {
        "disable": false,
        "sandbox": true,
        "disableTLS": true,
        "caCert": "",
        "identityProvider": {
            "type": "Azure",
            "federationServiceName": "ansible_test_federation",
            "relyingPartyIdentifier": "ansible_test_relying_party",
            "adminNodes": [
                {
                    "nodeId": "12345678-90ab-cdef-1234-567890aqcdef",
                    "federationMetadataUrl": "https://admin-node-1.example.com/metadata"
                }
            ]
        }
    }
"""

import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import SGRestAPI


class SgSSO:
    """
    Configure single sign-on (SSO) for StorageGRID
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
                disable=dict(type="bool", required=True),
                sandbox=dict(type="bool", required=True),
                identity_provider=dict(
                    required=True,
                    type="dict",
                    options=dict(
                        idp_type=dict(type="str", required=False),
                        federation_service_name=dict(type="str", required=False),
                        relying_party_identifier=dict(type="str", required=True),
                        admin_nodes=dict(
                            required=False,
                            type="list",
                            elements="dict",
                            options=dict(
                                name=dict(type="str", required=False),
                                federation_metadata_url=dict(type="str", required=False),
                            )
                        ),
                    ),
                ),
                disable_tls=dict(type="bool", required=False, default=False),
                ca_cert=dict(type="str", required=False)
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

        # Checking for the parameters passed and create new parameters list
        self.data = {}

        self.data["disable"] = self.parameters["disable"]
        self.data["sandbox"] = self.parameters["sandbox"]
        if self.parameters.get("disable_tls") is not None:
            self.data["disableTLS"] = self.parameters["disable_tls"]
        if self.parameters.get("ca_cert") is not None:
            self.data["caCert"] = self.parameters["ca_cert"]
        if self.parameters.get("identity_provider") is not None:
            self.data["identityProvider"] = {
                "type": self.parameters["identity_provider"].get("idp_type"),
                "federationServiceName": self.parameters["identity_provider"].get("federation_service_name"),
                "relyingPartyIdentifier": self.parameters["identity_provider"].get("relying_party_identifier"),
                "adminNodes": self.build_admin_nodes(
                    self.parameters["identity_provider"].get("admin_nodes") or []
                ),
            }

    def build_admin_nodes(self, admin_nodes):
        """Map user-supplied admin node names to node IDs via node-health"""
        if not admin_nodes:
            return []

        node_health = self.get_admin_grid_name()
        if not node_health:
            self.module.fail_json(msg="Unable to retrieve node list from node-health API.")

        name_to_id = {
            node.get("name"): node.get("id")
            for node in node_health
            if node.get("type") == "adminNode"
        }

        mapped = []
        for admin_node in admin_nodes:
            name = admin_node["name"]
            node_id = name_to_id.get(name)
            if not node_id:
                self.module.fail_json(
                    msg="Admin node '%s' not found or is not of type 'adminNode'." % name
                )
            mapped.append({
                "nodeId": node_id,
                "federationMetadataUrl": admin_node["federation_metadata_url"],
            })
        return mapped

    def get_sso_configuration(self):
        """ Get SSO configuration """
        api = "api/%s/private/single-sign-on" % self.api_version
        response, error = self.rest_api.get(api)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def get_admin_grid_name(self):
        """ Get admin grid name """
        api = "api/%s/grid/node-health" % self.api_version
        response, error = self.rest_api.get(api)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def update_sso_configuration(self):
        """ Update SSO configuration """
        api = "api/%s/private/single-sign-on" % self.api_version
        response, error = self.rest_api.put(api, self.data)

        if error:
            self.module.fail_json(msg=error)

        return response["data"]

    def apply(self):
        ''' Apply SSO configuration '''

        current_sso = self.get_sso_configuration()

        if self.parameters["state"] == "present":
            # let's see if we need to update parameters
            modify = self.na_helper.get_modified_attributes(current_sso, self.data)

        result_message = ""
        resp_data = current_sso
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            elif modify:
                resp_data = self.update_sso_configuration()
                result_message = "SSO configuration updated successfully."

        self.module.exit_json(changed=self.na_helper.changed, msg=result_message, resp=resp_data)


def main():
    """
    Main function
    """
    na_sg_grid_sso = SgSSO()
    na_sg_grid_sso.apply()


if __name__ == "__main__":
    main()
