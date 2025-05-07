# (c) 2025, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Alert Receiver Ansible module: na_sg_grid_alert_receiver """

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_alert_receiver import (
    SgAlertReceiver as alert_receiver_module,
)

if sys.version_info < (3, 11):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 3.11")

# REST API canned responses when mocking send_request
SRR = {
    "empty_good": ({"data": []}, None),
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "generic_error": (None, "Expected error"),
    "delete_good": ({"code": 204}, None),
    "version_114": ({"data": {"productVersion": "11.4.0-20200721.1338.d3969b3"}}, None),
    "api_response_creation_succeeded": (
        {
            "data": [
                {
                    "type": "email",
                    "enable": True,
                    "smtpHost": "smtp.example.com",
                    "smtpPort": 25,
                    "fromEmail": "user@example.com",
                    "toEmails": [
                        "user@example.com"
                    ],
                    "minimumSeverity": "minor",
                    "caCert": "-----BEGIN CERTIFICATE-----*******-----END CERTIFICATE-----",
                    "clientCert": "-----BEGIN CERTIFICATE-----*******-----END CERTIFICATE-----",
                    "clientKey": "-----BEGIN PRIVATE KEY-----*******-----END PRIVATE KEY-----",
                    "id": "00000000-0000-0000-0000-000000000000"
                }
            ]},
        None,
    ),
    "api_response_existing_alert_receiver": (
        {
            "data": {
                "type": "email",
                "enable": True,
                "smtpHost": "smtp.example.com",
                "smtpPort": 25,
                "fromEmail": "user@example.com",
                "toEmails": [
                    "user@example.com"
                ],
                "minimumSeverity": "minor",
                "caCert": "-----BEGIN CERTIFICATE-----*******-----END CERTIFICATE-----",
                "clientCert": "-----BEGIN CERTIFICATE-----*******-----END CERTIFICATE-----",
                "clientKey": "-----BEGIN PRIVATE KEY-----*******-----END PRIVATE KEY-----",
                "id": "00000000-0000-0000-0000-000000000000"
            }
        },
        None,
    ),
    "api_response_alert_receiver_updated": (
        {
            "data": {
                "type": "email",
                "enable": True,
                "smtpHost": "smtp.example.com",
                "smtpPort": 25,
                "fromEmail": "user@example.com",
                "toEmails": [
                    "user@example.com"
                ],
                "minimumSeverity": "minor",
                "caCert": "-----BEGIN CERTIFICATE-----*******-----END CERTIFICATE-----",
                "clientCert": "-----BEGIN CERTIFICATE-----*******-----END CERTIFICATE-----",
                "clientKey": "-----BEGIN PRIVATE KEY-----*******-----END PRIVATE KEY-----",
                "id": "00000000-0000-0000-0000-000000000000"
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


class TestAlertReceiverModule(unittest.TestCase):
    """Unit Tests for na_sg_grid_alert_receiver module"""

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args_fail_check(self):
        return dict(
            {
                "validate_certs": False,
                "type": "email",
                "enable": True,
                "smtp_host": "smtp.example.com",
                "smtp_port": 25,
                "from_email": "user@example.com",
                "to_emails": [
                    "user@example.com"
                ],
                "minimum_severity": "minor",
                "ca_cert": "-----BEGIN CERTIFICATE-----*******-----END CERTIFICATE-----",
                "client_cert": "-----BEGIN CERTIFICATE-----*******-----END CERTIFICATE-----",
                "client_key": "-----BEGIN PRIVATE KEY-----*******-----END PRIVATE KEY-----",
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "auth_token": "storagegrid-auth-token",
                "state": "present",
                "validate_certs": False,
                "type": "email",
                "enable": True,
                "smtp_host": "smtp.example.com",
                "smtp_port": 25,
                "from_email": "user@example.com",
                "to_emails": [
                    "user@example.com"
                ],
                "minimum_severity": "minor",
                "ca_cert": "-----BEGIN CERTIFICATE-----*******-----END CERTIFICATE-----",
                "client_cert": "-----BEGIN CERTIFICATE-----*******-----END CERTIFICATE-----",
                "client_key": "-----BEGIN PRIVATE KEY-----*******-----END PRIVATE KEY-----",
            }
        )

    def set_args_create_alert_receiver(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "auth_token": "storagegrid-auth-token",
                "state": "present",
                "validate_certs": False,
                "type": "email",
                "enable": True,
                "smtp_host": "smtp.example.com",
                "smtp_port": 25,
                "from_email": "user@example.com",
                "to_emails": [
                    "user@example.com"
                ],
                "minimum_severity": "minor",
                "ca_cert": "-----BEGIN CERTIFICATE-----*******-----END CERTIFICATE-----",
                "client_cert": "-----BEGIN CERTIFICATE-----*******-----END CERTIFICATE-----",
                "client_key": "-----BEGIN PRIVATE KEY-----*******-----END PRIVATE KEY-----",
            }
        )

    def set_args_delete_alert_receiver(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "auth_token": "storagegrid-auth-token",
                "state": "absent",
                "validate_certs": False,
                "type": "email",
                "smtp_host": "smtp.example.com",
                "smtp_port": 25,
                "from_email": "user@example.com",
                "to_emails": [
                    "user@example.com"
                ],
                "minimum_severity": "minor",
            }
        )

    def test_missing_required_args(self):
        """Test missing required arguments"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            alert_receiver_module()
        assert "missing required arguments" in str(exc.value)

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_alert_receiver_pass(self, mock_request):
        set_module_args(self.set_args_create_alert_receiver())
        mock_request.side_effect = [
            SRR["empty_good"],  # Check if alert receiver exists
            SRR["api_response_creation_succeeded"],  # Create new alert receiver
            SRR["end_of_sequence"],
        ]
        my_obj = alert_receiver_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_grid_alert_receiver_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_create_na_sg_grid_alert_receiver_pass(self, mock_request):
        set_module_args(self.set_args_create_alert_receiver())
        mock_request.side_effect = [
            SRR["api_response_creation_succeeded"],
            SRR["api_response_existing_alert_receiver"],  # Alert receiver already exists
            SRR["end_of_sequence"],
        ]
        my_obj = alert_receiver_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_create_na_sg_grid_alert_receiver_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_alert_receiver_pass(self, mock_request):
        args = self.set_args_create_alert_receiver()
        args["smtp_port"] = 35
        args["minimum_severity"] = "major"
        set_module_args(args)
        mock_request.side_effect = [
            SRR["api_response_creation_succeeded"],  # get
            SRR["api_response_existing_alert_receiver"],  # get
            SRR["api_response_alert_receiver_updated"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = alert_receiver_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_alert_receiver_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_delete_na_sg_grid_alert_receiver_pass(self, mock_request):
        set_module_args(self.set_args_delete_alert_receiver())
        mock_request.side_effect = [
            SRR["api_response_creation_succeeded"],  # get
            SRR["api_response_existing_alert_receiver"],  # Alert receiver exists.
            SRR["delete_good"],  # Successfully deleted.
            SRR["end_of_sequence"],
        ]
        my_obj = alert_receiver_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]["changed"]
