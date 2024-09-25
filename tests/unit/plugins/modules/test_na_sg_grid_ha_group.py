# (c) 2022, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Grid HA Group Ansible module: na_sg_grid_ha_group"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_ha_group import (
    SgGridHaGroup as grid_ha_group_module,
)

if sys.version_info < (3, 11):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 3.11")

# REST API canned responses when mocking send_request
SRR = {
    # common responses
    "empty_good": ({"data": []}, None),
    "not_found": (
        {"status": "error", "code": 404, "data": {}},
        {"key": "error.404"},
    ),
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "generic_error": (None, "Expected error"),
    "delete_good": (None, None),
    "update_good": (None, None),
    "version_114": ({"data": {"productVersion": "11.4.0-20200721.1338.d3969b3"}}, None),
    "version_116": ({"data": {"productVersion": "11.6.0-20211120.0301.850531e"}}, None),
    "ha_group_record": (
        {
            "data": {
                "id": "fbe724da-c941-439b-bb61-a536f6211ca9",
                "name": "ansible-ha-group",
                "description": None,
                "virtualIps": ["192.168.50.5"],
                "interfaces": [
                    {"nodeId": "0b1866ed-d6e7-41b4-815f-bf867348b76b", "interface": "ens256"},
                    {"nodeId": "7bb5bf05-a04c-4344-8abd-08c5c4048666", "interface": "ens256"},
                ],
                "gatewayCidr": "192.168.50.1/24",
            }
        },
        None,
    ),
    "ha_group_record_twovip": (
        {
            "data": {
                "id": "fbe724da-c941-439b-bb61-a536f6211ca9",
                "name": "ansible-ha-group",
                "description": "2 VIP HA Group",
                "virtualIps": ["192.168.50.5", "192.168.50.6"],
                "interfaces": [
                    {"nodeId": "0b1866ed-d6e7-41b4-815f-bf867348b76b", "interface": "ens256"},
                    {"nodeId": "7bb5bf05-a04c-4344-8abd-08c5c4048666", "interface": "ens256"},
                ],
                "gatewayCidr": "192.168.50.1/24",
            }
        },
        None,
    ),
    "ha_group_record_rename": (
        {
            "data": {
                "id": "fbe724da-c941-439b-bb61-a536f6211ca9",
                "name": "ansible-ha-group-rename",
                "description": None,
                "virtualIps": ["192.168.50.5"],
                "interfaces": [
                    {"nodeId": "0b1866ed-d6e7-41b4-815f-bf867348b76b", "interface": "ens256"},
                    {"nodeId": "7bb5bf05-a04c-4344-8abd-08c5c4048666", "interface": "ens256"},
                ],
                "gatewayCidr": "192.168.50.1/24",
            }
        },
        None,
    ),
    "ha_groups": (
        {
            "data": [
                {
                    "id": "c08e6dca-038d-4a05-9499-6fbd1e6a4c3e",
                    "name": "site1_primary",
                    "description": "test ha group",
                    "virtualIps": ["10.193.174.117"],
                    "interfaces": [
                        {
                            "nodeId": "0b1866ed-d6e7-41b4-815f-bf867348b76b",
                            "nodeName": "SITE1-ADM1",
                            "interface": "eth2",
                            "preferredMaster": True,
                        },
                        {
                            "nodeId": "970ad050-b68b-4aae-a94d-aef73f3095c4",
                            "nodeName": "SITE2-ADM1",
                            "interface": "eth2",
                        },
                    ],
                    "gatewayCidr": "192.168.14.1/24",
                },
                {
                    "id": "fbe724da-c941-439b-bb61-a536f6211ca9",
                    "name": "ansible-ha-group",
                    "description": None,
                    "virtualIps": ["192.168.50.5"],
                    "interfaces": [
                        {"nodeId": "0b1866ed-d6e7-41b4-815f-bf867348b76b", "interface": "ens256"},
                        {"nodeId": "7bb5bf05-a04c-4344-8abd-08c5c4048666", "interface": "ens256"},
                    ],
                    "gatewayCidr": "192.168.50.1/24",
                },
            ]
        },
        None,
    ),
    "node_health": (
        {
            "data": [
                {
                    "id": "0b1866ed-d6e7-41b4-815f-bf867348b76b",
                    "isPrimaryAdmin": True,
                    "name": "SITE1-ADM1",
                    "siteId": "ae56d06d-bd83-46bd-adce-77146b1d94bd",
                    "siteName": "SITE1",
                    "severity": "normal",
                    "state": "connected",
                    "type": "adminNode",
                },
                {
                    "id": "7bb5bf05-a04c-4344-8abd-08c5c4048666",
                    "isPrimaryAdmin": None,
                    "name": "SITE1-G1",
                    "siteId": "ae56d06d-bd83-46bd-adce-77146b1d94bd",
                    "siteName": "SITE1",
                    "severity": "normal",
                    "state": "connected",
                    "type": "apiGatewayNode",
                },
                {
                    "id": "970ad050-b68b-4aae-a94d-aef73f3095c4",
                    "isPrimaryAdmin": False,
                    "name": "SITE2-ADM1",
                    "siteId": "7c24002e-5157-43e9-83e5-02db9b265b02",
                    "siteName": "SITE2",
                    "severity": "normal",
                    "state": "connected",
                    "type": "adminNode",
                },
            ]
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


class TestMyModule(unittest.TestCase):
    """a group of related Unit Tests"""

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args_fail_check(self):
        return dict(
            {
                "gateway_cidr": "192.168.50.1/24",
                "virtual_ips": "192.168.50.5",
                "interfaces": [
                    {"node": "SITE1-ADM1", "interface": "ens256"},
                    {"node": "SITE1-G1", "interface": "ens256"},
                ],
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "state": "present",
                "name": "ansible-test-ha-group",
                "gateway_cidr": "192.168.50.1/24",
                "virtual_ips": "192.168.50.5",
                "interfaces": [
                    {"node": "SITE1-ADM1", "interface": "ens256"},
                    {"node": "SITE1-G1", "interface": "ens256"},
                ],
                "api_url": "https://gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_create_na_sg_grid_ha_group(self):
        return dict(
            {
                "state": "present",
                "name": "ansible-ha-group",
                "gateway_cidr": "192.168.50.1/24",
                "virtual_ips": "192.168.50.5",
                "interfaces": [
                    {"node": "SITE1-ADM1", "interface": "ens256"},
                    {"node": "SITE1-G1", "interface": "ens256"},
                ],
                "api_url": "https://gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_delete_na_sg_grid_ha_group(self):
        return dict(
            {
                "state": "absent",
                "name": "ansible-ha-group",
                "gateway_cidr": "192.168.50.1/24",
                "virtual_ips": "192.168.50.5",
                "interfaces": [
                    {"node": "SITE1-ADM1", "interface": "ens256"},
                    {"node": "SITE1-G1", "interface": "ens256"},
                ],
                "api_url": "https://gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_when_required_args_missing(self, mock_request):
        """required arguments are reported as errors"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            grid_ha_group_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_pass_when_required_args_present(self, mock_request):
        """required arguments are reported as errors"""
        mock_request.side_effect = [
            SRR["node_health"],  # get
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            grid_ha_group_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_pass_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_ha_group_pass(self, mock_request):
        set_module_args(self.set_args_create_na_sg_grid_ha_group())
        mock_request.side_effect = [
            SRR["node_health"],  # get
            SRR["empty_good"],  # get
            SRR["ha_group_record"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_ha_group_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_grid_ha_group_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_create_na_sg_grid_ha_group_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_ha_group()
        set_module_args(args)
        mock_request.side_effect = [
            SRR["node_health"],  # get
            SRR["ha_groups"],  # get
            SRR["ha_group_record"],  # get
            SRR["end_of_sequence"],
        ]
        my_obj = grid_ha_group_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_create_na_sg_grid_ha_group_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_ha_group_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_ha_group()
        args["description"] = "2 VIP HA Group"
        args["virtual_ips"] = ["192.168.50.5", "192.168.50.6"]
        set_module_args(args)
        mock_request.side_effect = [
            SRR["node_health"],  # get
            SRR["ha_groups"],  # get
            SRR["ha_group_record"],  # get
            SRR["ha_group_record_twovip"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_ha_group_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_ha_group_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_rename_na_sg_grid_ha_group_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_ha_group()
        args["ha_group_id"] = "fbe724da-c941-439b-bb61-a536f6211ca9"
        args["name"] = "ansible-ha-group-rename"
        set_module_args(args)
        mock_request.side_effect = [
            SRR["node_health"],  # get
            SRR["ha_group_record"],  # get
            SRR["ha_group_record_rename"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_ha_group_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_rename_na_sg_grid_ha_group_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_delete_na_sg_grid_ha_group_pass(self, mock_request):
        args = self.set_args_delete_na_sg_grid_ha_group()
        set_module_args(args)
        mock_request.side_effect = [
            SRR["ha_groups"],  # get
            SRR["ha_group_record"],  # get
            SRR["delete_good"],  # delete
            SRR["end_of_sequence"],
        ]
        my_obj = grid_ha_group_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_delete_na_sg_grid_ha_group_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_ha_group_bad_node_fail(self, mock_request):
        args = self.set_args_create_na_sg_grid_ha_group()
        args["interfaces"] = [{"node": "FakeNode", "interface": "eth0"}]
        set_module_args(args)
        mock_request.side_effect = [
            SRR["node_health"],  # get
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            grid_ha_group_module()
        print("Info: test_create_na_sg_grid_ha_group_bad_node_fail: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["failed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_ha_group_bad_ha_group_id_fail(self, mock_request):
        args = self.set_args_create_na_sg_grid_ha_group()
        args["ha_group_id"] = "ffffffff-ffff-aaaa-aaaa-000000000000"
        args["virtual_ips"] = "192.168.50.10"
        set_module_args(args)
        mock_request.side_effect = [
            SRR["node_health"],  # get
            SRR["not_found"],  # get
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj = grid_ha_group_module()
            my_obj.apply()
        print("Info: test_create_na_sg_grid_ha_group_bad_node_fail: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["failed"]
