# (c) 2020, NetApp, Inc
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
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_org_container import (
    SgOrgContainer as org_container_module,
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
    "version_116": ({"data": {"productVersion": "11.6.0-20211120.0301.850531e"}}, None),
    "global_compliance_disabled": (
        {
            "data": {
                "complianceEnabled": False,
            }
        },
        None,
    ),
    "global_compliance_enabled": (
        {
            "data": {
                "complianceEnabled": True,
            }
        },
        None,
    ),
    "org_containers": (
        {"data": [{"name": "testbucket", "creationTime": "2020-02-04T12:43:50.777Z", "region": "us-east-1"}]},
        None,
    ),
    "org_container_record": (
        {"data": {"name": "testbucket", "creationTime": "2020-02-04T12:43:50.777Z", "region": "us-east-1"}},
        None,
    ),
    "org_container_objectlock_record": (
        {
            "data": {
                "name": "testbucket",
                "creationTime": "2020-02-04T12:43:50.777Z",
                "region": "us-east-1",
                "s3ObjectLock": {"enabled": True},
            }
        },
        None,
    ),
    "org_container_record_update": (
        {
            "data": {
                "name": "testbucket",
                "creationTime": "2020-02-04T12:43:50.777Z",
                "region": "us-east-1",
                "compliance": {"autoDelete": False, "legalHold": False},
            }
        },
        None,
    ),
    "org_container_versioning_disabled": ({"data": {"versioningEnabled": False, "versioningSuspended": False}}, None),
    "org_container_versioning_enabled": ({"data": {"versioningEnabled": True, "versioningSuspended": False}}, None),
    "org_container_versioning_suspended": ({"data": {"versioningEnabled": False, "versioningSuspended": True}}, None),
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
            {"name": "testbucket", "auth_token": "01234567-5678-9abc-78de-9fgabc123def", "validate_certs": False}
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "state": "present",
                "name": "testbucket",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_create_na_sg_org_container(self):
        return dict(
            {
                "state": "present",
                "name": "testbucket",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_delete_na_sg_org_container(self):
        return dict(
            {
                "state": "absent",
                "name": "testbucket",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_when_required_args_missing(self, mock_request):
        """required arguments are reported as errors"""
        mock_request.side_effect = [
            SRR["version_114"],
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            org_container_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_when_required_args_present(self, mock_request):
        """required arguments are reported as errors"""
        mock_request.side_effect = [
            SRR["version_114"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            org_container_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_fail_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_org_container_pass(self, mock_request):
        set_module_args(self.set_args_create_na_sg_org_container())
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["empty_good"],  # get
            SRR["org_container_record"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = org_container_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_org_container_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_create_na_sg_org_container_pass(self, mock_request):
        set_module_args(self.set_args_create_na_sg_org_container())
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["org_containers"],  # get
            SRR["end_of_sequence"],
        ]
        my_obj = org_container_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_create_na_sg_org_container_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_org_container_pass(self, mock_request):
        args = self.set_args_create_na_sg_org_container()
        args["compliance"] = {"auto_delete": False, "legal_hold": False}
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["org_containers"],  # get
            SRR["org_container_record_update"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = org_container_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_org_container_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_delete_na_sg_org_container_pass(self, mock_request):
        set_module_args(self.set_args_delete_na_sg_org_container())
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["org_containers"],  # get
            SRR["delete_good"],  # delete
            SRR["end_of_sequence"],
        ]
        my_obj = org_container_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_delete_na_sg_org_container_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_minimum_version_not_met_object_lock(self, mock_request):
        args = self.set_args_create_na_sg_org_container()
        args["s3_object_lock_enabled"] = True
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],  # get
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            org_container_module()
        print("Info: test_module_fail_minimum_version_not_met_object_lock: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_org_container_objectlock_global_compliance_fail(self, mock_request):
        args = self.set_args_create_na_sg_org_container()
        args["s3_object_lock_enabled"] = True
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_116"],
            SRR["empty_good"],  # get
            SRR["global_compliance_disabled"],  # get
        ]
        my_obj = org_container_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_org_container_objectlock_global_compliance_fail: %s" % repr(exc.value.args[0]))

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_org_container_objectlock_pass(self, mock_request):
        set_module_args(self.set_args_create_na_sg_org_container())
        mock_request.side_effect = [
            SRR["version_116"],
            SRR["empty_good"],  # get
            SRR["global_compliance_enabled"],  # get
            SRR["org_container_objectlock_record"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = org_container_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_org_container_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_minimum_version_not_met_versioning(self, mock_request):
        args = self.set_args_create_na_sg_org_container()
        args["bucket_versioning_enabled"] = True
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],  # get
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            org_container_module()
        print("Info: test_module_fail_minimum_version_not_met_versioning: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_org_container_with_versioning_pass(self, mock_request):
        args = self.set_args_create_na_sg_org_container()
        args["bucket_versioning_enabled"] = True
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_116"],
            SRR["empty_good"],  # get
            SRR["org_container_record"],  # post
            SRR["org_container_versioning_enabled"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = org_container_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_org_container_with_versioning_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_org_container_enable_versioning_pass(self, mock_request):
        args = self.set_args_create_na_sg_org_container()
        args["bucket_versioning_enabled"] = True
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_116"],
            SRR["org_containers"],  # get
            SRR["org_container_versioning_disabled"],  # get
            SRR["org_container_versioning_enabled"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = org_container_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_org_container_enable_versioning_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]
