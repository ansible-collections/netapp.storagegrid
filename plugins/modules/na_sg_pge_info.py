#!/usr/bin/python

# (c) 2025, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" NetApp StorageGRID pge info using REST APIs """


from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: na_sg_pge_info
short_description: NetApp StorageGRID node PGE information gatherer.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg_pge
version_added: '21.16.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
  - Gather various information about StorageGRID node Pre-Grid Environment (PGE) configuration.
options:
    gather_subset:
        type: list
        elements: str
        description:
            - When supplied, this argument will restrict the information collected to a given subset.
            - Either the info name or the REST API can be given.
            - Possible values for this argument include
            - C(pge_storage_configuration_networking) or C(pge/storage-configuration/networking)
            - C(pge_bmc_config) or C(pge/bmc-config)
            - C(pge_install_status) or C(pge/install-status)
            - C(pge_networks) or C(pge/networks)
            - C(pge_link_config) or C(pge/link-config)
            - C(pge_dns) or C(pge/dns)
            - C(pge_system_info) or C(pge/system-info)
            - C(pge_system_config) or C(pge/system-config)
            - C(pge_admin_connection) or C(pge/admin-connection)
            - C(pge_ipmi_sensors) or C(pge/ipmi-sensors)
            - C(pge_upgrade_status) or C(pge/upgrade/status)
            - C(pge_debug_dump_addr_show) or C(pge/debug/dump-addr-show)
            - C(pge_debug_dump_routes) or C(pge/debug/dump-routes)
            - C(pge_debug_dump_bonding) or C(pge/debug/dump-bonding)
            - C(pge_debug_dump_netlink) or C(pge/debug/dump-netlink)
            - C(pge_debug_dump_bonding_raw) or C(pge/debug/dump-bonding-raw)
            - C(pge_debug_dump_lldp_attributes) or C(pge/debug/dump-lldp-attributes)
            - Can specify a list of values to include a larger subset.
        default: all
    parameters:
        description:
        - Allows for any rest option to be passed in.
        type: dict
"""

EXAMPLES = """
- name: Gather StorageGRID node PGE info
  netapp.storagegrid.na_sg_pge_info:
    api_url: "https://1.2.3.4/"
    validate_certs: false
  register: sg_pge_info

- name: Gather StorageGRID PGE info for pge/bmc-config and pge_dns subsets
  netapp.storagegrid.na_sg_pge_info:
    api_url: "https://1.2.3.4/"
    validate_certs: false
    gather_subset:
      - pge/bmc-config
      - pge_dns
  register: sg_pge_info

- name: Gather StorageGRID PGE info for all subsets
  netapp.storagegrid.na_sg_pge_info:
    api_url: "https://1.2.3.4/"
    validate_certs: false
    gather_subset:
      - all
  register: sg_pge_info

- name: Gather StorageGRID PGE info for pge/system-config and pge/system-info subsets, limit to 5 results for each subset
  netapp.storagegrid.na_sg_pge_info:
    api_url: "https://1.2.3.4/"
    validate_certs: false
    gather_subset:
      - pge/system-config
      - pge/system-info
    parameters:
      limit: 5
  register: sg_pge_info
"""

RETURN = """
sg_pge_info:
    description: Returns various information about the StorageGRID node PGE configuration.
    returned: always
    type: dict
    sample: {
        "pge/storage-configuration/networking": {...},
        "pge/bmc-config": {...},
        "pge/install-status": {...},
        "pge/networks": {...},
        "pge/link-config": {...},
        "pge/dns": {...},
        "pge/system-info": {...},
        "pge/system-config": {...},
        "pge/admin-connection": {...},
        "pge/ipmi-sensors": {...},
        "pge/upgrade/status": {...},
        "pge/debug/dump-addr-show": {...},
        "pge/debug/dump-routes": {...},
        "pge/debug/dump-bonding": {...},
        "pge/debug/dump-netlink": {...},
        "pge/debug/dump-bonding-raw": {...},
        "pge/debug/dump-lldp-attributes": {...}
    }
"""

from ansible.module_utils.basic import AnsibleModule
import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import PgeRestAPI


class NetAppSgGatherPgeInfo(object):
    """ Class with gather pge info methods """

    def __init__(self):
        """
        Parse arguments, setup variables, check parameters and ensure
        request module is installed.
        """
        self.argument_spec = netapp_utils.na_storagegrid_pge_argument_spec()
        self.argument_spec.update(dict(
            gather_subset=dict(default=['all'], type='list', elements='str', required=False),
            parameters=dict(type='dict', required=False)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        # set up variables
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.rest_api = PgeRestAPI(self.module)

    def get_subset_info(self, gather_subset_info):
        """
        Gather StorageGRID node pge information for the given subset using REST APIs
        Input for REST APIs call : (api, data)
        return gathered_sg_info
        """

        api = gather_subset_info['api_call']
        data = {}
        # allow for passing in any additional rest api parameters
        if self.parameters.get('parameters'):
            for each in self.parameters['parameters']:
                data[each] = self.parameters['parameters'][each]

        gathered_sg_info, error = self.rest_api.get(api, data)

        if error:
            self.module.fail_json(msg=error)
        else:
            return gathered_sg_info

        return None

    def convert_subsets(self):
        """ Convert an info to the REST API """
        info_to_rest_mapping = {
            'pge_storage_configuration_networking': 'pge/storage-configuration/networking',
            'pge_bmc_config': 'pge/bmc-config',
            'pge_install_status': 'pge/install-status',
            'pge_networks': 'pge/networks',
            'pge_link_config': 'pge/link-config',
            'pge_dns': 'pge/dns',
            'pge_system_info': 'pge/system-info',
            'pge_system_config': 'pge/system-config',
            'pge_admin_connection': 'pge/admin-connection',
            'pge_ipmi_sensors': 'pge/ipmi-sensors',
            'pge_upgrade_status': 'pge/upgrade/status',
            'pge_debug_dump_addr_show': 'pge/debug/dump-addr-show',
            'pge_debug_dump_routes': 'pge/debug/dump-routes',
            'pge_debug_dump_bonding': 'pge/debug/dump-bonding',
            'pge_debug_dump_netlink': 'pge/debug/dump-netlink',
            'pge_debug_dump_bonding_raw': 'pge/debug/dump-bonding-raw',
            'pge_debug_dump_lldp_attributes': 'pge/debug/dump-lldp-attributes',
        }
        # Add rest API names as there info version, also make sure we don't add a duplicate.
        subsets = []
        for subset in self.parameters['gather_subset']:
            if subset in info_to_rest_mapping:
                if info_to_rest_mapping[subset] not in subsets:
                    subsets.append(info_to_rest_mapping[subset])
            else:
                if subset not in subsets:
                    subsets.append(subset)
        return subsets

    def apply(self):
        """ Perform pre-checks, call functions and exit """

        result_message = dict()

        # Defining gather_subset and appropriate api_call.
        get_sg_subset_info = {
            'pge/storage-configuration/networking': {
                'api_call': 'api/v2/storage-configuration/networking',
            },
            'pge/bmc-config': {
                'api_call': 'api/v2/bmc-config',
            },
            'pge/install-status': {
                'api_call': 'api/v2/install-status',
            },
            'pge/networks': {
                'api_call': 'api/v2/networks',
            },
            'pge/link-config': {
                'api_call': 'api/v2/link-config',
            },
            'pge/dns': {
                'api_call': 'api/v2/dns',
            },
            'pge/system-info': {
                'api_call': 'api/v2/system-info',
            },
            'pge/system-config': {
                'api_call': 'api/v2/system-config',
            },
            'pge/admin-connection': {
                'api_call': 'api/v2/admin-connection',
            },
            'pge/ipmi-sensors': {
                'api_call': 'api/v2/ipmi-sensors',
            },
            'pge/upgrade/status': {
                'api_call': 'api/v2/upgrade/status',
            },
            'pge/debug/dump-addr-show': {
                'api_call': 'api/v2/debug/dump-addr-show',
            },
            'pge/debug/dump-routes': {
                'api_call': 'api/v2/debug/dump-routes',
            },
            'pge/debug/dump-bonding': {
                'api_call': 'api/v2/debug/dump-bonding',
            },
            'pge/debug/dump-netlink': {
                'api_call': 'api/v2/debug/dump-netlink',
            },
            'pge/debug/dump-bonding-raw': {
                'api_call': 'api/v2/debug/dump-bonding-raw',
            },
            'pge/debug/dump-lldp-attributes': {
                'api_call': 'api/v2/debug/dump-lldp-attributes',
            },
        }

        if 'all' in self.parameters['gather_subset']:
            # If all in subset list, get the information of all subsets.
            self.parameters['gather_subset'] = sorted(get_sg_subset_info.keys())

        converted_subsets = self.convert_subsets()
        for subset in converted_subsets:
            try:
                # Verify whether the supported subset passed.
                specified_subset = get_sg_subset_info[subset]
            except KeyError:
                self.module.fail_json(msg="Specified subset %s not found, supported subsets are %s" %
                                      (subset, list(get_sg_subset_info.keys())))

            result_message[subset] = self.get_subset_info(specified_subset)

        self.module.exit_json(changed=False, sg_info=result_message)


def main():
    """ Main function """
    obj = NetAppSgGatherPgeInfo()
    obj.apply()


if __name__ == '__main__':
    main()
