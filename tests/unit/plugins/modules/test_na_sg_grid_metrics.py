# (c) 2025, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests NetApp StorageGRID Metrics Ansible module: na_sg_grid_metrics """

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json
import pytest
import sys

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_metrics import (
    SgMetrics as metrics_module,
)

if sys.version_info < (3, 11):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 3.11")

# REST API canned responses when mocking send_request
SRR = {
    "empty_good": ({"data": []}, None),
    "end_of_sequence": (None, "Unexpected call to send_request"),
    "generic_error": (None, "Expected error"),
    "version_114": ({"data": {"productVersion": "11.4.0-20200721.1338.d3969b3"}}, None),
    "api_response_get_succeeded": (
        {
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {
                            "__name__": "storagegrid_storage_utilization_usable_space_bytes",
                            "instance": "sgf6112-tme-01",
                            "job": "ldr",
                            "node_id": "658a91d7-d6f4-4d8e-a8ba-e15e6408b604",
                            "service": "ldr",
                            "site_id": "99d94acc-b2d4-4e4e-86e5-b715af68b40b",
                            "site_name": "site1",
                        },
                        "value": [1756363578.839, "29456490549248"],
                    },
                ]
            }
        },
        None,
    ),
    "expected_sg_metric": (
        {
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {
                            "__name__": "storagegrid_storage_utilization_usable_space_bytes",
                            "instance": "sgf6112-tme-01",
                            "job": "ldr",
                            "node_id": "658a91d7-d6f4-4d8e-a8ba-e15e6408b604",
                            "service": "ldr",
                            "site_id": "99d94acc-b2d4-4e4e-86e5-b715af68b40b",
                            "site_name": "site1",
                        },
                        "value": [1756363578.839, "29456490549248"],
                    },
                ]
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


class TestMetricsModule(unittest.TestCase):
    """Unit Tests for na_sg_grid_metrics module"""

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args_fail_check(self):
        return dict(
            {
                "validate_certs": False,
                "timeout": 30
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "auth_token": "storagegrid-auth-token",
                "validate_certs": False,
                "query": "storagegrid_storage_utilization_usable_space_bytes",
                "time": "2025-08-01T00:00:00.000Z",
                "timeout": "120s"
            }
        )

    def set_args_get_metrics(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "auth_token": "storagegrid-auth-token",
                "validate_certs": False,
                "query": "storagegrid_storage_utilization_usable_space_bytes",
                "time": "2025-08-01T00:00:00.000Z",
                "timeout": "30s"
            }
        )

    def set_args_get_metrics_over_range(self):
        return dict(
            {
                "api_url": "https://<storagegrid-endpoint-url>",
                "auth_token": "storagegrid-auth-token",
                "validate_certs": False,
                "query": "storagegrid_storage_utilization_usable_space_bytes",
                "time": "2025-08-01T00:00:00.000Z",
                "end_time": "2025-08-02T00:00:00.000Z",
                "step": "60s",
                "timeout": "30s"
            }
        )

    def test_missing_required_args(self):
        """Test missing required arguments"""
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            metrics_module()
        assert "missing required arguments" in str(exc.value)

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_module_fail_when_required_args_present(self, mock_request):
        """required arguments are reported as errors"""
        mock_request.side_effect = [
            SRR["version_114"],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            metrics_module()
            exit_json(changed=False, msg="Induced arguments check")
        print("Info: test_module_fail_when_required_args_present: %s" % exc.value.args[0]["msg"])
        assert exc.value.args[0]["changed"] is False

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_get_na_sg_grid_metrics_pass(self, mock_request):
        set_module_args(self.set_args_get_metrics())
        mock_request.side_effect = [
            SRR["version_114"],  # SG version check
            SRR["api_response_get_succeeded"],  # Get Metrics
            SRR["end_of_sequence"],
        ]
        my_obj = metrics_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_get_na_sg_grid_metrics_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["sg_metric"] == SRR["expected_sg_metric"][0]["data"]
        assert exc.value.args[0]["changed"] is False

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_get_na_sg_grid_metrics_over_range_pass(self, mock_request):
        set_module_args(self.set_args_get_metrics_over_range())
        mock_request.side_effect = [
            SRR["version_114"],  # SG version check
            SRR["api_response_get_succeeded"],  # Get Metrics
            SRR["end_of_sequence"],
        ]
        my_obj = metrics_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print("Info: test_get_na_sg_grid_metrics_over_range_pass: %s" % repr(exc.value.args[0]))
        assert exc.value.args[0]["sg_metric"] == SRR["expected_sg_metric"][0]["data"]
        assert exc.value.args[0]["changed"] is False

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.SGRestAPI.send_request")
    def test_get_na_sg_grid_metrics_over_range_missing_step_fail(self, mock_request):
        args = self.set_args_get_metrics_over_range()
        args.pop("step")
        set_module_args(args)
        mock_request.side_effect = [
            SRR["version_114"],
            SRR["api_response_get_succeeded"],  # Get Metrics
            SRR["end_of_sequence"],
        ]
        my_obj = metrics_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        print("Info: test_get_na_sg_grid_metrics_over_range_missing_step_fail: %s" % repr(exc.value.args[0]))
        error = "If 'query' provided, 'time' (or 'start_time'), 'end_time', and 'step' must also be specified for query over range of time."
        assert exc.value.args[0]["msg"] == error
