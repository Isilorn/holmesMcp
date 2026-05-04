"""Tests unitaires — tools/search.py (Famille 6, 1 tool)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from _domain.sanitize import FILTERED
from tools import search

_MOCK_CONN = MagicMock()

_ROW_EQ = {
    'id': 1,
    'name': 'Prise Salon',
    'eqType_name': 'virtualAlarm',
    'object_id': 2,
    'isEnable': 1,
    'isVisible': 1,
}
_ROW_CMD = {
    'id': 10,
    'name': 'Lumière Salon ON',
    'eqLogic_id': 1,
    'type': 'action',
    'subType': 'other',
    'generic_type': 'LIGHT_ON',
}
_ROW_SCEN = {
    'id': 5,
    'name': 'Réveil Salon',
    'group': 'Matin',
    'isActive': 1,
    'mode': 'schedule',
}
_ROW_EXPR = {
    'id': 100,
    'scenarioSubElement_id': 20,
    'type': 'action',
    'expression': 'cmd::execCmd id=10 options={"message":"salon on"}',
}


def _make_se(eq=None, cmd=None, scen=None, expr=None):
    return [eq or [], cmd or [], scen or [], expr or []]


# ---------------------------------------------------------------------------
# search_text — validation
# ---------------------------------------------------------------------------


class TestSearchTextValidation:
    def test_empty_string_returns_error(self):
        with patch('tools.search._db.query', side_effect=_make_se()):
            result = search.search_text(_MOCK_CONN, '')

        assert 'error' in result
        assert '_filtered_fields' in result

    def test_single_char_returns_error(self):
        with patch('tools.search._db.query', side_effect=_make_se()):
            result = search.search_text(_MOCK_CONN, 'x')

        assert 'error' in result

    def test_two_chars_is_valid(self):
        with patch('tools.search._db.query', side_effect=_make_se()):
            result = search.search_text(_MOCK_CONN, 'sa')

        assert 'error' not in result


# ---------------------------------------------------------------------------
# search_text — résultats
# ---------------------------------------------------------------------------


class TestSearchTextResults:
    def test_empty_results_all_categories(self):
        with patch('tools.search._db.query', side_effect=_make_se()):
            result = search.search_text(_MOCK_CONN, 'salon')

        assert result['query'] == 'salon'
        assert result['equipements'] == []
        assert result['commandes'] == []
        assert result['scenarios'] == []
        assert result['expressions'] == []
        assert result['totals'] == {
            'equipements': 0,
            'commandes': 0,
            'scenarios': 0,
            'expressions': 0,
        }

    def test_equipements_found(self):
        with patch('tools.search._db.query', side_effect=_make_se(eq=[_ROW_EQ])):
            result = search.search_text(_MOCK_CONN, 'salon')

        assert len(result['equipements']) == 1
        assert result['equipements'][0]['name'] == 'Prise Salon'
        assert result['totals']['equipements'] == 1

    def test_commandes_found(self):
        with patch('tools.search._db.query', side_effect=_make_se(cmd=[_ROW_CMD])):
            result = search.search_text(_MOCK_CONN, 'salon')

        assert len(result['commandes']) == 1
        assert result['commandes'][0]['name'] == 'Lumière Salon ON'
        assert result['totals']['commandes'] == 1

    def test_scenarios_found(self):
        with patch('tools.search._db.query', side_effect=_make_se(scen=[_ROW_SCEN])):
            result = search.search_text(_MOCK_CONN, 'salon')

        assert len(result['scenarios']) == 1
        assert result['scenarios'][0]['name'] == 'Réveil Salon'
        assert result['totals']['scenarios'] == 1

    def test_expressions_found(self):
        with patch('tools.search._db.query', side_effect=_make_se(expr=[_ROW_EXPR])):
            result = search.search_text(_MOCK_CONN, 'salon')

        assert len(result['expressions']) == 1
        assert 'salon' in result['expressions'][0]['expression']
        assert result['totals']['expressions'] == 1

    def test_all_categories_found_simultaneously(self):
        with patch(
            'tools.search._db.query',
            side_effect=_make_se(eq=[_ROW_EQ], cmd=[_ROW_CMD], scen=[_ROW_SCEN], expr=[_ROW_EXPR]),
        ):
            result = search.search_text(_MOCK_CONN, 'salon')

        assert result['totals']['equipements'] == 1
        assert result['totals']['commandes'] == 1
        assert result['totals']['scenarios'] == 1
        assert result['totals']['expressions'] == 1

    def test_query_field_in_result(self):
        with patch('tools.search._db.query', side_effect=_make_se()):
            result = search.search_text(_MOCK_CONN, 'thermostat')

        assert result['query'] == 'thermostat'


# ---------------------------------------------------------------------------
# search_text — SQL et params
# ---------------------------------------------------------------------------


class TestSearchTextSql:
    def test_pattern_uses_percent_wildcards(self):
        with patch('tools.search._db.query', side_effect=_make_se()) as mock_q:
            search.search_text(_MOCK_CONN, 'salon')

        for c in mock_q.call_args_list:
            sql = c[0][1]
            params = c[0][2]
            if 'LIKE' in sql:
                assert '%salon%' in params

    def test_all_four_tables_queried(self):
        with patch('tools.search._db.query', side_effect=_make_se()) as mock_q:
            search.search_text(_MOCK_CONN, 'test')

        assert mock_q.call_count == 4
        sqls = [c[0][1] for c in mock_q.call_args_list]
        assert any('eqLogic' in s for s in sqls)
        assert any('cmd' in s for s in sqls)
        assert any('scenario' in s for s in sqls)
        assert any('scenarioExpression' in s for s in sqls)

    def test_limit_passed_to_queries(self):
        with patch('tools.search._db.query', side_effect=_make_se()) as mock_q:
            search.search_text(_MOCK_CONN, 'test', limit=30)

        for c in mock_q.call_args_list:
            params = c[0][2]
            assert 30 in params

    def test_limit_capped_at_50(self):
        with patch('tools.search._db.query', side_effect=_make_se()) as mock_q:
            search.search_text(_MOCK_CONN, 'test', limit=999)

        for c in mock_q.call_args_list:
            params = c[0][2]
            assert search._SEARCH_LIMIT_EACH in params


# ---------------------------------------------------------------------------
# search_text — sanitisation
# ---------------------------------------------------------------------------


class TestSearchTextSanitize:
    def test_non_whitelisted_eq_field_filtered(self):
        row = {**_ROW_EQ, 'internal_secret': 'hidden'}
        with patch('tools.search._db.query', side_effect=_make_se(eq=[row])):
            result = search.search_text(_MOCK_CONN, 'salon')

        assert result['equipements'][0]['internal_secret'] == FILTERED
        assert 'internal_secret' in result['_filtered_fields']

    def test_non_whitelisted_cmd_field_filtered(self):
        row = {**_ROW_CMD, 'db_internal': 'hidden'}
        with patch('tools.search._db.query', side_effect=_make_se(cmd=[row])):
            result = search.search_text(_MOCK_CONN, 'salon')

        assert result['commandes'][0]['db_internal'] == FILTERED

    def test_filtered_fields_deduplicated(self):
        eq_row = {**_ROW_EQ, 'secret_col': 'x'}
        cmd_row = {**_ROW_CMD, 'secret_col': 'y'}
        with patch(
            'tools.search._db.query',
            side_effect=_make_se(eq=[eq_row], cmd=[cmd_row]),
        ):
            result = search.search_text(_MOCK_CONN, 'salon')

        assert result['_filtered_fields'].count('secret_col') == 1

    def test_filtered_fields_empty_when_all_whitelisted(self):
        with patch('tools.search._db.query', side_effect=_make_se(eq=[_ROW_EQ])):
            result = search.search_text(_MOCK_CONN, 'salon')

        assert result['_filtered_fields'] == []
