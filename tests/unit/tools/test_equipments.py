"""Tests unitaires — tools/equipments.py (Famille 2, 7 tools)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from _domain.sanitize import FILTERED
from tools import equipments

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOCK_CONN = MagicMock()


def _eq_row(**kwargs) -> dict:
    base = {
        'id': 1,
        'name': 'Thermostat Salon',
        'eqType_name': 'thermostat',
        'object_id': 1,
        'isEnable': 1,
        'isVisible': 1,
        'logicalId': 'thermo_salon',
        'generic_type': None,
        'order': 1,
        'tags': '',
    }
    return {**base, **kwargs}


def _eq_detail_row(**kwargs) -> dict:
    base = {
        **_eq_row(),
        'category': None,
        'timeout': None,
        'comment': None,
        'status': None,
        'configuration': None,
    }
    return {**base, **kwargs}


def _cmd_row(**kwargs) -> dict:
    base = {
        'id': 10,
        'name': 'Température',
        'eqLogic_id': 1,
        'type': 'info',
        'subType': 'numeric',
        'logicalId': 'temperature',
        'generic_type': 'TEMPERATURE',
        'isVisible': 1,
        'unite': '°C',
        'isHistorized': 1,
        'display': None,
        'order': 1,
        'value': '21.5',
        'configuration': None,
        'template': None,
    }
    return {**base, **kwargs}


def _hist_row(**kwargs) -> dict:
    base = {
        'id': 100,
        'cmd_id': 10,
        'datetime': '2026-05-04 12:00:00',
        'value': '21.5',
    }
    return {**base, **kwargs}


# ---------------------------------------------------------------------------
# list_equipments
# ---------------------------------------------------------------------------


class TestListEquipments:
    def test_empty_db_returns_empty(self):
        with patch('tools.equipments._db.query', return_value=[]):
            result = equipments.list_equipments(_MOCK_CONN)

        assert result['equipements'] == []
        assert result['total'] == 0
        assert result['offset'] == 0
        assert result['_filtered_fields'] == []

    def test_returns_equipements_structure(self):
        rows = [_eq_row(id=1), _eq_row(id=2, name='Prise Salon')]
        with patch('tools.equipments._db.query', return_value=rows):
            result = equipments.list_equipments(_MOCK_CONN)

        assert result['total'] == 2
        assert result['equipements'][0]['name'] == 'Thermostat Salon'
        assert result['equipements'][1]['name'] == 'Prise Salon'

    def test_filter_object_id_adds_param(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.list_equipments(_MOCK_CONN, object_id=3)

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'object_id' in sql
        assert 3 in params

    def test_filter_plugin_adds_param(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.list_equipments(_MOCK_CONN, plugin='jMQTT')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'eqType_name' in sql
        assert 'jMQTT' in params

    def test_filter_is_enable_true_passes_1(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.list_equipments(_MOCK_CONN, is_enable=True)

        params = mock_q.call_args[0][2]
        assert 1 in params

    def test_filter_is_enable_false_passes_0(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.list_equipments(_MOCK_CONN, is_enable=False)

        params = mock_q.call_args[0][2]
        assert 0 in params

    def test_limit_capped_at_max(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.list_equipments(_MOCK_CONN, limit=9999)

        params = mock_q.call_args[0][2]
        assert equipments._EQ_LIMIT in params

    def test_offset_passed_to_query(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.list_equipments(_MOCK_CONN, offset=20)

        params = mock_q.call_args[0][2]
        assert 20 in params

    def test_non_whitelisted_column_filtered(self):
        rows = [_eq_row(secret_col='leak')]
        with patch('tools.equipments._db.query', return_value=rows):
            result = equipments.list_equipments(_MOCK_CONN)

        assert result['equipements'][0]['secret_col'] == FILTERED
        assert 'secret_col' in result['_filtered_fields']


# ---------------------------------------------------------------------------
# find_equipments_advanced
# ---------------------------------------------------------------------------


class TestFindEquipmentsAdvanced:
    def test_empty_returns_empty(self):
        with patch('tools.equipments._db.query', return_value=[]):
            result = equipments.find_equipments_advanced(_MOCK_CONN)

        assert result['equipements'] == []
        assert result['total'] == 0
        assert result['_filtered_fields'] == []

    def test_name_contains_uses_like(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.find_equipments_advanced(_MOCK_CONN, name_contains='salon')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'LIKE' in sql
        assert '%salon%' in params

    def test_generic_type_filter(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.find_equipments_advanced(_MOCK_CONN, generic_type='THERMOSTAT')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'generic_type' in sql
        assert 'THERMOSTAT' in params

    def test_tags_uses_like(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.find_equipments_advanced(_MOCK_CONN, tags='chauffage')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'LIKE' in sql
        assert '%chauffage%' in params

    def test_multiple_filters_combined(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.find_equipments_advanced(
                _MOCK_CONN, plugin='thermostat', is_enable=True, object_id=2
            )

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'eqType_name' in sql
        assert 'object_id' in sql
        assert 'isEnable' in sql
        assert 'thermostat' in params
        assert 2 in params
        assert 1 in params

    def test_limit_capped_at_adv_max(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.find_equipments_advanced(_MOCK_CONN, limit=9999)

        params = mock_q.call_args[0][2]
        assert equipments._EQ_LIMIT_ADV in params


# ---------------------------------------------------------------------------
# get_equipment
# ---------------------------------------------------------------------------


class TestGetEquipment:
    def test_not_found_returns_error(self):
        with patch('tools.equipments._db.query', return_value=[]):
            result = equipments.get_equipment(_MOCK_CONN, equipment_id=999)

        assert 'error' in result
        assert result['equipment_id'] == 999
        assert result['_filtered_fields'] == []

    def test_returns_equipment_and_commands(self):
        eq_rows = [_eq_detail_row()]
        cmd_rows = [_cmd_row(id=10), _cmd_row(id=11, name='Consigne')]
        with patch('tools.equipments._db.query', side_effect=[eq_rows, cmd_rows]):
            result = equipments.get_equipment(_MOCK_CONN, equipment_id=1)

        assert result['equipment']['name'] == 'Thermostat Salon'
        assert result['nb_commandes'] == 2
        assert result['commandes'][0]['name'] == 'Température'

    def test_no_commands_returns_empty_list(self):
        eq_rows = [_eq_detail_row()]
        with patch('tools.equipments._db.query', side_effect=[eq_rows, []]):
            result = equipments.get_equipment(_MOCK_CONN, equipment_id=1)

        assert result['commandes'] == []
        assert result['nb_commandes'] == 0

    def test_non_whitelisted_eq_column_filtered(self):
        eq_rows = [_eq_detail_row(internal_pw='secret')]
        with patch('tools.equipments._db.query', side_effect=[eq_rows, []]):
            result = equipments.get_equipment(_MOCK_CONN, equipment_id=1)

        assert result['equipment']['internal_pw'] == FILTERED
        assert 'internal_pw' in result['_filtered_fields']

    def test_non_whitelisted_cmd_column_filtered(self):
        eq_rows = [_eq_detail_row()]
        cmd_rows = [_cmd_row(hidden_key='val')]
        with patch('tools.equipments._db.query', side_effect=[eq_rows, cmd_rows]):
            result = equipments.get_equipment(_MOCK_CONN, equipment_id=1)

        assert result['commandes'][0]['hidden_key'] == FILTERED
        assert 'hidden_key' in result['_filtered_fields']


# ---------------------------------------------------------------------------
# find_equipment_by_name
# ---------------------------------------------------------------------------


class TestFindEquipmentByName:
    def test_empty_returns_empty(self):
        with patch('tools.equipments._db.query', return_value=[]):
            result = equipments.find_equipment_by_name(_MOCK_CONN, 'inexistant')

        assert result['equipements'] == []
        assert result['total'] == 0

    def test_returns_matching_equipment(self):
        rows = [_eq_row(name='Thermostat Salon')]
        with patch('tools.equipments._db.query', return_value=rows):
            result = equipments.find_equipment_by_name(_MOCK_CONN, 'salon')

        assert result['total'] == 1
        assert result['equipements'][0]['name'] == 'Thermostat Salon'

    def test_query_in_result(self):
        with patch('tools.equipments._db.query', return_value=[]):
            result = equipments.find_equipment_by_name(_MOCK_CONN, 'salon')

        assert result['query'] == 'salon'

    def test_uses_like_pattern(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.find_equipment_by_name(_MOCK_CONN, 'salon')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'LIKE' in sql
        assert '%salon%' in params

    def test_limit_capped(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.find_equipment_by_name(_MOCK_CONN, 'x', limit=999)

        params = mock_q.call_args[0][2]
        assert equipments._EQ_LIMIT_ADV in params


# ---------------------------------------------------------------------------
# list_commands
# ---------------------------------------------------------------------------


class TestListCommands:
    def test_empty_equipment_no_commands(self):
        with patch('tools.equipments._db.query', return_value=[]):
            result = equipments.list_commands(_MOCK_CONN, equipment_id=1)

        assert result['commandes'] == []
        assert result['total'] == 0
        assert result['equipment_id'] == 1
        assert result['_filtered_fields'] == []

    def test_returns_commands_with_correct_fields(self):
        rows = [_cmd_row(), _cmd_row(id=11, name='Consigne', type='action')]
        with patch('tools.equipments._db.query', return_value=rows):
            result = equipments.list_commands(_MOCK_CONN, equipment_id=1)

        assert result['total'] == 2
        assert result['commandes'][0]['name'] == 'Température'
        assert result['commandes'][0]['unite'] == '°C'

    def test_filter_by_type_info(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.list_commands(_MOCK_CONN, equipment_id=1, cmd_type='info')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'type' in sql
        assert 'info' in params

    def test_filter_by_type_action(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.list_commands(_MOCK_CONN, equipment_id=5, cmd_type='action')

        params = mock_q.call_args[0][2]
        assert 5 in params
        assert 'action' in params

    def test_offset_in_result_and_query(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            result = equipments.list_commands(_MOCK_CONN, equipment_id=1, offset=50)

        assert result['offset'] == 50
        params = mock_q.call_args[0][2]
        assert 50 in params

    def test_limit_capped_at_max(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.list_commands(_MOCK_CONN, equipment_id=1, limit=9999)

        params = mock_q.call_args[0][2]
        assert equipments._CMD_LIMIT in params

    def test_non_whitelisted_cmd_column_filtered(self):
        rows = [_cmd_row(internal='secret')]
        with patch('tools.equipments._db.query', return_value=rows):
            result = equipments.list_commands(_MOCK_CONN, equipment_id=1)

        assert result['commandes'][0]['internal'] == FILTERED
        assert 'internal' in result['_filtered_fields']


# ---------------------------------------------------------------------------
# find_commands_advanced
# ---------------------------------------------------------------------------


class TestFindCommandsAdvanced:
    def test_no_filters_returns_all(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.find_commands_advanced(_MOCK_CONN)

        sql = mock_q.call_args[0][1]
        assert 'WHERE' not in sql

    def test_name_contains_uses_like(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.find_commands_advanced(_MOCK_CONN, name_contains='temp')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'LIKE' in sql
        assert '%temp%' in params

    def test_is_historized_filter_true(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.find_commands_advanced(_MOCK_CONN, is_historized=True)

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'isHistorized' in sql
        assert 1 in params

    def test_multiple_filters_combined(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.find_commands_advanced(
                _MOCK_CONN,
                equipment_id=3,
                cmd_type='info',
                subtype='numeric',
            )

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'eqLogic_id' in sql
        assert 'type' in sql
        assert 'subType' in sql
        assert 3 in params
        assert 'info' in params
        assert 'numeric' in params

    def test_generic_type_filter(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.find_commands_advanced(_MOCK_CONN, generic_type='TEMPERATURE')

        params = mock_q.call_args[0][2]
        assert 'TEMPERATURE' in params

    def test_limit_capped_at_adv_max(self):
        with patch('tools.equipments._db.query', return_value=[]) as mock_q:
            equipments.find_commands_advanced(_MOCK_CONN, limit=9999)

        params = mock_q.call_args[0][2]
        assert equipments._CMD_LIMIT_ADV in params


# ---------------------------------------------------------------------------
# get_command_history
# ---------------------------------------------------------------------------


class TestGetCommandHistory:
    def test_no_history_returns_empty(self):
        with patch('tools.equipments._db.query', side_effect=[[], []]):
            result = equipments.get_command_history(_MOCK_CONN, cmd_id=10)

        assert result['history_recent'] == []
        assert result['history_archived'] == []
        assert result['total_recent'] == 0
        assert result['total_archived'] == 0
        assert result['cmd_id'] == 10
        assert result['_filtered_fields'] == []

    def test_returns_recent_and_archived(self):
        recent = [_hist_row(id=1), _hist_row(id=2, datetime='2026-05-03 10:00:00')]
        archived = [_hist_row(id=100, datetime='2025-12-01 08:00:00')]
        with patch('tools.equipments._db.query', side_effect=[recent, archived]):
            result = equipments.get_command_history(_MOCK_CONN, cmd_id=10)

        assert result['total_recent'] == 2
        assert result['total_archived'] == 1
        assert result['history_recent'][0]['value'] == '21.5'

    def test_limit_applied_to_both_tables(self):
        with patch('tools.equipments._db.query', side_effect=[[], []]) as mock_q:
            equipments.get_command_history(_MOCK_CONN, cmd_id=10, limit=20)

        calls = mock_q.call_args_list
        assert len(calls) == 2
        params_first = calls[0][0][2]
        params_second = calls[1][0][2]
        assert 20 in params_first
        assert 20 in params_second

    def test_limit_capped_at_max(self):
        with patch('tools.equipments._db.query', side_effect=[[], []]) as mock_q:
            equipments.get_command_history(_MOCK_CONN, cmd_id=10, limit=9999)

        params = mock_q.call_args_list[0][0][2]
        assert equipments._HISTORY_LIMIT in params

    def test_cmd_id_in_both_queries(self):
        with patch('tools.equipments._db.query', side_effect=[[], []]) as mock_q:
            equipments.get_command_history(_MOCK_CONN, cmd_id=42)

        calls = mock_q.call_args_list
        assert 42 in calls[0][0][2]
        assert 42 in calls[1][0][2]


# ---------------------------------------------------------------------------
# Runtime API enrichment — get_equipment / list_commands
# ---------------------------------------------------------------------------


class TestGetEquipmentRuntime:
    def test_injects_current_value_in_info_cmds(self):
        eq_rows = [_eq_detail_row()]
        cmd_rows = [_cmd_row(id=10, type='info')]
        api_result = {
            'id': '1',
            'cmds': [{'id': '10', 'currentValue': '21.5', 'collectDate': '2026-05-04 10:00:00'}],
        }
        with (
            patch('tools.equipments._db.query', side_effect=[eq_rows, cmd_rows]),
            patch('tools.equipments._api.call', return_value={'result': api_result}),
        ):
            result = equipments.get_equipment(_MOCK_CONN, equipment_id=1, apikey='test-key')

        cmd = result['commandes'][0]
        assert cmd['currentValue'] == '21.5'
        assert cmd['collectDate'] == '2026-05-04 10:00:00'

    def test_does_not_inject_current_value_in_action_cmds(self):
        eq_rows = [_eq_detail_row()]
        cmd_rows = [_cmd_row(id=20, type='action')]
        api_result = {
            'cmds': [{'id': '20', 'currentValue': 'ignored', 'collectDate': 'ignored'}],
        }
        with (
            patch('tools.equipments._db.query', side_effect=[eq_rows, cmd_rows]),
            patch('tools.equipments._api.call', return_value={'result': api_result}),
        ):
            result = equipments.get_equipment(_MOCK_CONN, equipment_id=1, apikey='test-key')

        cmd = result['commandes'][0]
        assert 'currentValue' not in cmd

    def test_graceful_degradation_on_api_error(self):
        eq_rows = [_eq_detail_row()]
        cmd_rows = [_cmd_row(id=10)]
        with (
            patch('tools.equipments._db.query', side_effect=[eq_rows, cmd_rows]),
            patch('tools.equipments._api.call', return_value={'error': 'timeout'}),
        ):
            result = equipments.get_equipment(_MOCK_CONN, equipment_id=1, apikey='test-key')

        assert 'equipment' in result
        assert result['nb_commandes'] == 1

    def test_no_api_call_when_empty_apikey(self):
        eq_rows = [_eq_detail_row()]
        cmd_rows = [_cmd_row(id=10)]
        with (
            patch('tools.equipments._db.query', side_effect=[eq_rows, cmd_rows]),
            patch('tools.equipments._api.call') as mock_api,
        ):
            equipments.get_equipment(_MOCK_CONN, equipment_id=1, apikey='')

        mock_api.assert_not_called()

    def test_list_commands_also_enriches(self):
        cmd_rows = [_cmd_row(id=10, type='info')]
        api_result = {
            'cmds': [{'id': '10', 'currentValue': '19.3', 'collectDate': '2026-05-04 09:00:00'}],
        }
        with (
            patch('tools.equipments._db.query', return_value=cmd_rows),
            patch('tools.equipments._api.call', return_value={'result': api_result}),
        ):
            result = equipments.list_commands(_MOCK_CONN, equipment_id=1, apikey='test-key')

        assert result['commandes'][0]['currentValue'] == '19.3'

    def test_list_commands_no_api_when_empty_apikey(self):
        cmd_rows = [_cmd_row(id=10)]
        with (
            patch('tools.equipments._db.query', return_value=cmd_rows),
            patch('tools.equipments._api.call') as mock_api,
        ):
            equipments.list_commands(_MOCK_CONN, equipment_id=1, apikey='')

        mock_api.assert_not_called()


# ---------------------------------------------------------------------------
# _fetch_cmd_runtime_map — internal helper
# ---------------------------------------------------------------------------


class TestFetchCmdRuntimeMap:
    def test_returns_empty_on_empty_apikey(self):
        with patch('tools.equipments._api.call') as mock_api:
            result = equipments._fetch_cmd_runtime_map('', 1)

        mock_api.assert_not_called()
        assert result == {}

    def test_returns_empty_on_api_error(self):
        with patch('tools.equipments._api.call', return_value={'error': 'ko'}):
            result = equipments._fetch_cmd_runtime_map('key', 1)

        assert result == {}

    def test_returns_empty_when_result_not_dict(self):
        with patch('tools.equipments._api.call', return_value={'result': []}):
            result = equipments._fetch_cmd_runtime_map('key', 1)

        assert result == {}

    def test_returns_empty_when_cmds_not_list(self):
        with patch('tools.equipments._api.call', return_value={'result': {'cmds': 'bad'}}):
            result = equipments._fetch_cmd_runtime_map('key', 1)

        assert result == {}

    def test_parses_cmd_ids_as_int(self):
        api_result = {
            'cmds': [{'id': '42', 'currentValue': '100', 'collectDate': '2026-05-04'}],
        }
        with patch('tools.equipments._api.call', return_value={'result': api_result}):
            result = equipments._fetch_cmd_runtime_map('key', 1)

        assert 42 in result
        assert result[42]['currentValue'] == '100'

    def test_skips_cmds_with_zero_id(self):
        api_result = {'cmds': [{'id': '0', 'currentValue': 'x'}]}
        with patch('tools.equipments._api.call', return_value={'result': api_result}):
            result = equipments._fetch_cmd_runtime_map('key', 1)

        assert result == {}
