# (c) 2026, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID PGE Ansible module: na_sg_pge_setup """

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import sys
import json
import pytest

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_pge_setup import (
    NetAppSgPgeSetup as pge_setup_module,
)

if sys.version_info < (3, 11):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 3.11")

# REST API canned responses when mocking send_request
SRR = {
    "empty_good": ({"data": []}, None),
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "generic_error": (None, "Expected error"),
    "api_response_existing_system_config": (
        {
            "data": {
                "driveSizesArray": [
                    {
                        "driveSize": "960 GB",
                        "driveType": "ssd",
                        "numDrives": 2
                    }
                ],
                "name": "sg100-tme-05",
                "nodeType": "non_primary_admin",
                "raidMode": "raid1",
                "rawCapacityArray": [],
                "supportedModes": [
                    "raid1"
                ],
                "supportedNodeTypes": [
                    "primary_admin",
                    "non_primary_admin",
                    "gateway"
                ]
            }
        },
        None,
    ),
    "api_response_existing_admin_connection": (
        {
            "data": {
                "compatibilityErrors": [],
                "connectionState": "ready",
                "detailMessage": "Connection validated at 2026-03-26T09:14:49.773059",
                "discoveredAddresses": [
                    "10.193.204.21",
                    "10.193.204.153",
                    "10.193.204.162",
                    "10.193.204.32",
                    "10.193.204.43",
                    "10.193.204.79"
                ],
                "ip": "10.193.204.43",
                "storagegridRelease": "12.0.0-20250821.2204.150f19d",
                "storagegridVersion": "12.0.0",
                "useDiscovery": True
            }
        },
        None,
    ),
    "api_response_system_config_updated": (
        {
            "data": {
                "driveSizesArray": [
                    {
                        "driveSize": "960 GB",
                        "driveType": "ssd",
                        "numDrives": 2
                    }
                ],
                "name": "sg100-tme-01",
                "nodeType": "non_primary_admin",
                "raidMode": "raid1",
                "rawCapacityArray": [],
                "supportedModes": [
                    "raid1"
                ],
                "supportedNodeTypes": [
                    "primary_admin",
                    "non_primary_admin",
                    "gateway"
                ]
            }
        },
        None,
    ),
    "api_response_admin_connection_updated": (
        {
            "data": {
                "compatibilityErrors": [],
                "connectionState": "ready",
                "detailMessage": "Connection validated at 2026-03-26T09:14:49.773059",
                "discoveredAddresses": [
                    "10.193.204.21",
                    "10.193.204.153",
                    "10.193.204.162",
                    "10.193.204.32",
                    "10.193.204.43",
                    "10.193.204.79"
                ],
                "ip": "10.193.204.32",
                "storagegridRelease": "12.0.0-20250821.2204.150f19d",
                "storagegridVersion": "12.0.0",
                "useDiscovery": True
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


class TestPgeSetupModule(unittest.TestCase):
    """Unit Tests for na_sg_pge_setup module"""

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args_fail_check(self):
        return dict(
            {
                "validate_certs": False,
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                'api_url': 'sgmi.example.com'
            }
        )

    def set_args_update_system_config(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "node_name": "sg100-tme-01",
                "node_type": "non_primary_admin",
                "raid_mode": "raid1",
                "validate_certs": False,
            }
        )

    def set_args_update_admin_connection_ip(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "validate_certs": False,
                "admin_target_ip": "10.193.204.32",
                "discovery": True
            }
        )

    def test_missing_required_args(self):
        """Test missing required arguments"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            pge_setup_module()
        assert "missing required arguments" in str(exc.value)

    @patch('ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request')
    def test_update_na_sg_pge_setup_system_config_pass(self, mock_request):
        set_module_args(self.set_args_update_system_config())
        mock_request.side_effect = [
            SRR["api_response_existing_system_config"],  # Get current system config
            SRR["api_response_existing_system_config"],  # Get current system config
            SRR["api_response_system_config_updated"],  # Update system config
            SRR["api_response_existing_system_config"],  # Get current system config
            SRR["api_response_existing_system_config"],  # Get current system config
            SRR["end_of_sequence"],
        ]
        my_obj = pge_setup_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_pge_setup_system_config_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request")
    def test_update_na_sg_pge_setup_admin_connection_ip_pass(self, mock_request):
        args = self.set_args_update_admin_connection_ip()
        set_module_args(args)
        mock_request.side_effect = [
            SRR["api_response_existing_admin_connection"],  # Get current admin connection info
            SRR["api_response_existing_admin_connection"],  # Get current admin connection info
            SRR["api_response_admin_connection_updated"],  # Update admin connection info
            SRR["api_response_existing_admin_connection"],  # Get current admin connection info
            SRR["end_of_sequence"],
        ]
        my_obj = pge_setup_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_pge_setup_admin_connection_ip_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]
