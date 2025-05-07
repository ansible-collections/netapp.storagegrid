# (c) 2025, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests for NetApp StorageGRID Hotfix Ansible module: na_sg_grid_hotfix"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import sys
import pytest

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from unittest.mock import mock_open
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_hotfix import (
    SgHotfix as grid_hotfix_module,
)

if sys.version_info < (3, 11):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 3.11")

# REST API canned responses when mocking send_request
SRR = {
    "empty_good": ({"data": []}, None),
    "version_114": ({"data": {"productVersion": "11.4.0-20200721.1338.d3969b3"}}, None),
    "version_119": ({"data": {"productVersion": "11.9.0-20204721.1338.d3459b3"}}, None),
    "hotfix_in_progress": ({"data": {"inProgress": True, "validationError": None, "uploadType": "hotfix"}}, None),
    "hotfix_not_in_progress": ({"data": {"inProgress": False, "validationError": None, "uploadType": "hotfix"}}, None),
    "hotfix_validation_error": ({"data": {"inProgress": True, "validationError": "Failed to validate installer file"}}, None),
    "hotfix_completed": ({"data": {"inProgress": False, "validationError": None, "uploadType": "hotfix"}}, None),
    "hotfix_timeout_error": (None, "Timeout waiting for hotfix to complete"),
    "hotfix_upload_success": ({"status_code": 202}, None),
    "hotfix_node_update_success": ({"status_code": 204}, None),
    "hotfix_upload_error": ({"status_code": 400, "error": "Failed to upload hotfix file"}, None),
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "hotfix_current_details": ({
        "data": {
            "type": "hotfix",
            "inProgress": False,
            "percent": 0,
            "updatedNodeCount": 0,
            "validationError": None,
        }
    }, None),
    "hotfix_current_node": ({
        "data": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": "DC1-S1",
                "type": "storageNode",
                "progress": {
                    "stage": "upgrading",
                    "percent": 100,
                    "error": None
                },
                "applicable": True,
                "queued": False,
                "done": True
            }
        ]
    }, None),
    "hotfix_node_details": ({
        "data": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": "DC1-S1",
                "type": "storageNode",
                "progress": {
                    "stage": "upgrading",
                    "percent": 12,
                    "error": "Failed to restart node services"
                },
                "applicable": True,
                "queued": False,
                "done": True
            },
            {
                "id": "023000000-0000-0000-0000-000000000000",
                "name": "DC1-S2",
                "type": "storageNode",
                "progress": {
                    "stage": "upgrading",
                    "percent": 12,
                    "error": "Failed to restart node services"
                },
                "applicable": True,
                "queued": False,
                "done": True
            }
        ]
    }, None),
}


def set_module_args(args):
    """Prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({"ANSIBLE_MODULE_ARGS": args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):  # pylint: disable=unused-argument
    """Function to patch over exit_json; package return data into an exception"""
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):  # pylint: disable=unused-argument
    """Function to patch over fail_json; package return data into an exception"""
    kwargs["failed"] = True
    raise AnsibleFailJson(kwargs)


class TestMyModule(unittest.TestCase):
    """a group of related Unit Tests"""

    def setUp(self):
        self.mock_module_helper = patch.multiple(
            basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json
        )
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args_fail_check(self):
        return dict(
            {
                "state": "present",
                "passphrase": "test_passphrase",
                "timeout": 10
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
                "state": "present",
                "passphrase": "test_passphrase",
                "type": "hotfix",
                "timeout": 10
            }
        )

    def set_default_args_upload_file_pass_check(self):
        return dict(
            {
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
                "state": "present",
                "file_path": "/tmp/hotfix_file",
                "passphrase": "test_passphrase",
                "type": "hotfix"
            }
        )

    def set_default_args_node_schedule_pass_check(self):
        return dict(
            {
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
                "state": "absent",
                "passphrase": "test_passphrase",
                "type": "hotfix",
            }
        )

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_when_required_args_missing(self, mock_request):
        """Test failure when required arguments are missing"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            grid_hotfix_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_succeed_when_required_args_present(self, mock_request):
        """required arguments are reported as errors"""
        mock_request.side_effect = [
            SRR["version_114"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            grid_hotfix_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_fail_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("builtins.open", new_callable=mock_open, read_data="dummy data")
    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_hotfix_apply_sg_119_pass_check(self, mock_request, mock_open_file):
        """Test apply hotfix on SG 11.9"""
        mock_request.side_effect = [
            SRR["version_119"],
            SRR["hotfix_current_details"],
            SRR["hotfix_upload_success"],
            SRR["hotfix_not_in_progress"],
            SRR["hotfix_current_details"],
            SRR["hotfix_current_node"],
            SRR["hotfix_node_update_success"],
            SRR["hotfix_current_details"],
            SRR["hotfix_current_node"],
            SRR["hotfix_completed"],
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_upload_file_pass_check())
            my_obj = grid_hotfix_module()
            my_obj.apply()
        print("Info: test_hotfix_apply_sg_119_pass_check: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("builtins.open", new_callable=mock_open, read_data="dummy data")
    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_hotfix_file_upload_failure(self, mock_request, mock_open_file):
        """Test failure during hotfix upload"""
        mock_request.side_effect = [
            SRR["version_119"],
            SRR["hotfix_upload_error"]
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_upload_file_pass_check())
            my_obj = grid_hotfix_module()
            my_obj.upload_hotfix_software_update_file("/tmp/hotfix_file")
        assert "Failed to upload hotfix file" in str(exc.value)

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_hotfix_apply_timeout(self, mock_request):
        """Test timeout during hotfix apply"""
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["hotfix_current_details"],
            SRR["hotfix_node_details"],
            SRR["hotfix_timeout_error"]
        ]
        hotfix_current_node = {
            "id": "00000000-0000-0000-0000-000000000000",
            "name": "DC1-S1",
            "progress": {
                "stage": "upgrading",
                "percent": 75,
                "error": None
            }
        }
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            my_obj = grid_hotfix_module()
            my_obj.wait_for_hotfix_to_complete(hotfix_current_node)
        assert "Failed to restart node services" in str(exc.value)

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_hotfix_apply_fail_with_file_path_sg_114(self, mock_request):
        """Test failure when file_path is provided for SG 11.4"""
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["hotfix_upload_success"]
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_upload_file_pass_check())
            my_obj = grid_hotfix_module()
            my_obj.apply()
        assert "msg': 'Error: flie_path requires StorageGRID 11.9 or later.  Found: 11.4." in str(exc.value)

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_hotfix_apply_remove_node_queue(self, mock_request):
        """Test remove of node from hotfix queue"""
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["hotfix_in_progress"],
            SRR["hotfix_node_details"],
            SRR["hotfix_node_update_success"],
            SRR["hotfix_node_details"],
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_node_schedule_pass_check())
            my_obj = grid_hotfix_module()
            my_obj.apply()
        assert exc.value.args[0]["changed"]
