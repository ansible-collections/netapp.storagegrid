# (c) 2026, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID PGE Ansible module: na_sg_pge_install """

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import sys
import json
import pytest

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_pge_install import (
    NetAppSgPgeInstall as pge_install_module,
)

if sys.version_info < (3, 11):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 3.11")

# REST API canned responses when mocking send_request
SRR = {
    "empty_good": ({"data": []}, None),
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "generic_error": (None, "Expected error"),
    "install_endpoint_gone": (
        None,
        {
            "text": "GET https://host/install/ does not match a valid endpoint.",
            "key": "error.405",
            "developerMessage": "Route does not match, double-check the URL."
        },
    ),
    "api_response_node_type_admin_node": (
        {
            "data": {
                "nodeType": "primary_admin"
            }
        },
        None,
    ),
    "api_response_node_type_non_admin_node": (
        {
            "data": {
                "nodeType": "storage"
            }
        },
        None,
    ),
    "api_response_monitor_install_admin_node": (
        {
            "data": {
                "complete": False,
                "failed": False,
                "logLines": [],
                "okToRedirect": True,
                "running": True,
                "started": True,
                "status": [
                    {
                        "errors": [],
                        "name": "Configure storage",
                        "state": "complete",
                        "steps": [
                            {
                                "message": None,
                                "name": "Evaluate local node storage",
                                "progress": 100,
                                "state": "complete"
                            },
                            {
                                "message": None,
                                "name": "Create local node storage",
                                "progress": 100,
                                "state": "skipped"
                            },
                            {
                                "message": None,
                                "name": "Map local node storage",
                                "progress": 100,
                                "state": "complete"
                            }
                        ]
                    },
                    {
                        "errors": [],
                        "name": "Install OS",
                        "state": "complete",
                        "steps": [
                            {
                                "message": None,
                                "name": "Obtain installer binaries",
                                "progress": 100,
                                "state": "complete"
                            },
                            {
                                "message": None,
                                "name": "Configure installer",
                                "progress": 100,
                                "state": "complete"
                            },
                            {
                                "message": None,
                                "name": "Install OS",
                                "progress": 100,
                                "state": "complete"
                            }
                        ]
                    },
                    {
                        "errors": [],
                        "name": "Install StorageGRID",
                        "state": "complete",
                        "steps": [
                            {
                                "message": None,
                                "name": "Install StorageGRID",
                                "progress": 100,
                                "state": "complete"
                            }
                        ]
                    },
                    {
                        "errors": [],
                        "name": "Finalize installation",
                        "state": "complete",
                        "steps": [
                            {
                                "message": None,
                                "name": "Prepare for bare metal",
                                "progress": 100,
                                "state": "complete"
                            },
                            {
                                "message": None,
                                "name": "Initiate bare metal reboot",
                                "progress": 100,
                                "state": "complete"
                            }
                        ]
                    },
                    {
                        "errors": [],
                        "name": "Load StorageGRID Installer",
                        "state": "running",
                        "steps": [
                            {
                                "endTime": None,
                                "message": "Do not refresh. You will be redirected when the installer is ready",
                                "name": "Starting StorageGRID Installer",
                                "progress": 50,
                                "state": "running"
                            }
                        ]
                    }
                ]
            }
        },
        None,
    ),
    "api_response_monitor_non_admin_node": (
        {
            "data": {
                "complete": False,
                "failed": False,
                "logLines": [
                    "2026-01-01T00:00:00Z: Approve this node on the Admin Node GMI to continue installation"
                ],
                "okToRedirect": False,
                "running": True,
                "started": True,
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


class TestPgeInstallModule(unittest.TestCase):
    """Unit Tests for na_sg_pge_install module"""

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

    def set_args_start_install(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "start_install": True,
                "validate_certs": False,
            }
        )

    def test_missing_required_args(self):
        """Test missing required arguments"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            pge_install_module()
        assert "missing required arguments" in str(exc.value)

    @patch('ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request')
    def test_start_na_sg_pge_install_admin_node_pass(self, mock_request):
        set_module_args(self.set_args_start_install())
        mock_request.side_effect = [
            SRR["api_response_monitor_install_admin_node"],
            SRR["api_response_node_type_admin_node"],
            SRR["install_endpoint_gone"],
            SRR["api_response_monitor_install_admin_node"],
            SRR["end_of_sequence"],
        ]
        my_obj = pge_install_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_start_na_sg_pge_install_admin_node_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch('ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request')
    def test_start_na_sg_pge_install_non_admin_node_pass(self, mock_request):
        set_module_args(self.set_args_start_install())
        mock_request.side_effect = [
            SRR["api_response_monitor_install_admin_node"],
            SRR["api_response_node_type_non_admin_node"],
            SRR["api_response_monitor_non_admin_node"],
            SRR["install_endpoint_gone"],
            SRR["end_of_sequence"],
        ]
        my_obj = pge_install_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_start_na_sg_pge_install_non_admin_node_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]
