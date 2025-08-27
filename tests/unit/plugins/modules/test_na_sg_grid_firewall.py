# (c) 2025, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Firewall Ansible module: na_sg_grid_firewall """

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_firewall import (
    SgFirewall as firewall_module,
)

if sys.version_info < (3, 11):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 3.11")

# REST API canned responses when mocking send_request
SRR = {
    "empty_good": ({"data": []}, None),
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "generic_error": (None, "Expected error"),
    "delete_good": ({"code": 204}, None),
    "version_114": ({"data": {"productVersion": "11.4.0-20200721.1338.d3969b3"}}, None),
    "api_response_external_ports": (
        {
            "data": {
                "externalTcpPorts": [22, 80, 111, 903, 2022, 8080, 8443],
                "externalUdpPorts": [53, 68, 123]
            }
        },
        None,
    ),
    "api_response_existing_blocked_port": (
        {
            "data": [
                {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "tcpPorts": [
                        22,
                        2022
                    ],
                    "udpPorts": [
                        68
                    ]
                }
            ]
        },
        None,
    ),
    "api_response_blocked_port_creation_succeeded": (
        {
            "data": {
                "id": "00000000-0000-0000-0000-000000000000",
                "tcpPorts": [
                    2022,
                    22
                ],
                "udpPorts": [
                    68
                ]
            }
        },
        None,
    ),
    "api_response_port_blocked_updated": (
        {
            "data": {
                "id": "00000000-0000-0000-0000-000000000000",
                "tcpPorts": [
                    2022,
                    22,
                    111
                ],
                "udpPorts": [
                    68
                ]
            }
        },
        None,
    ),
    "api_response_existing_privileged_ip": (
        {
            "data": [
                {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "privilegedIps": [
                        "192.168.1.100"
                    ],
                    "gridInternalAccess": False
                }
            ]
        },
        None,
    ),
    "api_response_privileged_ip_creation_succeeded": (
        {
            "data": {
                "id": "00000000-0000-0000-0000-000000000000",
                "privilegedIps": [
                    "192.168.1.100"
                ],
                "gridInternalAccess": False
            }
        },
        None,
    ),
    "api_response_privileged_ip_updated": (
        {
            "data": {
                "id": "00000000-0000-0000-0000-000000000000",
                "privilegedIps": [
                    "192.168.1.100",
                    "10.19.10.0/24"
                ],
                "gridInternalAccess": True

            }
        },
        None,
    ),
}


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({"ANSIBLE_MODULE_ARGS": args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""

    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""

    pass


def exit_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over exit_json; package return data into an exception"""
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over fail_json; package return data into an exception"""
    kwargs["failed"] = True
    raise AnsibleFailJson(kwargs)


class TestFirewallModule(unittest.TestCase):
    """Unit Tests for na_sg_grid_firewall module"""

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args_fail_check(self):
        return dict(
            {
                "validate_certs": False,
                "state": "present",
                "blocked_tcp_ports": [2022, 22],
                "blocked_udp_ports": [68],
                "privileged_ips": ["192.168.1.100"],
                "grid_internal_access": False
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "auth_token": "storagegrid-auth-token",
                "state": "present",
                "validate_certs": False,
                "id": "00000000-0000-0000-0000-000000000000",
                "blocked_tcp_ports": [2022, 22],
                "blocked_udp_ports": [68],
                "privileged_ips": ["192.168.1.100"],
                "grid_internal_access": False
            }
        )

    def set_args_create_blocked_port(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "auth_token": "storagegrid-auth-token",
                "state": "present",
                "validate_certs": False,
                "id": "00000000-0000-0000-0000-000000000000",
                "blocked_tcp_ports": [2022, 22],
                "blocked_udp_ports": [68]
            }
        )

    def set_args_create_privileged_ip(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "auth_token": "storagegrid-auth-token",
                "state": "present",
                "validate_certs": False,
                "id": "00000000-0000-0000-0000-000000000000",
                "privileged_ips": ["192.168.1.100"],
                "grid_internal_access": False
            }
        )

    def set_args_create_firewall(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "auth_token": "storagegrid-auth-token",
                "state": "present",
                "validate_certs": False,
                "id": "00000000-0000-0000-0000-000000000000",
                "blocked_tcp_ports": [2022, 22],
                "blocked_udp_ports": [68],
                "privileged_ips": ["192.168.1.100"],
                "grid_internal_access": False
            }
        )

    def set_args_delete_firewall(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "auth_token": "storagegrid-auth-token",
                "state": "absent",
                "validate_certs": False,
                "id": "00000000-0000-0000-0000-000000000000",
            }
        )

    def test_missing_required_args(self):
        """Test missing required arguments"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            firewall_module()
        assert "missing required arguments" in str(exc.value)

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_firewall_blocked_ports_pass(self, mock_request):
        set_module_args(self.set_args_create_blocked_port())
        mock_request.side_effect = [
            SRR["version_114"],  # Get version
            SRR["empty_good"],  # Check if blocked ports exists
            SRR["empty_good"],  # Check if privileged IPs exists
            SRR["api_response_external_ports"],  # Get external ports
            SRR["api_response_blocked_port_creation_succeeded"],  # Create blocked ports
            SRR["end_of_sequence"],
        ]
        my_obj = firewall_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_grid_firewall_blocked_ports_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_create_na_sg_grid_firewall_blocked_ports_pass(self, mock_request):
        set_module_args(self.set_args_create_blocked_port())
        mock_request.side_effect = [
            SRR["version_114"],  # Get version
            SRR["api_response_existing_blocked_port"],  # Get existing blocked ports
            SRR["empty_good"],  # Check if privileged IPs exists
            SRR["api_response_blocked_port_creation_succeeded"],  # Blocked ports already exist.
            SRR["end_of_sequence"],
        ]
        my_obj = firewall_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_create_na_sg_grid_firewall_blocked_ports_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_firewall_blocked_ports_pass(self, mock_request):
        args = self.set_args_create_blocked_port()
        args["blocked_udp_ports"] = [68]
        args["blocked_tcp_ports"] = [2022, 22, 111]
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],  # Get version
            SRR["api_response_existing_blocked_port"],  # Get existing blocked ports
            SRR["empty_good"],  # Check if privileged IPs exists
            SRR["api_response_external_ports"],  # Get external ports
            SRR["api_response_port_blocked_updated"],  # Update blocked ports
            SRR["end_of_sequence"],
        ]
        my_obj = firewall_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_firewall_blocked_ports_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_firewall_privileged_ip_pass(self, mock_request):
        set_module_args(self.set_args_create_privileged_ip())
        mock_request.side_effect = [
            SRR["version_114"],  # Get version
            SRR["empty_good"],  # Check if blocked ports exists
            SRR["empty_good"],  # Check if privileged IPs exists
            SRR["api_response_external_ports"],  # Get external ports
            SRR["api_response_privileged_ip_creation_succeeded"],  # Create privileged IP
            SRR["end_of_sequence"],
        ]
        my_obj = firewall_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_create_na_sg_grid_firewall_privileged_ip_pass(self, mock_request):
        set_module_args(self.set_args_create_privileged_ip())
        mock_request.side_effect = [
            SRR["version_114"],  # Get version
            SRR["empty_good"],  # Check if blocked ports exists
            SRR["api_response_existing_privileged_ip"],  # Get existing privileged IPs
            SRR["api_response_blocked_port_creation_succeeded"],  # Blocked ports already exist.
            SRR["end_of_sequence"],
        ]
        my_obj = firewall_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_create_na_sg_grid_firewall_privileged_ip_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_firewall_privileged_ip_pass(self, mock_request):
        args = self.set_args_create_privileged_ip()
        args["privileged_ips"] = ["192.168.10.10", "10.19.10.0/24"]
        args["grid_internal_access"] = True
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],  # Get version
            SRR["empty_good"],  # Check if blocked ports exists
            SRR["api_response_existing_privileged_ip"],  # Get existing privileged IPs
            SRR["api_response_blocked_port_creation_succeeded"],  # Blocked ports already exist.
            SRR["end_of_sequence"],
        ]
        my_obj = firewall_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_firewall_privileged_ip_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_delete_na_sg_grid_firewall_pass(self, mock_request):
        set_module_args(self.set_args_delete_firewall())
        mock_request.side_effect = [
            SRR["version_114"],  # Get version
            SRR["api_response_existing_blocked_port"],  # Get existing blocked ports
            SRR["api_response_existing_privileged_ip"],  # Get existing privileged IPs
            SRR["delete_good"],  # Delete blocked ports
            SRR["delete_good"],  # Delete privileged IPs
            SRR["end_of_sequence"],
        ]
        my_obj = firewall_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_delete_na_sg_grid_firewall_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_firewall_blocked_ports_privileged_ips_pass(self, mock_request):
        set_module_args(self.set_args_create_firewall())
        mock_request.side_effect = [
            SRR["version_114"],  # Get version
            SRR["empty_good"],  # Check if blocked ports exists
            SRR["empty_good"],  # Check if privileged IPs exists
            SRR["api_response_external_ports"],  # Get existing blocked ports
            SRR["api_response_blocked_port_creation_succeeded"],  # Create blocked port
            SRR["api_response_privileged_ip_creation_succeeded"],  # Create privileged IP
            SRR["end_of_sequence"],
        ]
        my_obj = firewall_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]["changed"]
