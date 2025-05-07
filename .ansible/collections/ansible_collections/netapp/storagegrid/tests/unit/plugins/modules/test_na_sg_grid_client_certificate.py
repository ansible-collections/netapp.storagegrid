# (c) 2022, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Grid HA Group Ansible module: na_sg_grid_client_certificate"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_client_certificate import (
    SgGridClientCertificate as grid_client_certificate_module,
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
    "update_good": (None, None),
    "version_114": ({"data": {"productVersion": "11.4.0-20200721.1338.d3969b3"}}, None),
    "version_116": ({"data": {"productVersion": "11.6.0-20211120.0301.850531e"}}, None),
    "client_cert_record": (
        {
            "data": {
                "id": "841ee2c7-3144-4c3c-8709-335462c5b05d",
                "displayName": "testcert1",
                "publicKey": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIIEOzCCAyOgAwIBAgIIFuVL2ktGT0MwDQYJKoZIhvcNAQELBQAwbzELMAkGA1UE\n"
                    "BhMCVVMxCzAJBgNVBAgMAkNBMRIwEAYDVQQHDAlTdW5ueXZhbGUxFDASBgNVBAoM\n"
                    "-----END CERTIFICATE-----\n"
                ),
                "allowPrometheus": True,
                "expiryDate": "2024-01-01T00:00:00.000Z",
            }
        },
        None,
    ),
    "client_cert_record_updated": (
        {
            "data": {
                "id": "841ee2c7-3144-4c3c-8709-335462c5b05d",
                "displayName": "testcert1",
                "publicKey": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIICrDCCAZSgAwIBAgIUM3IQEKIypqPrXmoA/KmELXfFAz8wDQYJKoZIhvcNAQEL\n"
                    "BQAwADAeFw0yMjA5MDUyMzI3MTVaFw0yNDA5MDQyMzI3MTVaMAAwggEiMA0GCSqG\n"
                    "-----END CERTIFICATE-----\n"
                ),
                "allowPrometheus": True,
                "expiryDate": "2024-01-01T00:00:00.000Z",
            }
        },
        None,
    ),
    "client_cert_record_rename": (
        {
            "data": {
                "id": "841ee2c7-3144-4c3c-8709-335462c5b05d",
                "displayName": "testcert1-rename",
                "publicKey": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIIEOzCCAyOgAwIBAgIIFuVL2ktGT0MwDQYJKoZIhvcNAQELBQAwbzELMAkGA1UE\n"
                    "BhMCVVMxCzAJBgNVBAgMAkNBMRIwEAYDVQQHDAlTdW5ueXZhbGUxFDASBgNVBAoM\n"
                    "-----END CERTIFICATE-----\n"
                ),
                "allowPrometheus": True,
                "expiryDate": "2024-01-01T00:00:00.000Z",
            }
        },
        None,
    ),
    "client_certificates": (
        {
            "data": [
                {
                    "id": "841ee2c7-3144-4c3c-8709-335462c5b05d",
                    "displayName": "testcert1",
                    "publicKey": (
                        "-----BEGIN CERTIFICATE-----\n"
                        "MIIEOzCCAyOgAwIBAgIIFuVL2ktGT0MwDQYJKoZIhvcNAQELBQAwbzELMAkGA1UE\n"
                        "BhMCVVMxCzAJBgNVBAgMAkNBMRIwEAYDVQQHDAlTdW5ueXZhbGUxFDASBgNVBAoM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                    "allowPrometheus": True,
                    "expiryDate": "2024-01-01T00:00:00.000Z",
                },
                {
                    "id": "869e1792-5505-42f1-a1fc-57a04e56f644",
                    "displayName": "testcert2",
                    "publicKey": (
                        "-----BEGIN CERTIFICATE-----\n"
                        "MIIC9DCCAdygAwIBAgIUD7y+AyrSqRjQdYVflLJ9aTIJu3wwDQYJKoZIhvcNAQEL\n"
                        "BQAwFTETMBEGA1UEAwwKUHJvbWV0aGV1czAeFw0yMjA4MjQxMjQxNDhaFw0yNDA4\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                    "allowPrometheus": True,
                    "expiryDate": "2024-01-01T00:00:00.000Z",
                },
            ]
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
                "allow_prometheus": True,
                "public_key": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIIEOzCCAyOgAwIBAgIIFuVL2ktGT0MwDQYJKoZIhvcNAQELBQAwbzELMAkGA1UE\n"
                    "BhMCVVMxCzAJBgNVBAgMAkNBMRIwEAYDVQQHDAlTdW5ueXZhbGUxFDASBgNVBAoM\n"
                    "-----END CERTIFICATE-----\n"
                ),
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "state": "present",
                "display_name": "testcert1",
                "allow_prometheus": True,
                "public_key": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIIEOzCCAyOgAwIBAgIIFuVL2ktGT0MwDQYJKoZIhvcNAQELBQAwbzELMAkGA1UE\n"
                    "BhMCVVMxCzAJBgNVBAgMAkNBMRIwEAYDVQQHDAlTdW5ueXZhbGUxFDASBgNVBAoM\n"
                    "-----END CERTIFICATE-----\n"
                ),
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_create_na_sg_grid_client_certificate(self):
        return dict(
            {
                "state": "present",
                "display_name": "testcert1",
                "allow_prometheus": True,
                "public_key": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIIEOzCCAyOgAwIBAgIIFuVL2ktGT0MwDQYJKoZIhvcNAQELBQAwbzELMAkGA1UE\n"
                    "BhMCVVMxCzAJBgNVBAgMAkNBMRIwEAYDVQQHDAlTdW5ueXZhbGUxFDASBgNVBAoM\n"
                    "-----END CERTIFICATE-----\n"
                ),
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_delete_na_sg_grid_client_certificate(self):
        return dict(
            {
                "state": "absent",
                "display_name": "testcert1",
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
            grid_client_certificate_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_pass_when_required_args_present(self, mock_request):
        """required arguments are reported as errors"""
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            grid_client_certificate_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_pass_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_client_certificate_pass(self, mock_request):
        set_module_args(self.set_args_create_na_sg_grid_client_certificate())
        mock_request.side_effect = [
            SRR["empty_good"],  # get
            SRR["client_cert_record"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_client_certificate_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_grid_client_certificate_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_create_na_sg_grid_client_certificate_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_client_certificate()
        set_module_args(args)
        mock_request.side_effect = [
            SRR["client_certificates"],  # get
            SRR["client_cert_record"],  # get
            SRR["end_of_sequence"],
        ]
        my_obj = grid_client_certificate_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_create_na_sg_grid_client_certificate_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_client_certificate_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_client_certificate()
        args["public_key"] = (
            "-----BEGIN CERTIFICATE-----\n"
            "MIICrDCCAZSgAwIBAgIUM3IQEKIypqPrXmoA/KmELXfFAz8wDQYJKoZIhvcNAQEL\n"
            "BQAwADAeFw0yMjA5MDUyMzI3MTVaFw0yNDA5MDQyMzI3MTVaMAAwggEiMA0GCSqG\n"
            "-----END CERTIFICATE-----\n",
        )
        set_module_args(args)
        mock_request.side_effect = [
            SRR["client_certificates"],  # get
            SRR["client_cert_record"],  # get
            SRR["client_cert_record_updated"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_client_certificate_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_client_certificate_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_rename_na_sg_grid_client_certificate_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_client_certificate()
        args["certificate_id"] = "841ee2c7-3144-4c3c-8709-335462c5b05d"
        args["display_name"] = "testcert1-rename"
        set_module_args(args)
        mock_request.side_effect = [
            SRR["client_cert_record"],  # get
            SRR["client_cert_record_rename"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_client_certificate_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_rename_na_sg_grid_client_certificate_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_delete_na_sg_grid_client_certificate_pass(self, mock_request):
        args = self.set_args_delete_na_sg_grid_client_certificate()
        set_module_args(args)
        mock_request.side_effect = [
            SRR["client_certificates"],  # get
            SRR["client_cert_record"],  # get
            SRR["delete_good"],  # delete
            SRR["end_of_sequence"],
        ]
        my_obj = grid_client_certificate_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_delete_na_sg_grid_client_certificate_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_client_certificate_bad_certificate_id_fail(self, mock_request):
        args = self.set_args_create_na_sg_grid_client_certificate()
        args["certificate_id"] = "ffffffff-ffff-aaaa-aaaa-000000000000"
        args["display_name"] = "Bad ID"
        set_module_args(args)
        mock_request.side_effect = [
            SRR["not_found"],  # get
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj = grid_client_certificate_module()
            my_obj.apply()
        print("Info: test_update_na_sg_grid_client_certificate_bad_certificate_id_fail: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["failed"]
