# (c) 2025, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Autosupport Ansible module: na_sg_grid_autosupport"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_autosupport import (
    SgAutosupport as grid_autosupport_module,
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
    "version_114": ({"data": {"productVersion": "11.4.0-20200721.1338.d3969b3"}}, None),
    "api_response_existing_autosupport": (
        {
            "data": {
                "weeklyEnable": False,
                "transport": "HTTPS",
                "aodEnable": False,
                "eventEnable": True,
                "destinations": [
                    {
                        "hostname": "asup.example.com",
                        "port": 443
                    }
                ],
                "certEnable": True,
                "availableUpdatesEnable": True
            }
        },
        None,
    ),
    "api_response_existing_autosupport_updated": (
        {
            "data": {
                "weeklyEnable": True,
                "transport": "HTTPS",
                "aodEnable": False,
                "eventEnable": True,
                "destinations": [
                    {
                        "hostname": "asup.example.com",
                        "port": 445
                    }
                ],
                "certEnable": True,
                "availableUpdatesEnable": True
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
        return dict({"weeklyEnable": True, "transport": "HTTPS", "aodEnable": False, "eventEnable": True, })

    def set_default_args_pass_check(self):
        return dict(
            {
                "state": "present",
                "weekly_enable": False,
                "transport": "HTTP",
                "aod_enable": True,
                "event_enable": False,
                "destinations": [
                    {
                        "hostname": "asup.example.com",
                        "port": 444
                    }
                ],
                "cert_enable": True,
                "available_updates_enable": False,
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_update_na_sg_grid_autosupport_pass_check(self):
        return dict(
            {
                "state": "present",
                "weekly_enable": False,
                "transport": "HTTP",
                "aod_enable": True,
                "event_enable": False,
                "destinations": [
                    {
                        "hostname": "asup.example.com",
                        "port": 444
                    }
                ],
                "cert_enable": True,
                "available_updates_enable": False,
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
            grid_autosupport_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_succeed_when_required_args_present(self, mock_request):
        """required arguments are present"""
        mock_request.side_effect = [
            SRR["version_114"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            grid_autosupport_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_succeed_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_autosupport_pass(self, mock_request):
        args = self.set_args_update_na_sg_grid_autosupport_pass_check()
        args["weekly_enable"] = True
        args["transport"] = "HTTPS"
        set_module_args(args)
        mock_request.side_effect = [
            # SRR["version_114"],
            SRR["api_response_existing_autosupport"],  # get
            SRR["api_response_existing_autosupport_updated"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_autosupport_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_autosupport_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_update_na_sg_grid_autosupport_pass(self, mock_request):
        set_module_args(self.set_args_update_na_sg_grid_autosupport_pass_check())
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["api_response_existing_autosupport"],  # get
            SRR["end_of_sequence"],
        ]
        my_obj = grid_autosupport_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_update_na_sg_grid_autosupport_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]
