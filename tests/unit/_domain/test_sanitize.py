"""Tests unitaires _domain/sanitize.py — couverture 100% obligatoire (D15.5, ADR-0017).

Structure :
  - is_sensitive_key : regex mech 2 + extras plugin mech 3 + cas non-sensibles
  - sanitize_json_blob : tous les cas de parsing + filtrage
  - _sanitize_config_row : cas spécial table config
  - sanitize_row : mech 1 (whitelist) + mech 2+3 sur blob + défense en profondeur
  - sanitize_rows : agrégation et déduplication
  - wrap_result : list vs dict
  - Fixtures "no credential in output" : aucun credential connu ne doit passer
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from _domain.sanitize import (
    _PLUGIN_EXTRA_KEYS,
    _TABLE_WHITELISTS,
    FILTERED,
    _sanitize_config_row,
    is_sensitive_key,
    sanitize_json_blob,
    sanitize_row,
    sanitize_rows,
    wrap_result,
)

# ---------------------------------------------------------------------------
# is_sensitive_key
# ---------------------------------------------------------------------------


class TestIsSensitiveKey:
    @pytest.mark.parametrize(
        'key',
        [
            'password',
            'PASSWORD',
            'Password',
            'pwd',
            'PWD',
            'token',
            'TOKEN',
            'oauth_token',
            'refresh_token',
            'apikey',
            'APIKEY',
            'api_key',
            'API_KEY',
            'secret',
            'client_secret',
            'SECRET',
            'hash',
            'HASH',
            'password_hash',
            'credentials',
            'CREDENTIALS',
            'auth',
            'AUTH',
            'basic_auth',
            'cert',
            'CERT',
            'ssl_cert',
            'private_key',
            'PRIVATE_KEY',
            'access_key',
            'ACCESS_KEY',
            'bearer',
            'BEARER',
            # Partial matches (regex is a search, not fullmatch)
            'mqtt_password',
            'jeedom_token',
            'broker_apikey',
        ],
    )
    def test_regex_patterns_caught(self, key: str) -> None:
        assert is_sensitive_key(key) is True

    @pytest.mark.parametrize(
        'key',
        [
            'id',
            'name',
            'eqType_name',
            'object_id',
            'isEnable',
            'isVisible',
            'logicalId',
            'generic_type',
            'order',
            'tags',
            'category',
            'timeout',
            'comment',
            'status',
            'configuration',
            'type',
            'subType',
            'value',
            'datetime',
            'version',
            'state',
            'lastLaunch',
            'description',
            'group',
            'father_id',
            'image',
            'unite',
            'isHistorized',
            'display',
            'template',
            'query',
            'reply',
            'expression',
        ],
    )
    def test_non_sensitive_keys(self, key: str) -> None:
        assert is_sensitive_key(key) is False

    def test_plugin_extra_match(self) -> None:
        assert is_sensitive_key('pin', plugin='Alarme') is True
        assert is_sensitive_key('code', plugin='Alarme') is True
        assert is_sensitive_key('armCode', plugin='Alarme') is True
        assert is_sensitive_key('disarmCode', plugin='Alarme') is True
        assert is_sensitive_key('userCode', plugin='Alarme') is True

    def test_plugin_extra_mqtt_manager(self) -> None:
        assert is_sensitive_key('login', plugin='MQTT Manager') is True
        assert is_sensitive_key('user', plugin='MQTT Manager') is True
        assert is_sensitive_key('username', plugin='MQTT Manager') is True
        assert is_sensitive_key('broker_user', plugin='MQTT Manager') is True

    def test_plugin_extra_jmqtt(self) -> None:
        assert is_sensitive_key('mqttuser', plugin='jMQTT') is True
        assert is_sensitive_key('mqttlogin', plugin='jMQTT') is True
        assert is_sensitive_key('login', plugin='jMQTT') is True

    def test_plugin_extra_jeedom_connect(self) -> None:
        assert is_sensitive_key('installCode', plugin='Jeedom Connect') is True
        assert is_sensitive_key('pairing_code', plugin='Jeedom Connect') is True
        assert is_sensitive_key('device_code', plugin='Jeedom Connect') is True

    def test_plugin_extra_philips_hue(self) -> None:
        assert is_sensitive_key('username', plugin='Philips Hue') is True
        assert is_sensitive_key('bridge_user', plugin='Philips Hue') is True

    def test_plugin_extra_zigbee2mqtt(self) -> None:
        assert is_sensitive_key('user', plugin='Zigbee2MQTT') is True
        assert is_sensitive_key('login', plugin='Zigbee2MQTT') is True

    def test_plugin_extra_netatmo(self) -> None:
        assert is_sensitive_key('client_id', plugin='Netatmo') is True
        assert is_sensitive_key('app_id', plugin='Netatmo') is True

    def test_plugin_extra_aqara(self) -> None:
        assert is_sensitive_key('app_id', plugin='Aqara') is True
        assert is_sensitive_key('region_key', plugin='Aqara') is True

    def test_plugin_extra_ecodevices(self) -> None:
        assert is_sensitive_key('login', plugin='ecodevices') is True

    def test_plugin_extra_case_sensitive(self) -> None:
        # Extras are exact-match (not lowercased) — "Login" ≠ "login"
        assert is_sensitive_key('Login', plugin='MQTT Manager') is False

    def test_plugin_none_skips_extras(self) -> None:
        # "pin" is only caught via plugin extra, not by regex
        assert is_sensitive_key('pin') is False
        assert is_sensitive_key('user') is False
        assert is_sensitive_key('login') is False

    def test_unknown_plugin_uses_empty_extras(self) -> None:
        assert is_sensitive_key('pin', plugin='UnknownPlugin') is False

    def test_plugin_with_empty_extras(self) -> None:
        # Agenda, Script, Virtuel, etc. have frozenset() extras
        assert is_sensitive_key('pin', plugin='Agenda') is False
        assert is_sensitive_key('code', plugin='Script') is False
        assert is_sensitive_key('user', plugin='Virtuel') is False


# ---------------------------------------------------------------------------
# sanitize_json_blob
# ---------------------------------------------------------------------------


class TestSanitizeJsonBlob:
    def test_none_input(self) -> None:
        result, filtered = sanitize_json_blob(None)
        assert result is None
        assert filtered == []

    def test_empty_string(self) -> None:
        result, filtered = sanitize_json_blob('')
        assert result == {}
        assert filtered == []

    def test_whitespace_only_string(self) -> None:
        result, filtered = sanitize_json_blob('   ')
        assert result == {}
        assert filtered == []

    def test_invalid_json(self) -> None:
        raw = 'not-json-at-all'
        result, filtered = sanitize_json_blob(raw)
        assert result == raw
        assert filtered == []

    def test_json_array_not_dict(self) -> None:
        blob = json.dumps([1, 2, 3])
        result, filtered = sanitize_json_blob(blob)
        assert result == [1, 2, 3]
        assert filtered == []

    def test_json_scalar_not_dict(self) -> None:
        result, filtered = sanitize_json_blob(json.dumps(42))
        assert result == 42
        assert filtered == []

    def test_dict_input_already_parsed(self) -> None:
        data = {'name': 'test', 'password': 'secret'}
        result, filtered = sanitize_json_blob(data)
        assert result['name'] == 'test'
        assert result['password'] == FILTERED
        assert 'password' in filtered

    def test_clean_blob_no_filter(self) -> None:
        blob = json.dumps({'mqtt_host': '192.0.2.1', 'mqtt_port': '1883'})
        result, filtered = sanitize_json_blob(blob)
        assert isinstance(result, dict)
        assert result['mqtt_host'] == '192.0.2.1'
        assert result['mqtt_port'] == '1883'
        assert filtered == []

    def test_password_key_masked(self) -> None:
        blob = json.dumps({'mqtt_host': '192.0.2.1', 'mqtt_password': 'supersecret'})
        result, filtered = sanitize_json_blob(blob)
        assert result['mqtt_password'] == FILTERED
        assert result['mqtt_host'] == '192.0.2.1'
        assert 'mqtt_password' in filtered

    def test_token_key_masked(self) -> None:
        blob = json.dumps({'jeedomToken': 'abc123'})
        result, filtered = sanitize_json_blob(blob)
        assert result['jeedomToken'] == FILTERED
        assert 'jeedomToken' in filtered

    def test_apikey_key_masked(self) -> None:
        blob = json.dumps({'apikey': 'xyz789', 'name': 'ok'})
        result, filtered = sanitize_json_blob(blob)
        assert result['apikey'] == FILTERED
        assert result['name'] == 'ok'

    def test_secret_key_masked(self) -> None:
        blob = json.dumps({'client_secret': 'mysecret'})
        result, filtered = sanitize_json_blob(blob)
        assert result['client_secret'] == FILTERED

    def test_multiple_sensitive_keys(self) -> None:
        blob = json.dumps(
            {
                'host': 'localhost',
                'password': 'pass1',
                'token': 'tok1',
                'port': '1883',
            }
        )
        result, filtered = sanitize_json_blob(blob)
        assert result['host'] == 'localhost'
        assert result['port'] == '1883'
        assert result['password'] == FILTERED
        assert result['token'] == FILTERED
        assert 'password' in filtered
        assert 'token' in filtered

    def test_plugin_extra_key_in_blob(self) -> None:
        blob = json.dumps({'pin': '1234', 'mode': 'armed'})
        result, filtered = sanitize_json_blob(blob, plugin='Alarme')
        assert result['pin'] == FILTERED
        assert result['mode'] == 'armed'
        assert 'pin' in filtered

    def test_nested_dict_sensitive_key(self) -> None:
        blob = json.dumps(
            {
                'zone1': {
                    'name': 'entrée',
                    'armCode': '9999',
                }
            }
        )
        result, filtered = sanitize_json_blob(blob, plugin='Alarme')
        assert result['zone1']['armCode'] == FILTERED
        assert 'zone1.armCode' in filtered

    def test_nested_dict_clean(self) -> None:
        blob = json.dumps({'zone1': {'name': 'entrée', 'type': 'motion'}})
        result, filtered = sanitize_json_blob(blob)
        assert result == {'zone1': {'name': 'entrée', 'type': 'motion'}}
        assert filtered == []

    def test_all_sensitive_regex_patterns_in_blob(self) -> None:
        data = {
            'password': 'p',
            'pwd': 'p',
            'token': 't',
            'apikey': 'a',
            'api_key': 'a',
            'secret': 's',
            'hash': 'h',
            'credentials': 'c',
            'auth': 'a',
            'cert': 'c',
            'private_key': 'k',
            'access_key': 'k',
            'client_secret': 's',
            'bearer': 'b',
        }
        result, filtered = sanitize_json_blob(dict(data))
        assert all(result[k] == FILTERED for k in data)
        assert len(filtered) == len(data)


# ---------------------------------------------------------------------------
# _sanitize_config_row
# ---------------------------------------------------------------------------


class TestSanitizeConfigRow:
    def test_sensitive_key_masks_value(self) -> None:
        row = {'plugin': 'core', 'key': 'apikey', 'value': 'secret123'}
        result, filtered = _sanitize_config_row(row)
        assert result['key'] == 'apikey'  # key reste visible
        assert result['value'] == FILTERED
        assert result['plugin'] == 'core'
        assert 'apikey' in filtered

    def test_non_sensitive_key_passes_through(self) -> None:
        row = {'plugin': 'core', 'key': 'jeedom_version', 'value': '4.5.0'}
        result, filtered = _sanitize_config_row(row)
        assert result['value'] == '4.5.0'
        assert filtered == []

    def test_token_key_masks_value(self) -> None:
        row = {'plugin': 'holmesMcp', 'key': 'user_token', 'value': 'tok_xyz'}
        result, filtered = _sanitize_config_row(row)
        assert result['value'] == FILTERED
        assert 'user_token' in filtered

    def test_password_key_masks_value(self) -> None:
        row = {'plugin': 'core', 'key': 'db_password', 'value': 'db_pass'}
        result, filtered = _sanitize_config_row(row)
        assert result['value'] == FILTERED

    def test_missing_key_field(self) -> None:
        row = {'plugin': 'core', 'value': 'some_value'}
        result, filtered = _sanitize_config_row(row)
        assert result['value'] == 'some_value'
        assert filtered == []

    def test_empty_key_field(self) -> None:
        row = {'plugin': 'core', 'key': '', 'value': 'some_value'}
        result, filtered = _sanitize_config_row(row)
        assert result['value'] == 'some_value'
        assert filtered == []

    def test_all_fields_preserved_except_value(self) -> None:
        row = {'plugin': 'core', 'key': 'apikey', 'value': 'v', 'extra': 'x'}
        result, filtered = _sanitize_config_row(row)
        assert result['extra'] == 'x'
        assert result['plugin'] == 'core'


# ---------------------------------------------------------------------------
# sanitize_row
# ---------------------------------------------------------------------------


class TestSanitizeRow:
    # --- Table inconnue (None) : pas de whitelist, regex sur noms de champs ---

    def test_unknown_table_sensitive_field_name(self) -> None:
        row = {'id': 1, 'password': 'secret', 'name': 'test'}
        result, filtered = sanitize_row(row)
        assert result['id'] == 1
        assert result['name'] == 'test'
        assert result['password'] == FILTERED
        assert 'password' in filtered

    def test_unknown_table_clean_row(self) -> None:
        row = {'id': 1, 'name': 'test', 'value': 42}
        result, filtered = sanitize_row(row)
        assert result == {'id': 1, 'name': 'test', 'value': 42}
        assert filtered == []

    def test_unknown_table_blob_column_filtered(self) -> None:
        row = {'id': 1, 'configuration': json.dumps({'token': 'tok123', 'host': '192.0.2.1'})}
        result, filtered = sanitize_row(row)
        assert result['configuration']['token'] == FILTERED
        assert result['configuration']['host'] == '192.0.2.1'
        assert 'configuration.token' in filtered

    # --- Table connue : whitelist mech 1 ---

    def test_known_table_whitelisted_field_passes(self) -> None:
        row = {'id': 1, 'name': 'Eq', 'eqType_name': 'jMQTT'}
        result, filtered = sanitize_row(row, table='eqLogic')
        assert result['id'] == 1
        assert result['name'] == 'Eq'
        assert filtered == []

    def test_known_table_non_whitelisted_field_masked(self) -> None:
        row = {'id': 1, 'name': 'Eq', 'internal_field': 'sensitive_data'}
        result, filtered = sanitize_row(row, table='eqLogic')
        assert result['internal_field'] == FILTERED
        assert 'internal_field' in filtered

    def test_known_table_blob_column_parsed(self) -> None:
        config = json.dumps({'mqtt_host': '192.0.2.1', 'mqttpassword': 'pass123'})
        row = {'id': 1, 'name': 'Eq', 'eqType_name': 'jMQTT', 'configuration': config}
        result, filtered = sanitize_row(row, table='eqLogic')
        assert result['configuration']['mqtt_host'] == '192.0.2.1'
        assert result['configuration']['mqttpassword'] == FILTERED
        assert 'configuration.mqttpassword' in filtered

    def test_known_table_blob_with_plugin_extras(self) -> None:
        config = json.dumps({'pin': '1234', 'mode': 'armed'})
        row = {'id': 5, 'name': 'Alarme', 'eqType_name': 'Alarme', 'configuration': config}
        result, filtered = sanitize_row(row, table='eqLogic', plugin='Alarme')
        assert result['configuration']['pin'] == FILTERED
        assert result['configuration']['mode'] == 'armed'
        assert 'configuration.pin' in filtered

    def test_known_table_options_column_parsed(self) -> None:
        options = json.dumps({'enable': True, 'token': 'opttok'})
        row = {'id': 1, 'element_id': 2, 'type': 'if', 'order': 0, 'options': options}
        result, filtered = sanitize_row(row, table='scenarioSubElement')
        assert result['options']['token'] == FILTERED
        assert 'options.token' in filtered

    def test_regex_defense_in_depth_on_whitelisted_field(self) -> None:
        # Si un champ whitelisté a un nom sensible (défense en profondeur)
        # Note: "configuration" est dans la whitelist eqLogic, mais c'est un blob column.
        # Test avec une table custom qui passerait un champ sensible dans la whitelist.
        # On simule table=None pour tester la défense en profondeur.
        row = {'id': 1, 'apikey': 'leak'}
        result, filtered = sanitize_row(row)
        assert result['apikey'] == FILTERED

    # --- Table config : délégation à _sanitize_config_row ---

    def test_config_table_delegated(self) -> None:
        row = {'plugin': 'core', 'key': 'apikey', 'value': 'secret'}
        result, filtered = sanitize_row(row, table='config')
        assert result['value'] == FILTERED
        assert result['key'] == 'apikey'

    def test_config_table_clean(self) -> None:
        row = {'plugin': 'core', 'key': 'jeedom_version', 'value': '4.5.0'}
        result, filtered = sanitize_row(row, table='config')
        assert result['value'] == '4.5.0'
        assert filtered == []

    # --- Blob column : None / empty / invalid ---

    def test_blob_column_none_value(self) -> None:
        row = {'id': 1, 'name': 'Eq', 'configuration': None}
        result, filtered = sanitize_row(row, table='eqLogic')
        assert result['configuration'] is None
        assert filtered == []

    def test_blob_column_empty_string(self) -> None:
        row = {'id': 1, 'name': 'Eq', 'configuration': ''}
        result, filtered = sanitize_row(row, table='eqLogic')
        assert result['configuration'] == {}
        assert filtered == []

    def test_blob_column_invalid_json(self) -> None:
        row = {'id': 1, 'name': 'Eq', 'configuration': 'not-json'}
        result, filtered = sanitize_row(row, table='eqLogic')
        assert result['configuration'] == 'not-json'
        assert filtered == []

    # --- Tous les whitelists couverts ---

    def test_cmd_table_whitelist(self) -> None:
        row = {
            'id': 1,
            'name': 'cmd',
            'eqLogic_id': 2,
            'type': 'info',
            'subType': 'numeric',
            'hidden_field': 'leak',
        }
        result, filtered = sanitize_row(row, table='cmd')
        assert result['hidden_field'] == FILTERED

    def test_scenario_table_whitelist(self) -> None:
        row = {'id': 1, 'name': 'sc', 'isActive': 1, 'hidden_field': 'leak'}
        result, filtered = sanitize_row(row, table='scenario')
        assert result['hidden_field'] == FILTERED

    def test_object_table_whitelist(self) -> None:
        row = {'id': 1, 'name': 'Salon', 'hidden_field': 'leak'}
        result, filtered = sanitize_row(row, table='object')
        assert result['hidden_field'] == FILTERED

    def test_datastore_table_whitelist(self) -> None:
        row = {
            'id': 1,
            'type': 'global',
            'link_id': 0,
            'key': 'var1',
            'value': '42',
            'hidden_field': 'leak',
        }
        result, filtered = sanitize_row(row, table='dataStore')
        assert result['hidden_field'] == FILTERED

    def test_plugin_table_whitelist(self) -> None:
        row = {
            'id': 'jMQTT',
            'name': 'jMQTT',
            'version': '4.3.0',
            'state': 'ok',
            'logical_id': 'jMQTT',
            'hidden_field': 'leak',
        }
        result, filtered = sanitize_row(row, table='plugin')
        assert result['hidden_field'] == FILTERED

    def test_history_table_whitelist(self) -> None:
        row = {
            'id': 1,
            'cmd_id': 5,
            'datetime': '2026-05-04 10:00:00',
            'value': '21.5',
            'hidden_field': 'leak',
        }
        result, filtered = sanitize_row(row, table='history')
        assert result['hidden_field'] == FILTERED

    def test_historyArch_table_whitelist(self) -> None:
        row = {
            'id': 1,
            'cmd_id': 5,
            'datetime': '2026-04-01 00:00:00',
            'value': '20.0',
            'hidden_field': 'leak',
        }
        result, filtered = sanitize_row(row, table='historyArch')
        assert result['hidden_field'] == FILTERED

    def test_scenarioElement_table_whitelist(self) -> None:
        row = {'id': 1, 'scenario_id': 3, 'type': 'if', 'order': 0, 'hidden': 'x'}
        result, filtered = sanitize_row(row, table='scenarioElement')
        assert result['hidden'] == FILTERED

    def test_scenarioSubElement_table_whitelist(self) -> None:
        row = {'id': 1, 'element_id': 1, 'type': 'if', 'order': 0, 'options': '{}', 'hidden': 'x'}
        result, filtered = sanitize_row(row, table='scenarioSubElement')
        assert result['hidden'] == FILTERED

    def test_scenarioExpression_table_whitelist(self) -> None:
        row = {
            'id': 1,
            'subElement_id': 1,
            'type': 'condition',
            'order': 0,
            'expression': '#[O][E][C]# == 1',
            'options': '{}',
            'hidden': 'x',
        }
        result, filtered = sanitize_row(row, table='scenarioExpression')
        assert result['hidden'] == FILTERED

    def test_interactDef_table_whitelist(self) -> None:
        row = {
            'id': 1,
            'query': 'allume',
            'reply': 'ok',
            'isEnable': 1,
            'group': 'g1',
            'hidden': 'x',
        }
        result, filtered = sanitize_row(row, table='interactDef')
        assert result['hidden'] == FILTERED


# ---------------------------------------------------------------------------
# sanitize_rows
# ---------------------------------------------------------------------------


class TestSanitizeRows:
    def test_empty_list(self) -> None:
        rows, filtered = sanitize_rows([])
        assert rows == []
        assert filtered == []

    def test_single_clean_row(self) -> None:
        rows, filtered = sanitize_rows([{'id': 1, 'name': 'test'}])
        assert rows == [{'id': 1, 'name': 'test'}]
        assert filtered == []

    def test_single_row_with_sensitive_field(self) -> None:
        rows, filtered = sanitize_rows([{'id': 1, 'password': 'x'}])
        assert rows[0]['password'] == FILTERED
        assert 'password' in filtered

    def test_multiple_rows_merged_filtered(self) -> None:
        rows_input = [
            {'id': 1, 'token': 't1', 'name': 'a'},
            {'id': 2, 'secret': 's2', 'name': 'b'},
            {'id': 3, 'name': 'c'},
        ]
        rows, filtered = sanitize_rows(rows_input)
        assert rows[0]['token'] == FILTERED
        assert rows[1]['secret'] == FILTERED
        assert rows[2] == {'id': 3, 'name': 'c'}
        assert 'token' in filtered
        assert 'secret' in filtered

    def test_deduplication_of_filtered_fields(self) -> None:
        rows_input = [
            {'id': 1, 'password': 'x'},
            {'id': 2, 'password': 'y'},
        ]
        rows, filtered = sanitize_rows(rows_input)
        # "password" appears twice but deduplicated
        assert filtered.count('password') == 1

    def test_filtered_fields_sorted(self) -> None:
        rows_input = [{'token': 't', 'apikey': 'a', 'secret': 's'}]
        _, filtered = sanitize_rows(rows_input)
        assert filtered == sorted(filtered)

    def test_with_table_and_plugin(self) -> None:
        config = json.dumps({'pin': '1111', 'mode': 'armed'})
        rows_input = [
            {
                'id': 1,
                'name': 'A1',
                'eqType_name': 'Alarme',
                'configuration': config,
                'isEnable': 1,
            },
        ]
        rows, filtered = sanitize_rows(rows_input, table='eqLogic', plugin='Alarme')
        assert rows[0]['configuration']['pin'] == FILTERED
        assert 'configuration.pin' in filtered


# ---------------------------------------------------------------------------
# wrap_result
# ---------------------------------------------------------------------------


class TestWrapResult:
    def test_list_data(self) -> None:
        rows = [{'id': 1}]
        result = wrap_result(rows, ['token'])
        assert result == {'rows': [{'id': 1}], '_filtered_fields': ['token']}

    def test_dict_data(self) -> None:
        data = {'id': 1, 'name': 'test'}
        result = wrap_result(data, [])
        assert result == {'id': 1, 'name': 'test', '_filtered_fields': []}

    def test_empty_filtered_fields(self) -> None:
        result = wrap_result([], [])
        assert result['_filtered_fields'] == []

    def test_non_empty_filtered_fields(self) -> None:
        result = wrap_result({'id': 1}, ['password', 'token'])
        assert result['_filtered_fields'] == ['password', 'token']

    def test_dict_data_doesnt_overwrite_rows_key(self) -> None:
        # If dict has a "rows" key, it's preserved (not wrapped again)
        data = {'rows': [1, 2], 'count': 2}
        result = wrap_result(data, [])
        # wrap_result on dict does {**data, ...}, so rows key is preserved
        assert result['rows'] == [1, 2]


# ---------------------------------------------------------------------------
# Fixtures "no credential in output" — D15.5
# Aucun credential connu ne doit apparaître dans la sortie sanitisée.
# ---------------------------------------------------------------------------

CREDENTIAL_FIXTURES = [
    # 1. eqLogic jMQTT — password dans blob configuration
    {
        'id': 'jmqtt_eqlogic',
        'table': 'eqLogic',
        'plugin': 'jMQTT',
        'row': {
            'id': 10,
            'name': 'Broker MQTT',
            'eqType_name': 'jMQTT',
            'object_id': 1,
            'isEnable': 1,
            'isVisible': 1,
            'configuration': json.dumps(
                {
                    'mqtt_host': '192.0.2.100',
                    'mqtt_port': '1883',
                    'mqttpassword': 'SuperSecret123!',
                    'mqttuser': 'jeedom_user',
                }
            ),
        },
        'credentials': ['SuperSecret123!', 'jeedom_user'],
    },
    # 2. config table — apikey Jeedom
    {
        'id': 'config_apikey',
        'table': 'config',
        'plugin': None,
        'row': {'plugin': 'core', 'key': 'apikey', 'value': 'AbCdEf123456XyZ'},
        'credentials': ['AbCdEf123456XyZ'],
    },
    # 3. eqLogic Alarme — PIN et code dans configuration
    {
        'id': 'alarme_pin',
        'table': 'eqLogic',
        'plugin': 'Alarme',
        'row': {
            'id': 5,
            'name': 'Alarme Maison',
            'eqType_name': 'Alarme',
            'object_id': 2,
            'isEnable': 1,
            'isVisible': 1,
            'configuration': json.dumps(
                {
                    'armCode': '1234',
                    'disarmCode': '5678',
                    'mode': 'armed_away',
                }
            ),
        },
        'credentials': ['1234', '5678'],
    },
    # 4. eqLogic Jeedom Connect — install code
    {
        'id': 'jeedomconnect_code',
        'table': 'eqLogic',
        'plugin': 'Jeedom Connect',
        'row': {
            'id': 20,
            'name': 'Mon App',
            'eqType_name': 'Jeedom Connect',
            'object_id': 1,
            'isEnable': 1,
            'isVisible': 1,
            'configuration': json.dumps(
                {
                    'installCode': 'INSTALL-PAIRING-99ZZ',
                    'device_name': 'iPhone de Pierre',
                }
            ),
        },
        'credentials': ['INSTALL-PAIRING-99ZZ'],
    },
    # 5. eqLogic MQTT Manager — broker credentials
    {
        'id': 'mqttmanager_creds',
        'table': 'eqLogic',
        'plugin': 'MQTT Manager',
        'row': {
            'id': 30,
            'name': 'MQTT Broker',
            'eqType_name': 'MQTT Manager',
            'object_id': 1,
            'isEnable': 1,
            'isVisible': 1,
            'configuration': json.dumps(
                {
                    'host': '192.0.2.50',
                    'port': '1883',
                    'username': 'mqtt_admin',
                    'password': 'BrokerPass!2026',
                }
            ),
        },
        'credentials': ['mqtt_admin', 'BrokerPass!2026'],
    },
    # 6. Champ token hors whitelist (table connue)
    {
        'id': 'eqlogic_token_field',
        'table': 'eqLogic',
        'plugin': None,
        'row': {
            'id': 40,
            'name': 'Netatmo',
            'eqType_name': 'Netatmo',
            'object_id': 1,
            'isEnable': 1,
            'isVisible': 1,
            'configuration': json.dumps(
                {
                    'access_token': 'nat_access_tok_xyz789',
                    'refresh_token': 'nat_refresh_tok_abc123',
                    'client_secret': 'ClientSecretValue',
                }
            ),
        },
        'credentials': ['nat_access_tok_xyz789', 'nat_refresh_tok_abc123', 'ClientSecretValue'],
    },
    # 7. Champ directement nommé password dans la row (table inconnue)
    {
        'id': 'raw_password_field',
        'table': None,
        'plugin': None,
        'row': {'id': 1, 'name': 'test', 'password': 'DirectLeak42'},
        'credentials': ['DirectLeak42'],
    },
    # 8. config table — token bearer
    {
        'id': 'config_bearer',
        'table': 'config',
        'plugin': None,
        'row': {'plugin': 'holmesMcp', 'key': 'bearer_token', 'value': 'Bearer_XYZ_789'},
        'credentials': ['Bearer_XYZ_789'],
    },
    # 9. Nested configuration — hash dans sous-objet
    {
        'id': 'nested_hash',
        'table': 'eqLogic',
        'plugin': None,
        'row': {
            'id': 50,
            'name': 'Plugin tiers',
            'eqType_name': 'custom',
            'object_id': 1,
            'isEnable': 1,
            'isVisible': 1,
            'configuration': json.dumps(
                {
                    'zone1': {
                        'name': 'zone entrée',
                        'hash': 'sha256_hash_value_secret',
                    }
                }
            ),
        },
        'credentials': ['sha256_hash_value_secret'],
    },
    # 10. Philips Hue — username (bridge user)
    {
        'id': 'hue_username',
        'table': 'eqLogic',
        'plugin': 'Philips Hue',
        'row': {
            'id': 60,
            'name': 'Hue Bridge',
            'eqType_name': 'Philips Hue',
            'object_id': 3,
            'isEnable': 1,
            'isVisible': 1,
            'configuration': json.dumps(
                {
                    'bridge_ip': '192.0.2.200',
                    'username': 'hue_bridge_api_user_xyz',
                }
            ),
        },
        'credentials': ['hue_bridge_api_user_xyz'],
    },
]


class TestNoCredentialInOutput:
    @pytest.mark.parametrize(
        'fixture', CREDENTIAL_FIXTURES, ids=[f['id'] for f in CREDENTIAL_FIXTURES]
    )
    def test_no_credential_leaks(self, fixture: dict) -> None:
        """Vérifie qu'aucun credential connu n'apparaît dans la sortie sanitisée."""
        result, _ = sanitize_row(
            fixture['row'],
            table=fixture['table'],
            plugin=fixture['plugin'],
        )
        result_str = json.dumps(result, ensure_ascii=False)
        for credential in fixture['credentials']:
            assert credential not in result_str, (
                f"[{fixture['id']}] credential '{credential}' détecté dans la sortie sanitisée"
            )

    def test_filtered_fields_non_empty_for_all_fixtures(self) -> None:
        """Chaque fixture doit produire au moins un champ filtré."""
        for fixture in CREDENTIAL_FIXTURES:
            _, filtered = sanitize_row(
                fixture['row'],
                table=fixture['table'],
                plugin=fixture['plugin'],
            )
            assert len(filtered) > 0, (
                f"[{fixture['id']}] aucun champ filtré — la sanitisation n'a pas fonctionné"
            )


# ---------------------------------------------------------------------------
# Constantes et données internes
# ---------------------------------------------------------------------------


class TestInternals:
    def test_filtered_constant(self) -> None:
        assert FILTERED == '***FILTERED***'

    def test_all_plugin_extras_are_frozensets(self) -> None:
        for plugin, extras in _PLUGIN_EXTRA_KEYS.items():
            assert isinstance(extras, frozenset), f'{plugin} extras doit être frozenset'

    def test_all_whitelists_are_frozensets(self) -> None:
        for table, wl in _TABLE_WHITELISTS.items():
            assert isinstance(wl, frozenset), f'{table} whitelist doit être frozenset'

    def test_po_plugins_in_extra_keys(self) -> None:
        """Les plugins de l'install PO sont dans _PLUGIN_EXTRA_KEYS (même si extras vides)."""
        po_plugins = [
            'jMQTT',
            'Agenda',
            'Alarme',
            'Thermostat',
            'thermostat',
            'Jeedom Connect',
            'Script',
            'MQTT Manager',
            'Virtuel',
        ]
        for plugin in po_plugins:
            assert plugin in _PLUGIN_EXTRA_KEYS, f'{plugin} absent de _PLUGIN_EXTRA_KEYS'

    # E01 (J3-5) : position dans le whitelist object (J3-4 avait conservé 'order' par erreur)
    def test_object_whitelist_has_position_not_order(self) -> None:
        wl = _TABLE_WHITELISTS['object']
        assert 'position' in wl, "'position' doit être dans le whitelist 'object'"
        assert 'order' not in wl, "'order' est stale depuis J3-4 et ne doit plus figurer"
        assert 'image' not in wl, "'image' est stale (jamais sélectionnée) et ne doit plus figurer"

    def test_object_position_not_filtered(self) -> None:
        row = {'id': 1, 'name': 'Salon', 'father_id': None, 'isVisible': 1, 'position': 2}
        sanitized, filtered = sanitize_row(row, 'object')
        assert sanitized['position'] == 2
        assert 'position' not in filtered

    # E06 (J3-5) : currentValue/collectDate dans le whitelist cmd
    def test_cmd_whitelist_has_current_value_and_collect_date(self) -> None:
        wl = _TABLE_WHITELISTS['cmd']
        assert 'currentValue' in wl, "'currentValue' doit être dans le whitelist 'cmd'"
        assert 'collectDate' in wl, "'collectDate' doit être dans le whitelist 'cmd'"

    def test_cmd_current_value_not_filtered(self) -> None:
        row = {
            'id': 10,
            'name': 'Température',
            'eqLogic_id': 1,
            'type': 'info',
            'subType': 'numeric',
            'logicalId': '',
            'generic_type': 'TEMPERATURE',
            'isVisible': 1,
            'unite': '°C',
            'isHistorized': 1,
            'display': None,
            'order': 1,
            'value': None,
            'configuration': None,
            'template': None,
            'currentValue': '21.3',
            'collectDate': '2026-05-04 10:00:00',
        }
        sanitized, filtered = sanitize_row(row, 'cmd')
        assert sanitized['currentValue'] == '21.3'
        assert sanitized['collectDate'] == '2026-05-04 10:00:00'
        assert 'currentValue' not in filtered
        assert 'collectDate' not in filtered

    # E07 (J3-5) : id stale retiré des whitelists history / historyArch
    def test_history_whitelist_has_no_id(self) -> None:
        assert 'id' not in _TABLE_WHITELISTS['history'], \
            "'id' stale (supprimé du SELECT en J3-4) ne doit plus figurer dans 'history'"
        assert 'id' not in _TABLE_WHITELISTS['historyArch'], \
            "'id' stale ne doit plus figurer dans 'historyArch'"

    def test_history_whitelist_has_expected_fields(self) -> None:
        for table in ('history', 'historyArch'):
            wl = _TABLE_WHITELISTS[table]
            assert 'cmd_id' in wl
            assert 'datetime' in wl
            assert 'value' in wl
