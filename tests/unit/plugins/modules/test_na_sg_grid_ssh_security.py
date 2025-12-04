# (c) 2025, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID SSH Security Ansible module: na_sg_grid_ssh_security """

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import sys
import pytest

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_ssh_security import (
    SgSSHsecurity as ssh_security_module,
)

if sys.version_info < (3, 11):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 3.11")

# REST API canned responses when mocking send_request
SRR = {
    "empty_good": ({"data": []}, None),
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "generic_error": (None, "Expected error"),
    "delete_good": ({"code": 204}, None),
    "version_120": ({"data": {"productVersion": "12.0.0-2020721.1338.d3969b3"}}, None),
    "api_response_existing_ssh_security_succeeded": (
        {
            "data": {
                "allowExternalAccess": False
            }
        },
        None,
    ),
    "api_response_creation_ssh_security_succeeded": (
        {
            "data": {
                "allowExternalAccess": True
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


class TestSSHsecurityModule(unittest.TestCase):
    """Unit Tests for na_sg_grid_ssh_security module"""

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args_fail_check(self):
        return dict(
            {
                "validate_certs": False
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "auth_token": "storagegrid-auth-token",
                "state": "present",
                "validate_certs": False
            }
        )

    def set_args_create_ssh_security(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "auth_token": "storagegrid-auth-token",
                "state": "present",
                "validate_certs": False,
                "allow_external_access": True
            }
        )

    def test_missing_required_args(self):
        """Test missing required arguments"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            ssh_security_module()
        assert "missing required arguments" in str(exc.value)

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_ssh_security_pass(self, mock_request):
        set_module_args(self.set_args_create_ssh_security())
        mock_request.side_effect = [
            SRR["version_120"],
            SRR["api_response_existing_ssh_security_succeeded"],  # Check if SSH security exists
            SRR["api_response_creation_ssh_security_succeeded"],  # Create new SSH security
            SRR["end_of_sequence"],
        ]
        my_obj = ssh_security_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_grid_ssh_security_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_create_na_sg_grid_ssh_security_pass(self, mock_request):
        set_module_args(self.set_args_create_ssh_security())
        mock_request.side_effect = [
            SRR["version_120"],
            SRR["api_response_creation_ssh_security_succeeded"],
            SRR["api_response_existing_ssh_security_succeeded"],  # SSH security already exists
            SRR["end_of_sequence"],
        ]
        my_obj = ssh_security_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_create_na_sg_grid_ssh_security_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]
