# (c) 2020, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Tenant Ansible module: na_sg_grid_account"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_account import (
    SgGridAccount as grid_account_module,
)

if sys.version_info < (3, 11):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 3.11")


# REST API canned responses when mocking send_request
SRR = {
    # common responses
    "empty_good": ({"data": []}, None),
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "generic_error": (None, "Expected error"),
    "delete_good": ({"code": 204}, None),
    "version_114": ({"data": {"productVersion": "11.4.0-20200721.1338.d3969b3"}}, None),
    "version_116": ({"data": {"productVersion": "11.6.0-20211120.0301.850531e"}}, None),
    "version_119": ({"data": {"productVersion": "11.9.0-20241190.0301.431531e"}}, None),
    "pw_change_good": ({"code": 204}, None),
    "grid_accounts": (
        {
            "data": [
                {
                    "name": "TestTenantAccount",
                    "description": "Ansible Test",
                    "capabilities": ["management", "s3"],
                    "policy": {
                        "useAccountIdentitySource": True,
                        "allowPlatformServices": False,
                        "quotaObjectBytes": None,
                    },
                    "id": "12345678901234567890",
                }
            ]
        },
        None,
    ),
    "grid_account_record": (
        {
            "data": {
                "name": "TestTenantAccount",
                "description": "Ansible Test",
                "capabilities": ["management", "s3"],
                "policy": {
                    "useAccountIdentitySource": True,
                    "allowPlatformServices": False,
                    "quotaObjectBytes": None,
                },
                "id": "12345678901234567890",
            }
        },
        None,
    ),
    "grid_account_record_with_quota": (
        {
            "data": {
                "name": "TestTenantAccount",
                "description": "Update Account",
                "capabilities": ["management", "s3"],
                "policy": {
                    "useAccountIdentitySource": True,
                    "allowPlatformServices": False,
                    "quotaObjectBytes": 10737418240,
                },
                "id": "12345678901234567890",
            }
        },
        None,
    ),
    "grid_account_record_update_quota": (
        {
            "data": {
                "name": "TestTenantAccount",
                "capabilities": ["management", "s3"],
                "policy": {
                    "useAccountIdentitySource": True,
                    "allowPlatformServices": False,
                    "quotaObjectBytes": 21474836480,
                },
                "id": "12345678901234567890",
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
        return dict(
            {
                "name": "TestTenantAccount",
                "protocol": "s3",
                "management": True,
                "use_own_identity_source": True,
                "allow_platform_services": False,
                "password": "abc123",
                "quota_size": 0,
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "state": "present",
                "name": "TestTenantAccount",
                "protocol": "s3",
                "management": True,
                "use_own_identity_source": True,
                "allow_platform_services": False,
                "password": "abc123",
                "quota_size": 0,
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_create_na_sg_grid_account(self):
        return dict(
            {
                "state": "present",
                "name": "TestTenantAccount",
                "description": "Ansible Test",
                "protocol": "s3",
                "management": True,
                "use_own_identity_source": True,
                "allow_platform_services": False,
                "password": "abc123",
                "quota_size": 0,
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_delete_na_sg_grid_account(self):
        return dict(
            {
                "state": "absent",
                "name": "TestTenantAccount",
                "protocol": "s3",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def test_module_fail_when_required_args_missing(self):
        """required arguments are reported as errors"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            grid_account_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_when_required_args_present(self, mock_request):
        """required arguments are reported as errors"""
        mock_request.side_effect = [
            SRR["version_114"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            grid_account_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_fail_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_account_pass(self, mock_request):
        set_module_args(self.set_args_create_na_sg_grid_account())
        mock_request.side_effect = [
            SRR["version_114"],  # get
            SRR["empty_good"],  # get
            SRR["grid_accounts"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_account_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_tenant_account_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_create_na_sg_grid_account_pass(self, mock_request):
        set_module_args(self.set_args_create_na_sg_grid_account())
        mock_request.side_effect = [
            SRR["version_114"],  # get
            SRR["grid_accounts"],  # get id
            SRR["grid_account_record"],  # get account
            SRR["end_of_sequence"],
        ]
        my_obj = grid_account_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_create_na_sg_tenant_account_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_account_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_account()
        args["quota_size"] = 10
        args["description"] = "Update Account"
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],  # get
            SRR["grid_accounts"],  # get
            SRR["grid_account_record"],  # get
            SRR["grid_account_record_with_quota"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_account_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_tenant_account_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_account_quota_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_account()
        args["quota_size"] = 20480
        args["quota_size_unit"] = "mb"
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],  # get
            SRR["grid_accounts"],  # get
            SRR["grid_account_record_with_quota"],  # get
            SRR["grid_account_record_update_quota"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_account_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_tenant_account_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    # update Tenant Account and set pass
    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_account_and_set_password_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_account()
        args["quota_size"] = 20480
        args["quota_size_unit"] = "mb"
        args["update_password"] = "always"

        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],  # get
            SRR["grid_accounts"],  # get
            SRR["grid_account_record_with_quota"],  # get
            SRR["grid_account_record_update_quota"],  # put
            SRR["pw_change_good"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_account_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_account_and_set_password_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    # set pass only

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_set_na_sg_grid_account_root_password_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_account()
        args["update_password"] = "always"

        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],  # get
            SRR["grid_accounts"],  # get id
            SRR["grid_account_record"],  # get account
            SRR["pw_change_good"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_account_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_set_na_sg_grid_account_root_password_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_delete_na_sg_grid_account_pass(self, mock_request):
        set_module_args(self.set_args_delete_na_sg_grid_account())
        mock_request.side_effect = [
            SRR["version_114"],  # get
            SRR["grid_accounts"],  # get
            SRR["grid_account_record"],  # get
            SRR["delete_good"],  # delete
            SRR["end_of_sequence"],
        ]
        my_obj = grid_account_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_tenant_account_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_minimum_version_not_met(self, mock_request):
        args = self.set_args_create_na_sg_grid_account()
        args["allow_select_object_content"] = True
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],  # get
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            grid_account_module()
        print("Info: test_module_fail_minimum_version_not_met: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_minimum_version_not_met_for_compliance_and_retention(self, mock_request):
        args = self.set_args_create_na_sg_grid_account()
        args["allow_compliance_mode"] = True
        args["max_retention_days"] = 365
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_116"],  # get
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            grid_account_module()
        print("Info: test_module_fail_minimum_version_not_met_for_compliance_and_retention: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_account_with_allow_select_object_content_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_account()
        args["allow_select_object_content"] = True
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_116"],  # get
            SRR["empty_good"],  # get
            SRR["grid_accounts"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_account_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print(
            "Info: test_create_na_sg_tenant_account_with_allow_select_object_content_pass: %s" % repr(exc.value.args[0])
        )
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_account_with_compliance_mode_and_retention_time(self, mock_request):
        args = self.set_args_create_na_sg_grid_account()
        args["allow_compliance_mode"] = True
        args["max_retention_days"] = 365
        print("args", args)
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_119"],  # get
            SRR["empty_good"],  # get
            SRR["grid_accounts"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_account_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print(
            "Info: test_create_na_sg_grid_account_with_compliance_mode_and_retention_time: %s" % repr(exc.value.args[0])
        )
        assert exc.value.args[0]["changed"]
