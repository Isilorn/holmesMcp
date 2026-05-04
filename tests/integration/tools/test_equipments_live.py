"""Tests d'intégration live — tools/equipments.py (Famille 2, 7 tools)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from tools import equipments

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# list_equipments
# ---------------------------------------------------------------------------


class TestListEquipmentsLive:
    def test_structure(self, db_conn):
        result = equipments.list_equipments(db_conn)
        assert 'equipements' in result
        assert 'total' in result
        assert 'offset' in result
        assert isinstance(result['equipements'], list)
        assert isinstance(result['_filtered_fields'], list)

    def test_retourne_des_equipements(self, db_conn):
        result = equipments.list_equipments(db_conn)
        assert result['total'] >= 1

    def test_filtre_is_enable(self, db_conn):
        result = equipments.list_equipments(db_conn, is_enable=True)
        for eq in result['equipements']:
            assert eq['isEnable'] == 1, f"Équipement désactivé dans résultat filtré : {eq['id']}"

    def test_pagination_offset(self, db_conn):
        page0 = equipments.list_equipments(db_conn, limit=5, offset=0)
        page1 = equipments.list_equipments(db_conn, limit=5, offset=5)
        if page0['total'] >= 5 and page1['total'] >= 1:
            ids_p0 = {e['id'] for e in page0['equipements']}
            ids_p1 = {e['id'] for e in page1['equipements']}
            assert ids_p0.isdisjoint(ids_p1), 'Chevauchement entre pages'

    def test_champs_equipement(self, db_conn):
        result = equipments.list_equipments(db_conn, limit=1)
        eq = result['equipements'][0]
        for field in ('id', 'name', 'eqType_name', 'isEnable', 'isVisible'):
            assert field in eq, f'Champ manquant : {field}'


# ---------------------------------------------------------------------------
# find_equipments_advanced
# ---------------------------------------------------------------------------


class TestFindEquipmentsAdvancedLive:
    def test_structure(self, db_conn):
        result = equipments.find_equipments_advanced(db_conn)
        assert 'equipements' in result
        assert 'total' in result
        assert isinstance(result['equipements'], list)

    def test_filtre_name_contains(self, db_conn):
        result = equipments.find_equipments_advanced(db_conn, name_contains='e')
        for eq in result['equipements']:
            assert 'e' in eq['name'].lower(), (
                f"Nom {eq['name']!r} ne contient pas 'e'"
            )

    def test_filtre_is_enable(self, db_conn):
        result = equipments.find_equipments_advanced(db_conn, is_enable=True)
        for eq in result['equipements']:
            assert eq['isEnable'] == 1


# ---------------------------------------------------------------------------
# get_equipment
# ---------------------------------------------------------------------------


class TestGetEquipmentLive:
    def test_structure(self, db_conn, first_equipment):
        result = equipments.get_equipment(db_conn, first_equipment)
        assert 'equipment' in result
        assert 'commandes' in result
        assert 'nb_commandes' in result
        assert isinstance(result['commandes'], list)
        assert isinstance(result['_filtered_fields'], list)

    def test_id_correspond(self, db_conn, first_equipment):
        result = equipments.get_equipment(db_conn, first_equipment)
        assert result['equipment']['id'] == first_equipment

    def test_nb_commandes_coherent(self, db_conn, first_equipment):
        result = equipments.get_equipment(db_conn, first_equipment)
        assert result['nb_commandes'] == len(result['commandes'])

    def test_equipement_inexistant(self, db_conn):
        result = equipments.get_equipment(db_conn, 999999)
        assert 'error' in result
        assert result['equipment_id'] == 999999


# ---------------------------------------------------------------------------
# find_equipment_by_name
# ---------------------------------------------------------------------------


class TestFindEquipmentByNameLive:
    def test_structure(self, db_conn):
        result = equipments.find_equipment_by_name(db_conn, 'e')
        assert 'equipements' in result
        assert 'total' in result
        assert 'query' in result
        assert result['query'] == 'e'

    def test_resultats_contiennent_fragment(self, db_conn):
        result = equipments.find_equipment_by_name(db_conn, 'e')
        for eq in result['equipements']:
            assert 'e' in eq['name'].lower(), (
                f"Nom {eq['name']!r} ne contient pas 'e'"
            )

    def test_nom_inexistant_retourne_vide(self, db_conn):
        result = equipments.find_equipment_by_name(db_conn, '__aucun_match_xyz_987__')
        assert result['total'] == 0


# ---------------------------------------------------------------------------
# list_commands
# ---------------------------------------------------------------------------


class TestListCommandsLive:
    def test_structure(self, db_conn, first_equipment):
        result = equipments.list_commands(db_conn, first_equipment)
        assert 'commandes' in result
        assert 'total' in result
        assert 'equipment_id' in result
        assert result['equipment_id'] == first_equipment
        assert isinstance(result['commandes'], list)

    def test_filtre_type_info(self, db_conn, first_equipment):
        result = equipments.list_commands(db_conn, first_equipment, cmd_type='info')
        for cmd in result['commandes']:
            assert cmd['type'] == 'info', f"Commande de type {cmd['type']!r} dans résultat info"

    def test_filtre_type_action(self, db_conn, first_equipment):
        result = equipments.list_commands(db_conn, first_equipment, cmd_type='action')
        for cmd in result['commandes']:
            assert cmd['type'] == 'action'

    def test_champs_commande(self, db_conn, first_equipment):
        result = equipments.list_commands(db_conn, first_equipment)
        if result['commandes']:
            cmd = result['commandes'][0]
            for field in ('id', 'name', 'eqLogic_id', 'type', 'subType'):
                assert field in cmd, f'Champ manquant : {field}'


# ---------------------------------------------------------------------------
# find_commands_advanced
# ---------------------------------------------------------------------------


class TestFindCommandsAdvancedLive:
    def test_structure(self, db_conn):
        result = equipments.find_commands_advanced(db_conn)
        assert 'commandes' in result
        assert 'total' in result
        assert isinstance(result['commandes'], list)

    def test_filtre_type(self, db_conn):
        result = equipments.find_commands_advanced(db_conn, cmd_type='info', limit=10)
        for cmd in result['commandes']:
            assert cmd['type'] == 'info'

    def test_filtre_is_historized(self, db_conn):
        result = equipments.find_commands_advanced(db_conn, is_historized=True, limit=10)
        for cmd in result['commandes']:
            assert int(cmd['isHistorized']) == 1


# ---------------------------------------------------------------------------
# get_command_history
# ---------------------------------------------------------------------------


class TestGetCommandHistoryLive:
    def test_structure(self, db_conn, first_historized_cmd):
        result = equipments.get_command_history(db_conn, first_historized_cmd)
        assert 'cmd_id' in result
        assert 'history_recent' in result
        assert 'history_archived' in result
        assert 'total_recent' in result
        assert 'total_archived' in result
        assert result['cmd_id'] == first_historized_cmd

    def test_listes_sont_des_listes(self, db_conn, first_historized_cmd):
        result = equipments.get_command_history(db_conn, first_historized_cmd)
        assert isinstance(result['history_recent'], list)
        assert isinstance(result['history_archived'], list)

    def test_totaux_coherents(self, db_conn, first_historized_cmd):
        result = equipments.get_command_history(db_conn, first_historized_cmd)
        assert result['total_recent'] == len(result['history_recent'])
        assert result['total_archived'] == len(result['history_archived'])

    def test_cmd_inexistante_retourne_vide(self, db_conn):
        result = equipments.get_command_history(db_conn, 999999)
        assert result['total_recent'] == 0
        assert result['total_archived'] == 0
