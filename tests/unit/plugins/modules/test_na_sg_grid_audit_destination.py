# (c) 2025, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Audit destination Ansible module: na_sg_grid_audit_destination"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_audit_destination import (
    SgAuditDestination as grid_audit_destination_module,
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
    "api_response_existing_audit_destination_defaults": (
        {
            "data": {
                "defaults": {
                    "adminNodes": {
                        "enabled": True
                    },
                    "remoteSyslogServerA": {
                        "enabled": False,
                        "protocol": "udp",
                        "insecureTLS": False,
                        "hostname": "syslog1.example.com",
                        "port": 514,
                        "authEventsSend": True,
                        "authEventsFacility": -1,
                        "authEventsSeverity": -1,
                        "auditLogsSend": True,
                        "auditLogsFacility": 23,
                        "auditLogsSeverity": 6,
                        "applicationLogsSend": True,
                        "applicationLogsFacility": -1,
                        "applicationLogsSeverity": -1
                    },
                    "remoteSyslogServerATest": {
                        "enabled": True,
                        "protocol": "udp",
                        "insecureTLS": False,
                        "hostname": "syslog.example.com",
                        "port": 514,
                        "authEventsSend": True,
                        "authEventsFacility": -1,
                        "authEventsSeverity": -1,
                        "auditLogsSend": True,
                        "auditLogsFacility": 23,
                        "auditLogsSeverity": 6,
                        "applicationLogsSend": True,
                        "applicationLogsFacility": -1,
                        "applicationLogsSeverity": -1
                    }
                },
            }
        },
        None,
    ),
    "api_response_existing_audit_destination_defaults_updated": (
        {
            "data": {
                "defaults": {
                    "adminNodes": {
                        "enabled": False
                    },
                    "remoteSyslogServerA": {
                        "enabled": False,
                        "protocol": "udp",
                        "insecureTLS": False,
                        "hostname": "syslog1.example.com",
                        "port": 514,
                        "authEventsSend": True,
                        "authEventsFacility": -1,
                        "authEventsSeverity": -1,
                        "auditLogsSend": True,
                        "auditLogsFacility": 23,
                        "auditLogsSeverity": 6,
                        "applicationLogsSend": True,
                        "applicationLogsFacility": -1,
                        "applicationLogsSeverity": -1
                    },
                    "remoteSyslogServerATest": {
                        "enabled": True,
                        "protocol": "udp",
                        "insecureTLS": False,
                        "hostname": "syslog.example.com",
                        "port": 514,
                        "authEventsSend": True,
                        "authEventsFacility": -1,
                        "authEventsSeverity": -1,
                        "auditLogsSend": True,
                        "auditLogsFacility": 23,
                        "auditLogsSeverity": 6,
                        "applicationLogsSend": True,
                        "applicationLogsFacility": -1,
                        "applicationLogsSeverity": -1
                    }
                },
            }
        },
        None,
    ),
    "api_response_existing_audit_destination_node": (
        {
            "data": {
                "nodes": {
                    "node": {
                        "adminNodes": {
                            "enabled": True
                        },
                        "remoteSyslogServerA": {
                            "enabled": False,
                            "protocol": "tcp",
                            "insecureTLS": False,
                            "hostname": "syslog.example.com",
                            "port": 514,
                            "authEventsSend": True,
                            "authEventsFacility": -1,
                            "authEventsSeverity": -1,
                            "auditLogsSend": True,
                            "auditLogsFacility": 23,
                            "auditLogsSeverity": 7,
                            "applicationLogsSend": True,
                            "applicationLogsFacility": -1,
                            "applicationLogsSeverity": -1
                        },
                        "remoteSyslogServerATest": {
                            "enabled": True,
                            "protocol": "tls",
                            "hostname": "syslog.example.com",
                            "port": 514,
                            "authEventsSend": True,
                            "authEventsFacility": -1,
                            "authEventsSeverity": -1,
                            "auditLogsSend": True,
                            "auditLogsFacility": -1,
                            "auditLogsSeverity": -1,
                            "applicationLogsSend": True,
                            "applicationLogsFacility": -1,
                            "applicationLogsSeverity": -1
                        }
                    },
                }
            }
        },
        None,
    ),
    "api_response_existing_audit_destination_node_updated": (
        {
            "data": {
                "nodes": {
                    "node": {
                        "adminNodes": {
                            "enabled": False
                        },
                        "remoteSyslogServerA": {
                            "enabled": False,
                            "protocol": "tcp",
                            "insecureTLS": False,
                            "hostname": "syslog.example.com",
                            "port": 514,
                            "authEventsSend": True,
                            "authEventsFacility": -1,
                            "authEventsSeverity": -1,
                            "auditLogsSend": True,
                            "auditLogsFacility": 23,
                            "auditLogsSeverity": 7,
                            "applicationLogsSend": True,
                            "applicationLogsFacility": -1,
                            "applicationLogsSeverity": -1
                        },
                        "remoteSyslogServerATest": {
                            "enabled": True,
                            "protocol": "tls",
                            "hostname": "syslog.example.com",
                            "insecureTLS": False,
                            "port": 514,
                            "authEventsSend": True,
                            "authEventsFacility": -1,
                            "authEventsSeverity": -1,
                            "auditLogsSend": True,
                            "auditLogsFacility": -1,
                            "auditLogsSeverity": -1,
                            "applicationLogsSend": True,
                            "applicationLogsFacility": -1,
                            "applicationLogsSeverity": -1
                        }
                    },
                }
            }
        },
        None,
    )
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
                "defaults": {
                    "admin_nodes": {
                        "enabled": True
                    },
                    "remote_syslog_server": {
                        "enabled": False,
                        "protocol": "udp"
                    },
                    "remote_syslog_server_test": {
                        "enabled": True,
                        "protocol": "udp"
                    },
                }
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "state": "present",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
                "defaults": {
                    "admin_nodes": {
                        "enabled": True
                    },
                    "remote_syslog_server": {
                        "enabled": False,
                        "protocol": "udp",
                        "port": 514,
                        "hostname": "syslog1.example.com",
                        "auth_events_send": True,
                        "auth_events_facility": -1,
                        "auth_events_severity": -1,
                        "audit_logs_send": True,
                        "audit_logs_facility": 23,
                        "audit_logs_severity": 6,
                        "application_logs_send": True,
                        "application_logs_facility": -1,
                        "application_logs_severity": -1
                    },
                    "remote_syslog_server_test": {
                        "enabled": True,
                        "protocol": "udp",
                        "port": 514,
                        "hostname": "syslog.example.com",
                        "auth_events_send": True,
                        "auth_events_facility": -1,
                        "auth_events_severity": -1,
                        "audit_logs_send": True,
                        "audit_logs_facility": 23,
                        "audit_logs_severity": 6,
                        "application_logs_send": True,
                        "application_logs_facility": -1,
                        "application_logs_severity": -1,
                    },
                }
            }
        )

    def set_args_update_na_sg_grid_audit_destination_defaults_pass_check(self):
        return dict(
            {
                "state": "present",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
                "defaults": {
                    "admin_nodes": {
                        "enabled": False
                    },
                    "remote_syslog_server": {
                        "enabled": False,
                        "protocol": "udp",
                        "port": 514,
                        "hostname": "syslog1.example.com",
                        "auth_events_send": True,
                        "auth_events_facility": -1,
                        "auth_events_severity": -1,
                        "audit_logs_send": True,
                        "audit_logs_facility": 23,
                        "audit_logs_severity": 6,
                        "application_logs_send": True,
                        "application_logs_facility": -1,
                        "application_logs_severity": -1,
                    },
                    "remote_syslog_server_test": {
                        "enabled": True,
                        "protocol": "udp",
                        "port": 514,
                        "hostname": "syslog.example.com",
                        "auth_events_send": True,
                        "auth_events_facility": -1,
                        "auth_events_severity": -1,
                        "audit_logs_send": True,
                        "audit_logs_facility": 23,
                        "audit_logs_severity": 6,
                        "application_logs_send": True,
                        "application_logs_facility": -1,
                        "application_logs_severity": -1,
                    },
                },
            }
        )

    def set_args_update_na_sg_grid_audit_destination_nodes_pass_check(self):
        return dict(
            {
                "state": "present",
                "api_url": "gmi.example.com",
                "auth_token": "01234567-5678-9abc-78de-9fgabc123def",
                "validate_certs": False,
                "nodes": [
                    {
                        "node_id": "node",
                        "admin_nodes": {
                            "enabled": False
                        },
                        "remote_syslog_server": {
                            "enabled": False,
                            "protocol": "tcp",
                            "insecure_TLS": False,
                            "hostname": "syslog.example.com",
                            "port": 514,
                            "auth_events_send": True,
                            "auth_events_facility": -1,
                            "auth_events_severity": -1,
                            "audit_logs_send": True,
                            "audit_logs_facility": 23,
                            "audit_logs_severity": 7,
                            "application_logs_send": True,
                            "application_logs_facility": -1,
                            "application_logs_severity": -1
                        },
                        "remote_syslog_server_test": {
                            "enabled": True,
                            "protocol": "tls",
                            "insecure_TLS": False,
                            "hostname": "syslog.example.com",
                            "port": 514,
                            "auth_events_send": True,
                            "auth_events_facility": -1,
                            "auth_events_severity": -1,
                            "audit_logs_send": True,
                            "audit_logs_facility": -1,
                            "audit_logs_severity": -1,
                            "application_logs_send": True,
                            "application_logs_facility": -1,
                            "application_logs_severity": -1
                        }
                    },
                ],
            }
        )

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_when_required_args_missing(self, mock_request):
        """required arguments are reported as errors"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            grid_audit_destination_module()
        print("Info: test_module_fail_when_required_args_missing: %s" % exc.value.args[0]["msg"])

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_succeed_when_required_args_present(self, mock_request):
        """required arguments are present"""
        mock_request.side_effect = [
            SRR["version_114"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            grid_audit_destination_module()
            exit_json(changed=True, msg="Induced arguments check")
        print("Info: test_module_succeed_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_audit_destination_defaults_pass(self, mock_request):
        args = self.set_args_update_na_sg_grid_audit_destination_defaults_pass_check()

        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["api_response_existing_audit_destination_defaults"],  # get
            SRR["api_response_existing_audit_destination_defaults_updated"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_audit_destination_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_audit_destination_defaults_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_update_na_sg_grid_audit_destination_defaults_pass(self, mock_request):
        set_module_args(self.set_args_update_na_sg_grid_audit_destination_defaults_pass_check())
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["api_response_existing_audit_destination_defaults_updated"],  # get
            SRR["end_of_sequence"],
        ]
        my_obj = grid_audit_destination_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_update_na_sg_grid_audit_destination_defaults_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_update_na_sg_grid_audit_destination_nodes_pass(self, mock_request):
        args = self.set_args_update_na_sg_grid_audit_destination_nodes_pass_check()

        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["api_response_existing_audit_destination_node"],  # get
            SRR["api_response_existing_audit_destination_node_updated"],  # put
            SRR["end_of_sequence"],
        ]
        my_obj = grid_audit_destination_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_update_na_sg_grid_audit_destination_nodes_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_idempotent_update_na_sg_grid_audit_destination_nodes_pass(self, mock_request):
        set_module_args(self.set_args_update_na_sg_grid_audit_destination_nodes_pass_check())
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["api_response_existing_audit_destination_node_updated"],  # get
            SRR["end_of_sequence"],
        ]
        my_obj = grid_audit_destination_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_idempotent_update_na_sg_grid_audit_destination_nodes_pass: %s" % repr(exc.value.args[0]))
        assert not exc.value.args[0]["changed"]
