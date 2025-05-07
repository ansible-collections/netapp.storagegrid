# (c) 2025, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Org Container Ansible module: na_sg_org_container"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_ilm_rule import (
    ILM_rule as grid_ilm_rule_module,
)

if sys.version_info < (3, 11):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 3.11")

# REST API canned responses when mocking send_request
SRR = {
    # common responses
    "empty_good": ({"data": []}, None),
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "delete_good": (None, None),
    "version_114": ({"data": {"productVersion": "11.4.0-20200721.1338.d3969b3"}}, None),
    "api_response_creation_succeeded": (
        {
            "data": {
                "displayName": "rule1",
                "placements": [
                    {
                        "retention": {"after": 0, "duration": 30},
                        "replicated": [{"poolId": "p1", "copies": 2}],
                    }
                ],
                "id": "r1",
            }
        },
        None,
    ),
    "api_response_existing_ilm_rule": (
        {
            "data": [
                {
                    "displayName": "rule1",
                    "ingestBehavior": "balanced",
                    "placements": [
                        {
                            "retention": {"after": 0, "duration": 30},
                            "replicated": [{"poolId": "p1", "copies": 2}],
                        }
                    ],
                    "id": "r1",
                    "referenceTime": "ingestTime",
                }
            ]
        },
        None,
    ),
    "api_response_existing_ilm_rule_updated": (
        {
            "data": {
                "displayName": "rule1",
                "ingestBehavior": "balanced",
                "placements": [
                    {
                        "retention": {"after": 0, "duration": 30},
                        "replicated": [{"poolId": "p2", "copies": 3}],
                    }
                ],
                "referenceTime": "ingestTime",
                "id": "r1",
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
        return dict({"name": "rule1", "auth_token": "01234567-5678-9abc-78de-9fgabc123def", "validate_certs": False})  # missing "api_url"

    def set_default_args_pass_check(self):
        return dict(
            {
                "state": "present",
                "name": "rule1",
                "placements": [
                    {
                        "retention": {"after": 0, "duration": 30},
                        "replicated": [{"poolId": "p1", "copies": 2}],
                    }
                ],
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_create_na_sg_grid_ilm_rule(self):
        return dict(
            {
                "state": "present",
                "name": "rule1",
                "placements": [
                    {
                        "retention": {"after": 0, "duration": 30},
                        "replicated": [{"poolId": "p1", "copies": 2}],
                    }
                ],
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_delete_na_sg_grid_ilm_rule(self):
        return dict(
            {
                "state": "absent",
                "name": "rule1",
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
            grid_ilm_rule_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_succeed_when_required_args_present(self, mock_request):
        """required arguments are reported as errors"""
        mock_request.side_effect = [
            SRR["version_114"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            grid_ilm_rule_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_fail_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_ilm_rule_pass(self, mock_request):
        set_module_args(self.set_args_create_na_sg_grid_ilm_rule())
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["empty_good"],  # get
            SRR["api_response_creation_succeeded"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_ilm_rule_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_org_container_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_create_na_sg_grid_ilm_rule_pass(self, mock_request):
        set_module_args(self.set_args_create_na_sg_grid_ilm_rule())
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["api_response_existing_ilm_rule"],  # get
            SRR["end_of_sequence"],
        ]
        my_obj = grid_ilm_rule_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_create_na_sg_grid_ilm_rule_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_ilm_rule_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_ilm_rule()
        args.update(
            {
                "placements": [
                    {
                        "retention": {"after": 0, "duration": 30},
                        "replicated": [{"poolId": "p2", "copies": 3}],
                    }
                ]
            }
        )
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["api_response_existing_ilm_rule"],  # get
            SRR["api_response_existing_ilm_rule_updated"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_ilm_rule_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_org_container_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_delete_na_sg_grid_ilm_rule_pass(self, mock_request):
        set_module_args(self.set_args_delete_na_sg_grid_ilm_rule())
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["api_response_existing_ilm_rule"],  # get
            SRR["delete_good"],  # delete
            SRR["end_of_sequence"],
        ]
        my_obj = grid_ilm_rule_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_delete_na_sg_grid_ilm_rule_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]
