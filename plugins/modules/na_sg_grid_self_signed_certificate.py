#!/usr/bin/python

# (c) 2026, NetApp Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""NetApp StorageGRID - Generate self signed certificate"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.0",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
module: na_sg_grid_self_signed_certificate
short_description: Generate self signed certificate on StorageGRID.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg
version_added: '21.17.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
  - Generate self signed certificate on NetApp StorageGRID.
options:
  state:
    description:
    - The self signed certificate should be present.
    choices: ['present']
    default: 'present'
    type: str
  subject:
    description:
    - The distinguished name of this certificate's entity.
    - If the subject does not contain a CN value, the CN is set to /CN=[first domain or IP] if a domain or IP is present.
    - Otherwise, it is set to /CN=StorageGRID or /CN StorageGRID client, based on the extendedKeyUsage for the generated certificate.
    type: str
  valid_days:
    description:
    - The number of days the certificate is valid.
    type: int
    default: 730
  domains:
    description:
    - Domain name identities in addition to or in place of the identity in the subject field.
    - If the subject common name is not set, the first domain name in the list is used as the common name.
    - It is optional when C(certificate_type) is C(clientAuth).
    type: list
    elements: str
  ips:
    description:
    - IP identities in addition to or in place of the identity in the subject field.
    - If subject common name and domains are not set, the first IP in the list is used as the common name.
    - It is optional when C(certificate_type) is C(clientAuth).
    type: list
    elements: str
  certificate_type:
    description:
    - The type of self-signed certificate to be generated.
    type: str
    choices: ['clientAuth', 'serverAuth']
    default: 'serverAuth'
  key_usage_extension:
    description:
    - Whether or not the generated certificate includes key usage extensions.
    - This should be set to true unless you are experiencing connection problems with older clients.
    type: bool
    default: false
notes:
  - Module is not idempotent.
"""

EXAMPLES = """
- name: generate self signed certificate
  netapp.storagegrid.na_sg_grid_self_signed_certificate:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    subject: "/CN=StorageGRID"
    valid_days: 365
    domains:
      - storagegrid.example.com
    ips:
      - "1.2.3.4"
    certificate_type: "serverAuth"
    key_usage_extension: true
"""

RETURN = """
resp:
    description: Returns information about the StorageGRID self signed certificate.
    returned: If state is 'present'.
    type: dict
    sample: {
        "privateKeyEncoded": "<private key in PEM-encoding>",
        "serverCertificateEncoded": "<certificate in PEM-encoding>"
    }
"""

import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import SGRestAPI


class SgSelfSignedCertificate:
    """
    Generate self signed certificate for StorageGRID
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
                subject=dict(type="str", required=False),
                valid_days=dict(type="int", required=False, default=730),
                domains=dict(type="list", elements="str", required=False),
                ips=dict(type="list", elements="str", required=False),
                certificate_type=dict(type="str", required=False, choices=["clientAuth", "serverAuth"], default="serverAuth"),
                key_usage_extension=dict(type="bool", required=False, default=False),

            )
        )
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[("certificate_type", "serverAuth", ("domains", "ips"), True)],
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

        if self.parameters.get("subject"):
            self.data["subject"] = self.parameters["subject"]
        if self.parameters.get("valid_days"):
            self.data["validDays"] = self.parameters["valid_days"]
        if self.parameters.get("domains"):
            self.data["domains"] = self.parameters["domains"]
        if self.parameters.get("ips"):
            self.data["ips"] = self.parameters["ips"]
        if self.parameters.get("certificate_type"):
            self.data["certificateType"] = self.parameters["certificate_type"]
        if self.parameters.get("key_usage_extension") is not None:
            self.data["includeKeyUsageExtensions"] = self.parameters["key_usage_extension"]

    def generate_self_signed_certificate(self):
        """ Generate self signed certificate """
        api = "api/%s/private/generate-self-signed-certificate" % self.api_version
        response, error = self.rest_api.post(api, self.data)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def apply(self):
        ''' Apply signed certificate changes '''

        resp_data = self.generate_self_signed_certificate()
        result_message = "self signed certificate generated successfully."
        self.na_helper.changed = True

        self.module.exit_json(changed=self.na_helper.changed, msg=result_message, resp=resp_data)


def main():
    """
    Main function
    """
    na_sg_grid_self_signed_certificate = SgSelfSignedCertificate()
    na_sg_grid_self_signed_certificate.apply()


if __name__ == "__main__":
    main()
