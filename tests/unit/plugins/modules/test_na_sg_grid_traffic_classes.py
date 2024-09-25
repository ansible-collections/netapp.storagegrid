# (c) 2022, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Grid HA Group Ansible module: na_sg_grid_traffic_classes"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_traffic_classes import (
    SgGridTrafficClasses as grid_traffic_classes_module,
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
    "traffic_class_record": (
        {
            "data": {
                "id": "6b2946e6-7fed-40d0-9262-8e922580aba7",
                "name": "ansible-test-traffic-class",
                "description": "Ansible Test",
                "matchers": [
                    {"type": "cidr", "inverse": False, "members": ["192.168.50.0/24"]},
                    {"type": "bucket", "inverse": False, "members": ["ansible-test1", "ansible-test2"]},
                ],
                "limits": [],
            }
        },
        None,
    ),
    "traffic_class_record_updated": (
        {
            "data": {
                "id": "6b2946e6-7fed-40d0-9262-8e922580aba7",
                "name": "ansible-test-traffic-class",
                "description": "Ansible Test",
                "matchers": [
                    {"type": "cidr", "inverse": False, "members": ["192.168.50.0/24"]},
                    {"type": "bucket", "inverse": False, "members": ["ansible-test1", "ansible-test2"]},
                ],
                "limits": [{"type": "aggregateBandwidthIn", "value": 888888}],
            }
        },
        None,
    ),
    "traffic_class_record_rename": (
        {
            "data": {
                "id": "6b2946e6-7fed-40d0-9262-8e922580aba7",
                "name": "ansible-test-traffic-class-rename",
                "description": "Ansible Test",
                "matchers": [
                    {"type": "cidr", "inverse": False, "members": ["192.168.50.0/24"]},
                    {"type": "bucket", "inverse": False, "members": ["ansible-test1", "ansible-test2"]},
                ],
                "limits": [],
            }
        },
        None,
    ),
    "traffic_classes": (
        {
            "data": [
                {
                    "id": "6b2946e6-7fed-40d0-9262-8e922580aba7",
                    "name": "ansible-test-traffic-class",
                    "description": "Ansible Test",
                },
                {
                    "id": "531e6be1-e9b1-4010-bb79-03437c7c13d2",
                    "name": "policy-test1",
                    "description": "First test policy",
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
                "matchers": [
                    {"type": "bucket", "members": ["ansible-test1", "ansible-test2"]},
                    {"type": "cidr", "members": ["192.168.50.0/24"]},
                ],
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "state": "present",
                "name": "ansible-test-traffic-class",
                "matchers": [
                    {"type": "bucket", "members": ["ansible-test1", "ansible-test2"]},
                    {"type": "cidr", "members": ["192.168.50.0/24"]},
                ],
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_create_na_sg_grid_traffic_class(self):
        return dict(
            {
                "state": "present",
                "name": "ansible-test-traffic-class",
                "description": "Ansible Test",
                "matchers": [
                    {"type": "bucket", "members": ["ansible-test1", "ansible-test2"]},
                    {"type": "cidr", "members": ["192.168.50.0/24"]},
                ],
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_delete_na_sg_grid_traffic_class(self):
        return dict(
            {
                "state": "absent",
                "name": "ansible-test-traffic-class",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_when_required_args_missing(self, mock_request):
        """required arguments are reported as errors"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            grid_traffic_classes_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_pass_when_required_args_present(self, mock_request):
        """required arguments are reported as errors"""
        mock_request.side_effect = [
            SRR["node_health"],  # get
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            grid_traffic_classes_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_pass_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_traffic_class_pass(self, mock_request):
        set_module_args(self.set_args_create_na_sg_grid_traffic_class())
        mock_request.side_effect = [
            SRR["empty_good"],  # get
            SRR["traffic_class_record"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_traffic_classes_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_grid_traffic_class_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_create_na_sg_grid_traffic_class_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_traffic_class()
        set_module_args(args)
        mock_request.side_effect = [
            SRR["traffic_classes"],  # get
            SRR["traffic_class_record"],  # get
            SRR["end_of_sequence"],
        ]
        my_obj = grid_traffic_classes_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_create_na_sg_grid_traffic_class_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_traffic_class_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_traffic_class()
        args["description"] = "Ansible Test with Limit"
        args["limits"] = [{"type": "aggregateBandwidthIn", "value": 888888}]
        set_module_args(args)
        mock_request.side_effect = [
            SRR["traffic_classes"],  # get
            SRR["traffic_class_record"],  # get
            SRR["traffic_class_record_updated"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_traffic_classes_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_traffic_class_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_rename_na_sg_grid_traffic_class_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_traffic_class()
        args["policy_id"] = "6b2946e6-7fed-40d0-9262-8e922580aba7"
        args["name"] = "ansible-test-traffic-class-rename"
        set_module_args(args)
        mock_request.side_effect = [
            SRR["traffic_class_record"],  # get
            SRR["traffic_class_record_rename"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_traffic_classes_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_rename_na_sg_grid_traffic_class_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_delete_na_sg_grid_traffic_class_pass(self, mock_request):
        args = self.set_args_delete_na_sg_grid_traffic_class()
        set_module_args(args)
        mock_request.side_effect = [
            SRR["traffic_classes"],  # get
            SRR["traffic_class_record"],  # get
            SRR["delete_good"],  # delete
            SRR["end_of_sequence"],
        ]
        my_obj = grid_traffic_classes_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_delete_na_sg_grid_traffic_class_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_traffic_class_bad_policy_id_fail(self, mock_request):
        args = self.set_args_create_na_sg_grid_traffic_class()
        args["policy_id"] = "ffffffff-ffff-aaaa-aaaa-000000000000"
        args["description"] = "Bad ID"
        set_module_args(args)
        mock_request.side_effect = [
            SRR["not_found"],  # get
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj = grid_traffic_classes_module()
            my_obj.apply()
        print("Info: test_update_na_sg_grid_traffic_class_bad_policy_id_fail: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["failed"]
