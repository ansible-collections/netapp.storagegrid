# (c) 2026, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID PGE Ansible module: na_sg_reset_node_to_pge """

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import sys
import json
import pytest

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_reset_node_to_pge import (
    NetAppSgPgeReset as pge_reset_module,
)

if sys.version_info < (3, 11):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 3.11")

# REST API canned responses when mocking send_request
SRR = {
    "empty_good": ({"data": []}, None),
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "generic_error": (None, "Expected error"),
    "install_status_installed": (
        {"data": {"started": True, "running": True, "complete": False}},
        None,
    ),
    "install_status_fresh": (
        {"data": {"started": False, "running": False, "complete": False}},
        None,
    ),
}
SSH_REBOOT_RESP = {
    "host": "storagegrid-endpoint-url",
    "command": "sudo -S -p '' bash -lc 'yes | sgareinstall'",
    "exit_status": 255,
    "stdout": "",
    "stderr": "",
    "rebooted": True,
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


class TestResetNodeToPgeModule(unittest.TestCase):
    """Unit Tests for na_sg_reset_node_to_pge module"""

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

    def set_args_reset_primary_admin_node(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "validate_certs": False,
                "ssh_password": "my_ssh_password",
            }
        )

    def test_missing_required_args(self):
        """Test missing required arguments"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            pge_reset_module()
        assert "missing required arguments" in str(exc.value)

    @patch('ansible_collections.netapp.storagegrid.plugins.modules.na_sg_reset_node_to_pge.PgeSSH.run')
    @patch('ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request')
    def test_run_na_sg_reset_node_to_pge_pass(self, mock_request, mock_ssh_run):
        """Node needs a reset -> sgareinstall runs and reports changed."""
        set_module_args(self.set_args_reset_primary_admin_node())
        mock_request.side_effect = [
            SRR["install_status_installed"],
            SRR["end_of_sequence"],
        ]
        mock_ssh_run.return_value = SSH_REBOOT_RESP
        my_obj = pge_reset_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_run_na_sg_reset_node_to_pge_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]
        mock_ssh_run.assert_called_once()

    @patch('ansible_collections.netapp.storagegrid.plugins.modules.na_sg_reset_node_to_pge.PgeSSH.run')
    @patch('ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request')
    def test_run_na_sg_reset_node_to_pge_idempotent(self, mock_request, mock_ssh_run):
        """Node already in a fresh PGE state"""
        set_module_args(self.set_args_reset_primary_admin_node())
        mock_request.side_effect = [
            SRR["install_status_fresh"],
            SRR["end_of_sequence"],
        ]
        my_obj = pge_reset_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_run_na_sg_reset_node_to_pge_idempotent: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]
        mock_ssh_run.assert_not_called()
