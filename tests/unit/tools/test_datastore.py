"""Tests unitaires — tools/datastore.py (Famille 4, 2 tools)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from _domain.sanitize import FILTERED
from tools import datastore

_MOCK_CONN = MagicMock()

_ROW_GLOBAL = {'id': 1, 'type': 'global', 'link_id': 0, 'key': 'temp_salon', 'value': '21.5'}
_ROW_SCENARIO = {'id': 2, 'type': 'scenario', 'link_id': 42, 'key': 'compteur', 'value': '3'}


# ---------------------------------------------------------------------------
# list_datastore_variables
# ---------------------------------------------------------------------------


class TestListDatastoreVariables:
    def test_empty_db_returns_empty_list(self):
        with patch('tools.datastore._db.query', return_value=[]):
            result = datastore.list_datastore_variables(_MOCK_CONN)

        assert result['variables'] == []
        assert result['total'] == 0
        assert result['_filtered_fields'] == []

    def test_returns_rows_with_correct_fields(self):
        with patch('tools.datastore._db.query', return_value=[_ROW_GLOBAL, _ROW_SCENARIO]):
            result = datastore.list_datastore_variables(_MOCK_CONN)

        assert result['total'] == 2
        assert result['variables'][0]['key'] == 'temp_salon'
        assert result['variables'][0]['value'] == '21.5'
        assert result['variables'][0]['type'] == 'global'
        assert result['variables'][1]['link_id'] == 42

    def test_filter_by_type(self):
        with patch('tools.datastore._db.query', return_value=[]) as mock_q:
            datastore.list_datastore_variables(_MOCK_CONN, var_type='global')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'type=%s' in sql
        assert 'global' in params

    def test_filter_by_link_id(self):
        with patch('tools.datastore._db.query', return_value=[]) as mock_q:
            datastore.list_datastore_variables(_MOCK_CONN, link_id=42)

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'link_id=%s' in sql
        assert 42 in params

    def test_filter_by_key_pattern(self):
        with patch('tools.datastore._db.query', return_value=[]) as mock_q:
            datastore.list_datastore_variables(_MOCK_CONN, key_pattern='temp%')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'LIKE' in sql
        assert 'temp%' in params

    def test_multiple_filters_combined(self):
        with patch('tools.datastore._db.query', return_value=[]) as mock_q:
            datastore.list_datastore_variables(
                _MOCK_CONN, var_type='scenario', link_id=10, key_pattern='cpt%'
            )

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'type=%s' in sql
        assert 'link_id=%s' in sql
        assert 'LIKE' in sql
        assert 'scenario' in params
        assert 10 in params
        assert 'cpt%' in params

    def test_no_filter_no_where_clause(self):
        with patch('tools.datastore._db.query', return_value=[]) as mock_q:
            datastore.list_datastore_variables(_MOCK_CONN)

        sql = mock_q.call_args[0][1]
        assert 'WHERE' not in sql

    def test_limit_capped_at_200(self):
        with patch('tools.datastore._db.query', return_value=[]) as mock_q:
            datastore.list_datastore_variables(_MOCK_CONN, limit=999)

        params = mock_q.call_args[0][2]
        assert datastore._DATASTORE_LIMIT in params

    def test_limit_and_offset_in_query(self):
        with patch('tools.datastore._db.query', return_value=[]) as mock_q:
            datastore.list_datastore_variables(_MOCK_CONN, limit=50, offset=10)

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'LIMIT %s OFFSET %s' in sql
        assert 50 in params
        assert 10 in params

    def test_non_whitelisted_column_filtered(self):
        row = {**_ROW_GLOBAL, 'internal_secret': 'should_be_masked'}
        with patch('tools.datastore._db.query', return_value=[row]):
            result = datastore.list_datastore_variables(_MOCK_CONN)

        assert result['variables'][0]['internal_secret'] == FILTERED
        assert 'internal_secret' in result['_filtered_fields']

    def test_whitelisted_fields_all_visible(self):
        with patch('tools.datastore._db.query', return_value=[_ROW_GLOBAL]):
            result = datastore.list_datastore_variables(_MOCK_CONN)

        v = result['variables'][0]
        assert v['id'] == 1
        assert v['type'] == 'global'
        assert v['link_id'] == 0
        assert v['key'] == 'temp_salon'
        assert v['value'] == '21.5'

    def test_query_has_order_by(self):
        with patch('tools.datastore._db.query', return_value=[]) as mock_q:
            datastore.list_datastore_variables(_MOCK_CONN)

        sql = mock_q.call_args[0][1]
        assert 'ORDER BY' in sql


# ---------------------------------------------------------------------------
# get_datastore_variable
# ---------------------------------------------------------------------------


class TestGetDatastoreVariable:
    def test_found_single_variable(self):
        with patch('tools.datastore._db.query', return_value=[_ROW_GLOBAL]):
            result = datastore.get_datastore_variable(_MOCK_CONN, 'temp_salon')

        assert result['key'] == 'temp_salon'
        assert result['total'] == 1
        assert result['variables'][0]['value'] == '21.5'
        assert result['_filtered_fields'] == []

    def test_not_found_returns_error(self):
        with patch('tools.datastore._db.query', return_value=[]):
            result = datastore.get_datastore_variable(_MOCK_CONN, 'inconnu')

        assert 'error' in result
        assert 'inconnu' in result['error']
        assert result['_filtered_fields'] == []

    def test_key_in_where_clause(self):
        with patch('tools.datastore._db.query', return_value=[]) as mock_q:
            datastore.get_datastore_variable(_MOCK_CONN, 'ma_var')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert '`key`=%s' in sql
        assert 'ma_var' in params

    def test_optional_var_type_filter(self):
        with patch('tools.datastore._db.query', return_value=[]) as mock_q:
            datastore.get_datastore_variable(_MOCK_CONN, 'ma_var', var_type='global')

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'type=%s' in sql
        assert 'global' in params

    def test_optional_link_id_filter(self):
        with patch('tools.datastore._db.query', return_value=[]) as mock_q:
            datastore.get_datastore_variable(_MOCK_CONN, 'ma_var', link_id=5)

        sql = mock_q.call_args[0][1]
        params = mock_q.call_args[0][2]
        assert 'link_id=%s' in sql
        assert 5 in params

    def test_multiple_matches_returns_list(self):
        rows = [_ROW_GLOBAL, _ROW_SCENARIO]
        with patch('tools.datastore._db.query', return_value=rows):
            result = datastore.get_datastore_variable(_MOCK_CONN, 'compteur')

        assert result['total'] == 2
        assert len(result['variables']) == 2

    def test_non_whitelisted_column_filtered(self):
        row = {**_ROW_GLOBAL, 'db_internal': 'secret'}
        with patch('tools.datastore._db.query', return_value=[row]):
            result = datastore.get_datastore_variable(_MOCK_CONN, 'temp_salon')

        assert result['variables'][0]['db_internal'] == FILTERED
        assert 'db_internal' in result['_filtered_fields']

    def test_has_limit_in_query(self):
        with patch('tools.datastore._db.query', return_value=[]) as mock_q:
            datastore.get_datastore_variable(_MOCK_CONN, 'x')

        sql = mock_q.call_args[0][1]
        assert 'LIMIT' in sql
