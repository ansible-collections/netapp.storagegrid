#!/usr/bin/python

# (c) 2026, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" NetApp StorageGRID pge initial system setup using REST APIs """


from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: na_sg_pge_setup
short_description: NetApp StorageGRID PGE initial system setup.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg_pge
version_added: '21.17.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
  - Perform initial system setup for StorageGRID Pre-Grid Environment (PGE).
options:
  node_name:
    description:
      - Name of the node to be setup.
    type: str
  node_type:
    description:
      - The node type that will be used. Some appliance models do not support all node types.
    type: str
    choices: ['primary_admin', 'non_primary_admin', 'gateway', 'storage', 'data', 'metadata']
  raid_mode:
    description:
      - The RAID mode that will be used. Some appliance models do not support all modes.
    type: str
    choices: ['ddp', 'ddp16', 'raid1', 'raid6', 'raid5', 'mraida', 'mraidb', 'mraidc', 'mraidd',
              'mraide', 'mraidf', 'mraidg', 'mraidh', 'mraidi', 'mraidj']
  admin_target_ip:
    description:
      - The IP of the primary Admin Node.
    type: str
  discovery:
    description:
      - Whether or not to use primary Admin Node discovery. If this is set to true, the ip parameter will be ignored.
    type: bool
    default: True
"""

EXAMPLES = """
- name: Setup StorageGRID PGE configuration
  netapp.storagegrid.na_sg_pge_setup:
    node_name: "sg100-tme-01"
    node_type: "non_primary_admin"
    raid_mode: "raid1"

- name: Setup StorageGRID PGE primary admin node IP
  netapp.storagegrid.na_sg_pge_setup:
    admin_target_ip: "10.0.0.1"
    discovery: false
"""

RETURN = """
resp:
    description: Returns information about the StorageGRID PGE system setup.
    returned: success
    type: dict
    sample: {
        "compatibilityErrors": [],
        "connectionState": "ready",
        "detailMessage": "Connection validated at 2026-03-24T11:06:14.446304",
        "discoveredAddresses": [
            "10.0.0.1",
            "10.0.0.5",
            "10.0.0.7",
            "10.0.0.9",
            "10.0.0.11",
        ],
        "ip": "10.0.0.1",
        "storagegridRelease": "12.0.0-20250821.2204.150f19d",
        "storagegridVersion": "12.0.0",
        "useDiscovery": true
    }
"""

import time
from ansible.module_utils.basic import AnsibleModule
import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import PgeRestAPI


class NetAppSgPgeSetup(object):
    """ Class with update pge system setup """

    def __init__(self):
        """
        Parse arguments, setup variables, check parameters and ensure
        request module is installed.
        """
        self.argument_spec = netapp_utils.na_storagegrid_pge_argument_spec()
        self.argument_spec.update(
            dict(
                node_name=dict(type='str', required=False),
                node_type=dict(type='str', required=False, choices=['primary_admin', 'non_primary_admin', 'gateway', 'storage', 'data', 'metadata']),
                raid_mode=dict(type='str', required=False, choices=['ddp', 'ddp16', 'raid1', 'raid6', 'raid5', 'mraida', 'mraidb', 'mraidc', 'mraidd',
                                                                    'mraide', 'mraidf', 'mraidg', 'mraidh', 'mraidi', 'mraidj']),
                admin_target_ip=dict(type='str', required=False),
                discovery=dict(type='bool', required=False, default=True),
            )
        )

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        # set up variables
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.rest_api = PgeRestAPI(self.module)

        # Checking for the parameters passed and create new parameters list
        self.system_config = {}
        if self.parameters.get("node_name"):
            self.system_config["name"] = self.parameters["node_name"]
        if self.parameters.get("node_type"):
            self.system_config["nodeType"] = self.parameters["node_type"]
        if self.parameters.get("raid_mode"):
            self.system_config["raidMode"] = self.parameters["raid_mode"]

        self.admin_connection = {}
        if self.parameters.get("discovery") is not None:
            self.admin_connection["useDiscovery"] = self.parameters["discovery"]
        if self.parameters.get("admin_target_ip"):
            self.admin_connection["ip"] = self.parameters["admin_target_ip"]

    def get_system_config_info(self):
        """ Get the system configuration information for the storagegrid """
        api = "api/v2/system-config"
        response, error = self.rest_api.get(api)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def get_admin_node_connection_info(self):
        """ Get the admin node connection information for the storagegrid """
        api = "api/v2/admin-connection"
        response, error = self.rest_api.get(api)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def update_system_config_info(self):
        """ Update the system configuration information for the storagegrid """
        api = "api/v2/system-config"
        response, error = self.rest_api.put(api, data=self.system_config)

        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def update_admin_node_ip_info(self):
        """ Update the admin node IP information for the storagegrid """
        api = "api/v2/admin-connection"
        response, error = self.rest_api.put(api, data=self.admin_connection)
        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def apply(self):
        """ Perform pre-checks, call functions and exit """

        current_system_config = self.get_system_config_info()
        current_admin_node_info = self.get_admin_node_connection_info()

        modify_system_config = False
        modify_admin_node_info = False

        for key in ("name", "nodeType", "raidMode"):
            if self.system_config.get(key) and self.system_config[key] != current_system_config.get(key):
                modify_system_config = True

        if self.admin_connection.get("useDiscovery") is not None and self.admin_connection["useDiscovery"] != current_admin_node_info.get("useDiscovery"):
            modify_admin_node_info = True

        # Only compare ip when discovery is off, Here API resolves ip via discovery
        if self.parameters.get("discovery"):
            if not current_admin_node_info.get("useDiscovery") or not current_admin_node_info.get("ip"):
                modify_admin_node_info = True
            # If discovery is on and ip is passed, check if ip is in discoveredAddresses and differs from current ip
            elif self.admin_connection.get("ip"):
                discovered = current_admin_node_info.get("discoveredAddresses", [])
                if self.admin_connection["ip"] in discovered and self.admin_connection["ip"] != current_admin_node_info.get("ip"):
                    modify_admin_node_info = True

        elif self.admin_connection.get("ip") is not None and self.admin_connection["ip"] != current_admin_node_info.get("ip"):
            modify_admin_node_info = True

        if modify_system_config or modify_admin_node_info:
            self.na_helper.changed = True

        result_message = ""
        resp_data = {}
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if modify_system_config:
                    resp_data["system_config"] = self.update_system_config_info()
                if modify_admin_node_info:
                    self.update_admin_node_ip_info()
                    time.sleep(10)
                    updated_admin_node_info = self.get_admin_node_connection_info()
                    resp_data["admin_connection"] = updated_admin_node_info
                result_message = "StorageGRID PGE system setup updated successfully."

        self.module.exit_json(changed=self.na_helper.changed, msg=result_message, resp=resp_data)


def main():
    """ Main function """
    obj = NetAppSgPgeSetup()
    obj.apply()


if __name__ == '__main__':
    main()
