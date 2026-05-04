"""Tests d'intégration live — tools/query_sql.py (Famille 7, 1 tool)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from tools import query_sql as qs_tools

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Refus non-SELECT
# ---------------------------------------------------------------------------


class TestQuerySqlRefusNonSelectLive:
    def test_insert_refuse(self, db_conn):
        result = qs_tools.query_sql(db_conn, "INSERT INTO eqLogic (name) VALUES ('x')")
        assert 'error' in result
        assert 'SELECT' in result['error']

    def test_update_refuse(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'UPDATE eqLogic SET name="x" WHERE id=1')
        assert 'error' in result

    def test_delete_refuse(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'DELETE FROM eqLogic WHERE id=1')
        assert 'error' in result

    def test_drop_refuse(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'DROP TABLE eqLogic')
        assert 'error' in result

    def test_multiple_statements_refuse(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT 1; SELECT 2')
        assert 'error' in result


# ---------------------------------------------------------------------------
# Blacklist tables sensibles
# ---------------------------------------------------------------------------


class TestQuerySqlBlacklistLive:
    def test_table_user_refusee(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id FROM user LIMIT 1')
        assert 'error' in result
        assert 'user' in result['error']

    def test_table_session_refusee(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id FROM session LIMIT 1')
        assert 'error' in result

    def test_table_network_refusee(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id FROM network LIMIT 1')
        assert 'error' in result

    def test_table_credentials_pattern_refusee(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id FROM credentials LIMIT 1')
        assert 'error' in result

    def test_table_password_store_refusee(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id FROM password_store LIMIT 1')
        assert 'error' in result

    def test_table_tokens_refusee(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id FROM tokens LIMIT 1')
        assert 'error' in result


# ---------------------------------------------------------------------------
# D15.3 — colonnes sensibles dans SELECT
# ---------------------------------------------------------------------------


class TestQuerySqlColonnesSensiblesLive:
    def test_colonne_password_refusee(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id, password FROM config LIMIT 1')
        assert 'error' in result
        assert 'D15.3' in result['error'] or 'sensibles' in result['error']

    def test_colonne_token_refusee(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id, token FROM config LIMIT 1')
        assert 'error' in result

    def test_colonne_apikey_refusee(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id, apikey FROM config LIMIT 1')
        assert 'error' in result

    def test_select_star_autorise(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT * FROM eqLogic LIMIT 1')
        assert 'error' not in result, f'SELECT * refusé à tort : {result.get("error")}'


# ---------------------------------------------------------------------------
# LIMIT injecté / plafonné
# ---------------------------------------------------------------------------


class TestQuerySqlLimitLive:
    def test_limit_injecte_si_absent(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id, name FROM eqLogic')
        assert 'error' not in result
        assert 'LIMIT' in result['query'].upper()
        assert result['count'] <= 50

    def test_limit_respecte_si_present(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id, name FROM eqLogic LIMIT 5')
        assert 'error' not in result
        assert result['count'] <= 5

    def test_limit_plafonne_a_200(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id FROM eqLogic LIMIT 9999')
        assert 'error' not in result
        assert result['count'] <= 200
        assert '200' in result['query']


# ---------------------------------------------------------------------------
# Requêtes valides — structure et sanitisation
# ---------------------------------------------------------------------------


class TestQuerySqlRequetesValidesLive:
    def test_select_eqlogic(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id, name FROM eqLogic LIMIT 3')
        assert 'error' not in result
        assert 'rows' in result
        assert 'count' in result
        assert 'query' in result
        assert isinstance(result['rows'], list)
        assert isinstance(result['_filtered_fields'], list)

    def test_select_scenario(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id, name, isActive FROM scenario LIMIT 3')
        assert 'error' not in result
        assert result['count'] >= 1

    def test_select_object(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id, name FROM object LIMIT 5')
        assert 'error' not in result
        assert result['count'] >= 1

    def test_select_config_star_sanitise(self, db_conn):
        result = qs_tools.query_sql(
            db_conn, "SELECT `key`, value FROM config WHERE plugin='core' LIMIT 5"
        )
        assert 'error' not in result
        for row in result['rows']:
            assert row.get('value') != '***FILTERED***' or row.get('key') is not None

    def test_count_coherent(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT id FROM eqLogic LIMIT 10')
        assert 'error' not in result
        assert result['count'] == len(result['rows'])

    def test_jointure_valide(self, db_conn):
        result = qs_tools.query_sql(
            db_conn,
            'SELECT e.id, e.name, o.name AS objet'
            ' FROM eqLogic e LEFT JOIN object o ON e.object_id = o.id'
            ' LIMIT 3',
        )
        assert 'error' not in result
        assert result['count'] >= 1

    def test_select_datastore(self, db_conn):
        result = qs_tools.query_sql(db_conn, 'SELECT type, `key`, value FROM dataStore LIMIT 3')
        assert 'error' not in result

    def test_select_update_table(self, db_conn):
        result = qs_tools.query_sql(
            db_conn, "SELECT logicalId, name, status FROM `update` WHERE type='plugin' LIMIT 5"
        )
        assert 'error' not in result
