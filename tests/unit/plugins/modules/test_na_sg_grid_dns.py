# (c) 2020, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID DNS Ansible module: na_sg_grid_dns"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

import ansible_collections.netapp.storagegrid.plugins.module_utils.netapp as netapp_utils
from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_dns import (
    SgGridDns as grid_dns_module,
)

if not netapp_utils.HAS_REQUESTS and sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 2.6 as requests is not available")

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
    "delete_good": ({"code": 204}, None),
    "no_dns_servers": (
        {"data": []},
        None,
    ),
    "dns_servers": (
        {"data": ["10.11.12.5", "10.11.12.6"]},
        None,
    ),
    "add_dns_servers": (
        {"data": ["10.11.12.5", "10.11.12.6", "10.11.12.7"]},
        None,
    ),
    "remove_dns_servers": (
        {"data": ["10.11.12.5"]},
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
                "dns_servers": "10.11.12.8",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "state": "present",
                "dns_servers": "10.11.12.8",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_set_na_sg_grid_dns_servers(self):
        return dict(
            {
                "state": "present",
                "dns_servers": "10.11.12.5,10.11.12.6",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_add_na_sg_grid_dns_server(self):
        return dict(
            {
                "state": "present",
                "dns_servers": "10.11.12.5,10.11.12.6,10.11.12.7",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_remove_na_sg_grid_dns_server(self):
        return dict(
            {
                "state": "present",
                "dns_servers": "10.11.12.5",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def test_module_fail_when_required_args_missing(self):
        """required arguments are reported as errors"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            grid_dns_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    def test_module_fail_when_required_args_present(self):
        """required arguments are reported as errors"""
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            grid_dns_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_fail_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_set_na_sg_grid_dns_servers_pass(self, mock_request):
        set_module_args(self.set_args_set_na_sg_grid_dns_servers())
        my_obj = grid_dns_module()
        mock_request.side_effect = [
            SRR["no_dns_servers"],  # get
            SRR["dns_servers"],  # post
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_set_na_sg_grid_dns_servers_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_set_na_sg_grid_dns_servers_pass(self, mock_request):
        set_module_args(self.set_args_set_na_sg_grid_dns_servers())
        my_obj = grid_dns_module()
        mock_request.side_effect = [
            SRR["dns_servers"],  # get
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_set_na_sg_grid_dns_servers_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_add_na_sg_grid_dns_servers_pass(self, mock_request):
        set_module_args(self.set_args_add_na_sg_grid_dns_server())
        my_obj = grid_dns_module()
        mock_request.side_effect = [
            SRR["dns_servers"],  # get
            SRR["add_dns_servers"],  # post
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_add_na_sg_grid_dns_servers_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_remove_na_sg_grid_dns_servers_pass(self, mock_request):
        set_module_args(self.set_args_remove_na_sg_grid_dns_server())
        my_obj = grid_dns_module()
        mock_request.side_effect = [
            SRR["dns_servers"],  # get
            SRR["remove_dns_servers"],  # post
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_remove_na_sg_grid_dns_servers_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]
