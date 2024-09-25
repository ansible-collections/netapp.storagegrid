# (c) 2020, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Grid Certificate Ansible module: na_sg_grid_certificate"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_certificate import (
    SgGridCertificate as grid_certificate_module,
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
    "cert_unset": ({"data": {"serverCertificateEncoded": None, "caBundleEncoded": None}}, None),
    "storage_api_cert": (
        {
            "data": {
                "serverCertificateEncoded": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIICyDCCAbACCQCgFntI3q7iADANBgkqhkiG9w0BAQsFADAmMQswCQYDVQQGEwJV\n"
                    "UzEXMBUGA1UEAwwOczMuZXhhbXBsZS5jb20wHhcNMjEwNDI5MDQ1NTM1WhcNMjIw\n"
                    "NDI5MDQ1NTM1WjAmMQswCQYDVQQGEwJVUzEXMBUGA1UEAwwOczMuZXhhbXBsZS5j\n"
                    "b20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQD0LMcJUdWmTtxi7U7B\n"
                    "yldDRfyCD9W+QJ1Ygm7E9iFwvkThUCV5q+DIcgSfogoSKaQuHaImLXMZn36QC22n\n"
                    "+Ah2EGrQiggyny3wDzuWf5/Qg7ogqQRqiespBFLlV4RGCREHK0y5uq8mzpIaQ8l8\n"
                    "STa7nLS7BIc6rD15BJaNWZpDVHIzhljlnhfnqwio/ZfP++lAjk4/j8pPGPEEI5Fe\n"
                    "WxhOtQjr7xTHeJxKHp2VKiLEvFxniL3qk4uJ3k5fJ7IqALUEPWH92brFp2IkObUA\n"
                    "EGsZYB4KFV7asBVhGuspYNzUQ6NqWbEUmtTjKEXcb1TA8RK+Pc2TotOrQ2E7Z+rU\n"
                    "gl2fAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAD5PW1WI7GCfxLQjaitnXpD1MR2O\n"
                    "6b5csymPYwRejMsSswd8egjs+vO2pbF9TptLjqGliE9XUoI+mWpuMzzd75F0jcjq\n"
                    "1DhlINgAmjUJEAg0RAqce0Kn8xQF+SofMtkOH+nZm3Q9nbTJKr1H5m2TnCq3v5TH\n"
                    "Qo0ASf0LLGgrwUtT0IghdSttYLS89dJprZ6c5wK7qeBzxfdHxxjiaSnvByL2Ryn5\n"
                    "cec9lptYKoRY42hWvkQv9Wkr3DDoyNA3xPdZJr0Hpf8/mSPnt9r/AR8E32xi0SXp\n"
                    "hOMTDgMicbK82ycxz0yW88gm6yhrChlJrWaEsVGod3FU+lbMAnagYZ/Vwp8=\n"
                    "-----END CERTIFICATE-----\n"
                ),
                "caBundleEncoded": None,
            }
        },
        None,
    ),
    "storage_api_cert_update": (
        {
            "data": {
                "serverCertificateEncoded": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIICzjCCAbYCCQDZVi1OT89SAjANBgkqhkiG9w0BAQsFADApMQswCQYDVQQGEwJV\n"
                    "UzEaMBgGA1UEAwwRczMubmV3ZXhhbXBsZS5jb20wHhcNMjEwNDI5MDQ1NzIxWhcN\n"
                    "MjIwNDI5MDQ1NzIxWjApMQswCQYDVQQGEwJVUzEaMBgGA1UEAwwRczMubmV3ZXhh\n"
                    "bXBsZS5jb20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCmg37q2sjZ\n"
                    "k+HsXtai3PSMtGUiqij04JtG9ahMqIejuxy5sDCWnigh//NjdK+wPYc2VfYd6KFA\n"
                    "Uk9rP84M7sqdqGzIzmyEu7INyCnlbxcXlST6UZDsZnVU7Gk2GvUzk2OoO5N+G0oI\n"
                    "Lfc/3eKTx9j9BguOaWUy+ni+Te8j6EwK6HolGRBjLYqf1SYFBzaoVpy7pmzaFZ4R\n"
                    "10jFSxHbotIZ+kR8pPE5jGkP8OjOfrpbhEgmffpeq2MSCMRuhRtRiVp4ULwkMTRN\n"
                    "tFj89mu1gl9T3lYM/LO1SmBv3il0mNmrTL+99UJ4s2eL0zr/uHAVYJcVqFgWP7X8\n"
                    "WnOk+d86b0TXAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAFmGV3IOuNYeM3LQxls+\n"
                    "/CNHznvIqvoiJOWq0S7LFy1eO7PVzCl3l/fDKjGMt2lGXeU89YKdFVPqsainNEFT\n"
                    "cNEWlezVut+/CWQpBXujyBqPLkYbzyGsakMImDb+MrSkBO5MCjlt38vppm5a97fB\n"
                    "9o/wM31e+N6gJLiHWs0XB9TK6bY9CvcutcGUOH/oxH1TEBgrJ3SoS7/HmZJSaCQA\n"
                    "hjZappzuEpGVXT8YDlb67PzUoE2rDWjdSFRXCk/0U6VR0xNgnN1WtfHaypU71DrB\n"
                    "zxbDaOIZoDp5G4OgjkFxoCoSWLant+LsqEwclIbCFgEvJPE8855UThelTHmIfivP\n"
                    "veI=\n-----END CERTIFICATE-----\n"
                ),
                "caBundleEncoded": None,
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
                "server_certificate": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIICyDCCAbACCQCgFntI3q7iADANBgkqhkiG9w0BAQsFADAmMQswCQYDVQQGEwJV\n"
                    "UzEXMBUGA1UEAwwOczMuZXhhbXBsZS5jb20wHhcNMjEwNDI5MDQ1NTM1WhcNMjIw\n"
                    "-----END CERTIFICATE-----\n"
                ),
                "private_key": (
                    "-----BEGIN PRIVATE KEY-----\n"
                    "MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQD0LMcJUdWmTtxi\n"
                    "7U7ByldDRfyCD9W+QJ1Ygm7E9iFwvkThUCV5q+DIcgSfogoSKaQuHaImLXMZn36Q\n"
                    "C22n+Ah2EGrQiggyny3wDzuWf5/Qg7ogqQRqiespBFLlV4RGCREHK0y5uq8mzpIa\n"
                    "-----END PRIVATE KEY-----\n"
                ),
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "state": "present",
                "type": "storage-api",
                "server_certificate": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIICyDCCAbACCQCgFntI3q7iADANBgkqhkiG9w0BAQsFADAmMQswCQYDVQQGEwJV\n"
                    "UzEXMBUGA1UEAwwOczMuZXhhbXBsZS5jb20wHhcNMjEwNDI5MDQ1NTM1WhcNMjIw\n"
                    "-----END CERTIFICATE-----\n"
                ),
                "private_key": (
                    "-----BEGIN PRIVATE KEY-----\n"
                    "MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQD0LMcJUdWmTtxi\n"
                    "7U7ByldDRfyCD9W+QJ1Ygm7E9iFwvkThUCV5q+DIcgSfogoSKaQuHaImLXMZn36Q\n"
                    "C22n+Ah2EGrQiggyny3wDzuWf5/Qg7ogqQRqiespBFLlV4RGCREHK0y5uq8mzpIa\n"
                    "-----END PRIVATE KEY-----\n"
                ),
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_set_na_sg_grid_storage_api_certificate(self):
        return dict(
            {
                "state": "present",
                "type": "storage-api",
                "server_certificate": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIICyDCCAbACCQCgFntI3q7iADANBgkqhkiG9w0BAQsFADAmMQswCQYDVQQGEwJV\n"
                    "UzEXMBUGA1UEAwwOczMuZXhhbXBsZS5jb20wHhcNMjEwNDI5MDQ1NTM1WhcNMjIw\n"
                    "NDI5MDQ1NTM1WjAmMQswCQYDVQQGEwJVUzEXMBUGA1UEAwwOczMuZXhhbXBsZS5j\n"
                    "b20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQD0LMcJUdWmTtxi7U7B\n"
                    "yldDRfyCD9W+QJ1Ygm7E9iFwvkThUCV5q+DIcgSfogoSKaQuHaImLXMZn36QC22n\n"
                    "+Ah2EGrQiggyny3wDzuWf5/Qg7ogqQRqiespBFLlV4RGCREHK0y5uq8mzpIaQ8l8\n"
                    "STa7nLS7BIc6rD15BJaNWZpDVHIzhljlnhfnqwio/ZfP++lAjk4/j8pPGPEEI5Fe\n"
                    "WxhOtQjr7xTHeJxKHp2VKiLEvFxniL3qk4uJ3k5fJ7IqALUEPWH92brFp2IkObUA\n"
                    "EGsZYB4KFV7asBVhGuspYNzUQ6NqWbEUmtTjKEXcb1TA8RK+Pc2TotOrQ2E7Z+rU\n"
                    "gl2fAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAD5PW1WI7GCfxLQjaitnXpD1MR2O\n"
                    "6b5csymPYwRejMsSswd8egjs+vO2pbF9TptLjqGliE9XUoI+mWpuMzzd75F0jcjq\n"
                    "1DhlINgAmjUJEAg0RAqce0Kn8xQF+SofMtkOH+nZm3Q9nbTJKr1H5m2TnCq3v5TH\n"
                    "Qo0ASf0LLGgrwUtT0IghdSttYLS89dJprZ6c5wK7qeBzxfdHxxjiaSnvByL2Ryn5\n"
                    "cec9lptYKoRY42hWvkQv9Wkr3DDoyNA3xPdZJr0Hpf8/mSPnt9r/AR8E32xi0SXp\n"
                    "hOMTDgMicbK82ycxz0yW88gm6yhrChlJrWaEsVGod3FU+lbMAnagYZ/Vwp8=\n"
                    "-----END CERTIFICATE-----\n"
                ),
                "private_key": (
                    "-----BEGIN PRIVATE KEY-----\n"
                    "MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQD0LMcJUdWmTtxi\n"
                    "7U7ByldDRfyCD9W+QJ1Ygm7E9iFwvkThUCV5q+DIcgSfogoSKaQuHaImLXMZn36Q\n"
                    "C22n+Ah2EGrQiggyny3wDzuWf5/Qg7ogqQRqiespBFLlV4RGCREHK0y5uq8mzpIa\n"
                    "Q8l8STa7nLS7BIc6rD15BJaNWZpDVHIzhljlnhfnqwio/ZfP++lAjk4/j8pPGPEE\n"
                    "I5FeWxhOtQjr7xTHeJxKHp2VKiLEvFxniL3qk4uJ3k5fJ7IqALUEPWH92brFp2Ik\n"
                    "ObUAEGsZYB4KFV7asBVhGuspYNzUQ6NqWbEUmtTjKEXcb1TA8RK+Pc2TotOrQ2E7\n"
                    "Z+rUgl2fAgMBAAECggEAAwSSqTDTvSx4WNiqAocnsPMqfckIUUOnLjLef5yzKRuQ\n"
                    "6l/9NpXDP3b5S6fLDBJrrw46tNIW/BgWjl01y7+rCxqE13L9SvLgtHjbua52ITOf\n"
                    "l0u/fDmcKHOfOqpsPhlaloYYeqsuAwLGl4CC+wBEpuj26uDRcw4x7E78NV8IIxDf\n"
                    "8kUNPQXI9ox6P3isXrFkMncDfKLWOYJ5fF5zCoVZai/SS8z3FhGjAXlMkay48RX4\n"
                    "4vuP7TNLZ2O2pAk2aVs54tQyBn9MOxIzOg3/ZFLiKZR4pY6H5sm+bT263TdvN+A4\n"
                    "C8kwML5HnsCjVkTzJ/3dYc9SeUOuqvJI332GCQ9YcQKBgQD8Ev2qhS61kZ3WGO6G\n"
                    "DRkZ6tDyt5vCuzWQ8uAAXcAerFDWN6XtDPfXq2UVcWnoCQOUpnjslCb/NJgCetLh\n"
                    "mOPeJGRWyMly+YuYb4/rnbwSbUs28PO4D9B/f5YQBnBjGDLL/i2+wnXg3WZTVogf\n"
                    "WfdKziOHGSxmWd6JinI+4UkpiwKBgQD3+krkFORTsUAlTgeIy8+QzXSuclwNygcX\n"
                    "HAe0F96hSYHBC7+1n7nzC1lwcbkU3jLIt3A90Uwew4nr5GCu4sSVwDeWrqP2I9WH\n"
                    "4w0zeaFPC1QKfKGBtsIf/89pDz/7iGlcKWlEg+56VVIJn7qC2lO8qbeUCoglsSwC\n"
                    "vr2Qld5WvQKBgQCHM2xpHHv8GPlOTxsIPVg8RW0C8iYSITVO5GXu7FnSWdwVuc0+\n"
                    "QtlgDObvxF/oe4U3Ir7zLVdpRH1Pvy8Cn22AxYYn4hPiniQYg6Xu2zB3tbVE56Hh\n"
                    "FGJhMD59o+Z90AnWziMdENIG5NkwU9Y48pknvz7hBEiDMSqiHObAATerlwKBgQCP\n"
                    "5LhCY3Ees3MCcqXilkmqv93eQFP0WHAG0+gQc+1m7+2QJI4pCTdwtfw/SG5akpkr\n"
                    "aW6DIIkoLNVCgbIsqT/jmbdoA4z3DlIg2PrXDNQytuMcdreNOoyo3trvHr9E6SIi\n"
                    "LZF9BYWDjTDejsY+mgwPJPh2uinInWdpbF85oA11jQKBgQCc6U2fSwpPQowOaat/\n"
                    "pY5bDCKxhfwrKk3Ecye5HfhbBZ0pu6Oneiq6cNhQC0X69iFn6ogTFx5qqyMQrWH0\n"
                    "L+kQRkyYFLnebCzUA8364lieRzc3cN+xQEn+jX8z7eDZ8JsvVnKdc6lTjPTwN1Fj\n"
                    "FZtaH2L1IEiA8ZZapMb/MNNozg==\n"
                    "-----END PRIVATE KEY-----\n"
                ),
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_delete_na_sg_grid_storage_api_certificate(self):
        return dict(
            {
                "state": "absent",
                "type": "storage-api",
                "server_certificate": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIICyDCCAbACCQCgFntI3q7iADANBgkqhkiG9w0BAQsFADAmMQswCQYDVQQGEwJV\n"
                    "UzEXMBUGA1UEAwwOczMuZXhhbXBsZS5jb20wHhcNMjEwNDI5MDQ1NTM1WhcNMjIw\n"
                    "-----END CERTIFICATE-----\n"
                ),
                "private_key": (
                    "-----BEGIN PRIVATE KEY-----\n"
                    "MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQD0LMcJUdWmTtxi\n"
                    "7U7ByldDRfyCD9W+QJ1Ygm7E9iFwvkThUCV5q+DIcgSfogoSKaQuHaImLXMZn36Q\n"
                    "C22n+Ah2EGrQiggyny3wDzuWf5/Qg7ogqQRqiespBFLlV4RGCREHK0y5uq8mzpIa\n"
                    "-----END PRIVATE KEY-----\n"
                ),
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def test_module_fail_when_required_args_missing(self):
        """required arguments are reported as errors"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            grid_certificate_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    def test_module_pass_when_required_args_present(self):
        """required arguments are reported as errors"""
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            grid_certificate_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_pass_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_set_na_sg_grid_storage_api_certificate_pass(self, mock_request):
        set_module_args(self.set_args_set_na_sg_grid_storage_api_certificate())
        my_obj = grid_certificate_module()
        mock_request.side_effect = [
            SRR["cert_unset"],  # get
            SRR["update_good"],  # post
            SRR["storage_api_cert"],  # get
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_set_na_sg_grid_storage_api_certificate_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_set_na_sg_grid_storage_api_certificate_pass(self, mock_request):
        set_module_args(self.set_args_set_na_sg_grid_storage_api_certificate())
        my_obj = grid_certificate_module()
        mock_request.side_effect = [
            SRR["storage_api_cert"],  # get
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_set_na_sg_grid_storage_api_certificate_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_storage_api_certificate_pass(self, mock_request):
        args = self.set_args_set_na_sg_grid_storage_api_certificate()
        args["server_certificate"] = ""
        args["private_key"] = ""

        set_module_args(args)
        my_obj = grid_certificate_module()
        mock_request.side_effect = [
            SRR["storage_api_cert"],  # get
            SRR["update_good"],  # put
            SRR["storage_api_cert_update"],  # get
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_storage_api_certificate_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_delete_na_sg_storage_api_certificate_pass(self, mock_request):
        set_module_args(self.set_args_delete_na_sg_grid_storage_api_certificate())
        my_obj = grid_certificate_module()
        mock_request.side_effect = [
            SRR["storage_api_cert"],  # get
            SRR["delete_good"],  # delete
            SRR["cert_unset"],  # get
            SRR["end_of_sequence"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_delete_na_sg_storage_api_certificate_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]
