#!/usr/bin/python

# (c) 2025, NetApp Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""NetApp StorageGRID - Manage Cloud Mirror Replication"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
module: na_sg_org_cloud_mirror_replication
short_description: Manage Cloud Mirror Replication on StorageGRID.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg
version_added: '21.16.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
-  Manage Cloud Mirror Replication on StorageGRID.
options:
  state:
    description:
    - The Cloud Mirror Replication should be present.
    type: str
    choices: ['present']
    default: present
  bucket_name:
    description:
    - The name of the bucket for which to configure Cloud Mirror Replication.
    required: true
    type: str
  xmlns:
    description:
    - The XML namespace for the replication configuration.
    type: str
  rule:
    description:
    - The replication rule configuration.
    type: dict
    suboptions:
      id:
        description:
        - The ID of the replication rule.
        type: str
      status:
        description:
        - The status of the replication rule.
        type: str
        choices: ['Enabled', 'Disabled']
      prefix:
        description:
        - The prefix filter for the replication rule.
        type: str
      destination:
        description:
        - The destination configuration for the replication rule.
        type: dict
        suboptions:
          bucket_urn:
            description:
            - The URN of the destination bucket.
            type: str
          storage_class:
            description:
            - The storage class for the destination bucket.
            type: str
            choices: ['STANDARD', 'STANDARD_IA', 'REDUCED_REDUNDANCY', 'NEARLINE', 'COLDLINE', 'ARCHIVE']
"""

EXAMPLES = """
- name: create cloud mirror replication
  netapp.storagegrid.na_sg_org_cloud_mirror_replication:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    state: present
    validate_certs: false
    bucket_name: bucket1
    xmlns: "http://1.2.3.4:10444/"
    rule:
      id: "rule1"
      status: "Enabled"
      prefix: "abc"
      destination:
        bucket_urn: "urn:sgws:s3:::bucket2"
        storage_class: "STANDARD"

- name: remove cloud mirror replication
  netapp.storagegrid.na_sg_org_cloud_mirror_replication:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    state: present
    validate_certs: false
    bucket_name: bucket1
"""

RETURN = """
resp:
    description: Returns information about the StorageGRID cloud mirror replication.
    returned: always
    type: dict
    sample:
      replication: |
        <?xml version="1.0" encoding="UTF-8"?>
        <ReplicationConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
          <Rule>
            <ID>rule1</ID>
            <Status>Enabled</Status>
            <Prefix></Prefix>
            <Destination>
              <Bucket>arn:aws:s3:::mybucket-replicated</Bucket>
              <StorageClass>STANDARD</StorageClass>
            </Destination>
            <Role>arn:aws:iam::35667example:role/CrossRegionReplicationRoleForS3</Role>
          </Rule>
        </ReplicationConfiguration>
"""

import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import SGRestAPI


class SgOrgCloudMirrorReplication(object):
    """
    Manage Cloud Mirror Replication
    """

    def __init__(self):
        """
        Parse arguments, setup state variables,
        check parameters and ensure request module is installed
        """
        self.argument_spec = netapp_utils.na_storagegrid_host_argument_spec()
        self.argument_spec.update(
            dict(
                state=dict(required=False, type="str", choices=["present"], default="present"),
                bucket_name=dict(required=True, type="str"),
                xmlns=dict(required=False, type="str"),
                rule=dict(
                    type="dict",
                    options=dict(
                        id=dict(type="str", required=False),
                        status=dict(type="str", required=False, choices=["Enabled", "Disabled"]),
                        prefix=dict(type="str", required=False),
                        destination=dict(
                            type="dict",
                            options=dict(
                                bucket_urn=dict(type="str", required=False),
                                storage_class=dict(
                                    type="str",
                                    required=False,
                                    choices=["STANDARD", "STANDARD_IA", "REDUCED_REDUNDANCY", "NEARLINE", "COLDLINE", "ARCHIVE"]
                                ),
                            )
                        ),
                    )
                )
            )
        )

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True,
        )

        self.na_helper = NetAppModule()

        # set up state variables
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # Calling generic SG rest_api class
        self.rest_api = SGRestAPI(self.module)

        # Get API version
        self.rest_api.get_sg_product_version(api_root="org")
        self.api_version = self.rest_api.get_api_version()

        # Build the XML for replication configuration
        if self.parameters.get("xmlns") and self.parameters.get("rule"):
            replication_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
            replication_xml += '<ReplicationConfiguration xmlns="{xmlns}">\n'.format(
                xmlns=self.parameters.get("xmlns")
            )
            rule = self.parameters.get("rule", {})
            replication_xml += '  <Rule>\n'
            if rule.get("id"):
                replication_xml += '    <ID>{}</ID>\n'.format(rule["id"])
            if rule.get("status"):
                replication_xml += '    <Status>{}</Status>\n'.format(rule["status"])
            if rule.get("prefix") is not None:
                replication_xml += '    <Prefix>{}</Prefix>\n'.format(rule["prefix"])
            destination = rule.get("destination", {})
            if destination:
                replication_xml += '    <Destination>\n'
                if destination.get("bucket_urn"):
                    replication_xml += '      <Bucket>{}</Bucket>\n'.format(destination["bucket_urn"])
                if destination.get("storage_class"):
                    replication_xml += '      <StorageClass>{}</StorageClass>\n'.format(destination["storage_class"])
                replication_xml += '    </Destination>\n'
            replication_xml += '  </Rule>\n'
            replication_xml += '</ReplicationConfiguration>\n'
            self.replication_xml = replication_xml

        elif self.parameters.get("xmlns") and not self.parameters.get("rule"):
            self.module.fail_json(msg="If 'xmlns' is provided, 'rule' must also be provided.")
        elif not self.parameters.get("xmlns") and self.parameters.get("rule"):
            self.module.fail_json(msg="If 'rule' is provided, 'xmlns' must also be provided.")
        else:
            self.replication_xml = None

    def get_org_bucket_replication(self):
        ''' Get org bucket replication '''
        api = "api/%s/org/containers/%s/replication" % (self.api_version, self.parameters["bucket_name"])
        response, error = self.rest_api.get(api)
        if error:
            self.module.fail_json(msg=error)

        return response["data"]

    def create_org_bucket_replication(self):
        ''' create org bucket replication '''
        api = "api/%s/org/containers/%s/replication" % (self.api_version, self.parameters["bucket_name"])
        data = {"replication": self.replication_xml}
        response, error = self.rest_api.put(api, data)
        if error:
            self.module.fail_json(msg=error)

        return response["data"]

    def apply(self):
        """
        Apply replication
        """

        current_replication = self.get_org_bucket_replication()

        if self.parameters["state"] == "present":
            set_replication = False

            current_xml = current_replication.get("replication")
            new_xml = self.replication_xml

            if self.parameters.get("xmlns") and self.parameters.get("rule") and current_xml != new_xml:
                set_replication = True
            if not self.parameters.get("xmlns") and not self.parameters.get("rule") and current_xml is not None:
                set_replication = True

            if set_replication:
                self.na_helper.changed = True

        result_message = ""
        resp_data = current_replication
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if set_replication:
                    resp_data = self.create_org_bucket_replication()
                    result_message = "Cloud Mirror Replication updated"

        self.module.exit_json(changed=self.na_helper.changed, msg=result_message, resp=resp_data)


def main():
    """
    Main function
    """
    na_sg_org_cloud_mirror_replication = SgOrgCloudMirrorReplication()
    na_sg_org_cloud_mirror_replication.apply()


if __name__ == "__main__":
    main()
