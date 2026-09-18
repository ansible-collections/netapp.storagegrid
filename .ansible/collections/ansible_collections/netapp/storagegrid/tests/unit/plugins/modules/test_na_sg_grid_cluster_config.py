# (c) 2026, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for na_sg_grid_cluster_config module."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import pytest

from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_grid_cluster_config import (
    SgGridClusterConfig as cluster_config_module,
)


SRR = {
    "grid_details_existing": ({"data": {"name": "my-grid"}}, None),
    "grid_details_updated": ({"data": {"name": "my-grid", "license": "abc"}}, None),
    "dns_existing": ({"data": ["10.224.223.130"]}, None),
    "dns_updated": ({"data": ["10.224.223.130"]}, None),
    "ntp_existing": ({"data": ["10.235.48.111"]}, None),
    "ntp_updated": ({"data": ["10.235.48.111"]}, None),
    "grid_networks_existing": ({"data": ["172.16.160.0/19"]}, None),
    "grid_networks_updated": ({"data": ["10.193.204.0/24", "172.16.160.0/19"]}, None),
    "sites_empty": ({"data": []}, None),
    "sites_existing": ({"data": [{"id": "site-1", "name": "gdl"}]}, None),
    "site_created": ({"data": {"id": "site-1", "name": "gdl"}}, None),
    "passwords_updated": ({"data": {}}, None),
    "nodes_pending": (
        {
            "data": [
                {
                    "id": "node-1",
                    "name": "sg100-tme-06",
                    "type": "adminNode",
                    "isPrimaryAdmin": True,
                    "configured": False,
                    "hardware": "",
                    "networks": {
                        "grid": {
                            "mac": "00:11:22:33:44:55",
                            "ip": "10.193.204.26/24",
                            "gateway": "10.193.204.1",
                        }
                    },
                }
            ]
        },
        None,
    ),
    "node_approved": ({"data": {}}, None),
    "start_ok": ({"data": {}}, None),
    "end_of_sequence": (None, "Unexpected call to send_request"),
}


def set_module_args(args):
    """Prepare arguments so they are picked up during module creation."""
    args = json.dumps({"ANSIBLE_MODULE_ARGS": args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


class AnsibleExitJson(Exception):
    """Raised when module.exit_json is called."""


class AnsibleFailJson(Exception):
    """Raised when module.fail_json is called."""


def exit_json(*args, **kwargs):  # pylint: disable=unused-argument
    """Patch exit_json to raise an exception for assertions."""
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):  # pylint: disable=unused-argument
    """Patch fail_json to raise an exception for assertions."""
    kwargs["failed"] = True
    raise AnsibleFailJson(kwargs)


class TestSgGridClusterConfig(unittest.TestCase):
    """Unit tests for na_sg_grid_cluster_config."""

    def setUp(self):
        self.mock_module_helper = patch.multiple(
            basic.AnsibleModule,
            exit_json=exit_json,
            fail_json=fail_json,
        )
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def base_args(self):
        return {
            "api_url": "https://10.193.174.26",
            "validate_certs": False,
            "state": "present",
        }

    def full_args(self):
        args = self.base_args()
        args.update(
            {
                "grid_name": "my-grid",
                "license": "abc",
                "dns_servers": ["10.224.223.130"],
                "ntp_servers": ["10.235.48.111"],
                "grid_networks": ["10.193.204.0/24", "172.16.160.0/19"],
                "site_name": "gdl",
                "provision_passphrase": "provision-pass",
                "management_passphrase": "management-pass",
                "use_random_passwords": False,
                "approve_nodes": True,
                "start_provisioning": True,
            }
        )
        return args

    def test_missing_required_args(self):
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            cluster_config_module()
        assert "missing required arguments" in str(exc.value)

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request")
    def test_no_changes_when_desired_matches_current(self, mock_request):
        args = self.base_args()
        args.update(
            {
                "grid_name": "my-grid",
                "dns_servers": ["10.224.223.130"],
                "ntp_servers": ["10.235.48.111"],
                "grid_networks": ["172.16.160.0/19"],
            }
        )
        set_module_args(args)
        mock_request.side_effect = [
            SRR["grid_details_existing"],
            SRR["dns_existing"],
            SRR["ntp_existing"],
            SRR["grid_networks_existing"],
            SRR["end_of_sequence"],
        ]

        my_obj = cluster_config_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()

        assert not exc.value.args[0]["changed"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request")
    def test_apply_full_flow_changed(self, mock_request):
        set_module_args(self.full_args())
        mock_request.side_effect = [
            SRR["grid_details_existing"],
            SRR["grid_details_updated"],
            SRR["dns_existing"],
            SRR["ntp_existing"],
            SRR["grid_networks_existing"],
            SRR["grid_networks_updated"],
            SRR["sites_empty"],
            SRR["site_created"],
            SRR["passwords_updated"],
            SRR["nodes_pending"],
            SRR["node_approved"],
            SRR["start_ok"],
            SRR["end_of_sequence"],
        ]

        my_obj = cluster_config_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()

        result = exc.value.args[0]
        assert result["changed"]
        assert result["resp"]["passwords_set"]
        assert result["resp"]["nodes_approved"] == 1
        assert result["resp"]["provisioning_started"]

    @patch("ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request")
    def test_approve_nodes_fails_without_site(self, mock_request):
        args = self.base_args()
        args.update({"approve_nodes": True})
        set_module_args(args)

        mock_request.side_effect = [
            SRR["nodes_pending"],
            SRR["sites_empty"],
            SRR["end_of_sequence"],
        ]

        my_obj = cluster_config_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()

        assert "No site found" in exc.value.args[0]["msg"]

    def test_password_validation_requires_both_passphrases(self):
        args = self.base_args()
        args.update(
            {
                "provision_passphrase": "only-provision",
                "management_passphrase": None,
                "use_random_passwords": False,
            }
        )
        set_module_args(args)

        my_obj = cluster_config_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()

        assert "Both 'provision_passphrase' and 'management_passphrase'" in exc.value.args[0]["msg"]
