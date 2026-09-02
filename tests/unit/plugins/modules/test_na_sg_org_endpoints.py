# (c) 2026, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Platform Service Endpoints Ansible module: na_sg_org_endpoints """

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_org_endpoints import (
    SgOrgEndpoint as org_endpoints_module,
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
    "delete_good": (None, None),
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "generic_error": (None, "Expected error"),
    "version_114": (
        {"data": {"productVersion": "11.4.0-20200721.1338.d3969b3"}},
        None,
    ),
    "api_response_existing_endpoints": (
        {
            "data": [
                {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "displayName": "My_endpoint",
                    "endpointURI": "https://s3-aws-region.amazonaws.com",
                    "endpointURN": "arn:aws:s3:::my-bucket",
                    "authType": "anonymous",
                    "caCert": "-----BEGIN CERTIFICATE----- abcdefghijkl12345678jklABCD -----END CERTIFICATE-----\n",
                    "clientCert": "-----BEGIN CERTIFICATE-----\nabcdefghijkl1234CDEFabcdefghijklABCD\n-----END CERTIFICATE-----\n",
                    "clientKey": "client-key",
                    "clientKeyPassphrase": "EXAMPLE-SG-mypassphrase",
                    "insecureTLS": False,
                    "credentials": {
                        "accessKeyId": "EXAMPLE_SG_AKIA12345abcABC",
                        "secretAccessKey": "abcABC+123456789012345678901234567890123"
                    },
                    "basicHttpCredentials": {
                        "username": "string",
                        "password": "string"
                    },
                    "capCredentials": {
                        "url": "https://123.45.67.89:1234/CAP/api/v1/credentials?agency=myagency&mission=mymission&role=myrole",
                        "serverCaCert": "-----BEGIN CERTIFICATE-----\nabcdelABCD\n-----END CERTIFICATE-----\n",
                        "clientCert": "-----BEGIN CERTIFICATE-----\nabcdefD\n-----END CERTIFICATE-----\n",
                        "clientKey": "client-key",
                        "clientKeyPassphrase": "mypassphrase"
                    },
                    "saslCredentials": {
                        "mechanism": "PLAIN",
                        "username": "string",
                        "password": "string",
                        "isDelegationToken": False
                    },
                }
            ]
        },
        None,
    ),
    "api_response_succeeded_endpoints": (
        {
            "data": [
                {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "displayName": "My_endpoint",
                    "endpointURI": "https://s3-aws-region.amazonaws.com",
                    "endpointURN": "arn:aws:s3:::my-bucket",
                    "authType": "anonymous",
                    "caCert": "-----BEGIN CERTIFICATE----- abcdefghijkl12345678jklABCD -----END CERTIFICATE-----\n",
                    "clientCert": "-----BEGIN CERTIFICATE-----\nabcdefghijkl1234CDEFabcdefghijklABCD\n-----END CERTIFICATE-----\n",
                    "clientKey": "client-key",
                    "clientKeyPassphrase": "EXAMPLE-SG-mypassphrase",
                    "insecureTLS": False,
                    "credentials": {
                        "accessKeyId": "EXAMPLE_SG_AKIA12345abcABC",
                        "secretAccessKey": "abcABC+123456789012345678901234567890123"
                    },
                    "basicHttpCredentials": {
                        "username": "string",
                        "password": "string"
                    },
                    "capCredentials": {
                        "url": "https://123.45.67.89:1234/CAP/api/v1/credentials?agency=myagency&mission=mymission&role=myrole",
                        "serverCaCert": "-----BEGIN CERTIFICATE-----\nabcdelABCD\n-----END CERTIFICATE-----\n",
                        "clientCert": "-----BEGIN CERTIFICATE-----\nabcdefD\n-----END CERTIFICATE-----\n",
                        "clientKey": "client-key",
                        "clientKeyPassphrase": "mypassphrase"
                    },
                    "saslCredentials": {
                        "mechanism": "PLAIN",
                        "username": "string",
                        "password": "string",
                        "isDelegationToken": False
                    },
                }
            ]
        },
        None,
    ),
    "api_response_updated_endpoints": (
        {
            "data": [
                {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "displayName": "My_endpoint",
                    "endpointURI": "https://s3-aws-region.amazonaws.com",
                    "endpointURN": "arn:aws:s3:::my-bucket1",
                    "authType": "anonymous",
                    "caCert": "-----BEGIN CERTIFICATE----- abcdefghijkl12345678jklABCD -----END CERTIFICATE-----\n",
                    "clientCert": "-----BEGIN CERTIFICATE-----\nabcdefghijkl1234CDEFabcdefghijklABCD\n-----END CERTIFICATE-----\n",
                    "clientKey": "client-key",
                    "clientKeyPassphrase": "EXAMPLE-SG-mypassphrase",
                    "insecureTLS": False,
                    "credentials": {
                        "accessKeyId": "EXAMPLE_SG_AKIA12345abcABC",
                        "secretAccessKey": "abcABC+123456789012345678901234567890123"
                    },
                    "basicHttpCredentials": {
                        "username": "string",
                        "password": "string"
                    },
                    "capCredentials": {
                        "url": "https://123.45.67.89:1234/CAP/api/v1/credentials?agency=myagency&mission=mymission&role=myrole",
                        "serverCaCert": "-----BEGIN CERTIFICATE-----\nabcdelABCD\n-----END CERTIFICATE-----\n",
                        "clientCert": "-----BEGIN CERTIFICATE-----\nabcdefD\n-----END CERTIFICATE-----\n",
                        "clientKey": "client-key",
                        "clientKeyPassphrase": "mypassphrase"
                    },
                    "saslCredentials": {
                        "mechanism": "PLAIN",
                        "username": "string",
                        "password": "string",
                        "isDelegationToken": False
                    },
                }
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
        return dict({"auth_token": "01234567-5678-9abc-78de-9fgabc123def", "validate_certs": False})  # missing "api_url" and "bucket_name"

    def set_default_args_pass_check(self):
        return dict(
            {
                "state": "present",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_update_na_sg_org_endpoints_pass_check(self):
        return dict(
            {
                "state": "present",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
                "name": "My endpoint",
                "endpoint_uri": "https://s3-aws-region.amazonaws.com",
                "endpoint_urn": "arn:aws:s3:::my-bucket1",
                "auth_type": "anonymous",
            }
        )

    def set_args_delete_na_sg_org_endpoints_pass_check(self):
        return dict(
            {
                "state": "absent",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
                "name": "My_endpoint",
            }
        )

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_when_required_args_missing(self, mock_request):
        """required arguments are reported as errors"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            org_endpoints_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_succeed_when_required_args_present(self, mock_request):
        """required arguments are present"""
        mock_request.side_effect = [
            SRR["version_114"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            org_endpoints_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_succeed_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_org_endpoints_pass(self, mock_request):
        args = self.set_args_update_na_sg_org_endpoints_pass_check()
        set_module_args(args)
        mock_request.side_effect = [
            SRR["api_response_existing_endpoints"],  # get
            SRR["api_response_updated_endpoints"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = org_endpoints_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_org_endpoints_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_delete_na_sg_org_endpoints_pass(self, mock_request):
        args = self.set_args_delete_na_sg_org_endpoints_pass_check()
        set_module_args(args)
        mock_request.side_effect = [
            SRR["api_response_existing_endpoints"],  # get
            # SRR["api_response_existing_endpoints"],  # get
            SRR["delete_good"],  # delete
            SRR["end_of_sequence"],
        ]
        my_obj = org_endpoints_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_delete_na_sg_org_endpoints_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]
