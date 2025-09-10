#!/usr/bin/python

# (c) 2025, NetApp Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""NetApp StorageGRID - Operations on Metrics"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.0",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
module: na_sg_grid_metrics
short_description: NetApp StorageGRID grab metrics.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg
version_added: '21.16.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
  - Get metrics on NetApp StorageGRID.
options:
  query:
    description:
    - Prometheus query string to execute.
    type: str
    required: true
  time:
    description:
    - Evaluation time for the query. If not provided, default current time(date-time) is used.
    - Use it as C(start_time) for query over range of time.
    aliases: ['start_time']
    type: str
  end_time:
    description:
    - End time for the query range.
    type: str
  step:
    description:
    - Step width/interval duration for the query range.
    type: str
  timeout:
    description:
    - Timeout duration for the query execution.
    type: str
"""

EXAMPLES = """
- name: Query metrics
  netapp.storagegrid.na_sg_grid_metrics:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    query: storagegrid_storage_utilization_usable_space_bytes
    time: 2025-08-01T00:00:00.000Z
    timeout: 30s
  register: sg_metric

- name: Query metrics over range of time
  netapp.storagegrid.na_sg_grid_metrics:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    query: storagegrid_storage_utilization_usable_space_bytes{site_name="site1"}
    start_time: 2025-08-27T10:10:58.668Z
    end_time: 2025-08-27T10:11:59.668Z
    step: 60s
    timeout: 30s
  register: sg_metric
"""

RETURN = """
sg_metric:
    description: Returns information about the StorageGRID metrics.
    returned: always
    type: dict
    sample: {
        "query": {
            "result": [
                {
                    "metric": {
                        "__name__": "storagegrid_storage_utilization_usable_space_bytes",
                        "instance": "sg-sn-01",
                        "job": "ldr",
                        "node_id": "658a91d7-d6f4-4d8e-a8ba-e15e6408b604",
                        "service": "ldr",
                        "site_id": "99d94acc-b2d4-4e4e-86e5-b715af68b40b",
                        "site_name": "site1"
                    },
                    "value": [
                        1756195871.224,
                        "29456490549248"
                    ]
                }
            ],
            "resultType": "vector"
        }
    }
"""

import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import SGRestAPI


class SgMetrics:
    """
    Operations on Metrics for StorageGRID
    """

    def __init__(self):
        """
        Parse arguments, setup variables,
        check parameters and ensure request module is installed
        """
        self.argument_spec = netapp_utils.na_storagegrid_host_argument_spec()
        self.argument_spec.update(
            dict(
                query=dict(type="str", required=True),
                time=dict(type="str", required=False, aliases=['start_time']),
                timeout=dict(type="str", required=False),
                end_time=dict(type="str", required=False),
                step=dict(type="str", required=False),
            )
        )
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()

        # set up variables
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # Calling generic SG rest_api class
        self.rest_api = SGRestAPI(self.module)
        # Get API version
        self.rest_api.get_sg_product_version(api_root="grid")
        # Checking for the parameters passed and create new parameters list

        self.params = {
            "query": self.parameters["query"],
            "timeout": self.parameters.get("timeout")
        }

    def get_metric_query(self):
        ''' Get metrics query'''
        api = "api/v4/grid/metric-query"
        self.params.update({
            "time": self.parameters.get("time")
        })
        response, error = self.rest_api.get(api, self.params)
        if error:
            self.module.fail_json(msg=error)

        return response["data"]

    def get_metric_query_range(self):
        ''' Get metrics query range'''
        api = "api/v4/grid/metric-query-range"
        self.params.update({
            "start": self.parameters.get("time"),
            "end": self.parameters.get("end_time"),
            "step": self.parameters.get("step")
        })
        response, error = self.rest_api.get(api, self.params)
        if error:
            self.module.fail_json(msg=error)

        return response["data"]

    def apply(self):
        ''' Apply metrics '''
        result_message = dict()
        if self.parameters.get("query") and not self.parameters.get("end_time") and not self.parameters.get("step"):
            result_message = self.get_metric_query()
        elif all(self.parameters.get(k) for k in ["query", "time", "end_time", "step"]):
            result_message = self.get_metric_query_range()
        else:
            self.module.fail_json(
                msg="If 'query' provided, 'time' (or 'start_time'), 'end_time', and 'step' must also be specified for query over range of time."
            )

        self.module.exit_json(changed=False, sg_metric=result_message)


def main():
    """
    Main function
    """
    na_sg_grid_metrics = SgMetrics()
    na_sg_grid_metrics.apply()


if __name__ == "__main__":
    main()
