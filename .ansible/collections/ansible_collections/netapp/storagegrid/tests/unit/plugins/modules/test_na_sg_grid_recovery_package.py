# (c) 2025, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Recovery Package Ansible module: na_sg_grid_recovery_package """

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from unittest.mock import Mock
import tempfile
import os
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_recovery_package import (
    SgGridRecoveryPackage as recovery_package_module,
)
if sys.version_info < (3, 11):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 3.11")
# Create mocked response with headers
mock_response = Mock()
mock_response.content = b"dummy zip content"
tmp_dir = tempfile.gettempdir()
mock_response.headers = {
    "Content-Disposition": f'attachment; filename="{os.path.join(tmp_dir, "tp_reco.zip")}"',
    "content-type": "application/zip"
}
mock_response.status_code = 200
mock_response.ok = True
# REST API canned responses when mocking send_request
SRR = {
    "empty_good": ({"data": []}, None),
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "generic_error": (None, "Expected error"),
    "delete_good": ({"code": 204}, None),
    "version_114": ({"data": {"productVersion": "11.4.0-20200721.1338.d3969b3"}}, None),
    "api_response_existing_recovery_package": (mock_response, None)
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


class TestRecoveryPackageModule(unittest.TestCase):
    """Unit Tests for na_sg_grid_recovery_package module"""

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args_fail_check(self):
        return dict(
            {
                "state": "present",
                "passphrase": "test_passphrase",
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "state": "present",
                "validate_certs": False,
                "passphrase": "test_passphrase",
            }
        )

    def set_args_create_recovery_package(self):
        return dict(
            {
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "state": "present",
                "validate_certs": False,
                "passphrase": "test_passphrase",
            }
        )

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_when_required_args_missing(self, mock_request):
        """Test failure when required arguments are missing"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            recovery_package_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_succeed_when_required_args_present(self, mock_request):
        """required arguments are reported as errors"""
        mock_request.side_effect = [
            SRR["version_114"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            recovery_package_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_fail_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_recovery_package_pass(self, mock_request):
        set_module_args(self.set_args_create_recovery_package())
        mock_request.side_effect = [
            SRR["empty_good"],  # get
            SRR["api_response_existing_recovery_package"],  # Create recovery package
            SRR["end_of_sequence"],
        ]
        my_obj = recovery_package_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_grid_recovery_package_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]
        assert "tp_reco.zip" in str(exc.value.args[0]["resp"])
