"""Tests unitaires — tools/discovery.py (Famille 1, 4 tools)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from _domain.sanitize import FILTERED
from tools import discovery

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOCK_CONN = MagicMock()


def _make_count(n: int) -> list[dict]:
    return [{'n': n}]


# ---------------------------------------------------------------------------
# get_install_overview
# ---------------------------------------------------------------------------


class TestGetInstallOverview:
    def test_returns_expected_structure(self):
        side_effects = [
            [{'value': '4.4.9'}],  # version
            _make_count(10),  # eq_total
            _make_count(8),  # eq_active
            _make_count(5),  # scen_total
            _make_count(3),  # scen_active
            _make_count(12),  # plugin_count
            _make_count(4),  # object_count
            _make_count(150),  # cmd_count
        ]
        with patch('tools.discovery._db.query', side_effect=side_effects):
            result = discovery.get_install_overview(_MOCK_CONN)

        assert result['jeedom_version'] == '4.4.9'
        assert result['equipements'] == {'total': 10, 'actifs': 8}
        assert result['scenarios'] == {'total': 5, 'actifs': 3}
        assert result['plugins'] == 12
        assert result['objets'] == 4
        assert result['commandes'] == 150
        assert result['_filtered_fields'] == []

    def test_version_unknown_when_no_rows(self):
        side_effects = [
            [],  # version not found
            _make_count(0),
            _make_count(0),
            _make_count(0),
            _make_count(0),
            _make_count(0),
            _make_count(0),
            _make_count(0),
        ]
        with patch('tools.discovery._db.query', side_effect=side_effects):
            result = discovery.get_install_overview(_MOCK_CONN)

        assert result['jeedom_version'] == 'inconnu'

    def test_zero_counts_valid(self):
        side_effects = [
            [{'value': '4.5.0'}],
        ] + [_make_count(0)] * 7
        with patch('tools.discovery._db.query', side_effect=side_effects):
            result = discovery.get_install_overview(_MOCK_CONN)

        assert result['equipements']['total'] == 0
        assert result['equipements']['actifs'] == 0
        assert result['scenarios']['total'] == 0

    def test_version_query_uses_core_plugin(self):
        side_effects = [
            [{'value': '4.4.9'}],
        ] + [_make_count(1)] * 7
        with patch('tools.discovery._db.query', side_effect=side_effects) as mock_q:
            discovery.get_install_overview(_MOCK_CONN)

        first_call_sql = mock_q.call_args_list[0][0][1]
        assert 'core' in first_call_sql
        assert 'version' in first_call_sql


# ---------------------------------------------------------------------------
# list_objects
# ---------------------------------------------------------------------------


class TestListObjects:
    def test_empty_db_returns_empty_list(self):
        with patch('tools.discovery._db.query', return_value=[]):
            result = discovery.list_objects(_MOCK_CONN)

        assert result['objects'] == []
        assert result['total'] == 0
        assert result['_filtered_fields'] == []

    def test_returns_objects_with_correct_fields(self):
        rows = [
            {'id': 1, 'name': 'Salon', 'father_id': None, 'isVisible': 1, 'order': 1},
            {'id': 2, 'name': 'Chambre', 'father_id': None, 'isVisible': 1, 'order': 2},
        ]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.list_objects(_MOCK_CONN)

        assert result['total'] == 2
        assert result['objects'][0]['name'] == 'Salon'
        assert result['objects'][1]['name'] == 'Chambre'

    def test_father_id_none_preserved(self):
        rows = [{'id': 1, 'name': 'Salon', 'father_id': None, 'isVisible': 1, 'order': 1}]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.list_objects(_MOCK_CONN)

        assert result['objects'][0]['father_id'] is None

    def test_child_object_has_father_id(self):
        rows = [
            {'id': 1, 'name': 'Rez-de-chaussée', 'father_id': None, 'isVisible': 1, 'order': 1},
            {'id': 2, 'name': 'Salon', 'father_id': 1, 'isVisible': 1, 'order': 2},
        ]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.list_objects(_MOCK_CONN)

        assert result['objects'][1]['father_id'] == 1

    def test_non_whitelisted_column_filtered(self):
        rows = [
            {
                'id': 1,
                'name': 'Salon',
                'father_id': None,
                'isVisible': 1,
                'order': 1,
                'secret_internal_col': 'should_be_filtered',
            }
        ]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.list_objects(_MOCK_CONN)

        assert result['objects'][0]['secret_internal_col'] == FILTERED
        assert 'secret_internal_col' in result['_filtered_fields']

    def test_query_uses_limit(self):
        with patch('tools.discovery._db.query', return_value=[]) as mock_q:
            discovery.list_objects(_MOCK_CONN)

        sql, params = mock_q.call_args[0][1], mock_q.call_args[0][2]
        assert 'LIMIT' in sql
        assert params[0] == discovery._OBJECTS_LIMIT


# ---------------------------------------------------------------------------
# list_plugins
# ---------------------------------------------------------------------------


class TestListPlugins:
    def test_empty_db_returns_empty_list(self):
        with patch('tools.discovery._db.query', return_value=[]):
            result = discovery.list_plugins(_MOCK_CONN)

        assert result['plugins'] == []
        assert result['total'] == 0
        assert result['_filtered_fields'] == []

    def test_returns_plugins_with_correct_fields(self):
        rows = [
            {'id': 1, 'name': 'jMQTT', 'version': '4.1.0', 'state': 'ok', 'logical_id': 'jMQTT'},
            {
                'id': 2,
                'name': 'Philips Hue',
                'version': '3.0',
                'state': 'ok',
                'logical_id': 'philipsHue',
            },
        ]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.list_plugins(_MOCK_CONN)

        assert result['total'] == 2
        assert result['plugins'][0]['name'] == 'jMQTT'
        assert result['plugins'][1]['logical_id'] == 'philipsHue'

    def test_plugin_state_nok_returned(self):
        rows = [
            {
                'id': 1,
                'name': 'BrokenPlugin',
                'version': '1.0',
                'state': 'nok',
                'logical_id': 'broken',
            },
        ]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.list_plugins(_MOCK_CONN)

        assert result['plugins'][0]['state'] == 'nok'

    def test_non_whitelisted_column_filtered(self):
        rows = [
            {
                'id': 1,
                'name': 'jMQTT',
                'version': '4.1.0',
                'state': 'ok',
                'logical_id': 'jMQTT',
                'internal_password': 'secret',
            }
        ]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.list_plugins(_MOCK_CONN)

        assert result['plugins'][0]['internal_password'] == FILTERED
        assert 'internal_password' in result['_filtered_fields']

    def test_query_uses_limit(self):
        with patch('tools.discovery._db.query', return_value=[]) as mock_q:
            discovery.list_plugins(_MOCK_CONN)

        sql, params = mock_q.call_args[0][1], mock_q.call_args[0][2]
        assert 'LIMIT' in sql
        assert params[0] == discovery._PLUGINS_LIMIT


# ---------------------------------------------------------------------------
# get_config
# ---------------------------------------------------------------------------


class TestGetConfig:
    def test_empty_result(self):
        with patch('tools.discovery._db.query', return_value=[]):
            result = discovery.get_config(_MOCK_CONN, 'core')

        assert result['config'] == []
        assert result['total'] == 0
        assert result['plugin'] == 'core'
        assert result['key_pattern'] is None
        assert result['_filtered_fields'] == []

    def test_returns_config_rows(self):
        rows = [
            {'plugin': 'core', 'key': 'version', 'value': '4.4.9'},
            {'plugin': 'core', 'key': 'port', 'value': '80'},
        ]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.get_config(_MOCK_CONN, 'core')

        assert result['total'] == 2
        assert result['config'][0]['key'] == 'version'
        assert result['config'][0]['value'] == '4.4.9'

    def test_sensitive_key_value_masked(self):
        rows = [
            {'plugin': 'core', 'key': 'jeedom::apikey', 'value': 'super_secret_apikey'},
        ]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.get_config(_MOCK_CONN, 'core')

        assert result['config'][0]['value'] == FILTERED
        assert 'jeedom::apikey' in result['_filtered_fields']

    def test_token_key_value_masked(self):
        rows = [
            {'plugin': 'holmesMcp', 'key': 'token_1', 'value': 'abc123def456'},
        ]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.get_config(_MOCK_CONN, 'holmesMcp')

        assert result['config'][0]['value'] == FILTERED

    def test_password_key_value_masked(self):
        rows = [
            {'plugin': 'jMQTT', 'key': 'mqtt_password', 'value': 'broker_secret'},
        ]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.get_config(_MOCK_CONN, 'jMQTT')

        assert result['config'][0]['value'] == FILTERED
        assert 'mqtt_password' in result['_filtered_fields']

    def test_non_sensitive_key_value_visible(self):
        rows = [
            {'plugin': 'core', 'key': 'port', 'value': '80'},
            {'plugin': 'core', 'key': 'language', 'value': 'fr_FR'},
        ]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.get_config(_MOCK_CONN, 'core')

        assert result['config'][0]['value'] == '80'
        assert result['config'][1]['value'] == 'fr_FR'
        assert result['_filtered_fields'] == []

    def test_key_visible_even_when_value_masked(self):
        rows = [
            {'plugin': 'core', 'key': 'jeedom::apikey', 'value': 'super_secret'},
        ]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.get_config(_MOCK_CONN, 'core')

        assert result['config'][0]['key'] == 'jeedom::apikey'

    def test_with_key_pattern_uses_like(self):
        with patch('tools.discovery._db.query', return_value=[]) as mock_q:
            discovery.get_config(_MOCK_CONN, 'core', key_pattern='mqtt%')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'LIKE' in sql
        assert 'mqtt%' in params

    def test_without_key_pattern_no_like(self):
        with patch('tools.discovery._db.query', return_value=[]) as mock_q:
            discovery.get_config(_MOCK_CONN, 'core')

        sql = mock_q.call_args[0][1]
        assert 'LIKE' not in sql

    def test_plugin_and_key_pattern_in_result(self):
        with patch('tools.discovery._db.query', return_value=[]):
            result = discovery.get_config(_MOCK_CONN, 'jMQTT', key_pattern='broker%')

        assert result['plugin'] == 'jMQTT'
        assert result['key_pattern'] == 'broker%'

    def test_query_uses_limit(self):
        with patch('tools.discovery._db.query', return_value=[]) as mock_q:
            discovery.get_config(_MOCK_CONN, 'core')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'LIMIT' in sql
        assert discovery._CONFIG_LIMIT in params

    def test_mixed_sensitive_and_safe_keys(self):
        rows = [
            {'plugin': 'core', 'key': 'language', 'value': 'fr_FR'},
            {'plugin': 'core', 'key': 'jeedom::apikey', 'value': 'secret'},
            {'plugin': 'core', 'key': 'port', 'value': '80'},
        ]
        with patch('tools.discovery._db.query', return_value=rows):
            result = discovery.get_config(_MOCK_CONN, 'core')

        assert result['config'][0]['value'] == 'fr_FR'
        assert result['config'][1]['value'] == FILTERED
        assert result['config'][2]['value'] == '80'
        assert len(result['_filtered_fields']) == 1
