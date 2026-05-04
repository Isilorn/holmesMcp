"""Tests d'intégration live — tools/discovery.py (Famille 1, 4 tools)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from tools import discovery

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# get_install_overview
# ---------------------------------------------------------------------------


class TestGetInstallOverviewLive:
    def test_structure_complete(self, db_conn):
        result = discovery.get_install_overview(db_conn)
        for key in ('jeedom_version', 'equipements', 'scenarios', 'plugins', 'objets', 'commandes'):
            assert key in result, f'Clé manquante : {key}'
        assert isinstance(result['_filtered_fields'], list)

    def test_jeedom_version_non_vide(self, db_conn):
        result = discovery.get_install_overview(db_conn)
        assert result['jeedom_version'] not in ('', 'inconnu')

    def test_comptages_coherents(self, db_conn):
        result = discovery.get_install_overview(db_conn)
        eq = result['equipements']
        scen = result['scenarios']
        assert eq['total'] >= eq['actifs'] >= 0
        assert scen['total'] >= scen['actifs'] >= 0
        assert result['plugins'] >= 1
        assert result['objets'] >= 1
        assert result['commandes'] >= 1

    def test_pas_de_champs_filtres(self, db_conn):
        result = discovery.get_install_overview(db_conn)
        assert result['_filtered_fields'] == []


# ---------------------------------------------------------------------------
# list_objects
# ---------------------------------------------------------------------------


class TestListObjectsLive:
    def test_structure(self, db_conn):
        result = discovery.list_objects(db_conn)
        assert 'objects' in result
        assert 'total' in result
        assert isinstance(result['objects'], list)
        assert isinstance(result['_filtered_fields'], list)

    def test_total_coherent(self, db_conn):
        result = discovery.list_objects(db_conn)
        assert result['total'] == len(result['objects'])

    def test_au_moins_un_objet(self, db_conn):
        result = discovery.list_objects(db_conn)
        assert result['total'] >= 1

    def test_champs_objet(self, db_conn):
        result = discovery.list_objects(db_conn)
        obj = result['objects'][0]
        assert 'id' in obj
        assert 'name' in obj
        assert obj['name']


# ---------------------------------------------------------------------------
# list_plugins
# ---------------------------------------------------------------------------


class TestListPluginsLive:
    def test_structure(self, db_conn):
        result = discovery.list_plugins(db_conn)
        assert 'plugins' in result
        assert 'total' in result
        assert isinstance(result['plugins'], list)
        assert isinstance(result['_filtered_fields'], list)

    def test_holmes_plugin_present(self, db_conn):
        result = discovery.list_plugins(db_conn)
        logical_ids = [p.get('logical_id') for p in result['plugins']]
        assert 'holmesMcp' in logical_ids, f'holmesMcp absent de {logical_ids}'

    def test_champs_plugin(self, db_conn):
        result = discovery.list_plugins(db_conn)
        p = result['plugins'][0]
        for field in ('id', 'name', 'version', 'state', 'logical_id'):
            assert field in p, f'Champ manquant : {field}'

    def test_total_coherent(self, db_conn):
        result = discovery.list_plugins(db_conn)
        assert result['total'] == len(result['plugins'])


# ---------------------------------------------------------------------------
# get_config
# ---------------------------------------------------------------------------


class TestGetConfigLive:
    def test_core_structure(self, db_conn):
        result = discovery.get_config(db_conn, 'core')
        assert result['plugin'] == 'core'
        assert result['key_pattern'] is None
        assert isinstance(result['config'], list)
        assert result['total'] >= 1
        assert isinstance(result['_filtered_fields'], list)

    def test_key_pattern_filtre(self, db_conn):
        result = discovery.get_config(db_conn, 'core', key_pattern='version%')
        assert result['key_pattern'] == 'version%'
        for entry in result['config']:
            assert entry['key'].startswith('version'), (
                f"Clé {entry['key']!r} ne commence pas par 'version'"
            )

    def test_plugin_inexistant_retourne_vide(self, db_conn):
        result = discovery.get_config(db_conn, '__plugin_inexistant_xyz__')
        assert result['total'] == 0
        assert result['config'] == []

    def test_valeurs_sensibles_filtrees(self, db_conn):
        """Les clés de token holmesMcp doivent avoir leur valeur masquée."""
        result = discovery.get_config(db_conn, 'holmesMcp')
        token_entries = [e for e in result['config'] if e.get('key', '').startswith('token_')]
        if token_entries:
            for entry in token_entries:
                assert entry['value'] == '***FILTERED***', (
                    f"Token {entry['key']!r} non filtré : {entry['value']!r}"
                )
            assert any('token_' in f for f in result['_filtered_fields'])
