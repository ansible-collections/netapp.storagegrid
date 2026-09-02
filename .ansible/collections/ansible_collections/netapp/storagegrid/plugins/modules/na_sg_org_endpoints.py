#!/usr/bin/python

# (c) 2026, NetApp Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""NetApp StorageGRID - Configure Platform Service Endpoint"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
module: na_sg_org_endpoints
short_description: NetApp StorageGRID configure Platform Service Endpoint.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg
version_added: '21.16.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
- Configure Platform Service Endpoint with in NetApp StorageGRID.
- If module is run with C(check_mode), a connectivity test will be performed using the supplied values without changing the configuration.
options:
  state:
    description:
    - Whether the specified endpoint should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
  name:
    description:
    - The name of the endpoint.
    required: false
    type: str
  endpoint_uri:
    description:
    - The URI of the endpoint.
    required: false
    type: str
  endpoint_urn:
    description:
    - The URN of the endpoint.
    required: false
    type: str
  auth_type:
    description:
    - The authentication type for the endpoint.
    required: false
    type: str
    choices: ['anonymous', 'accessKey', 'basicHttp', 'cap', 'sasl']
  ca_cert:
    description:
    - The CA certificate for the endpoint.
    required: false
    type: str
  insecure_tls:
    description:
    - Whether to allow insecure TLS connections to the endpoint.
    required: false
    type: bool
    default: false
  credentials:
    description:
    - The credentials for the endpoint.
    required: false
    type: dict
    suboptions:
      access_key:
        description:
        - The access key for the endpoint.
        required: false
        type: str
      secret_key:
        description:
        - The secret key for the endpoint.
        required: false
        type: str
  http_credentials:
    description:
    - The HTTP credentials for the endpoint.
    required: false
    type: dict
    suboptions:
      http_username:
        description:
        - The HTTP username for the endpoint.
        required: false
        type: str
      http_password:
        description:
        - The HTTP password for the endpoint.
        required: false
        type: str
  cap_credentials:
    description:
    - The CAP credentials for the endpoint.
    required: false
    type: dict
    suboptions:
      url:
        description:
        - The URL for the CAP endpoint.
        required: true
        type: str
      server_ca_cert:
        description:
        - The server CA certificate for the CAP endpoint.
        required: false
        type: str
      client_cert:
        description:
        - The client certificate for the CAP endpoint.
        required: true
        type: str
      client_key:
        description:
        - The client key for the CAP endpoint.
        required: true
        type: str
      client_key_passphrase:
        description:
        - The client key passphrase for the CAP endpoint.
        required: false
        type: str
  sasl_credentials:
    description:
    - The SASL credentials for the endpoint.
    required: false
    type: dict
    suboptions:
      mechanism:
        description:
        - The SASL mechanism for the endpoint.
        required: true
        type: str
        choices: ['PLAIN', 'SCRAM-SHA-256', 'SCRAM-SHA-512']
      sasl_username:
        description:
        - The SASL username for the endpoint.
        required: false
        type: str
      sasl_password:
        description:
        - The SASL password for the endpoint.
        required: false
        type: str
      delegation_token:
        description:
        - Whether to use a delegation token for the SASL endpoint.
        required: false
        type: bool
        default: false
"""

EXAMPLES = """
- name: Configure platform service endpoint
  netapp.storagegrid.na_sg_org_endpoints:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    state: present
    name: "My_endpoint"
    endpoint_uri: "https://s3-aws-region.amazonaws.com"
    endpoint_urn: "arn:aws:s3:::my-bucket"
    auth_type: "anonymous"
  check_mode: true

- name: Configure platform service endpoint with access key credentials
  netapp.storagegrid.na_sg_org_endpoints:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    state: present
    name: "My_endpoint"
    endpoint_uri: "https://s3-aws-region.amazonaws.com"
    endpoint_urn: "arn:aws:s3:::my-bucket"
    auth_type: "accessKey"
    credentials:
      access_key: "my-access-key"
      secret_key: "my-secret-key"

- name: Delete existing platform service endpoint
  netapp.storagegrid.na_sg_org_endpoints:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    state: absent
    name: "My_endpoint"
"""

RETURN = """
resp:
    description: Returns information about the StorageGRID endpoint configuration.
    returned: success
    type: dict
    sample: {
        "id": "00000000-0000-0000-0000-000000000000",
        "displayName": "My_endpoint",
        "endpointURI": "https://s3-aws-region.amazonaws.com",
        "endpointURN": "arn:aws:s3:::my-bucket",
        "authType": "anonymous",
        "insecureTLS": false,
        "caCert": null,
        "credentials": null,
    }
"""

import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import SGRestAPI


class SgOrgEndpoint:
    """
    Configure and modify StorageGRID Endpoint
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
                name=dict(required=False, type="str"),
                endpoint_uri=dict(required=False, type="str"),
                endpoint_urn=dict(required=False, type="str"),
                auth_type=dict(required=False, type="str", choices=["anonymous", "accessKey", "basicHttp", "cap", "sasl"]),
                ca_cert=dict(required=False, type="str"),
                insecure_tls=dict(required=False, type="bool", default=False),
                credentials=dict(
                    required=False,
                    type="dict",
                    options=dict(
                        access_key=dict(required=False, type="str", no_log=True),
                        secret_key=dict(required=False, type="str", no_log=True),
                    )
                ),
                http_credentials=dict(
                    required=False,
                    type="dict",
                    options=dict(
                        http_username=dict(required=False, type="str"),
                        http_password=dict(required=False, type="str", no_log=True),
                    )
                ),
                cap_credentials=dict(
                    required=False,
                    type="dict",
                    options=dict(
                        url=dict(required=True, type="str"),
                        server_ca_cert=dict(required=False, type="str", no_log=True),
                        client_cert=dict(required=True, type="str", no_log=True),
                        client_key=dict(required=True, type="str", no_log=True),
                        client_key_passphrase=dict(required=False, type="str", no_log=True),
                    )
                ),
                sasl_credentials=dict(
                    required=False,
                    type="dict",
                    options=dict(
                        mechanism=dict(required=True, type="str", choices=["PLAIN", "SCRAM-SHA-256", "SCRAM-SHA-512"]),
                        sasl_username=dict(required=False, type="str"),
                        sasl_password=dict(required=False, type="str", no_log=True),
                        delegation_token=dict(required=False, type="bool", default=False),
                    )
                ),
            )
        )

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ("auth_type", "accessKey", ["credentials"]),
                ("auth_type", "basicHttp", ["http_credentials"]),
                ("auth_type", "cap", ["cap_credentials"]),
                ("auth_type", "sasl", ["sasl_credentials"]),
            ],
            supports_check_mode=True,
        )

        self.na_helper = NetAppModule()

        # set up state variables
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # Calling generic SG rest_api class
        self.rest_api = SGRestAPI(self.module)
        # Checking for the parameters passed and create new parameters list
        self.data = {}

        if self.parameters.get("name"):
            self.data["displayName"] = self.parameters["name"]
        if self.parameters.get("endpoint_uri"):
            self.data["endpointURI"] = self.parameters["endpoint_uri"]
        if self.parameters.get("endpoint_urn"):
            self.data["endpointURN"] = self.parameters["endpoint_urn"]
        if self.parameters.get("auth_type"):
            self.data["authType"] = self.parameters["auth_type"]
        if self.parameters.get("ca_cert") is not None:
            self.data["caCert"] = self.parameters["ca_cert"]
        if self.parameters.get("insecure_tls") is not None:
            self.data["insecureTLS"] = self.parameters["insecure_tls"]

        if self.parameters.get("credentials") is not None:
            self.data["credentials"] = {}
            if self.parameters["credentials"].get("access_key") is not None:
                self.data["credentials"]["accessKey"] = self.parameters["credentials"]["access_key"]
            if self.parameters["credentials"].get("secret_key") is not None:
                self.data["credentials"]["secretKey"] = self.parameters["credentials"]["secret_key"]

        if self.parameters.get("http_credentials") is not None:
            self.data["basicHttpCredentials"] = {}
            if self.parameters["http_credentials"].get("http_username") is not None:
                self.data["basicHttpCredentials"]["username"] = self.parameters["http_credentials"]["http_username"]
            if self.parameters["http_credentials"].get("http_password") is not None:
                self.data["basicHttpCredentials"]["password"] = self.parameters["http_credentials"]["http_password"]

        if self.parameters.get("cap_credentials") is not None:
            self.data["capCredentials"] = {}
            if self.parameters["cap_credentials"].get("url") is not None:
                self.data["capCredentials"]["url"] = self.parameters["cap_credentials"]["url"]
            if self.parameters["cap_credentials"].get("server_ca_cert") is not None:
                self.data["capCredentials"]["serverCaCert"] = self.parameters["cap_credentials"]["server_ca_cert"]
            if self.parameters["cap_credentials"].get("client_cert") is not None:
                self.data["capCredentials"]["clientCert"] = self.parameters["cap_credentials"]["client_cert"]
            if self.parameters["cap_credentials"].get("client_key") is not None:
                self.data["capCredentials"]["clientKey"] = self.parameters["cap_credentials"]["client_key"]
            if self.parameters["cap_credentials"].get("client_key_passphrase") is not None:
                self.data["capCredentials"]["clientKeyPassphrase"] = self.parameters["cap_credentials"]["client_key_passphrase"]

        if self.parameters.get("sasl_credentials") is not None:
            self.data["saslCredentials"] = {}
            if self.parameters["sasl_credentials"].get("mechanism") is not None:
                self.data["saslCredentials"]["mechanism"] = self.parameters["sasl_credentials"]["mechanism"]
            if self.parameters["sasl_credentials"].get("sasl_username") is not None:
                self.data["saslCredentials"]["username"] = self.parameters["sasl_credentials"]["sasl_username"]
            if self.parameters["sasl_credentials"].get("sasl_password") is not None:
                self.data["saslCredentials"]["password"] = self.parameters["sasl_credentials"]["sasl_password"]
            if self.parameters["sasl_credentials"].get("delegation_token") is not None:
                self.data["saslCredentials"]["isDelegationToken"] = self.parameters["sasl_credentials"]["delegation_token"]

    def get_org_platform_service_endpoint(self):
        api = "api/v4/org/endpoints"
        response, error = self.rest_api.get(api)

        if error:
            self.module.fail_json(msg=error)

        for endpoint in response["data"]:
            if endpoint["displayName"] == self.parameters["name"]:
                self.id = endpoint["id"]
                return endpoint

    def create_org_platform_service_endpoint(self, test=False):
        api = "api/v4/org/endpoints"

        params = {}

        if test:
            params["test"] = True

        response, error = self.rest_api.post(api, self.data, params=params)
        if error:
            self.module.fail_json(msg=error, payload=self.data)

        if response:
            if response.get("status_code") == 204:
                return response
            if response.get("status_code") == 200:
                return response["data"]
        else:
            return None

    def update_org_platform_service_endpoint(self, test=False):
        api = "api/v4/org/endpoints/%s" % self.id

        params = {}

        if test:
            params["test"] = True

        response, error = self.rest_api.put(api, self.data, params=params)
        if error:
            self.module.fail_json(msg=error, payload=self.data)

        if response:
            if response.get("status_code") == 204:
                return response
            if response.get("status_code") == 200:
                return response["data"]
        else:
            return None

    def delete_org_platform_service_endpoint(self):
        api = "api/v4/org/endpoints/%s" % self.id

        response, error = self.rest_api.delete(api, None)
        if error:
            self.module.fail_json(msg=error)

        if response:
            return response["data"]
        else:
            return None

    def apply(self):
        """
        Perform pre-checks, call functions and exit
        """
        current_endpoint = self.get_org_platform_service_endpoint()

        cd_action = self.na_helper.get_cd_action(current_endpoint, self.parameters)

        if cd_action is None and self.parameters["state"] == "present":

            if self.data.get("displayName") and self.data["displayName"] != current_endpoint.get("displayName"):
                self.na_helper.changed = True
            if self.data.get("endpointURI") and self.data["endpointURI"] != current_endpoint.get("endpointURI"):
                self.na_helper.changed = True
            if self.data.get("endpointURN") and self.data["endpointURN"] != current_endpoint.get("endpointURN"):
                self.na_helper.changed = True
            if self.data.get("authType") and self.data["authType"] != current_endpoint.get("authType"):
                self.na_helper.changed = True
            if self.data.get("caCert") and self.data["caCert"] != current_endpoint.get("caCert"):
                self.na_helper.changed = True
            if self.data.get("insecureTLS") is not None and self.data["insecureTLS"] != current_endpoint.get("insecureTLS"):
                self.na_helper.changed = True
            if self.data.get("credentials") and self.data["credentials"] != current_endpoint.get("credentials"):
                self.na_helper.changed = True
            if self.data.get("basicHttpCredentials") and self.data["basicHttpCredentials"] != current_endpoint.get("basicHttpCredentials"):
                self.na_helper.changed = True
            if self.data.get("capCredentials") and self.data["capCredentials"] != current_endpoint.get("capCredentials"):
                self.na_helper.changed = True
            if self.data.get("saslCredentials") and self.data["saslCredentials"] != current_endpoint.get("saslCredentials"):
                self.na_helper.changed = True

        result_message = ""
        resp_data = current_endpoint
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == "create":
                    resp_data = self.create_org_platform_service_endpoint()
                    result_message = "Org platform service endpoint created successfully."
                elif cd_action == "delete":
                    self.delete_org_platform_service_endpoint()
                    result_message = "Org platform service endpoint deleted successfully."
                elif cd_action == "modify":
                    resp_data = self.update_org_platform_service_endpoint()
                    result_message = "Org platform service endpoint updated successfully."

                if self.module.check_mode:
                    self.create_org_platform_service_endpoint(test=True)
                    # if no error, connection test successful
                    self.module.exit_json(changed=self.na_helper.changed, msg="Connection test successful")

        self.module.exit_json(changed=self.na_helper.changed, msg=result_message, resp=resp_data)


def main():
    """
    Main function
    """
    na_sg_org_endpoints = SgOrgEndpoint()
    na_sg_org_endpoints.apply()


if __name__ == "__main__":
    main()
