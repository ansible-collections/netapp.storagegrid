# (c) 2025, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' Unit Tests NetApp StorageGRID PGE Ansible module: na_sg_pge_info '''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json
import pytest
import sys

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.storagegrid.tests.unit.compat import unittest
from ansible_collections.netapp.storagegrid.tests.unit.compat.mock import patch

from ansible_collections.netapp.storagegrid.plugins.modules.na_sg_pge_info \
    import NetAppSgGatherPgeInfo as sg_pge_info_module

if sys.version_info < (3, 11):
    pytestmark = pytest.mark.skip("Skipping Unit Tests on 3.11")

# REST API canned responses when mocking send_request.
SRR = {
    # common responses
    'empty_good': ({'data': []}, None),
    'end_of_sequence': (None, 'Unexpected call to send_request'),
    'generic_error': (None, 'Expected error'),
    'pge_storage_configuration_networking': (
        {
            "data": {
                "configUpdateBusy": False,
                "controllers": {
                    "A": {
                        "configIpv4": {
                            "cidr": "10.193.92.153/21",
                            "gateway": "10.193.91.3",
                            "useDhcp": False
                        },
                        "configIpv6": {
                            "address": "0000:0000:0000:0000:0000:0000:0000:0000",
                            "configType": "STATIC",
                            "gateway": "0000:0000:0000:0000:0000:0000:0000:0000",
                            "linkLocalAddress": "0000:0000:0000:0000:0000:0000:0000:0000",
                            "routableAddresses": []
                        },
                        "enableIpv4": True,
                        "enableIpv6": False,
                        "linkStatus": "UP",
                        "macAddr": "d0:38:ea:94:fe:20"
                    },
                    "B": {
                        "configIpv4": {
                            "cidr": "10.193.92.154/23",
                            "gateway": "10.193.91.3",
                            "useDhcp": False
                        },
                        "configIpv6": {
                            "address": "0000:0000:0000:0000:0000:0000:0000:0000",
                            "configType": "STATIC",
                            "gateway": "0000:0000:0000:0000:0000:0000:0000:0000",
                            "linkLocalAddress": "0000:0000:0000:0000:0000:0000:0000:0000",
                            "routableAddresses": []
                        },
                        "enableIpv4": True,
                        "enableIpv6": False,
                        "linkStatus": "UP",
                        "macAddr": "d0:38:ea:94:f2:dd"
                    }
                },
                "hasSc": True,
                "recentErrors": []
            },
        },
        None,
    ),
    'pge_bmc_config': ({'data': []}, None),
    'pge_install_status': ({'data': {}}, None),
    'pge_networks': ({'data': []}, None),
    'pge_link_config': ({'data': []}, None),
    'pge_dns': (
        {
            "data": {
                "nameservers": ["10.102.76.113", "10.102.76.214"],
                "search": []
            }
        },
        None,
    ),
    'pge_system_info': (
        {
            "data": {
                "boardName": "Excalibur",
                "canInstall": True,
                "chassisSerial": "952221000554",
                "cloneFlag": None,
                "compatibilityError": False,
                "computeControllerNeedsAttention": True,
                "computeSerialNumber": "372227000345",
                "controllerSSDWarning": False,
                "driveSizeError": False,
                "encryptionError": False,
                "installBtnMsgKey": "pge.home.install.msgs_html.ready",
                "installFailed": False,
                "installerVersion": "3.6.0",
                "installing": False,
                "lacpLinkWarning": False,
                "maintenanceMode": False,
                "modelName": "SG6060",
                "needsAttention": True,
                "networkConfigured": True,
                "networkError": False,
                "numberOfConfigurableShelves": 0,
                "numberOfConfiguredShelves": 1,
                "numberOfExpansionShelves": 0,
                "numberOfPartiallyConfiguredShelves": 0,
                "numberOfUnassignedDrives": 0,
                "numberOfUnconfigurableShelves": 0,
                "pairCfw": "08.73.00.00",
                "suboptimalVolumes": None,
                "symbolError": False,
                "utmTunnelSupported": True
            }
        },
        None
    ),
    'pge_system_config': (
        {
            "data": {
                "driveSizesArray": [
                    {
                        "driveSize": "800 GB",
                        "driveType": "ssd",
                        "numDrives": 2
                    },
                    {
                        "driveSize": "4.00 TB",
                        "driveType": "hdd",
                        "numDrives": 58
                    }
                ],
                "name": "sg6060-tme-13",
                "nodeType": "storage",
                "raidMode": "ddp",
                "rawCapacityArray": [
                    {
                        "raidMode": "ddp",
                        "rawCapacity": "174.81 TB"
                    },
                    {
                        "raidMode": "ddp16",
                        "rawCapacity": "193.26 TB"
                    },
                    {
                        "raidMode": "raid6",
                        "rawCapacity": "203.76 TB"
                    }
                ],
                "supportedModes": ["raid6", "ddp", "ddp16"],
                "supportedNodeTypes": ["storage"]
            }
        },
        None
    ),
    'pge_admin_connections': ({'data': []}, None),
    'pge_ipmi_sensors': ({'data': []}, None),
    'pge_upgrade_status': (
        {
            "data": {
                "activePartFirmware": "3.6.0-20220120.2255.054fec9",
                "checksumUploaded": False,
                "firmwareUploaded": False,
                "inactivePartFirmware": "3.6.0-20220120.2255.054fec9",
                "logMessages": [],
                "upgradeStatus": "awaiting-upload",
                "uploadedFirmwareVersion": None
            }
        },
        None,
    ),
    'pge_debug_dump_addr_show': ({'data': []}, None),
    'pge_debug_dump_routes': ({'data': []}, None),
    'pge_debug_dump_bonding': ({'data': []}, None),
    'pge_debug_dump_netlink': ({'data': []}, None),
    'pge_debug_dump_bonding_raw': ({'data': []}, None),
    'pge_debug_dump_lldp_attributes': ({'data': []}, None),

}


def set_module_args(args):
    ''' Prepare arguments so that they will be picked up during module creation '''
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


class AnsibleExitJson(Exception):
    ''' Exception class to be raised by module.exit_json and caught by the test case '''
    pass


class AnsibleFailJson(Exception):
    ''' Exception class to be raised by module.fail_json and caught by the test case '''
    pass


def exit_json(*args, **kwargs):  # pylint: disable=unused-argument
    ''' Function to patch over exit_json; package return data into an exception '''
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):  # pylint: disable=unused-argument
    ''' Function to patch over fail_json; package return data into an exception '''
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


class TestMyModule(unittest.TestCase):
    ''' A group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args_fail_check(self):
        return dict(
            {
                'validate_certs': False,
            }
        )

    def set_default_args_pass_check(self):
        return dict(
            {
                'api_url': 'sgmi.example.com'
            }
        )

    def set_default_optional_args_pass_check(self):
        return dict(
            {
                'api_url': 'sgmi.example.com',
                'validate_certs': False,
                'gather_subset': ['all'],
                'parameters': {'limit': 5},
            }
        )

    def set_args_run_sg_gather_facts_for_all_info(self):
        return dict({
            'api_url': 'sgmi.example.com',
            'validate_certs': False,
        })

    def set_args_run_sg_gather_facts_for_pge_system_info(self):
        return dict({
            'api_url': 'sgmi.example.com',
            'validate_certs': False,
            'gather_subset': ['pge_system_info'],
        })

    def set_args_run_sg_gather_facts_for_storage_configuration_networking_and_dns_info(self):
        return dict({
            'api_url': 'sgmi.example.com',
            'validate_certs': False,
            'gather_subset': ['pge_storage_configuration_networking', 'pge/dns'],
        })

    def set_args_run_sg_gather_facts_for_pge_upgrade_status(self):
        return dict({
            'api_url': 'sgmi.example.com',
            'validate_certs': False,
            'gather_subset': ['pge_upgrade_status'],
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            sg_pge_info_module()
        print(
            'Info: test_module_fail_when_required_args_missing: %s'
            % exc.value.args[0]['msg']
        )

    def test_module_pass_when_required_args_present(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            sg_pge_info_module()
            exit_json(changed=True, msg='Induced arguments check')
        print(
            'Info: test_module_pass_when_required_args_present: %s'
            % exc.value.args[0]['msg']
        )
        assert exc.value.args[0]['changed']

    def test_module_pass_when_optional_args_present(self):
        ''' Optional arguments are reported as pass '''
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_optional_args_pass_check())
            sg_pge_info_module()
            exit_json(changed=True, msg='Induced arguments check')
        print(
            'Info: test_module_pass_when_optional_args_present: %s'
            % exc.value.args[0]['msg']
        )
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request')
    def test_run_sg_gather_facts_for_all_info_pass(self, mock_request):
        set_module_args(self.set_args_run_sg_gather_facts_for_all_info())
        my_obj = sg_pge_info_module()
        gather_subset = [
            'pge/storage-configuration/networking',
            'pge/bmc-config',
            'pge/install-status',
            'pge/networks',
            'pge/link-config',
            'pge/dns',
            'pge/system-info',
            'pge/system-config',
            'pge/admin-connection',
            'pge/ipmi-sensors',
            'pge/upgrade/status',
            'pge/debug/dump-addr-show',
            'pge/debug/dump-routes',
            'pge/debug/dump-bonding',
            'pge/debug/dump-netlink',
            'pge/debug/dump-bonding-raw',
            'pge/debug/dump-lldp-attributes',
        ]
        mock_request.side_effect = [
            SRR['pge_storage_configuration_networking'],
            SRR['pge_bmc_config'],
            SRR['pge_install_status'],
            SRR['pge_networks'],
            SRR['pge_link_config'],
            SRR['pge_dns'],
            SRR['pge_system_info'],
            SRR['pge_system_config'],
            SRR['pge_admin_connections'],
            SRR['pge_ipmi_sensors'],
            SRR['pge_upgrade_status'],
            SRR['pge_debug_dump_addr_show'],
            SRR['pge_debug_dump_routes'],
            SRR['pge_debug_dump_bonding'],
            SRR['pge_debug_dump_netlink'],
            SRR['pge_debug_dump_bonding_raw'],
            SRR['pge_debug_dump_lldp_attributes'],
            SRR['end_of_sequence'],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_run_sg_gather_facts_for_all_info_pass: %s' % repr(exc.value.args))
        assert set(exc.value.args[0]['sg_info']) == set(gather_subset)

    @patch('ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request')
    def test_run_sg_gather_facts_for_pge_system_info_pass(self, mock_request):
        set_module_args(self.set_args_run_sg_gather_facts_for_pge_system_info())
        my_obj = sg_pge_info_module()
        gather_subset = ['pge/system-info']
        mock_request.side_effect = [
            SRR['pge_system_info'],
            SRR['end_of_sequence'],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_run_sg_gather_facts_for_pge_system_info_pass: %s' % repr(exc.value.args))
        assert set(exc.value.args[0]['sg_info']) == set(gather_subset)

    @patch('ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request')
    def test_run_sg_gather_facts_for_storage_configuration_networking_and_dns_info_pass(self, mock_request):
        set_module_args(self.set_args_run_sg_gather_facts_for_storage_configuration_networking_and_dns_info())
        my_obj = sg_pge_info_module()
        gather_subset = ['pge/storage-configuration/networking', 'pge/dns']
        mock_request.side_effect = [
            SRR['pge_storage_configuration_networking'],
            SRR['pge_dns'],
            SRR['end_of_sequence'],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_run_sg_gather_facts_for_storage_configuration_networking_and_dns_info_pass: %s' % repr(exc.value.args))
        assert set(exc.value.args[0]['sg_info']) == set(gather_subset)

    @patch('ansible_collections.netapp.storagegrid.plugins.module_utils.netapp.PgeRestAPI.send_request')
    def test_get_na_sg_pge_info_upgrade_status_pass(self, mock_request):
        set_module_args(self.set_args_run_sg_gather_facts_for_pge_upgrade_status())
        my_obj = sg_pge_info_module()
        gather_subset = ['pge/upgrade/status']
        mock_request.side_effect = [
            SRR['pge_upgrade_status'],
            SRR['end_of_sequence'],
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_get_na_sg_pge_info_upgrade_status_pass: %s' % repr(exc.value.args))
        assert set(exc.value.args[0]['sg_info']) == set(gather_subset)
