# (c) 2021, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Tenant Identity Federation Ansible module: na_sg_org_identity_federation"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys
try:
    from requests import Response
except ImportError:
    if sys.version_info < (2, 7):
        pytestmark = pytest.mark.skip('Skipping Unit Tests on 2.6 as requests is not available')
    else:
        raise

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import (
    patch,
    Mock,
)
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_org_identity_federation import (
    SgOrgIdentityFederation as org_identity_federation_module,
)

# REST API canned responses when mocking send_request
SRR = {
    # common responses
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "generic_error": (None, "Expected error"),
    "check_mode_good": (None, None),
    "identity_federation_unset": (
        {
            "data": {
                "id": "09876543-abcd-4321-abcd-0987654321ab",
                "disable": True,
                "type": "",
                "ldapServiceType": "",
                "hostname": "",
                "port": 0,
                "username": "",
                "password": None,
                "baseGroupDn": "",
                "baseUserDn": "",
                "disableTLS": False,
                "enableLDAPS": False,
                "caCert": "",
            }
        },
        None,
    ),
    "identity_federation": (
        {
            "data": {
                "id": "09876543-abcd-4321-abcd-0987654321ab",
                "disable": False,
                "type": "ldap",
                "ldapServiceType": "Active Directory",
                "hostname": "ad.example.com",
                "port": 389,
                "username": "binduser",
                "password": "********",
                "baseGroupDn": "DC=example,DC=com",
                "baseUserDn": "DC=example,DC=com",
                "disableTLS": True,
                "enableLDAPS": False,
                "caCert": "",
            }
        },
        None,
    ),
    "identity_federation_tls": (
        {
            "data": {
                "id": "09876543-abcd-4321-abcd-0987654321ab",
                "disable": False,
                "type": "ldap",
                "ldapServiceType": "Active Directory",
                "hostname": "ad.example.com",
                "port": 636,
                "username": "binduser",
                "password": "********",
                "baseGroupDn": "DC=example,DC=com",
                "baseUserDn": "DC=example,DC=com",
                "disableTLS": False,
                "enableLDAPS": True,
                "caCert": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIIF+DCCBOCgAwIBAgITRwAAAAIg5KzMrJo+kQAAAAAAAjANBgkqhkiG9w0BAQUF\n"
                    "ADBlMRIwEAYKCZImiZPyLGQBGRYCYXUxFjAUBgoJkiaJk/IsZAEZFgZuZXRhcHAx\n"
                    "FjAUBgoJkiaJk/IsZAEZFgZhdXNuZ3MxHzAdBgNVBAMTFmF1c25ncy1NRUxOR1NE\n"
                    "QzAxLUNBLTEwHhcNMjEwMjExMDkzMTIwWhcNMjMwMjExMDk0MTIwWjAAMIIBIjAN\n"
                    "BgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAt2xPi4FS4Uc37KrDLEXXUoc4lhhT\n"
                    "uQmMnLc0PYZCIpzYOaosFIeGqco3woiC7wSZJ2whKE4RDcxxgE+azuGiSWVjIxIL\n"
                    "AimmcDhFid/T3KRN5jmkjBzUKuPBYzZBFih8iU9056rqgN7eMKQYjRwPeV0+AeiB\n"
                    "irw46OgkwVQu3shEUtXxZPP2Mb6Md23+4vSmcElUcW28Opt2q/M5fs7DNomG3eaG\n"
                    "-----END CERTIFICATE-----\n"
                ),
            }
        },
        None,
    ),
    "identity_federation_disable": (
        {
            "data": {
                "id": "09876543-abcd-4321-abcd-0987654321ab",
                "disable": True,
                "type": "ldap",
                "ldapServiceType": "Active Directory",
                "hostname": "ad.example.com",
                "port": 389,
                "username": "binduser",
                "password": "********",
                "baseGroupDn": "DC=example,DC=com",
                "baseUserDn": "DC=example,DC=com",
                "disableTLS": True,
                "enableLDAPS": False,
                "caCert": "",
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
    """ a group of related Unit Tests """

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args_fail_check(self):
        return dict(
            {
                "ldap_service_type": "Active Directory",
                "hostname": "ad.example.com",
                "port": 389,
                "username": "binduser",
                "password": "bindpass",
                "base_group_dn": "DC=example,DC=com",
                "base_user_dn": "DC=example,DC=com",
                "tls": "Disabled",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "ldap_service_type": "Active Directory",
                "hostname": "ad.example.com",
                "port": 389,
                "username": "binduser",
                "password": "bindpass",
                "base_group_dn": "DC=example,DC=com",
                "base_user_dn": "DC=example,DC=com",
                "tls": "Disabled",
                "state": "present",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_set_na_sg_org_identity_federation(self):
        return dict(
            {
                "ldap_service_type": "Active Directory",
                "hostname": "ad.example.com",
                "port": 389,
                "username": "binduser",
                "password": "bindpass",
                "base_group_dn": "DC=example,DC=com",
                "base_user_dn": "DC=example,DC=com",
                "tls": "Disabled",
                "state": "present",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_set_na_sg_org_identity_federation_tls(self):
        return dict(
            {
                "ldap_service_type": "Active Directory",
                "hostname": "ad.example.com",
                "port": 636,
                "username": "binduser",
                "password": "bindpass",
                "base_group_dn": "DC=example,DC=com",
                "base_user_dn": "DC=example,DC=com",
                "tls": "LDAPS",
                "ca_cert": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIIF+DCCBOCgAwIBAgITRwAAAAIg5KzMrJo+kQAAAAAAAjANBgkqhkiG9w0BAQUF\n"
                    "ADBlMRIwEAYKCZImiZPyLGQBGRYCYXUxFjAUBgoJkiaJk/IsZAEZFgZuZXRhcHAx\n"
                    "FjAUBgoJkiaJk/IsZAEZFgZhdXNuZ3MxHzAdBgNVBAMTFmF1c25ncy1NRUxOR1NE\n"
                    "QzAxLUNBLTEwHhcNMjEwMjExMDkzMTIwWhcNMjMwMjExMDk0MTIwWjAAMIIBIjAN\n"
                    "BgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAt2xPi4FS4Uc37KrDLEXXUoc4lhhT\n"
                    "uQmMnLc0PYZCIpzYOaosFIeGqco3woiC7wSZJ2whKE4RDcxxgE+azuGiSWVjIxIL\n"
                    "AimmcDhFid/T3KRN5jmkjBzUKuPBYzZBFih8iU9056rqgN7eMKQYjRwPeV0+AeiB\n"
                    "irw46OgkwVQu3shEUtXxZPP2Mb6Md23+4vSmcElUcW28Opt2q/M5fs7DNomG3eaG\n"
                    "-----END CERTIFICATE-----\n"
                ),
                "state": "present",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_remove_na_sg_org_identity_federation(self):
        return dict(
            {
                "ldap_service_type": "Active Directory",
                "hostname": "ad.example.com",
                "state": "absent",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def test_module_fail_when_required_args_missing(self):
        """ required arguments are reported as errors """
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            org_identity_federation_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    def test_module_fail_when_required_args_present(self):
        """ required arguments are reported as errors """
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            org_identity_federation_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_fail_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_set_na_sg_org_identity_federation_pass(self, mock_request):
        set_module_args(self.set_args_set_na_sg_org_identity_federation())
        my_obj = org_identity_federation_module()
        mock_request.side_effect = [
            SRR["identity_federation_unset"],  # get
            SRR["identity_federation"],  # post
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_set_na_sg_org_identity_federation_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_set_na_sg_org_identity_federation_pass(self, mock_request):
        args = self.set_args_set_na_sg_org_identity_federation()
        # remove password
        del args["password"]
        set_module_args(args)
        my_obj = org_identity_federation_module()
        mock_request.side_effect = [
            SRR["identity_federation"],  # get
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_set_na_sg_org_identity_federation_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_set_na_sg_org_identity_federation_tls_pass(self, mock_request):
        set_module_args(self.set_args_set_na_sg_org_identity_federation_tls())
        my_obj = org_identity_federation_module()
        mock_request.side_effect = [
            SRR["identity_federation_unset"],  # get
            SRR["identity_federation_tls"],  # post
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_set_na_sg_org_identity_federation_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_remove_na_sg_org_identity_federation_pass(self, mock_request):
        set_module_args(self.set_args_remove_na_sg_org_identity_federation())
        my_obj = org_identity_federation_module()
        mock_request.side_effect = [
            SRR["identity_federation"],  # get
            SRR["identity_federation_disable"],  # post
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_remove_na_sg_org_identity_federation_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    # test check mode

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_check_mode_na_sg_org_identity_federation_pass(self, mock_request):
        set_module_args(self.set_args_set_na_sg_org_identity_federation())
        my_obj = org_identity_federation_module()
        my_obj.module.check_mode = True
        mock_request.side_effect = [
            SRR["identity_federation_unset"],  # get
            SRR["check_mode_good"],  # post
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_check_mode_na_sg_org_identity_federation_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]
        assert exc.value.args[0]["msg"] == "Connection test successful"
