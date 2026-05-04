"""Tests unitaires — tools/scenarios.py (Famille 3, 7 tools)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from _domain.sanitize import FILTERED
from tools import scenarios

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOCK_CONN = MagicMock()


def _scen_row(**kwargs) -> dict:
    base = {
        'id': 1,
        'name': 'Chauffage salon',
        'group': 'Chauffage',
        'isActive': 1,
        'mode': 'provoke',
        'trigger': '#123#',
        'lastLaunch': '2026-05-04 10:00:00',
        'timeout': None,
        'description': 'Gère le chauffage du salon',
        'state': 'on',
    }
    return {**base, **kwargs}


def _walker_result(scenario_id: int = 1, empty_tree: bool = False) -> dict:
    tree = [] if empty_tree else [
        {
            'element_id': 10,
            'depth': 0,
            'sub_elements': [
                {
                    'sub_id': 20,
                    'ss_type': 'if',
                    'ss_subtype': 'condition',
                    'expressions': [
                        {
                            'expr_id': 30,
                            'order': 1,
                            'type': 'condition',
                            'expression': '#456# > 19',
                            'options': None,
                        }
                    ],
                }
            ],
        }
    ]
    return {
        'scenario': {
            'id': scenario_id,
            'name': 'Chauffage salon',
            'isActive': 1,
            'mode': 'provoke',
            'trigger': '#123#',
            'description': 'Test',
        },
        'tree': tree,
        'truncated': False,
        'warnings': [],
    }


def _walker_error() -> dict:
    return {
        'error': 'Scénario 999 introuvable',
        'scenario': None,
        'tree': [],
        'truncated': False,
        'warnings': [],
    }


def _empty_cmd_refs_result() -> dict:
    return {'mapping': {}, 'unresolved': [], 'resolved': ''}


# ---------------------------------------------------------------------------
# list_scenarios
# ---------------------------------------------------------------------------


class TestListScenarios:
    def test_empty_db_returns_empty(self):
        with patch('tools.scenarios._db.query', return_value=[]):
            result = scenarios.list_scenarios(_MOCK_CONN)

        assert result['scenarios'] == []
        assert result['total'] == 0
        assert result['offset'] == 0
        assert result['_filtered_fields'] == []

    def test_returns_scenarios_structure(self):
        rows = [_scen_row(id=1), _scen_row(id=2, name='Volets')]
        with patch('tools.scenarios._db.query', return_value=rows):
            result = scenarios.list_scenarios(_MOCK_CONN)

        assert result['total'] == 2
        assert result['scenarios'][0]['name'] == 'Chauffage salon'

    def test_filter_group_adds_param(self):
        with patch('tools.scenarios._db.query', return_value=[]) as mock_q:
            scenarios.list_scenarios(_MOCK_CONN, group='Chauffage')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'group' in sql
        assert 'Chauffage' in params

    def test_filter_is_active_true_passes_1(self):
        with patch('tools.scenarios._db.query', return_value=[]) as mock_q:
            scenarios.list_scenarios(_MOCK_CONN, is_active=True)

        params = mock_q.call_args[0][2]
        assert 1 in params

    def test_filter_is_active_false_passes_0(self):
        with patch('tools.scenarios._db.query', return_value=[]) as mock_q:
            scenarios.list_scenarios(_MOCK_CONN, is_active=False)

        params = mock_q.call_args[0][2]
        assert 0 in params

    def test_limit_capped_at_max(self):
        with patch('tools.scenarios._db.query', return_value=[]) as mock_q:
            scenarios.list_scenarios(_MOCK_CONN, limit=9999)

        params = mock_q.call_args[0][2]
        assert scenarios._SCEN_LIMIT in params

    def test_offset_passed_to_query(self):
        with patch('tools.scenarios._db.query', return_value=[]) as mock_q:
            scenarios.list_scenarios(_MOCK_CONN, offset=20)

        params = mock_q.call_args[0][2]
        assert 20 in params

    def test_non_whitelisted_column_filtered(self):
        rows = [_scen_row(internal_config='secret')]
        with patch('tools.scenarios._db.query', return_value=rows):
            result = scenarios.list_scenarios(_MOCK_CONN)

        assert result['scenarios'][0]['internal_config'] == FILTERED
        assert 'internal_config' in result['_filtered_fields']


# ---------------------------------------------------------------------------
# find_scenarios_advanced
# ---------------------------------------------------------------------------


class TestFindScenariosAdvanced:
    def test_empty_returns_empty(self):
        with patch('tools.scenarios._db.query', return_value=[]):
            result = scenarios.find_scenarios_advanced(_MOCK_CONN)

        assert result['scenarios'] == []
        assert result['total'] == 0

    def test_name_contains_uses_like(self):
        with patch('tools.scenarios._db.query', return_value=[]) as mock_q:
            scenarios.find_scenarios_advanced(_MOCK_CONN, name_contains='chauf')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'LIKE' in sql
        assert '%chauf%' in params

    def test_group_filter_adds_param(self):
        with patch('tools.scenarios._db.query', return_value=[]) as mock_q:
            scenarios.find_scenarios_advanced(_MOCK_CONN, group='Sécurité')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'group' in sql
        assert 'Sécurité' in params

    def test_is_active_filter_true(self):
        with patch('tools.scenarios._db.query', return_value=[]) as mock_q:
            scenarios.find_scenarios_advanced(_MOCK_CONN, is_active=True)

        params = mock_q.call_args[0][2]
        assert 1 in params

    def test_trigger_type_uses_like(self):
        with patch('tools.scenarios._db.query', return_value=[]) as mock_q:
            scenarios.find_scenarios_advanced(_MOCK_CONN, trigger_type='schedule')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'trigger' in sql
        assert '%schedule%' in params

    def test_limit_capped_at_adv_max(self):
        with patch('tools.scenarios._db.query', return_value=[]) as mock_q:
            scenarios.find_scenarios_advanced(_MOCK_CONN, limit=9999)

        params = mock_q.call_args[0][2]
        assert scenarios._SCEN_LIMIT_ADV in params

    def test_no_filters_no_where_clause(self):
        with patch('tools.scenarios._db.query', return_value=[]) as mock_q:
            scenarios.find_scenarios_advanced(_MOCK_CONN)

        sql = mock_q.call_args[0][1]
        assert 'WHERE' not in sql


# ---------------------------------------------------------------------------
# get_scenario
# ---------------------------------------------------------------------------


class TestGetScenario:
    def test_not_found_returns_error(self):
        with patch('tools.scenarios._db.query', return_value=[]):
            result = scenarios.get_scenario(_MOCK_CONN, scenario_id=999)

        assert 'error' in result
        assert result['scenario_id'] == 999
        assert result['_filtered_fields'] == []

    def test_returns_scenario_structure(self):
        rows = [_scen_row()]
        with patch('tools.scenarios._db.query', return_value=rows):
            result = scenarios.get_scenario(_MOCK_CONN, scenario_id=1)

        assert result['scenario']['name'] == 'Chauffage salon'
        assert result['scenario']['isActive'] == 1
        assert result['_filtered_fields'] == []

    def test_non_whitelisted_field_filtered(self):
        rows = [_scen_row(internal_pw='secret')]
        with patch('tools.scenarios._db.query', return_value=rows):
            result = scenarios.get_scenario(_MOCK_CONN, scenario_id=1)

        assert result['scenario']['internal_pw'] == FILTERED
        assert 'internal_pw' in result['_filtered_fields']

    def test_scenario_id_in_query(self):
        with patch('tools.scenarios._db.query', return_value=[]) as mock_q:
            scenarios.get_scenario(_MOCK_CONN, scenario_id=42)

        params = mock_q.call_args[0][2]
        assert 42 in params


# ---------------------------------------------------------------------------
# get_scenario_structure
# ---------------------------------------------------------------------------


class TestGetScenarioStructure:
    def test_not_found_returns_error_dict(self):
        with patch('tools.scenarios._walker.walk', return_value=_walker_error()):
            result = scenarios.get_scenario_structure(_MOCK_CONN, scenario_id=999)

        assert result['scenario'] is None
        assert 'error' in result

    def test_returns_tree_structure(self):
        with patch('tools.scenarios._walker.walk', return_value=_walker_result()):
            result = scenarios.get_scenario_structure(_MOCK_CONN, scenario_id=1)

        assert result['scenario']['name'] == 'Chauffage salon'
        assert len(result['tree']) == 1
        assert result['tree'][0]['element_id'] == 10

    def test_default_max_depth_is_3(self):
        with patch('tools.scenarios._walker.walk', return_value=_walker_result()) as mock_w:
            scenarios.get_scenario_structure(_MOCK_CONN, scenario_id=1)

        assert mock_w.call_args.kwargs.get('max_depth') == 3

    def test_custom_max_depth_forwarded(self):
        with patch('tools.scenarios._walker.walk', return_value=_walker_result()) as mock_w:
            scenarios.get_scenario_structure(_MOCK_CONN, scenario_id=1, max_depth=5)

        assert mock_w.call_args.kwargs.get('max_depth') == 5

    def test_empty_tree_returns_empty_list(self):
        with patch('tools.scenarios._walker.walk', return_value=_walker_result(empty_tree=True)):
            result = scenarios.get_scenario_structure(_MOCK_CONN, scenario_id=1)

        assert result['tree'] == []

    def test_truncated_and_warnings_propagated(self):
        walker_res = {**_walker_result(), 'truncated': True, 'warnings': ['trunc']}
        with patch('tools.scenarios._walker.walk', return_value=walker_res):
            result = scenarios.get_scenario_structure(_MOCK_CONN, scenario_id=1)

        assert result['truncated'] is True
        assert 'trunc' in result['warnings']


# ---------------------------------------------------------------------------
# describe_scenario
# ---------------------------------------------------------------------------


class TestDescribeScenario:
    def test_not_found_scenario_returns_error(self):
        with patch('tools.scenarios._walker.walk', return_value=_walker_error()):
            result = scenarios.describe_scenario(_MOCK_CONN, scenario_id=999)

        assert result['scenario'] is None
        assert 'error' in result

    def test_empty_tree_no_error(self):
        with (
            patch('tools.scenarios._walker.walk', return_value=_walker_result(empty_tree=True)),
            patch('tools.scenarios._cmd_refs.resolve', return_value=_empty_cmd_refs_result()),
        ):
            result = scenarios.describe_scenario(_MOCK_CONN, scenario_id=1)

        assert 'scenario' in result
        assert result['blocks'] == []

    def test_resolves_trigger_cmd_refs(self):
        mapping = {'123': '[Salon][Thermostat][Température]'}
        with (
            patch('tools.scenarios._walker.walk', return_value=_walker_result(empty_tree=True)),
            patch(
                'tools.scenarios._cmd_refs.resolve',
                return_value={'mapping': mapping, 'unresolved': [], 'resolved': ''},
            ),
        ):
            result = scenarios.describe_scenario(_MOCK_CONN, scenario_id=1)

        assert result['scenario']['trigger_resolved'] == '#[Salon][Thermostat][Température]#'

    def test_resolves_expression_cmd_refs(self):
        mapping = {'456': '[Salon][Thermostat][Température]'}
        with (
            patch('tools.scenarios._walker.walk', return_value=_walker_result()),
            patch(
                'tools.scenarios._cmd_refs.resolve',
                return_value={'mapping': mapping, 'unresolved': [], 'resolved': ''},
            ),
        ):
            result = scenarios.describe_scenario(_MOCK_CONN, scenario_id=1)

        expr = result['blocks'][0]['sub_elements'][0]['expressions'][0]
        assert 'expression_resolved' in expr
        assert '[Salon][Thermostat][Température]' in expr['expression_resolved']

    def test_no_resolved_suffix_when_expression_has_no_cmd_ref(self):
        walker_res = _walker_result()
        walker_res['tree'][0]['sub_elements'][0]['expressions'][0]['expression'] = 'time() > 800'
        with (
            patch('tools.scenarios._walker.walk', return_value=walker_res),
            patch('tools.scenarios._cmd_refs.resolve', return_value=_empty_cmd_refs_result()),
        ):
            result = scenarios.describe_scenario(_MOCK_CONN, scenario_id=1)

        expr = result['blocks'][0]['sub_elements'][0]['expressions'][0]
        assert 'expression_resolved' not in expr

    def test_cmd_mapping_in_result(self):
        mapping = {'123': '[Salon][Thermostat][Température]'}
        with (
            patch('tools.scenarios._walker.walk', return_value=_walker_result(empty_tree=True)),
            patch(
                'tools.scenarios._cmd_refs.resolve',
                return_value={'mapping': mapping, 'unresolved': [], 'resolved': ''},
            ),
        ):
            result = scenarios.describe_scenario(_MOCK_CONN, scenario_id=1)

        assert result['cmd_mapping'] == mapping

    def test_unresolved_cmd_ids_propagated(self):
        with (
            patch('tools.scenarios._walker.walk', return_value=_walker_result(empty_tree=True)),
            patch(
                'tools.scenarios._cmd_refs.resolve',
                return_value={'mapping': {}, 'unresolved': [123], 'resolved': ''},
            ),
        ):
            result = scenarios.describe_scenario(_MOCK_CONN, scenario_id=1)

        assert 123 in result['unresolved_cmd_ids']

    def test_truncated_flag_propagated(self):
        walker_res = {**_walker_result(empty_tree=True), 'truncated': True}
        with (
            patch('tools.scenarios._walker.walk', return_value=walker_res),
            patch('tools.scenarios._cmd_refs.resolve', return_value=_empty_cmd_refs_result()),
        ):
            result = scenarios.describe_scenario(_MOCK_CONN, scenario_id=1)

        assert result['truncated'] is True

    def test_warnings_propagated(self):
        walker_res = {**_walker_result(empty_tree=True), 'warnings': ['trunc at element 5']}
        with (
            patch('tools.scenarios._walker.walk', return_value=walker_res),
            patch('tools.scenarios._cmd_refs.resolve', return_value=_empty_cmd_refs_result()),
        ):
            result = scenarios.describe_scenario(_MOCK_CONN, scenario_id=1)

        assert 'trunc at element 5' in result['warnings']

    def test_empty_trigger_returns_empty_string_resolved(self):
        """Couvre _resolve_text('') — branche `if not text: return text`."""
        walker_res = _walker_result(empty_tree=True)
        walker_res['scenario']['trigger'] = None
        with (
            patch('tools.scenarios._walker.walk', return_value=walker_res),
            patch('tools.scenarios._cmd_refs.resolve', return_value=_empty_cmd_refs_result()),
        ):
            result = scenarios.describe_scenario(_MOCK_CONN, scenario_id=1)

        assert result['scenario']['trigger_resolved'] == ''

    def test_nested_children_humanized(self):
        """Couvre _humanize — branche node avec children."""
        child_node = {
            'element_id': 99,
            'depth': 1,
            'sub_elements': [
                {
                    'sub_id': 50,
                    'ss_type': 'action',
                    'ss_subtype': 'do',
                    'expressions': [
                        {'expr_id': 60, 'order': 1, 'type': 'action',
                         'expression': 'cmd::execDuration', 'options': None}
                    ],
                }
            ],
        }
        walker_res = _walker_result()
        walker_res['tree'][0]['children'] = [child_node]
        with (
            patch('tools.scenarios._walker.walk', return_value=walker_res),
            patch('tools.scenarios._cmd_refs.resolve', return_value=_empty_cmd_refs_result()),
        ):
            result = scenarios.describe_scenario(_MOCK_CONN, scenario_id=1)

        assert 'children' in result['blocks'][0]
        assert result['blocks'][0]['children'][0]['element_id'] == 99


# ---------------------------------------------------------------------------
# find_scenario_dependencies
# ---------------------------------------------------------------------------


class TestFindScenarioDependencies:
    def test_scenario_not_found(self):
        error_result = {'error': 'Scénario introuvable : id=999'}
        with patch('tools.scenarios._usage_graph.resolve', return_value=error_result):
            result = scenarios.find_scenario_dependencies(_MOCK_CONN, scenario_id=999)

        assert 'error' in result

    def test_returns_callers(self):
        dep_result = {
            'target': {'type': 'scenario', 'id': 1, 'name': 'Chauffage'},
            'references': {
                'triggers': [],
                'conditions': [],
                'actions': [],
                'plugin_consumers': [],
                'datastore_refs': [],
                'scenario_calls': [{'id': 5, 'name': 'Main'}],
            },
            'false_positive_warnings': [],
        }
        with patch('tools.scenarios._usage_graph.resolve', return_value=dep_result):
            result = scenarios.find_scenario_dependencies(_MOCK_CONN, scenario_id=1)

        assert result['references']['scenario_calls'][0]['id'] == 5

    def test_no_dependencies_returns_empty_lists(self):
        dep_result = {
            'target': {'type': 'scenario', 'id': 1, 'name': 'Test'},
            'references': {
                'triggers': [],
                'conditions': [],
                'actions': [],
                'plugin_consumers': [],
                'datastore_refs': [],
                'scenario_calls': [],
            },
            'false_positive_warnings': [],
        }
        with patch('tools.scenarios._usage_graph.resolve', return_value=dep_result):
            result = scenarios.find_scenario_dependencies(_MOCK_CONN, scenario_id=1)

        assert result['references']['scenario_calls'] == []

    def test_calls_usage_graph_with_correct_args(self):
        with patch('tools.scenarios._usage_graph.resolve', return_value={}) as mock_r:
            scenarios.find_scenario_dependencies(_MOCK_CONN, scenario_id=42)

        args = mock_r.call_args[0]
        assert args[0] == 'scenario'
        assert args[1] == 42
        assert args[2] is _MOCK_CONN


# ---------------------------------------------------------------------------
# get_scenario_log
# ---------------------------------------------------------------------------


class TestGetScenarioLog:
    def test_log_found_returns_lines(self):
        log_result = {
            'log_file': '/var/www/html/log/scenarioLog/scenario1.log',
            'lines': ['[2026-05-04] Scénario démarré', '[2026-05-04] Fin'],
            'count': 2,
        }
        with patch('tools.scenarios._logs.tail', return_value=log_result):
            result = scenarios.get_scenario_log(_MOCK_CONN, scenario_id=1)

        assert result['count'] == 2
        assert result['lines'][0] == '[2026-05-04] Scénario démarré'

    def test_log_not_found_returns_error(self):
        error_result = {
            'error': "Fichier log introuvable : 'scenarioLog/scenario999.log'",
            'log_file': None,
            'lines': [],
            'count': 0,
        }
        with patch('tools.scenarios._logs.tail', return_value=error_result):
            result = scenarios.get_scenario_log(_MOCK_CONN, scenario_id=999)

        assert 'error' in result
        assert result['count'] == 0

    def test_log_name_format(self):
        with patch('tools.scenarios._logs.tail', return_value={'lines': [], 'count': 0}) as mock_t:
            scenarios.get_scenario_log(_MOCK_CONN, scenario_id=42)

        assert mock_t.call_args[0][0] == 'scenarioLog/scenario42.log'

    def test_custom_lines_passed(self):
        with patch('tools.scenarios._logs.tail', return_value={'lines': [], 'count': 0}) as mock_t:
            scenarios.get_scenario_log(_MOCK_CONN, scenario_id=1, lines=50)

        assert mock_t.call_args.kwargs.get('lines') == 50

    def test_lines_capped_at_500(self):
        with patch('tools.scenarios._logs.tail', return_value={'lines': [], 'count': 0}) as mock_t:
            scenarios.get_scenario_log(_MOCK_CONN, scenario_id=1, lines=9999)

        assert mock_t.call_args.kwargs.get('lines') == 500

    def test_db_not_queried_for_log(self):
        with (
            patch('tools.scenarios._logs.tail', return_value={'lines': [], 'count': 0}),
            patch('tools.scenarios._db.query') as mock_q,
        ):
            scenarios.get_scenario_log(_MOCK_CONN, scenario_id=1)

        mock_q.assert_not_called()


# ---------------------------------------------------------------------------
# Runtime API enrichment — list_scenarios / find_scenarios_advanced
# ---------------------------------------------------------------------------


class TestListScenariosRuntime:
    def test_enriches_with_state_and_last_launch(self):
        rows = [_scen_row(id=1, name='S1')]
        api_data = [{'id': '1', 'state': 'stop', 'lastLaunch': '2026-05-04 10:00:00'}]
        with (
            patch('tools.scenarios._db.query', return_value=rows),
            patch('tools.scenarios._api.call', return_value={'result': api_data}),
        ):
            result = scenarios.list_scenarios(_MOCK_CONN, apikey='test-key')

        scen = result['scenarios'][0]
        assert scen['state'] == 'stop'
        assert scen['lastLaunch'] == '2026-05-04 10:00:00'

    def test_graceful_degradation_on_api_error(self):
        rows = [_scen_row(id=1, name='S1', lastLaunch=None, state=None)]
        with (
            patch('tools.scenarios._db.query', return_value=rows),
            patch('tools.scenarios._api.call', return_value={'error': 'timeout'}),
        ):
            result = scenarios.list_scenarios(_MOCK_CONN, apikey='test-key')

        assert result['total'] == 1

    def test_no_api_call_when_empty_apikey(self):
        rows = [_scen_row(id=1)]
        with (
            patch('tools.scenarios._db.query', return_value=rows),
            patch('tools.scenarios._api.call') as mock_api,
        ):
            scenarios.list_scenarios(_MOCK_CONN, apikey='')

        mock_api.assert_not_called()

    def test_multiple_scenarios_enriched_from_single_api_call(self):
        rows = [_scen_row(id=1, name='S1'), _scen_row(id=2, name='S2')]
        api_data = [
            {'id': '1', 'state': 'stop', 'lastLaunch': '2026-05-04 08:00:00'},
            {'id': '2', 'state': 'run', 'lastLaunch': '2026-05-04 09:00:00'},
        ]
        with (
            patch('tools.scenarios._db.query', return_value=rows),
            patch('tools.scenarios._api.call', return_value={'result': api_data}) as mock_api,
        ):
            result = scenarios.list_scenarios(_MOCK_CONN, apikey='test-key')

        mock_api.assert_called_once()
        assert result['scenarios'][0]['state'] == 'stop'
        assert result['scenarios'][1]['state'] == 'run'

    def test_find_scenarios_advanced_also_enriches(self):
        rows = [_scen_row(id=5, name='S5')]
        api_data = [{'id': '5', 'state': 'error', 'lastLaunch': '2026-05-03 22:00:00'}]
        with (
            patch('tools.scenarios._db.query', return_value=rows),
            patch('tools.scenarios._api.call', return_value={'result': api_data}),
        ):
            result = scenarios.find_scenarios_advanced(_MOCK_CONN, apikey='test-key')

        assert result['scenarios'][0]['state'] == 'error'


# ---------------------------------------------------------------------------
# Runtime API enrichment — get_scenario / describe_scenario
# ---------------------------------------------------------------------------


class TestGetScenarioRuntime:
    def test_enriches_with_state_and_last_launch(self):
        rows = [_scen_row(id=1)]
        api_result = {'id': '1', 'name': 'S1', 'state': 'run', 'lastLaunch': '2026-05-04 11:00:00'}
        with (
            patch('tools.scenarios._db.query', return_value=rows),
            patch('tools.scenarios._api.call', return_value={'result': api_result}),
        ):
            result = scenarios.get_scenario(_MOCK_CONN, scenario_id=1, apikey='test-key')

        assert result['scenario']['state'] == 'run'
        assert result['scenario']['lastLaunch'] == '2026-05-04 11:00:00'

    def test_graceful_degradation_on_api_error(self):
        rows = [_scen_row(id=1)]
        with (
            patch('tools.scenarios._db.query', return_value=rows),
            patch('tools.scenarios._api.call', return_value={'error': 'timeout'}),
        ):
            result = scenarios.get_scenario(_MOCK_CONN, scenario_id=1, apikey='test-key')

        assert 'scenario' in result
        assert result['scenario']['name'] == 'Chauffage salon'

    def test_no_api_call_when_empty_apikey(self):
        rows = [_scen_row(id=1)]
        with (
            patch('tools.scenarios._db.query', return_value=rows),
            patch('tools.scenarios._api.call') as mock_api,
        ):
            scenarios.get_scenario(_MOCK_CONN, scenario_id=1, apikey='')

        mock_api.assert_not_called()

    def test_api_not_called_when_scenario_not_found(self):
        with (
            patch('tools.scenarios._db.query', return_value=[]),
            patch('tools.scenarios._api.call') as mock_api,
        ):
            result = scenarios.get_scenario(_MOCK_CONN, scenario_id=999, apikey='test-key')

        mock_api.assert_not_called()
        assert 'error' in result

    def test_describe_scenario_enriches_with_runtime(self):
        api_result = {'id': '1', 'state': 'stop', 'lastLaunch': '2026-05-04 12:00:00'}
        with (
            patch('tools.scenarios._walker.walk', return_value=_walker_result(empty_tree=True)),
            patch('tools.scenarios._cmd_refs.resolve', return_value=_empty_cmd_refs_result()),
            patch('tools.scenarios._api.call', return_value={'result': api_result}),
        ):
            result = scenarios.describe_scenario(_MOCK_CONN, scenario_id=1, apikey='test-key')

        assert result['scenario']['state'] == 'stop'
        assert result['scenario']['lastLaunch'] == '2026-05-04 12:00:00'


# ---------------------------------------------------------------------------
# _fetch_runtime_map / _fetch_runtime_single — internal helpers
# ---------------------------------------------------------------------------


class TestFetchRuntimeHelpers:
    def test_fetch_map_returns_empty_on_empty_apikey(self):
        with patch('tools.scenarios._api.call') as mock_api:
            result = scenarios._fetch_runtime_map('')

        mock_api.assert_not_called()
        assert result == {}

    def test_fetch_map_returns_empty_on_api_error(self):
        with patch('tools.scenarios._api.call', return_value={'error': 'ko'}):
            result = scenarios._fetch_runtime_map('key')

        assert result == {}

    def test_fetch_map_returns_empty_when_result_not_list(self):
        with patch('tools.scenarios._api.call', return_value={'result': {'id': '1'}}):
            result = scenarios._fetch_runtime_map('key')

        assert result == {}

    def test_fetch_map_parses_ids_as_int(self):
        api_data = [{'id': '42', 'state': 'stop', 'lastLaunch': '2026-05-04'}]
        with patch('tools.scenarios._api.call', return_value={'result': api_data}):
            result = scenarios._fetch_runtime_map('key')

        assert 42 in result
        assert result[42]['state'] == 'stop'

    def test_fetch_single_returns_empty_on_empty_apikey(self):
        with patch('tools.scenarios._api.call') as mock_api:
            result = scenarios._fetch_runtime_single('', 1)

        mock_api.assert_not_called()
        assert result == {}

    def test_fetch_single_returns_empty_on_api_error(self):
        with patch('tools.scenarios._api.call', return_value={'error': 'ko'}):
            result = scenarios._fetch_runtime_single('key', 1)

        assert result == {}

    def test_fetch_single_returns_state_and_last_launch(self):
        api_result = {'id': '1', 'state': 'run', 'lastLaunch': '2026-05-04 08:00:00'}
        with patch('tools.scenarios._api.call', return_value={'result': api_result}):
            result = scenarios._fetch_runtime_single('key', 1)

        assert result == {'state': 'run', 'lastLaunch': '2026-05-04 08:00:00'}
