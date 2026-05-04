"""Tests d'intégration live — tools/search.py (Famille 6, 1 tool)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from tools import search

pytestmark = pytest.mark.integration


class TestSearchTextLive:
    def test_texte_trop_court_1_char(self, db_conn):
        result = search.search_text(db_conn, 'a')
        assert 'error' in result
        assert '_filtered_fields' in result

    def test_texte_vide_refuse(self, db_conn):
        result = search.search_text(db_conn, '')
        assert 'error' in result

    def test_structure_retour(self, db_conn):
        result = search.search_text(db_conn, 'on')
        assert 'error' not in result, f'Erreur inattendue : {result.get("error")}'
        for key in ('query', 'equipements', 'commandes', 'scenarios', 'expressions', 'totals'):
            assert key in result, f'Clé manquante : {key}'
        assert isinstance(result['_filtered_fields'], list)

    def test_query_retourne_la_recherche(self, db_conn):
        result = search.search_text(db_conn, 'on')
        assert result['query'] == 'on'

    def test_totals_coherents(self, db_conn):
        result = search.search_text(db_conn, 'on')
        totals = result['totals']
        assert totals['equipements'] == len(result['equipements'])
        assert totals['commandes'] == len(result['commandes'])
        assert totals['scenarios'] == len(result['scenarios'])
        assert totals['expressions'] == len(result['expressions'])

    def test_au_moins_un_resultat_terme_commun(self, db_conn):
        result = search.search_text(db_conn, 'on')
        total = sum(result['totals'].values())
        assert total >= 1, 'Aucun résultat pour "on" — terme trop restrictif ou DB vide'

    def test_champs_equipement(self, db_conn):
        result = search.search_text(db_conn, 'on')
        if result['totals']['equipements'] == 0:
            pytest.skip('Aucun équipement trouvé pour "on"')
        eq = result['equipements'][0]
        for field in ('id', 'name', 'eqType_name', 'object_id', 'isEnable', 'isVisible'):
            assert field in eq, f'Champ manquant dans equipement : {field}'

    def test_champs_commande(self, db_conn):
        result = search.search_text(db_conn, 'on')
        if result['totals']['commandes'] == 0:
            pytest.skip('Aucune commande trouvée pour "on"')
        cmd = result['commandes'][0]
        for field in ('id', 'name', 'eqLogic_id', 'type', 'subType'):
            assert field in cmd, f'Champ manquant dans commande : {field}'

    def test_champs_scenario(self, db_conn):
        result = search.search_text(db_conn, 'on')
        if result['totals']['scenarios'] == 0:
            pytest.skip('Aucun scénario trouvé pour "on"')
        scen = result['scenarios'][0]
        for field in ('id', 'name', 'group', 'isActive', 'mode'):
            assert field in scen, f'Champ manquant dans scenario : {field}'

    def test_champs_expression(self, db_conn):
        result = search.search_text(db_conn, 'on')
        if result['totals']['expressions'] == 0:
            pytest.skip('Aucune expression trouvée pour "on"')
        expr = result['expressions'][0]
        for field in ('id', 'scenarioSubElement_id', 'type', 'expression'):
            assert field in expr, f'Champ manquant dans expression : {field}'

    def test_filtre_respecte_dans_equipements(self, db_conn):
        result = search.search_text(db_conn, 'on')
        for eq in result['equipements']:
            assert 'on' in eq['name'].lower(), f"Nom {eq['name']!r} ne contient pas 'on'"

    def test_filtre_respecte_dans_scenarios(self, db_conn):
        result = search.search_text(db_conn, 'on')
        for scen in result['scenarios']:
            assert 'on' in scen['name'].lower(), (
                f"Nom scénario {scen['name']!r} ne contient pas 'on'"
            )

    def test_limit_respecte(self, db_conn):
        result = search.search_text(db_conn, 'on', limit=3)
        assert result['totals']['equipements'] <= 3
        assert result['totals']['commandes'] <= 3
        assert result['totals']['scenarios'] <= 3
        assert result['totals']['expressions'] <= 3

    def test_term_specifique_filtre_correctement(self, db_conn):
        """Terme peu commun — vérifie que le filtre LIKE fonctionne."""
        result = search.search_text(db_conn, '__terme_tres_rare_xyz123__')
        assert result['totals']['equipements'] == 0
        assert result['totals']['commandes'] == 0
        assert result['totals']['scenarios'] == 0
        assert result['totals']['expressions'] == 0
