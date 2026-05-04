"""Tests d'intégration live — tools/datastore.py (Famille 4, 2 tools)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from tools import datastore

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# list_datastore_variables
# ---------------------------------------------------------------------------


class TestListDatastoreVariablesLive:
    def test_structure(self, db_conn):
        result = datastore.list_datastore_variables(db_conn)
        assert 'variables' in result
        assert 'total' in result
        assert isinstance(result['variables'], list)
        assert isinstance(result['_filtered_fields'], list)

    def test_total_coherent(self, db_conn):
        result = datastore.list_datastore_variables(db_conn)
        assert result['total'] == len(result['variables'])

    def test_filtre_type_global(self, db_conn):
        result = datastore.list_datastore_variables(db_conn, var_type='global')
        for var in result['variables']:
            assert var['type'] == 'global', f'Type inattendu : {var["type"]!r}'

    def test_filtre_type_scenario(self, db_conn):
        result = datastore.list_datastore_variables(db_conn, var_type='scenario')
        for var in result['variables']:
            assert var['type'] == 'scenario', f'Type inattendu : {var["type"]!r}'

    def test_limit_respecte(self, db_conn):
        result = datastore.list_datastore_variables(db_conn, limit=3)
        assert len(result['variables']) <= 3

    def test_champs_variable(self, db_conn):
        result = datastore.list_datastore_variables(db_conn, limit=1)
        if result['total'] == 0:
            pytest.skip('Aucune variable dataStore sur la box')
        var = result['variables'][0]
        for field in ('id', 'type', 'link_id', 'key', 'value'):
            assert field in var, f'Champ manquant : {field}'

    def test_key_pattern(self, first_datastore_var_key, db_conn):
        prefix = first_datastore_var_key[:2]
        result = datastore.list_datastore_variables(db_conn, key_pattern=f'{prefix}%')
        assert result['total'] >= 1
        for var in result['variables']:
            assert var['key'].lower().startswith(prefix.lower()), (
                f'Clé {var["key"]!r} ne commence pas par {prefix!r}'
            )

    def test_pagination(self, db_conn):
        all_vars = datastore.list_datastore_variables(db_conn, limit=200)
        if all_vars['total'] < 2:
            pytest.skip('Pas assez de variables pour tester la pagination')
        page0 = datastore.list_datastore_variables(db_conn, limit=1, offset=0)
        page1 = datastore.list_datastore_variables(db_conn, limit=1, offset=1)
        assert page0['variables'][0]['id'] != page1['variables'][0]['id']


# ---------------------------------------------------------------------------
# get_datastore_variable
# ---------------------------------------------------------------------------


class TestGetDatastoreVariableLive:
    def test_variable_existante(self, first_datastore_var_key, db_conn):
        result = datastore.get_datastore_variable(db_conn, first_datastore_var_key)
        assert 'error' not in result, f'Erreur inattendue : {result.get("error")}'
        assert result['key'] == first_datastore_var_key
        assert 'variables' in result
        assert result['total'] >= 1

    def test_variable_inexistante(self, db_conn):
        result = datastore.get_datastore_variable(db_conn, '__var_inexistante_xyz_holmes__')
        assert 'error' in result
        assert '_filtered_fields' in result

    def test_structure_retour(self, first_datastore_var_key, db_conn):
        result = datastore.get_datastore_variable(db_conn, first_datastore_var_key)
        if 'error' in result:
            pytest.skip('Variable introuvable')
        assert isinstance(result['variables'], list)
        assert isinstance(result['_filtered_fields'], list)
        var = result['variables'][0]
        for field in ('id', 'type', 'link_id', 'key', 'value'):
            assert field in var, f'Champ manquant : {field}'

    def test_filtre_type_restreint(
        self, first_datastore_var_key, first_datastore_var_type, db_conn
    ):
        result = datastore.get_datastore_variable(
            db_conn,
            first_datastore_var_key,
            var_type=first_datastore_var_type,
        )
        if 'error' in result:
            pytest.skip('Variable introuvable avec filtre type')
        for var in result['variables']:
            assert var['type'] == first_datastore_var_type
