"""Tests unitaires — tools/query_sql.py (Famille 7, 1 tool)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from _domain.sanitize import FILTERED
from tools import query_sql as qsql

_MOCK_CONN = MagicMock()

_ROW_EQ = {
    'id': 1,
    'name': 'Prise Salon',
    'eqType_name': 'virtual',
    'object_id': 2,
    'isEnable': 1,
    'isVisible': 1,
}


# ---------------------------------------------------------------------------
# _check_select_only
# ---------------------------------------------------------------------------


class TestCheckSelectOnly:
    def test_select_ok(self):
        assert qsql._check_select_only('SELECT id FROM eqLogic') is None

    def test_select_with_limit_ok(self):
        assert qsql._check_select_only('SELECT * FROM cmd LIMIT 10') is None

    def test_insert_rejected(self):
        err = qsql._check_select_only("INSERT INTO eqLogic (name) VALUES ('x')")
        assert err is not None
        assert 'INSERT' in err

    def test_update_rejected(self):
        err = qsql._check_select_only("UPDATE eqLogic SET name='x' WHERE id=1")
        assert err is not None
        assert 'UPDATE' in err

    def test_delete_rejected(self):
        err = qsql._check_select_only('DELETE FROM eqLogic WHERE id=1')
        assert err is not None
        assert 'DELETE' in err

    def test_drop_rejected(self):
        err = qsql._check_select_only('DROP TABLE eqLogic')
        assert err is not None

    def test_create_rejected(self):
        err = qsql._check_select_only('CREATE TABLE foo (id INT)')
        assert err is not None

    def test_multiple_statements_rejected(self):
        err = qsql._check_select_only('SELECT 1; DROP TABLE eqLogic')
        assert err is not None
        assert '2' in err

    def test_empty_string_rejected(self):
        err = qsql._check_select_only('')
        assert err is not None

    def test_semicolon_only_rejected(self):
        err = qsql._check_select_only(';')
        assert err is not None


# ---------------------------------------------------------------------------
# _extract_table_names
# ---------------------------------------------------------------------------


class TestExtractTableNames:
    def test_simple_from(self):
        tables = qsql._extract_table_names('SELECT * FROM eqLogic')
        assert tables == ['eqlogic']

    def test_from_with_backticks(self):
        tables = qsql._extract_table_names('SELECT * FROM `scenario`')
        assert tables == ['scenario']

    def test_join_extracted(self):
        tables = qsql._extract_table_names(
            'SELECT e.name, c.name FROM eqLogic e JOIN cmd c ON e.id = c.eqLogic_id'
        )
        assert 'eqlogic' in tables
        assert 'cmd' in tables

    def test_multiple_joins(self):
        sql = (
            'SELECT * FROM eqLogic e '
            'JOIN cmd c ON e.id = c.eqLogic_id '
            'JOIN object o ON e.object_id = o.id'
        )
        tables = qsql._extract_table_names(sql)
        assert len(tables) == 3

    def test_no_table(self):
        tables = qsql._extract_table_names('SELECT 1+1')
        assert tables == []


# ---------------------------------------------------------------------------
# _check_blacklist
# ---------------------------------------------------------------------------


class TestCheckBlacklist:
    def test_user_blocked(self):
        assert qsql._check_blacklist(['user']) is not None

    def test_session_blocked(self):
        assert qsql._check_blacklist(['session']) is not None

    def test_network_blocked(self):
        assert qsql._check_blacklist(['network']) is not None

    def test_creds_pattern_blocked(self):
        assert qsql._check_blacklist(['creds']) is not None
        assert qsql._check_blacklist(['credentials']) is not None

    def test_password_pattern_blocked(self):
        assert qsql._check_blacklist(['password_store']) is not None
        assert qsql._check_blacklist(['passwords']) is not None

    def test_token_pattern_blocked(self):
        assert qsql._check_blacklist(['tokens']) is not None
        assert qsql._check_blacklist(['token_cache']) is not None

    def test_eqlogic_allowed(self):
        assert qsql._check_blacklist(['eqlogic']) is None

    def test_cmd_allowed(self):
        assert qsql._check_blacklist(['cmd']) is None

    def test_config_allowed(self):
        assert qsql._check_blacklist(['config']) is None

    def test_mixed_blocked_and_allowed(self):
        assert qsql._check_blacklist(['eqlogic', 'user']) is not None

    def test_empty_list_ok(self):
        assert qsql._check_blacklist([]) is None


# ---------------------------------------------------------------------------
# _check_sensitive_columns — D15.3
# ---------------------------------------------------------------------------


class TestCheckSensitiveColumns:
    def test_password_column_blocked(self):
        err = qsql._check_sensitive_columns('SELECT password FROM config')
        assert err is not None
        assert 'D15.3' in err

    def test_token_column_blocked(self):
        err = qsql._check_sensitive_columns('SELECT token FROM config')
        assert err is not None

    def test_apikey_column_blocked(self):
        err = qsql._check_sensitive_columns('SELECT apikey FROM config')
        assert err is not None

    def test_secret_column_blocked(self):
        err = qsql._check_sensitive_columns('SELECT secret FROM plugin')
        assert err is not None

    def test_private_key_column_blocked(self):
        err = qsql._check_sensitive_columns('SELECT private_key, name FROM config')
        assert err is not None

    def test_star_allowed(self):
        # SELECT * → sanitisation gère, pas de refus
        err = qsql._check_sensitive_columns('SELECT * FROM config')
        assert err is None

    def test_safe_columns_allowed(self):
        err = qsql._check_sensitive_columns('SELECT id, name, value FROM eqLogic')
        assert err is None

    def test_no_from_clause_safe(self):
        err = qsql._check_sensitive_columns('SELECT 1')
        assert err is None

    def test_password_in_where_not_blocked(self):
        # La vérification ne porte que sur le SELECT, pas le WHERE
        err = qsql._check_sensitive_columns("SELECT key, value FROM config WHERE key = 'password'")
        assert err is None


# ---------------------------------------------------------------------------
# _ensure_limit
# ---------------------------------------------------------------------------


class TestEnsureLimit:
    def test_no_limit_injects_default(self):
        sql = qsql._ensure_limit('SELECT * FROM eqLogic')
        assert f'LIMIT {qsql._SQL_DEFAULT_LIMIT}' in sql

    def test_existing_limit_kept(self):
        sql = qsql._ensure_limit('SELECT * FROM eqLogic LIMIT 10')
        assert 'LIMIT 10' in sql

    def test_limit_exceeding_max_capped(self):
        sql = qsql._ensure_limit(f'SELECT * FROM eqLogic LIMIT {qsql._SQL_MAX_LIMIT + 100}')
        assert f'LIMIT {qsql._SQL_MAX_LIMIT}' in sql
        assert str(qsql._SQL_MAX_LIMIT + 100) not in sql

    def test_limit_at_max_kept(self):
        sql = qsql._ensure_limit(f'SELECT * FROM eqLogic LIMIT {qsql._SQL_MAX_LIMIT}')
        assert f'LIMIT {qsql._SQL_MAX_LIMIT}' in sql

    def test_semicolon_stripped_before_limit_injection(self):
        sql = qsql._ensure_limit('SELECT * FROM eqLogic;')
        assert ';' not in sql
        assert f'LIMIT {qsql._SQL_DEFAULT_LIMIT}' in sql

    def test_limit_1_kept(self):
        sql = qsql._ensure_limit('SELECT * FROM eqLogic LIMIT 1')
        assert 'LIMIT 1' in sql


# ---------------------------------------------------------------------------
# query_sql — refus DML
# ---------------------------------------------------------------------------


class TestQuerySqlDmlRejected:
    def test_insert_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, "INSERT INTO eqLogic (name) VALUES ('x')")
        assert 'error' in result
        assert '_filtered_fields' in result

    def test_update_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, "UPDATE eqLogic SET name='x'")
        assert 'error' in result

    def test_delete_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, 'DELETE FROM eqLogic')
        assert 'error' in result

    def test_drop_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, 'DROP TABLE eqLogic')
        assert 'error' in result

    def test_multiple_statements_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, 'SELECT 1; DROP TABLE eqLogic')
        assert 'error' in result


# ---------------------------------------------------------------------------
# query_sql — blacklist tables
# ---------------------------------------------------------------------------


class TestQuerySqlBlacklistTables:
    def test_user_table_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM user')
        assert 'error' in result
        assert 'user' in result['error']

    def test_session_table_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM session')
        assert 'error' in result

    def test_network_table_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM network')
        assert 'error' in result

    def test_credentials_table_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM credentials')
        assert 'error' in result

    def test_passwords_table_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM passwords')
        assert 'error' in result

    def test_tokens_table_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM tokens')
        assert 'error' in result

    def test_join_on_blacklisted_rejected(self):
        result = qsql.query_sql(
            _MOCK_CONN,
            'SELECT e.name FROM eqLogic e JOIN user u ON e.id = u.eq_id',
        )
        assert 'error' in result


# ---------------------------------------------------------------------------
# query_sql — D15.3 colonnes sensibles
# ---------------------------------------------------------------------------


class TestQuerySqlD153:
    def test_password_column_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, 'SELECT password FROM config')
        assert 'error' in result
        assert 'D15.3' in result['error']

    def test_token_column_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, 'SELECT token FROM config')
        assert 'error' in result

    def test_apikey_column_rejected(self):
        result = qsql.query_sql(_MOCK_CONN, 'SELECT apikey FROM config')
        assert 'error' in result

    def test_star_select_allowed_with_sanitization(self):
        with patch('tools.query_sql._db.query', return_value=[_ROW_EQ]):
            result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM eqLogic')
        assert 'error' not in result
        assert result['count'] == 1


# ---------------------------------------------------------------------------
# query_sql — LIMIT injection
# ---------------------------------------------------------------------------


class TestQuerySqlLimit:
    def test_limit_injected_when_absent(self):
        with patch('tools.query_sql._db.query', return_value=[]) as mock_q:
            qsql.query_sql(_MOCK_CONN, 'SELECT * FROM eqLogic')
        sql_executed = mock_q.call_args[0][1]
        assert f'LIMIT {qsql._SQL_DEFAULT_LIMIT}' in sql_executed

    def test_limit_capped_at_max(self):
        with patch('tools.query_sql._db.query', return_value=[]) as mock_q:
            qsql.query_sql(_MOCK_CONN, f'SELECT * FROM eqLogic LIMIT {qsql._SQL_MAX_LIMIT + 500}')
        sql_executed = mock_q.call_args[0][1]
        assert f'LIMIT {qsql._SQL_MAX_LIMIT}' in sql_executed

    def test_limit_within_max_kept(self):
        with patch('tools.query_sql._db.query', return_value=[]) as mock_q:
            qsql.query_sql(_MOCK_CONN, 'SELECT * FROM eqLogic LIMIT 10')
        sql_executed = mock_q.call_args[0][1]
        assert 'LIMIT 10' in sql_executed


# ---------------------------------------------------------------------------
# query_sql — résultats et sanitisation
# ---------------------------------------------------------------------------


class TestQuerySqlResults:
    def test_empty_result_ok(self):
        with patch('tools.query_sql._db.query', return_value=[]):
            result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM eqLogic')
        assert result['rows'] == []
        assert result['count'] == 0
        assert result['_filtered_fields'] == []

    def test_rows_returned(self):
        with patch('tools.query_sql._db.query', return_value=[_ROW_EQ]):
            result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM eqLogic')
        assert result['count'] == 1
        assert result['rows'][0]['name'] == 'Prise Salon'

    def test_sanitisation_applied_unknown_field(self):
        row = {**_ROW_EQ, 'internal_secret': 'hidden'}
        with patch('tools.query_sql._db.query', return_value=[row]):
            result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM eqLogic')
        # Whitelist eqLogic active → champ hors whitelist masqué
        assert result['rows'][0]['internal_secret'] == FILTERED
        assert 'internal_secret' in result['_filtered_fields']

    def test_sanitisation_regex_on_field_name(self):
        # Table inconnue — mechanism 2 : regex sur nom de champ
        row = {'id': 1, 'name': 'foo', 'apikey': 'secret123'}
        with patch('tools.query_sql._db.query', return_value=[row]):
            result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM unknown_table')
        assert result['rows'][0]['apikey'] == FILTERED

    def test_query_field_in_result(self):
        with patch('tools.query_sql._db.query', return_value=[]):
            result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM eqLogic')
        assert 'query' in result
        assert 'eqLogic' in result['query']

    def test_filtered_fields_in_result(self):
        with patch('tools.query_sql._db.query', return_value=[]):
            result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM eqLogic')
        assert '_filtered_fields' in result

    def test_config_table_sensitive_value_filtered(self):
        # config.value avec clé sensible → valeur masquée (_sanitize_config_row)
        row = {'plugin': 'core', 'key': 'apikey', 'value': 'abc123'}
        with patch('tools.query_sql._db.query', return_value=[row]):
            result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM config')
        assert result['rows'][0]['value'] == FILTERED
        assert 'apikey' in result['_filtered_fields']

    def test_config_table_safe_key_not_filtered(self):
        row = {'plugin': 'core', 'key': 'language', 'value': 'fr_FR'}
        with patch('tools.query_sql._db.query', return_value=[row]):
            result = qsql.query_sql(_MOCK_CONN, 'SELECT * FROM config')
        assert result['rows'][0]['value'] == 'fr_FR'
        assert result['_filtered_fields'] == []

    def test_multi_table_query_sanitized_without_whitelist(self):
        row = {'eq_name': 'Salon', 'cmd_name': 'ON', 'secret_col': 'hidden'}
        sql = (
            'SELECT e.name as eq_name, c.name as cmd_name, e.secret_col '
            'FROM eqLogic e JOIN cmd c ON e.id = c.eqLogic_id'
        )
        with patch('tools.query_sql._db.query', return_value=[row]):
            result = qsql.query_sql(_MOCK_CONN, sql)
        # Multi-table → table=None → pas de whitelist, mais regex sur field names
        assert result['count'] == 1
