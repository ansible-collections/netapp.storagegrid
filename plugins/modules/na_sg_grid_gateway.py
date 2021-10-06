#!/usr/bin/python

# (c) 2021, NetApp Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""NetApp StorageGRID - Manage Load Balancer Endpoints"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
module: na_sg_grid_gateway
short_description: Manage Load balancer (gateway) endpoints on StorageGRID.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg
version_added: '21.7.0'
author: NetApp Ansible Team (@jkandati) <ng-sg-ansibleteam@netapp.com>
description:
- Create or Update Load Balancer Endpoints on StorageGRID.
- This module is idempotent if C(private_key) is not specified
options:
  state:
    description:
    - Whether the specified load balancer endpoint should be configured
    type: str
    choices: ['present', 'absent']
    default: present
  display_name:
    description:
    - A display name for the configuration
    - This parameter cannot be modified after the load balancer endpoint has been created
    type: str
  port:
    description:
    - The TCP port to serve traffic on
    - This parameter cannot be modified after the load balancer endpoint has been created
    type: int
    required: true
  secure:
    description:
    - Whether the load balancer endpoint serves HTTP or HTTPS traffic
    - This parameter cannot be modified after the load balancer endpoint has been created
    type: bool
    default: true
  enable_ipv4:
    description:
    - Indicates whether to listen for connections on IPv4
    type: bool
    default: true
  enable_ipv6:
    description:
    - Indicates whether to listen for connections on IPv6
    type: bool
    default: true
  default_service_type:
    description:
    - The type of service to proxy through the load balancer
    type: str
    choices: ["s3","swift"]
    default: "s3"
  server_certificate:
    description:
    - X.509 server certificate in PEM-encoding
    - Omit if using default certificates
    type: str
    required: false
  private_key:
    description:
    - Certficate private key in PEM-encoding
    - Required if serverCertificateEncoded is not empty
    type: str
    required: false
  ca_bundle:
    description:
    - Intermediate CA certificate bundle in concatenated PEM-encoding
    - Omit when there is no intermediate CA
    type: str
    required: false

"""
EXAMPLES = """
  - name: Create and Upload Certificate to a Gateway Endpoint
    netapp.storagegrid.na_sg_grid_gateway:
      api_url: "https://<storagegrid-endpoint-url>"
      auth_token: "storagegrid-auth-token"
      displayName: "FabricPool Endpoint"
      port: 10443
      secure: True
      enable_ipv4: True
      enable_ipv6: True
      default_service_type: "s3"
      server_certificate: |
        -----BEGIN CERTIFICATE-----
        MIIC6DCCAdACCQC7l4WukhKD0zANBgkqhkiG9w0BAQsFADA2..swCQYDVQQGEwJB
        BAMMHnNnYW4wMS5kZXYubWljcm9icmV3Lm5ldGFwcC5hdTCC..IwDQYJKoZIhvcN
        AQEBBQADggEPADCCAQoCggEBAMvjm9I35lmKcC7ITVL8+QiZ..lvdkbfZCUQrfdy
        71inP+XmPjs0rnkhICA9ItODteRcVlO+t7nDTfm7HgG0mJFk..m0ffyEYrcx24qu
        S7gXYQjRsJmrep1awoaCa20BMGuqK2WKI3IvZ7YiT22qkBqK..+hIFffX6u3Jy+B
        77pR6YcATtpMHW/AaOx+OX9l80dIRsRZKMDxYQ==
        -----END CERTIFICATE-----
      private_key: |
        -----BEGIN PRIVATE KEY-----
        MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIB..DL45vSN+ZZinAu
        L25W0+cz1Oi69AKkI7d9nbFics2ay5+7o+4rKqf3en2R4MSx..vy+iDlOmATib5O
        x8TN5pJ9AgMBAAECggEADDLM8tHXXUoUFihzv+BUwff8p8Yc..cXFcSes+xTd5li
        po8lNsx/v2pQx4ByBkuaYLZGIEXOWS6gkp44xhIXgQKBgQD4..7862u5HLbmhrV3
        vs8nC69b3QKBgQDacCD8d8JpwPbg8t2VjXM3UvdmgAaLUfU7..DWV+W3jqzmDOoN
        zWVgPbPNj0UmzvLDbgxLoxe77wjn2BHsAJVAfJ9VeQKBgGqF..gYO+wHR8lJUoa5
        ZEe8Upy2oBtvND/0dnwO2ym2FGsBJN0Gr4NKdG5vkzLsthKk..Rm0ikwEUOUZQKE
        K8J5yEVeo9K2v3wggtq8fYn6
        -----END PRIVATE KEY-----
      validate_certs: false

"""

RETURN = """
resp:
    description: Returns information about the StorageGRID Load Balancer Endpoint.
    returned: success
    type: dict
    sample: {
        "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
        "displayName": "ansibletest-secure",
        "enableIPv4": True,
        "enableIPv6": True,
        "port": 10443,
        "secure": True,
        "accountId": "0",
        "defaultServiceType": "s3",
        "certSource": "plaintext",
        "plaintextCertData": {
            "serverCertificateEncoded": "-----BEGIN CERTIFICATE-----MIIC6DCCAdACCQC7l4WukhKD0zANBgkqhkiG9w0BAQsFADA2MQswCQYDVQQGE...-----END CERTIFICATE-----",
            "caBundleEncoded": "-----BEGIN CERTIFICATE-----MIIDdTCCAl2gAwIBAgILBAAAAAABFUtaw5QwDQYJKoZIhvcNAQEFBQAwVzELM...-----END CERTIFICATE-----",
            "metadata": {...}
        }
    }
"""

import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import SGRestAPI


class SgGridGateway:
    """
    Create, modify and delete Gateway entries for StorageGRID
    """

    def __init__(self):
        """
        Parse arguments, setup state variables,
        check parameters and ensure request module is installed
        """
        self.argument_spec = netapp_utils.na_storagegrid_host_argument_spec()
        self.argument_spec.update(
            dict(
                # Arguments for Creating Gateway Port
                state=dict(required=False, type="str", choices=["present", "absent"], default="present"),
                display_name=dict(required=False, type="str"),
                port=dict(required=True, type="int"),
                secure=dict(required=False, type="bool", default=True),
                enable_ipv4=dict(required=False, type="bool", default=True),
                enable_ipv6=dict(required=False, type="bool", default=True),
                # Arguments for setting Gateway Virtual Server
                default_service_type=dict(required=False, type="str", choices=["s3", "swift"], default="s3"),
                server_certificate=dict(required=False, type="str"),
                ca_bundle=dict(required=False, type="str"),
                private_key=dict(required=False, type="str", no_log=True),
            )
        )

        parameter_map_gateway = {
            "display_name": "displayName",
            "port": "port",
            "secure": "secure",
            "enable_ipv4": "enableIPv4",
            "enable_ipv6": "enableIPv6",
        }
        parameter_map_server = {
            "server_certificate": "serverCertificateEncoded",
            "ca_bundle": "caBundleEncoded",
            "private_key": "privateKeyEncoded",
        }
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[("state", "present", ["display_name"])],
            supports_check_mode=True,
        )

        self.na_helper = NetAppModule()

        # set up state variables
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # Calling generic SG rest_api class
        self.rest_api = SGRestAPI(self.module)
        # Checking for the parameters passed and create new parameters list

        # Parameters for creating a new gateway port configuration
        self.data_gateway = {}
        self.data_gateway["accountId"] = "0"

        for k in parameter_map_gateway.keys():
            if self.parameters.get(k) is not None:
                self.data_gateway[parameter_map_gateway[k]] = self.parameters[k]

        # Parameters for setting a gateway virtual server configuration for a gateway port
        self.data_server = {}
        self.data_server["defaultServiceType"] = self.parameters["default_service_type"]

        if self.parameters["secure"]:
            self.data_server["plaintextCertData"] = {}
            self.data_server["certSource"] = "plaintext"

            for k in parameter_map_server.keys():
                if self.parameters.get(k) is not None:
                    self.data_server["plaintextCertData"][parameter_map_server[k]] = self.parameters[k]

    def get_grid_gateway_server_config(self, gateway_id):
        api = "api/v3/private/gateway-configs/%s/server-config" % gateway_id
        response, error = self.rest_api.get(api)

        if error:
            self.module.fail_json(msg=error)

        return response["data"]

    def get_grid_gateway_ports(self, target_port):

        configured_ports = []
        gateway = {}
        gateway_config = {}

        api = "api/v3/private/gateway-configs"
        response, error = self.rest_api.get(api)

        if error:
            self.module.fail_json(msg=error)

        grid_gateway_ports = response["data"]

        # Get only a list of used ports
        configured_ports = [data["port"] for data in grid_gateway_ports]

        for index, port in enumerate(configured_ports):
            # if port already exists then get gateway ID and get the gateway port server configs
            if target_port == port:
                gateway = grid_gateway_ports[index]
                gateway_config = self.get_grid_gateway_server_config(gateway["id"])
                break

        return gateway, gateway_config

    def create_grid_gateway(self):
        api = "api/v3/private/gateway-configs"
        response, error = self.rest_api.post(api, self.data_gateway)

        if error:
            self.module.fail_json(msg=error)

        return response["data"]

    def delete_grid_gateway(self, gateway_id):
        api = "api/v3/private/gateway-configs/" + gateway_id
        self.data = None
        response, error = self.rest_api.delete(api, self.data)

        if error:
            self.module.fail_json(msg=error)

    def update_grid_gateway(self, gateway_id):
        api = "api/v3/private/gateway-configs/%s/server-config" % gateway_id
        response, error = self.rest_api.put(api, self.data_server)

        if error:
            self.module.fail_json(msg=error)

        return response["data"]

    def apply(self):
        # Get list of all gateway port configurations
        gateway, gateway_config = self.get_grid_gateway_ports(self.data_gateway["port"])

        cd_action = self.na_helper.get_cd_action(gateway.get("id"), self.parameters)

        if cd_action is None and self.parameters["state"] == "present":
            update = False

            if self.data_server.get("plaintextCertData"):
                if self.data_server["plaintextCertData"].get("privateKeyEncoded") is not None:
                    update = True
                    self.module.warn("This module is not idempotent when private_key is present.")

            if gateway_config.get("plaintextCertData"):
                # If certificate private key supplied, update
                if gateway_config["plaintextCertData"].get("metadata"):
                    # remove metadata because we can't compare that
                    del gateway_config["plaintextCertData"]["metadata"]

            # compare current and desired state
            self.na_helper.get_modified_attributes(gateway_config, self.data_server)

            if update:
                self.na_helper.changed = True

        result_message = ""
        resp_data = {}

        if self.na_helper.changed and not self.module.check_mode:
            if cd_action == "delete":
                self.delete_grid_gateway(gateway["id"])
                result_message = "Load Balancer Gateway Port Deleted"

            elif cd_action == "create":
                resp_data = self.create_grid_gateway()
                gateway["id"] = resp_data["id"]
                resp_data_server = self.update_grid_gateway(gateway["id"])
                resp_data.update(resp_data_server)
                result_message = "Load Balancer Gateway Port Created"

            else:
                resp_data = self.update_grid_gateway(gateway["id"])
                resp_data.update(gateway)
                result_message = "Load Balancer Gateway Port Updated"

        self.module.exit_json(changed=self.na_helper.changed, msg=result_message, resp=resp_data)


def main():
    """
    Main function
    """
    na_sg_grid_gateway = SgGridGateway()
    na_sg_grid_gateway.apply()


if __name__ == "__main__":
    main()
