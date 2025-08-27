#!/usr/bin/python

# (c) 2025, NetApp Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""NetApp StorageGRID - Manage Node Firewall"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.0",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
module: na_sg_grid_firewall
short_description: NetApp StorageGRID manage node firewall.
extends_documentation_fragment:
    - netapp.storagegrid.netapp.sg
version_added: '21.16.0'
author: NetApp Ansible Team (@vinaykus) <ng-ansibleteam@netapp.com>
description:
  - Create, update, or delete node firewall on NetApp StorageGRID.
options:
  state:
    description:
    - Whether the firewall should be present or absent.
    choices: ['present', 'absent']
    default: 'present'
    type: str
  id:
    description:
    - The node UUID or the default list ID.
    type: str
  blocked_udp_ports:
    description:
    - List of UDP ports to block for external communication.
    type: list
    elements: int
  blocked_tcp_ports:
    description:
    - List of TCP ports to block for external communication.
    type: list
    elements: int
  privileged_ips:
    description:
    - A list of privileged IP addresses, or subnets in CIDR notation.
    - Addresses in this list can access ports which are blocked for external communication.
    type: list
    elements: str
  grid_internal_access:
    description:
    - Whether to allow internal port access to the grid.
    type: bool
"""

EXAMPLES = """
- name: create list of blocked ports
  netapp.storagegrid.na_sg_grid_firewall:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    state: present
    id: "00000000-0000-0000-0000-000000000000"
    blocked_udp_ports: [68]
    blocked_tcp_ports: [22, 80]

- name: create list of privileged IP
  netapp.storagegrid.na_sg_grid_firewall:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    state: present
    id: "00000000-0000-0000-0000-000000000000"
    privileged_ips: ["192.168.1.1/32"]
    grid_internal_access: true

- name: create a firewall
  netapp.storagegrid.na_sg_grid_firewall:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    state: present
    id: "00000000-0000-0000-0000-000000000000"
    blocked_udp_ports: [68]
    blocked_tcp_ports: [22, 80]
    privileged_ips: ["192.168.1.1/32"]
    grid_internal_access: true

- name: delete a firewall
  netapp.storagegrid.na_sg_grid_firewall:
    api_url: "https://<storagegrid-endpoint-url>"
    auth_token: "storagegrid-auth-token"
    validate_certs: false
    state: absent
    id: "00000000-0000-0000-0000-000000000000"
"""

RETURN = """
resp:
    description: Returns the response from the StorageGRID API for firewall.
    returned: success
    type: dict
    sample: {
        "privileged_ip_info": {
            "id": "00000000-0000-0000-0000-000000000000",
            "privilegedIps": ["192.168.10.10", "10.19.10.0/24"],
            "gridInternalAccess": true
        },
        "blocked_port_info": {
            "id": "00000000-0000-0000-0000-000000000000",
            "tcpPorts": [2022, 22, 903],
            "udpPorts": [68]
        }
    }
"""

import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.storagegrid.plugins.module_utils.netapp import SGRestAPI


class SgFirewall(object):
    """
    Create, modify and delete Firewall for StorageGRID
    """

    def __init__(self):
        """
        Parse arguments, setup state variables,
        check parameters and ensure request module is installed
        """
        self.argument_spec = netapp_utils.na_storagegrid_host_argument_spec()
        self.argument_spec.update(
            dict(
                state=dict(type="str", choices=["present", "absent"], default="present"),
                id=dict(type="str", required=False),
                blocked_udp_ports=dict(type="list", elements="int", required=False),
                blocked_tcp_ports=dict(type="list", elements="int", required=False),
                privileged_ips=dict(type="list", elements="str", required=False),
                grid_internal_access=dict(type="bool", required=False),
            )
        )
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ("state", "present", ["id"]),
                ("state", "present", ["blocked_udp_ports", "blocked_tcp_ports", "privileged_ips", "grid_internal_access"], True)
            ],
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
        self.blocked_port_info = {}
        self.blocked_port_info["id"] = self.parameters["id"]
        if self.parameters.get("blocked_udp_ports") is not None:
            self.blocked_port_info["udpPorts"] = self.parameters["blocked_udp_ports"]
        if self.parameters.get("blocked_tcp_ports") is not None:
            self.blocked_port_info["tcpPorts"] = self.parameters["blocked_tcp_ports"]

        self.privileged_ips_info = {}
        self.privileged_ips_info["id"] = self.parameters["id"]
        if self.parameters.get("privileged_ips") is not None:
            self.privileged_ips_info["privilegedIps"] = self.parameters["privileged_ips"]
        if self.parameters.get("grid_internal_access") is not None:
            self.privileged_ips_info["gridInternalAccess"] = self.parameters["grid_internal_access"]

    def get_blocked_ports(self):
        ''' Get blocked ports list'''
        api = "api/v4/private/firewall-blocked-ports"
        response, error = self.rest_api.get(api)
        if error:
            self.module.fail_json(msg=error)
        # if blocked ports exists, return it, else none
        for blocked_port in response["data"]:
            if blocked_port["id"] == self.parameters["id"]:
                self.id = blocked_port["id"]
                return blocked_port
        return None

    def get_all_external_ports(self):
        ''' Get all external TCP and UDP ports '''
        api = "api/v4/private/firewall-external-ports"
        response, error = self.rest_api.get(api)
        if error:
            self.module.fail_json(msg=error)

        return response["data"]

    def create_blocked_port(self):
        ''' Create blocked port '''
        api = "api/v4/private/firewall-blocked-ports"
        response, error = self.rest_api.post(api, self.blocked_port_info)
        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def delete_blocked_port(self, blocked_id):
        ''' Delete blocked port '''
        api = "api/v4/private/firewall-blocked-ports/%s" % blocked_id
        response, error = self.rest_api.delete(api, None)
        if error:
            self.module.fail_json(msg=error)

    def update_blocked_port(self, blocked_id):
        ''' Update blocked port '''
        api = "api/v4/private/firewall-blocked-ports/%s" % blocked_id
        response, error = self.rest_api.put(api, self.blocked_port_info)
        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def get_privileged_ip(self):
        ''' Get privileged IPs '''
        api = "api/v4/private/firewall-privileged-ips"
        response, error = self.rest_api.get(api)
        if error:
            self.module.fail_json(msg=error)
        # if privileged IP exists, return it, else none
        for privileged_ips_id in response["data"]:
            if privileged_ips_id["id"] == self.parameters["id"]:
                self.id = privileged_ips_id["id"]
                return privileged_ips_id
        return None

    def create_privileged_ip(self):
        ''' Create privileged IP '''
        api = "api/v4/private/firewall-privileged-ips"
        response, error = self.rest_api.post(api, self.privileged_ips_info)
        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def update_privileged_ip(self, privileged_ips_id):
        ''' Update privileged IP '''
        api = "api/v4/private/firewall-privileged-ips/%s" % privileged_ips_id
        response, error = self.rest_api.put(api, self.privileged_ips_info)
        if error:
            self.module.fail_json(msg=error)
        else:
            return response["data"]

    def delete_privileged_ip(self, privileged_ips_id):
        ''' Delete privileged IP '''
        api = "api/v4/private/firewall-privileged-ips/%s" % privileged_ips_id
        response, error = self.rest_api.delete(api, None)
        if error:
            self.module.fail_json(msg=error)

    def check_if_tcp_udp_ports_present(self):
        ''' Check if user passed tcp/udp ports are present in external ports '''
        all_external_ports = self.get_all_external_ports()
        if self.parameters.get("blocked_tcp_ports") is not None:
            for port in self.parameters["blocked_tcp_ports"]:
                if port not in all_external_ports["externalTcpPorts"]:
                    self.module.fail_json(msg="TCP port %s is not a valid external port." % port)
        if self.parameters.get("blocked_udp_ports") is not None:
            for port in self.parameters["blocked_udp_ports"]:
                if port not in all_external_ports["externalUdpPorts"]:
                    self.module.fail_json(msg="UDP port %s is not a valid external port." % port)

    def apply(self):
        ''' Apply firewall changes '''

        blocked_ports = self.get_blocked_ports()
        privileged_ips = self.get_privileged_ip()

        # check blocked_ports and privileged_ips and prepare firewall_info
        if blocked_ports is None and privileged_ips is None:
            firewall_info = None
        elif blocked_ports is None:
            firewall_info = privileged_ips.copy()
        elif privileged_ips is None:
            firewall_info = blocked_ports.copy()
        else:
            # If both exist, merge them
            firewall_info = {**blocked_ports, **privileged_ips}

        # case1: blocked_ports exists, privileged_ips does not, but user wants to add privileged_ips
        # In this case, privileged_ips will be created and blocked_ports will be overridden (updated)
        if blocked_ports and not privileged_ips and (self.parameters.get("privileged_ips") or self.parameters.get("grid_internal_access")):
            firewall_info = None
        # case2: privileged_ips exists, blocked_ports does not, but user wants to add blocked_ports
        if privileged_ips and not blocked_ports and (self.parameters.get("blocked_tcp_ports") or self.parameters.get("blocked_udp_ports")):
            firewall_info = None

        cd_action = self.na_helper.get_cd_action(firewall_info, self.parameters)

        if cd_action is None and self.parameters["state"] == "present":
            # let's see if we need to update parameters
            blocked_ports_modify = False
            privileged_ips_modify = False

            blocked_ports_modify = self.na_helper.get_modified_attributes(blocked_ports, self.blocked_port_info)
            privileged_ips_modify = self.na_helper.get_modified_attributes(privileged_ips, self.privileged_ips_info)

        result_message = ""
        resp_data = {}
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == "create":
                    created_privileged_ip = False
                    created_blocked_port = False
                    self.check_if_tcp_udp_ports_present()
                    # Check what needs to be created
                    if blocked_ports and not privileged_ips:
                        resp_data["privileged_ip_info"] = self.create_privileged_ip()
                        created_privileged_ip = True
                    if privileged_ips and not blocked_ports:
                        resp_data["blocked_port_info"] = self.create_blocked_port()
                        created_blocked_port = True

                    # If neither exists, create both
                    if not blocked_ports and not privileged_ips:
                        if self.parameters.get("privileged_ips") or self.parameters.get("grid_internal_access"):
                            resp_data["privileged_ip_info"] = self.create_privileged_ip()
                            created_privileged_ip = True
                        if self.parameters.get("blocked_tcp_ports") or self.parameters.get("blocked_udp_ports"):
                            resp_data["blocked_port_info"] = self.create_blocked_port()
                            created_blocked_port = True

                    # Handle updates for existing resources when creating new ones
                    # If privileged IPs exist and user provided new privileged IP params, update it
                    if privileged_ips and (self.parameters.get("privileged_ips") or self.parameters.get("grid_internal_access")):
                        resp_data["privileged_ip_info"] = self.update_privileged_ip(privileged_ips["id"])
                        created_privileged_ip = True
                    # If blocked ports exist and user provided new blocked port params, update it
                    if blocked_ports and (self.parameters.get("blocked_tcp_ports") or self.parameters.get("blocked_udp_ports")):
                        resp_data["blocked_port_info"] = self.update_blocked_port(blocked_ports["id"])
                        created_blocked_port = True
                    # Set result message based on what was created
                    if created_privileged_ip and created_blocked_port:
                        result_message = "Firewall created successfully."
                    elif created_privileged_ip:
                        result_message = "Privileged IP created successfully."
                    elif created_blocked_port:
                        result_message = "Blocked port created successfully."
                    if not created_privileged_ip and not created_blocked_port:
                        self.na_helper.changed = False
                elif cd_action == "delete":
                    self.delete_blocked_port(self.id)
                    self.delete_privileged_ip(self.id)
                    result_message = "Firewall deleted successfully."
                elif blocked_ports_modify and privileged_ips_modify:
                    self.check_if_tcp_udp_ports_present()
                    resp_data["privileged_ip_info"] = self.update_privileged_ip(self.id)
                    resp_data["blocked_port_info"] = self.update_blocked_port(self.id)
                    result_message = "Firewall updated successfully."
                elif blocked_ports_modify:
                    self.check_if_tcp_udp_ports_present()
                    resp_data = self.update_blocked_port(self.id)
                    result_message = "Blocked port updated successfully."
                elif privileged_ips_modify:
                    resp_data = self.update_privileged_ip(self.id)
                    result_message = "Privileged IP updated successfully."

        self.module.exit_json(changed=self.na_helper.changed, msg=result_message, resp=resp_data)


def main():
    """
    Main function
    """
    na_sg_grid_firewall = SgFirewall()
    na_sg_grid_firewall.apply()


if __name__ == "__main__":
    main()
