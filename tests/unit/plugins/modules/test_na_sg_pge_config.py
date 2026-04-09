# (c) 2026, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID PGE Ansible module: na_sg_pge_config """

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch, mock_open
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_pge_config import (
    NetAppSgPgeConfig as grid_pge_config_module,
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
    "api_response_pge_config": (
        {
            "data": {
                "jsonFileName": None,
                "logMessages": None,
                "nodeNames": None,
                "selectedNode": None,
                "updateConfigStatus": "awaiting-upload"
            }
        },
        None,
    ),
    "api_response_pge_config_error": (
        {
            "data": {
                "jsonFileName": None,
                "logMessages": None,
                "nodeNames": None,
                "selectedNode": None,
                "updateConfigStatus": "json-error"
            }
        },
        None,
    ),
    "api_response_pge_config_uploaded": (
        {
            "data": {
                "jsonFileName": "config.json",
                "logMessages": None,
                "nodeNames": ["node1"],
                "selectedNode": None,
                "updateConfigStatus": "ready"
            }
        },
        None,
    ),
    "api_response_pge_config_apply": (
        {
            "data": {
                "jsonFileName": "config.json",
                "logMessages": None,
                "nodeNames": ["node1"],
                "selectedNode": "node1",
                "updateConfigStatus": "applying"
            }
        },
        None,
    ),
    "api_response_pge_config_apply_completed": (
        {
            "data": {
                "jsonFileName": "config.json",
                "nodeNames": ["node1"],
                "updateConfigStatus": "complete",
                "logMessages": "2026/01/10 19:41:55: Performing GET on /api/versions...... Received 200\n"
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


class TestMyModule(unittest.TestCase):
    """a group of related Unit Tests"""

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args_fail_check(self):
        return dict({"validate_certs": False})  # missing "api_url"

    def set_default_args_pass_check(self):
        return dict(
            {
                "api_url": "gmi.example.com",
                "validate_certs": False,
            }
        )

    def set_args_reset_na_sg_pge_config_pass_check(self):
        return dict(
            {
                "api_url": "gmi.example.com",
                "validate_certs": False,
                "reset_config": True
            }
        )

    def set_args_apply_na_sg_pge_config_pass_check(self):
        return dict(
            {
                "api_url": "gmi.example.com",
                "validate_certs": False,
                "reset_config": False,
                "file_path": "/path/to/configuration/config.json",
                "selected_node": "node1"
            }
        )

    def set_args_upload_na_sg_pge_config_pass_check(self):
        return dict(
            {
                "api_url": "gmi.example.com",
                "validate_certs": False,
                "reset_config": False,
                "file_path": "/path/to/configuration/config.json"
            }
        )

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request")
    def test_module_fail_when_required_args_missing(self, mock_request):
        """required arguments are reported as errors"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            grid_pge_config_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request")
    def test_module_succeed_when_required_args_present(self, mock_request):
        """required arguments are present"""
        mock_request.side_effect = []
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            grid_pge_config_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_succeed_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request")
    def test_reset_na_sg_pge_config_pass(self, mock_request):
        args = self.set_args_reset_na_sg_pge_config_pass_check()
        set_module_args(args)
        mock_request.side_effect = [
            SRR["api_response_pge_config_uploaded"],  # get
            SRR["api_response_pge_config"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_pge_config_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_reset_na_sg_pge_config_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.modules.na_sg_pge_config.NetAppSgPgeConfig.upload_update_config_file")
    @patch("builtins.open", new_callable=mock_open, read_data="dummy data")
    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request")
    def test_apply_na_sg_pge_config_pass(self, mock_request, mock_file, mock_upload):
        args = self.set_args_apply_na_sg_pge_config_pass_check()
        set_module_args(args)

        # Mock the upload to return a valid config status
        mock_upload.return_value = {
            'updateConfigStatus': 'complete',
            'jsonFileName': 'config.json'
        }

        mock_request.side_effect = [
            SRR["api_response_pge_config_uploaded"],  # get
            SRR["api_response_pge_config_apply"],  # apply
            SRR["api_response_pge_config_apply_completed"],  # get
            SRR["end_of_sequence"],
        ]
        my_obj = grid_pge_config_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_apply_na_sg_pge_config_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("builtins.open", new_callable=mock_open, read_data="dummy data")
    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request")
    def test_upload_na_sg_pge_config_error_pass(self, mock_request, mock_file):
        args = self.set_args_upload_na_sg_pge_config_pass_check()
        set_module_args(args)

        mock_request.side_effect = [
            SRR["api_response_pge_config"],  # get
            SRR["api_response_pge_config_error"],  # get error
            SRR["end_of_sequence"],
        ]
        my_obj = grid_pge_config_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        print("Info: test_upload_na_sg_pge_config_error_pass: %s" % repr(exc.value.args[0]))
        assert "uploaded config file has JSON error" in str(exc.value)
