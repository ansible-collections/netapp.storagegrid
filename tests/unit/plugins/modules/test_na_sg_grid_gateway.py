# (c) 2020, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Grid Load Balancer Endpoint Ansible module: na_sg_grid_gateway"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_gateway import (
    SgGridGateway as grid_gateway_module,
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
    "gateway_record": (
        {
            "data": {
                "id": "e777d415-057f-4d37-9b0c-6d132d872ea0",
                "displayName": "ansibletest-secure",
                "enableIPv4": True,
                "enableIPv6": True,
                "port": 10443,
                "secure": True,
                "accountId": "0",
            }
        },
        None,
    ),
    "gateway_record_ha_group_binding": (
        {
            "data": {
                "id": "e777d415-057f-4d37-9b0c-6d132d872ea0",
                "displayName": "ansibletest-secure",
                "enableIPv4": True,
                "enableIPv6": True,
                "port": 10443,
                "secure": True,
                "accountId": "0",
                "enable_tenant_manager": True,
                "enable_grid_manager": True,
                "pinTargets": {"haGroups": ["c08e6dca-038d-4a05-9499-6fbd1e6a4c3e"], "nodeInterfaces": [], "nodeTypes": ["adminNode"]},
            }
        },
        None,
    ),
    "gateway_record_node_interface_binding": (
        {
            "data": {
                "id": "e777d415-057f-4d37-9b0c-6d132d872ea0",
                "displayName": "ansibletest-secure",
                "enableIPv4": True,
                "enableIPv6": True,
                "port": 10443,
                "secure": True,
                "enable_tenant_manager": True,
                "enable_grid_manager": True,
                "accountId": "0",
                "pinTargets": {
                    "haGroups": [],
                    "nodeInterfaces": [
                        {"interface": "eth2", "nodeId": "0b1866ed-d6e7-41b4-815f-bf867348b76b"},
                        {"interface": "eth2", "nodeId": "970ad050-b68b-4aae-a94d-aef73f3095c4"},
                    ],
                    "nodeTypes": ["adminNode"],
                },
            }
        },
        None,
    ),
    "gateway_record_rename": (
        {
            "data": {
                "id": "e777d415-057f-4d37-9b0c-6d132d872ea0",
                "displayName": "ansibletest-rename",
                "enableIPv4": True,
                "enableIPv6": True,
                "port": 10443,
                "secure": True,
                "enable_tenant_manager": True,
                "enable_grid_manager": True,
                "accountId": "0",
                "pinTargets": {"haGroups": ["c08e6dca-038d-4a05-9499-6fbd1e6a4c3e"], "nodeInterfaces": [], "nodeTypes": ["adminNode"]},
            }
        },
        None,
    ),
    "ha_groups": (
        {
            "data": [
                {
                    "id": "c08e6dca-038d-4a05-9499-6fbd1e6a4c3e",
                    "name": "site1_primary",
                    "description": "test ha group",
                    "virtualIps": ["10.193.174.117"],
                    "interfaces": [
                        {
                            "nodeId": "0b1866ed-d6e7-41b4-815f-bf867348b76b",
                            "nodeName": "SITE1-ADM1",
                            "interface": "eth2",
                            "preferredMaster": True,
                        },
                        {
                            "nodeId": "970ad050-b68b-4aae-a94d-aef73f3095c4",
                            "nodeName": "SITE2-ADM1",
                            "interface": "eth2",
                        },
                    ],
                    "gatewayCidr": "192.168.14.1/24",
                },
                {
                    "id": "da9ac524-9a16-4be0-9d6e-ec9b22218e75",
                    "name": "site1_gw",
                    "description": "another test ha group",
                    "virtualIps": ["10.193.204.200"],
                    "interfaces": [
                        {
                            "nodeId": "7bb5bf05-a04c-4344-8abd-08c5c4048666",
                            "nodeName": "SITE1-GW1",
                            "interface": "eth0",
                            "preferredMaster": True,
                        },
                    ],
                    "gatewayCidr": "192.168.14.1/24",
                },
            ]
        },
        None,
    ),
    "node_health": (
        {
            "data": [
                {
                    "id": "0b1866ed-d6e7-41b4-815f-bf867348b76b",
                    "isPrimaryAdmin": True,
                    "name": "SITE1-ADM1",
                    "siteId": "ae56d06d-bd83-46bd-adce-77146b1d94bd",
                    "siteName": "SITE1",
                    "severity": "normal",
                    "state": "connected",
                    "type": "adminNode",
                },
                {
                    "id": "970ad050-b68b-4aae-a94d-aef73f3095c4",
                    "isPrimaryAdmin": False,
                    "name": "SITE2-ADM1",
                    "siteId": "7c24002e-5157-43e9-83e5-02db9b265b02",
                    "siteName": "SITE2",
                    "severity": "normal",
                    "state": "connected",
                    "type": "adminNode",
                },
            ]
        },
        None,
    ),
    "present_gateways": (
        {
            "data": [
                {
                    "id": "e777d415-057f-4d37-9b0c-6d132d872ea0",
                    "displayName": "ansibletest-secure",
                    "enableIPv4": True,
                    "enableIPv6": True,
                    "port": 10443,
                    "secure": True,
                    "accountId": "0",
                }
            ]
        },
        None,
    ),
    "present_gateways_with_binding": (
        {
            "data": [
                {
                    "id": "e777d415-057f-4d37-9b0c-6d132d872ea0",
                    "displayName": "ansibletest-secure",
                    "enableIPv4": True,
                    "enableIPv6": True,
                    "port": 10443,
                    "secure": True,
                    "accountId": "0",
                    "pinTargets": {"haGroups": [], "nodeInterfaces": []},
                }
            ]
        },
        None,
    ),
    "server_config": (
        {
            "data": {
                "defaultServiceType": "s3",
                "certSource": "plaintext",
                "plaintextCertData": {
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
                    "metadata": {
                        "serverCertificateDetails": {
                            "subject": "/CN=test",
                            "issuer": "/CN=test",
                            "serialNumber": "32:6F:20:EB:0E:90:60:7E:07:8F:6E:CC:02:2D:7C:37:3D:AB:42:7E",
                            "notBefore": "2021-09-27T12:39:17.000Z",
                            "notAfter": "2023-09-27T12:39:17.000Z",
                            "fingerPrints": {
                                "SHA-1": "A4:F9:74:BE:E8:A2:46:C2:E1:23:DE:8F:A8:1B:F1:C4:91:51:C5:56",
                                "SHA-256": "7B:65:7F:CD:35:8F:33:1C:C8:2D:F0:C1:9F:58:2F:2B:3B:78:44:95:4E:23:8C:1B:2B:91:6C:94:B0:71:64:E8",
                            },
                            "subjectAltNames": ["DNS:*.test.com"],
                        }
                    },
                },
            }
        },
        None,
    ),
    "server_config_cert_update": (
        {
            "data": {
                "defaultServiceType": "s3",
                "certSource": "plaintext",
                "plaintextCertData": {
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
                    "metadata": {
                        "serverCertificateDetails": {
                            "subject": "/CN=test",
                            "issuer": "/CN=test",
                            "serialNumber": "32:6F:20:EB:0E:90:60:7E:07:8F:6E:CC:02:2D:7C:37:3D:AB:42:7E",
                            "notBefore": "2021-09-27T12:39:17.000Z",
                            "notAfter": "2023-09-27T12:39:17.000Z",
                            "fingerPrints": {
                                "SHA-1": "F2:C2:6F:A8:45:DA:86:09:91:F5:04:B0:25:43:B7:FC:FA:C1:43:F8",
                                "SHA-256": "99:3E:21:1A:03:25:69:C8:0A:D5:FE:E3:FB:6E:51:03:BD:A7:0E:88:6B:53:06:04:92:3B:34:17:68:43:F7:2F",
                            },
                            "subjectAltNames": ["DNS:*.test.com"],
                        }
                    },
                },
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
                "display_name": "ansibletest-secure",
                "default_service_type": "s3",
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
                "display_name": "ansibletest-secure",
                "default_service_type": "s3",
                "port": 10443,
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
                "api_url": "https://gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_create_na_sg_grid_gateway_port(self):
        return dict(
            {
                "state": "present",
                "display_name": "ansibletest-secure",
                "default_service_type": "s3",
                "port": 10443,
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
                "api_url": "https://gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
            }
        )

    def set_args_delete_na_sg_grid_gateway_port(self):
        return dict(
            {
                "state": "absent",
                "display_name": "ansibletest-secure",
                "default_service_type": "s3",
                "port": 10443,
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
                "api_url": "https://gmi.example.com",
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
            grid_gateway_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_pass_when_required_args_present(self, mock_request):
        """required arguments are reported as errors"""
        mock_request.side_effect = [
            SRR["version_114"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            grid_gateway_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_pass_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_gateway_port_pass(self, mock_request):
        set_module_args(self.set_args_create_na_sg_grid_gateway_port())
        mock_request.side_effect = [
            SRR["version_114"],  # get
            SRR["empty_good"],  # get
            SRR["gateway_record"],  # post
            SRR["server_config"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_gateway_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_grid_gateway_port_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_create_na_sg_grid_gateway_port_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_gateway_port()
        del args["private_key"]
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],  # get
            SRR["present_gateways"],  # get
            SRR["server_config"],  # get
            SRR["end_of_sequence"],
        ]
        my_obj = grid_gateway_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_create_na_sg_grid_gateway_port_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_gateway_certificate_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_gateway_port()
        args["server_certificate"] = "-----BEGIN CERTIFICATE-----\nABCDEFGABCD\n-----END CERTIFICATE-----\n"
        args["private_key"] = "-----BEGIN PRIVATE KEY-----\nABCDEFGABCD\n-----END PRIVATE KEY-----\n"

        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],  # get
            SRR["present_gateways"],  # get
            SRR["server_config"],  # get
            SRR["server_config_cert_update"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_gateway_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_gateway_certificate_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_delete_na_sg_grid_gateway_port_pass(self, mock_request):
        set_module_args(self.set_args_delete_na_sg_grid_gateway_port())
        mock_request.side_effect = [
            SRR["version_114"],  # get
            SRR["present_gateways"],  # get
            SRR["server_config"],  # get
            SRR["delete_good"],  # delete
            SRR["end_of_sequence"],
        ]
        my_obj = grid_gateway_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_delete_na_sg_grid_gateway_port_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_minimum_version_not_met(self, mock_request):
        args = self.set_args_create_na_sg_grid_gateway_port()
        args["binding_mode"] = "ha-groups"
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],  # get
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            grid_gateway_module()
        print("Info: test_module_fail_minimum_version_not_met: %s" % exc.value.args[0]["msg"])

    # test create with ha groups
    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_gateway_port_with_ha_group_binding_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_gateway_port()
        args["binding_mode"] = "ha-groups"
        args["ha_groups"] = ["site1_primary", "da9ac524-9a16-4be0-9d6e-ec9b22218e75"]
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_116"],  # get
            SRR["ha_groups"],  # get
            SRR["empty_good"],  # get
            SRR["gateway_record_ha_group_binding"],  # post
            SRR["server_config"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_gateway_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_create_na_sg_grid_gateway_port_with_ha_group_binding_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    # test create with bad ha group ID
    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_gateway_port_with_bad_ha_group_binding_fail(self, mock_request):
        mock_request.side_effect = [
            SRR["version_116"],  # get
            SRR["ha_groups"],  # get
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            args = self.set_args_create_na_sg_grid_gateway_port()
            args["binding_mode"] = "ha-groups"
            args["ha_groups"] = ["fffac524-9a16-4be0-9d6e-ec9b22218e75"]
            set_module_args(args)
            grid_gateway_module()
        print("Info: test_create_na_sg_grid_gateway_port_with_bad_ha_group_binding_fail: %s" % repr(exc.value.args[0]))

    # test create with node interfaces
    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_create_na_sg_grid_gateway_port_with_node_interface_binding_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_gateway_port()
        args["binding_mode"] = "node-interfaces"
        args["node_interfaces"] = [
            {"node": "SITE1-ADM1", "interface": "eth2"},
            {"node": "SITE2-ADM1", "interface": "eth2"},
        ]
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_116"],  # get
            SRR["node_health"],  # get
            SRR["empty_good"],  # get
            SRR["gateway_record_node_interface_binding"],  # post
            SRR["server_config"],  # post
            SRR["end_of_sequence"],
        ]
        my_obj = grid_gateway_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print(
            "Info: test_create_na_sg_grid_gateway_port_with_node_interface_binding_pass: %s" % repr(exc.value.args[0])
        )
        assert exc.value.args[0]["changed"]

    # test change from global to ha groups
    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_gateway_binding_to_ha_groups_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_gateway_port()
        args["binding_mode"] = "ha-groups"
        args["ha_groups"] = "site1_primary"
        args["server_certificate"] = "-----BEGIN CERTIFICATE-----\nABCDEFGABCD\n-----END CERTIFICATE-----\n"
        args["private_key"] = "-----BEGIN PRIVATE KEY-----\nABCDEFGABCD\n-----END PRIVATE KEY-----\n"
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_116"],  # get
            SRR["ha_groups"],  # get
            SRR["present_gateways_with_binding"],  # get
            SRR["server_config"],  # get
            SRR["gateway_record_ha_group_binding"],  # put
            SRR["server_config_cert_update"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_gateway_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_gateway_binding_to_ha_groups_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    # test rename by supplying gateway_id
    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_gateway_rename_pass(self, mock_request):
        args = self.set_args_create_na_sg_grid_gateway_port()
        args["gateway_id"] = "e777d415-057f-4d37-9b0c-6d132d872ea0"
        args["binding_mode"] = "ha-groups"
        args["ha_groups"] = "site1_primary"
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_116"],  # get
            SRR["ha_groups"],  # get
            SRR["gateway_record_ha_group_binding"],  # get
            SRR["server_config"],  # get
            SRR["gateway_record_rename"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_gateway_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_gateway_rename_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]
