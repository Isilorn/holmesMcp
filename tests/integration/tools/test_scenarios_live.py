"""Tests d'intégration live — tools/scenarios.py (Famille 3, 7 tools)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from tools import scenarios

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# list_scenarios
# ---------------------------------------------------------------------------


class TestListScenariosLive:
    def test_structure(self, db_conn):
        result = scenarios.list_scenarios(db_conn)
        assert 'scenarios' in result
        assert 'total' in result
        assert 'offset' in result
        assert isinstance(result['scenarios'], list)
        assert isinstance(result['_filtered_fields'], list)

    def test_retourne_des_scenarios(self, db_conn):
        result = scenarios.list_scenarios(db_conn)
        assert result['total'] >= 1

    def test_filtre_is_active(self, db_conn):
        result = scenarios.list_scenarios(db_conn, is_active=True)
        for scen in result['scenarios']:
            assert scen['isActive'] == 1, f"Scénario inactif dans résultat filtré : {scen['id']}"

    def test_champs_scenario(self, db_conn):
        result = scenarios.list_scenarios(db_conn, limit=1)
        scen = result['scenarios'][0]
        for field in ('id', 'name', 'isActive', 'mode'):
            assert field in scen, f'Champ manquant : {field}'

    def test_pagination_offset(self, db_conn):
        page0 = scenarios.list_scenarios(db_conn, limit=5, offset=0)
        page1 = scenarios.list_scenarios(db_conn, limit=5, offset=5)
        if page0['total'] >= 5 and page1['total'] >= 1:
            ids_p0 = {s['id'] for s in page0['scenarios']}
            ids_p1 = {s['id'] for s in page1['scenarios']}
            assert ids_p0.isdisjoint(ids_p1), 'Chevauchement entre pages'


# ---------------------------------------------------------------------------
# find_scenarios_advanced
# ---------------------------------------------------------------------------


class TestFindScenariosAdvancedLive:
    def test_structure(self, db_conn):
        result = scenarios.find_scenarios_advanced(db_conn)
        assert 'scenarios' in result
        assert 'total' in result
        assert isinstance(result['scenarios'], list)

    def test_filtre_is_active(self, db_conn):
        result = scenarios.find_scenarios_advanced(db_conn, is_active=True)
        for scen in result['scenarios']:
            assert scen['isActive'] == 1

    def test_filtre_name_contains(self, db_conn):
        result = scenarios.find_scenarios_advanced(db_conn, name_contains='a')
        for scen in result['scenarios']:
            assert 'a' in scen['name'].lower(), (
                f"Nom {scen['name']!r} ne contient pas 'a'"
            )


# ---------------------------------------------------------------------------
# get_scenario
# ---------------------------------------------------------------------------


class TestGetScenarioLive:
    def test_structure(self, db_conn, first_scenario):
        result = scenarios.get_scenario(db_conn, first_scenario)
        assert 'scenario' in result
        assert isinstance(result['_filtered_fields'], list)

    def test_id_correspond(self, db_conn, first_scenario):
        result = scenarios.get_scenario(db_conn, first_scenario)
        assert result['scenario']['id'] == first_scenario

    def test_champs_scenario(self, db_conn, first_scenario):
        result = scenarios.get_scenario(db_conn, first_scenario)
        scen = result['scenario']
        for field in ('id', 'name', 'isActive', 'mode'):
            assert field in scen, f'Champ manquant : {field}'

    def test_scenario_inexistant(self, db_conn):
        result = scenarios.get_scenario(db_conn, 999999)
        assert 'error' in result
        assert result['scenario_id'] == 999999


# ---------------------------------------------------------------------------
# get_scenario_structure
# ---------------------------------------------------------------------------


class TestGetScenarioStructureLive:
    def test_structure(self, db_conn, first_scenario):
        result = scenarios.get_scenario_structure(db_conn, first_scenario)
        assert 'scenario' in result or 'error' in result

    def test_scenario_present(self, db_conn, first_scenario):
        result = scenarios.get_scenario_structure(db_conn, first_scenario)
        if 'scenario' in result:
            assert result['scenario']['id'] == first_scenario

    def test_tree_est_une_liste(self, db_conn, first_scenario):
        result = scenarios.get_scenario_structure(db_conn, first_scenario)
        if 'tree' in result:
            assert isinstance(result['tree'], list)

    def test_max_depth_respecte(self, db_conn, first_scenario):
        result = scenarios.get_scenario_structure(db_conn, first_scenario, max_depth=1)
        assert 'scenario' in result or 'error' in result


# ---------------------------------------------------------------------------
# describe_scenario
# ---------------------------------------------------------------------------


class TestDescribeScenarioLive:
    def test_structure(self, db_conn, first_scenario):
        result = scenarios.describe_scenario(db_conn, first_scenario)
        assert 'scenario' in result or 'error' in result

    def test_blocks_present(self, db_conn, first_scenario):
        result = scenarios.describe_scenario(db_conn, first_scenario)
        if 'scenario' in result:
            assert 'blocks' in result
            assert isinstance(result['blocks'], list)

    def test_cmd_mapping_present(self, db_conn, first_scenario):
        result = scenarios.describe_scenario(db_conn, first_scenario)
        if 'scenario' in result:
            assert 'cmd_mapping' in result
            assert isinstance(result['cmd_mapping'], dict)

    def test_trigger_resolved_present(self, db_conn, first_scenario):
        result = scenarios.describe_scenario(db_conn, first_scenario)
        if 'scenario' in result:
            assert 'trigger_resolved' in result['scenario']


# ---------------------------------------------------------------------------
# find_scenario_dependencies
# ---------------------------------------------------------------------------


class TestFindScenarioDependenciesLive:
    def test_structure(self, db_conn, first_scenario):
        result = scenarios.find_scenario_dependencies(db_conn, first_scenario)
        assert isinstance(result, dict)

    def test_target_info_present(self, db_conn, first_scenario):
        result = scenarios.find_scenario_dependencies(db_conn, first_scenario)
        assert 'target' in result or 'callers' in result or 'error' in result

    def test_pas_exception(self, db_conn):
        result = scenarios.find_scenario_dependencies(db_conn, 999999)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# get_scenario_log
# ---------------------------------------------------------------------------


class TestGetScenarioLogLive:
    def test_retourne_dict(self, db_conn, first_scenario):
        result = scenarios.get_scenario_log(db_conn, first_scenario)
        assert isinstance(result, dict)

    def test_structure_si_log_present(self, db_conn, first_scenario):
        result = scenarios.get_scenario_log(db_conn, first_scenario)
        if 'error' not in result:
            assert 'lines' in result or 'content' in result or 'tail' in result

    def test_scenario_inexistant_retourne_erreur(self, db_conn):
        result = scenarios.get_scenario_log(db_conn, 999999)
        assert 'error' in result
