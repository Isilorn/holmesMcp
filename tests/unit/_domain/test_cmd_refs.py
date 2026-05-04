"""Tests unitaires _domain/cmd_refs.py — couverture 100% obligatoire.

Structure :
  - _fetch_names : requête batch SQL → mapping id → label
  - resolve : texte sans ID / IDs tous résolus / partiellement résolus / tous non résolus
  - resolve : IDs dupliqués dans le texte (déduplication)
  - resolve : objet NULL (COALESCE '' dans SQL)
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from _domain.cmd_refs import _fetch_names, resolve

# ── Fixture commune ───────────────────────────────────────────────────────────


@pytest.fixture
def conn():
    return MagicMock()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_row(cmd_id: int, objet: str, equipement: str, commande: str) -> dict:
    return {'id': cmd_id, 'objet': objet, 'equipement': equipement, 'commande': commande}


# ── _fetch_names ──────────────────────────────────────────────────────────────


def test_fetch_names_single_row(conn):
    row = _make_row(100, 'Salon', 'Lumière', 'Etat')
    with patch('_domain.cmd_refs.db.query', return_value=[row]) as mock_q:
        result = _fetch_names([100], conn)
    assert result == {100: '[Salon][Lumière][Etat]'}
    mock_q.assert_called_once()


def test_fetch_names_multiple_rows(conn):
    rows = [
        _make_row(10, 'Cuisine', 'Thermostat', 'Température'),
        _make_row(20, 'Chambre', 'Volet', 'Position'),
    ]
    with patch('_domain.cmd_refs.db.query', return_value=rows):
        result = _fetch_names([10, 20], conn)
    assert result == {
        10: '[Cuisine][Thermostat][Température]',
        20: '[Chambre][Volet][Position]',
    }


def test_fetch_names_objet_null_coalesced(conn):
    # COALESCE retourne '' si objet NULL
    row = _make_row(5, '', 'Présence', 'BLE détecté')
    with patch('_domain.cmd_refs.db.query', return_value=[row]):
        result = _fetch_names([5], conn)
    assert result == {5: '[][Présence][BLE détecté]'}


def test_fetch_names_objet_none_python(conn):
    # La valeur None côté Python (pas COALESCE) doit aussi produire ''
    row = {'id': 7, 'objet': None, 'equipement': 'Capteur', 'commande': 'Valeur'}
    with patch('_domain.cmd_refs.db.query', return_value=[row]):
        result = _fetch_names([7], conn)
    assert result == {7: '[][Capteur][Valeur]'}


def test_fetch_names_equipement_none_python(conn):
    row = {'id': 8, 'objet': 'Maison', 'equipement': None, 'commande': 'Cmd'}
    with patch('_domain.cmd_refs.db.query', return_value=[row]):
        result = _fetch_names([8], conn)
    assert result == {8: '[Maison][][Cmd]'}


def test_fetch_names_commande_none_python(conn):
    row = {'id': 9, 'objet': 'Maison', 'equipement': 'Eq', 'commande': None}
    with patch('_domain.cmd_refs.db.query', return_value=[row]):
        result = _fetch_names([9], conn)
    assert result == {9: '[Maison][Eq][]'}


def test_fetch_names_no_match_returns_empty(conn):
    with patch('_domain.cmd_refs.db.query', return_value=[]):
        result = _fetch_names([999], conn)
    assert result == {}


def test_fetch_names_sql_has_correct_placeholder_count(conn):
    """Le SQL généré doit avoir autant de %s que d'IDs."""
    captured = {}

    def _spy(conn_, sql, params):
        captured['sql'] = sql
        captured['params'] = params
        return []

    with patch('_domain.cmd_refs.db.query', side_effect=_spy):
        _fetch_names([1, 2, 3], conn)

    assert captured['params'] == (1, 2, 3)
    assert captured['sql'].count('%s') == 3


def test_fetch_names_id_as_string_in_row(conn):
    # PyMySQL peut retourner les IDs en string selon le curseur
    row = {'id': '42', 'objet': 'Bureau', 'equipement': 'PC', 'commande': 'CPU'}
    with patch('_domain.cmd_refs.db.query', return_value=[row]):
        result = _fetch_names([42], conn)
    assert result == {42: '[Bureau][PC][CPU]'}


# ── resolve — texte sans aucun #ID# ──────────────────────────────────────────


def test_resolve_empty_text(conn):
    result = resolve('', conn)
    assert result == {'resolved': '', 'mapping': {}, 'unresolved': []}


def test_resolve_text_without_ids(conn):
    text = 'Aucun identifiant ici.'
    result = resolve(text, conn)
    assert result == {'resolved': text, 'mapping': {}, 'unresolved': []}


def test_resolve_no_ids_does_not_call_db(conn):
    with patch('_domain.cmd_refs.db.query') as mock_q:
        resolve('Texte sans IDs', conn)
    mock_q.assert_not_called()


# ── resolve — IDs tous résolus ────────────────────────────────────────────────


def test_resolve_single_id_found(conn):
    row = _make_row(15663, 'Maison', 'Présence Géraud', 'BLE présent')
    with patch('_domain.cmd_refs.db.query', return_value=[row]):
        result = resolve('Si #15663# == 1', conn)
    assert result['resolved'] == 'Si #[Maison][Présence Géraud][BLE présent]# == 1'
    assert result['mapping'] == {'15663': '[Maison][Présence Géraud][BLE présent]'}
    assert result['unresolved'] == []


def test_resolve_two_ids_found(conn):
    rows = [
        _make_row(10, 'Salon', 'Lumière', 'Etat'),
        _make_row(20, 'Cuisine', 'Chauffage', 'Consigne'),
    ]
    with patch('_domain.cmd_refs.db.query', return_value=rows):
        result = resolve('Si #10# == 1 alors #20# = 21', conn)
    assert '#[Salon][Lumière][Etat]#' in result['resolved']
    assert '#[Cuisine][Chauffage][Consigne]#' in result['resolved']
    assert result['unresolved'] == []
    assert len(result['mapping']) == 2


# ── resolve — IDs non résolus ─────────────────────────────────────────────────


def test_resolve_single_id_not_found(conn):
    with patch('_domain.cmd_refs.db.query', return_value=[]):
        result = resolve('#99999#', conn)
    assert result['resolved'] == '#ID_NON_RÉSOLU:99999#'
    assert result['mapping'] == {}
    assert result['unresolved'] == [99999]


def test_resolve_unresolved_sorted(conn):
    with patch('_domain.cmd_refs.db.query', return_value=[]):
        result = resolve('#30# et #10# et #20#', conn)
    assert result['unresolved'] == [10, 20, 30]


# ── resolve — IDs partiellement résolus ──────────────────────────────────────


def test_resolve_partial_resolution(conn):
    rows = [_make_row(100, 'Jardin', 'Arrosage', 'Etat')]
    with patch('_domain.cmd_refs.db.query', return_value=rows):
        result = resolve('#100# active #999#', conn)
    assert '#[Jardin][Arrosage][Etat]#' in result['resolved']
    assert '#ID_NON_RÉSOLU:999#' in result['resolved']
    assert '100' in result['mapping']
    assert result['unresolved'] == [999]


# ── resolve — IDs dupliqués dans le texte ────────────────────────────────────


def test_resolve_duplicate_ids_single_db_call(conn):
    """Un ID apparaissant 2 fois → 1 seule ligne en DB, les 2 occurrences remplacées."""
    row = _make_row(42, 'Entrée', 'Porte', 'Ouverture')
    with patch('_domain.cmd_refs.db.query', return_value=[row]) as mock_q:
        result = resolve('#42# et encore #42#', conn)
    mock_q.assert_called_once()
    expected = '#[Entrée][Porte][Ouverture]# et encore #[Entrée][Porte][Ouverture]#'
    assert result['resolved'] == expected
    assert result['mapping'] == {'42': '[Entrée][Porte][Ouverture]'}


# ── resolve — mapping clés en str ────────────────────────────────────────────


def test_resolve_mapping_keys_are_strings(conn):
    row = _make_row(7, 'Couloir', 'Détecteur', 'Mouvement')
    with patch('_domain.cmd_refs.db.query', return_value=[row]):
        result = resolve('#7#', conn)
    assert '7' in result['mapping']
    assert isinstance(list(result['mapping'].keys())[0], str)


# ── resolve — texte avec guillemets et caractères spéciaux ───────────────────


def test_resolve_text_with_special_chars(conn):
    row = _make_row(1, 'Maison', 'Eq', 'Cmd')
    with patch('_domain.cmd_refs.db.query', return_value=[row]):
        result = resolve('Test #1# avec "guillemets" & accents éàü', conn)
    assert '#[Maison][Eq][Cmd]#' in result['resolved']
    assert 'guillemets' in result['resolved']
