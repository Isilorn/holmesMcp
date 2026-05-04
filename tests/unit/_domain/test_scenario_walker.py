"""Tests unitaires _domain/scenario_walker.py — couverture 100% obligatoire.

Structure :
  - _fetch_scenario : trouvé / introuvable
  - _fetch_elements : liste vide / non-vide
  - _group_by_element : regroupement rows SQL
  - _child_element_ids : détection type='element'
  - _extract_scenario_call_id : tous les cas (type, action, options, cycle)
  - _walk : profondeur, ids déjà visités, troncature, follow_scenario_calls,
             cycle, visited_scenarios=None, enfants présents/absents
  - walk : scénario introuvable, scenarioElement valide/invalide/None,
            first call (visited_scenarios=None), recursive call (non-None)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from _domain.scenario_walker import (
    DEFAULT_MAX_DEPTH,
    MAX_SUB_ELEMENTS,
    _child_element_ids,
    _extract_scenario_call_id,
    _fetch_elements,
    _fetch_scenario,
    _group_by_element,
    _walk,
    walk,
)


# ── Fixture commune ───────────────────────────────────────────────────────────


@pytest.fixture
def conn():
    return MagicMock()


def _make_sql_row(
    el_id: int = 8,
    sub_id: int = 12,
    ss_type: str = 'if',
    ss_subtype: str = 'condition',
    expr_id: int | None = 5,
    expr_order: int | None = 1,
    expr_type: str = 'condition',
    expression: str = '#123# == 1',
    options: str = '{}',
) -> dict:
    return {
        'element_id': el_id, 'sub_id': sub_id,
        'ss_type': ss_type, 'ss_subtype': ss_subtype,
        'expr_id': expr_id, 'expr_order': expr_order,
        'expr_type': expr_type, 'expression': expression,
        'options': options,
    }


def _make_scenario_row(
    scenario_id: int = 70,
    name: str = 'Scénario test',
    isActive: int = 1,
    mode: str = 'schedule',
    trigger: str | None = None,
    scenario_element: str = '[]',
    description: str | None = None,
    timeout: int | None = None,
) -> dict:
    return {
        'id': scenario_id, 'name': name, 'isActive': isActive,
        'mode': mode, 'trigger': trigger,
        'scenarioElement': scenario_element,
        'description': description, 'timeout': timeout,
    }


# ── _fetch_scenario ───────────────────────────────────────────────────────────


def test_fetch_scenario_not_found(conn):
    with patch('_domain.scenario_walker.db.query', return_value=[]):
        assert _fetch_scenario(999, conn) is None


def test_fetch_scenario_found(conn):
    row = _make_scenario_row(70)
    with patch('_domain.scenario_walker.db.query', return_value=[row]):
        result = _fetch_scenario(70, conn)
    assert result == row


# ── _fetch_elements ───────────────────────────────────────────────────────────


def test_fetch_elements_empty_list_no_query(conn):
    with patch('_domain.scenario_walker.db.query') as mock_q:
        result = _fetch_elements([], conn)
    assert result == []
    mock_q.assert_not_called()


def test_fetch_elements_single_id(conn):
    rows = [_make_sql_row()]
    with patch('_domain.scenario_walker.db.query', return_value=rows):
        result = _fetch_elements([8], conn)
    assert result == rows


def test_fetch_elements_multiple_ids(conn):
    rows = [_make_sql_row(8), _make_sql_row(9, sub_id=20)]
    with patch('_domain.scenario_walker.db.query', return_value=rows):
        result = _fetch_elements([8, 9], conn)
    assert result == rows


# ── _group_by_element ─────────────────────────────────────────────────────────


def test_group_by_element_empty():
    assert _group_by_element([]) == {}


def test_group_by_element_single_row():
    rows = [_make_sql_row(el_id=8, sub_id=12)]
    result = _group_by_element(rows)
    assert 8 in result
    assert len(result[8]) == 1
    assert result[8][0]['sub_id'] == 12
    assert len(result[8][0]['expressions']) == 1


def test_group_by_element_multiple_expressions_same_sub():
    rows = [
        _make_sql_row(el_id=8, sub_id=12, expr_id=5, expr_order=1, expression='#123# == 1'),
        _make_sql_row(el_id=8, sub_id=12, expr_id=6, expr_order=2, expression='#124# == 0'),
    ]
    result = _group_by_element(rows)
    assert len(result[8][0]['expressions']) == 2


def test_group_by_element_multiple_subs():
    rows = [
        _make_sql_row(el_id=8, sub_id=12, ss_type='if', ss_subtype='condition'),
        _make_sql_row(el_id=8, sub_id=13, ss_type='if', ss_subtype='then', expr_type='action'),
    ]
    result = _group_by_element(rows)
    assert len(result[8]) == 2


def test_group_by_element_none_expr_id_and_order():
    rows = [_make_sql_row(expr_id=None, expr_order=None)]
    result = _group_by_element(rows)
    expr = result[8][0]['expressions'][0]
    assert expr['expr_id'] is None
    assert expr['order'] == 0


def test_group_by_element_sorts_subs_by_sub_id():
    rows = [
        _make_sql_row(el_id=8, sub_id=20),
        _make_sql_row(el_id=8, sub_id=10),
    ]
    result = _group_by_element(rows)
    assert result[8][0]['sub_id'] == 10
    assert result[8][1]['sub_id'] == 20


# ── _child_element_ids ────────────────────────────────────────────────────────


def test_child_element_ids_empty():
    assert _child_element_ids([]) == []


def test_child_element_ids_no_element_type():
    exprs = [{'type': 'condition', 'expression': '#123# == 1'}]
    assert _child_element_ids(exprs) == []


def test_child_element_ids_with_valid_element():
    exprs = [{'type': 'element', 'expression': '9'}]
    assert _child_element_ids(exprs) == [9]


def test_child_element_ids_invalid_expression_skipped():
    exprs = [{'type': 'element', 'expression': 'not_an_int'}]
    assert _child_element_ids(exprs) == []


def test_child_element_ids_none_expression_skipped():
    exprs = [{'type': 'element', 'expression': None}]
    assert _child_element_ids(exprs) == []


def test_child_element_ids_mixed():
    exprs = [
        {'type': 'condition', 'expression': '#123#'},
        {'type': 'element', 'expression': '9'},
        {'type': 'element', 'expression': '11'},
    ]
    assert _child_element_ids(exprs) == [9, 11]


# ── _extract_scenario_call_id ─────────────────────────────────────────────────


def test_extract_not_action_type():
    assert _extract_scenario_call_id({'type': 'condition', 'expression': 'scenario'}) is None


def test_extract_not_scenario_expression():
    assert _extract_scenario_call_id({'type': 'action', 'expression': 'slider'}) is None


def test_extract_action_stop_returns_none():
    opts = json.dumps({'action': 'stop', 'scenario_id': '5'})
    assert _extract_scenario_call_id({'type': 'action', 'expression': 'scenario', 'options': opts}) is None


def test_extract_action_activate_returns_none():
    opts = json.dumps({'action': 'activate', 'scenario_id': '5'})
    assert _extract_scenario_call_id({'type': 'action', 'expression': 'scenario', 'options': opts}) is None


def test_extract_action_start_returns_id():
    opts = json.dumps({'action': 'start', 'scenario_id': '5'})
    assert _extract_scenario_call_id({'type': 'action', 'expression': 'scenario', 'options': opts}) == 5


def test_extract_action_none_returns_id():
    opts = json.dumps({'action': None, 'scenario_id': '5'})
    assert _extract_scenario_call_id({'type': 'action', 'expression': 'scenario', 'options': opts}) == 5


def test_extract_action_empty_string_returns_id():
    opts = json.dumps({'action': '', 'scenario_id': '5'})
    assert _extract_scenario_call_id({'type': 'action', 'expression': 'scenario', 'options': opts}) == 5


def test_extract_scenario_id_missing_returns_none():
    opts = json.dumps({'action': 'start'})
    assert _extract_scenario_call_id({'type': 'action', 'expression': 'scenario', 'options': opts}) is None


def test_extract_invalid_json_returns_none():
    expr = {'type': 'action', 'expression': 'scenario', 'options': 'not-json'}
    assert _extract_scenario_call_id(expr) is None


def test_extract_no_options_key_returns_none():
    expr = {'type': 'action', 'expression': 'scenario'}
    assert _extract_scenario_call_id(expr) is None


def test_extract_options_none_returns_none():
    expr = {'type': 'action', 'expression': 'scenario', 'options': None}
    # options None → json.loads('{}') → scenario_id absent → None
    assert _extract_scenario_call_id(expr) is None


# ── _walk ─────────────────────────────────────────────────────────────────────


def test_walk_internal_depth_exceeded(conn):
    """depth > max_depth → retourne [] sans appeler db."""
    with patch('_domain.scenario_walker.db.query') as mock_q:
        result = _walk([8], conn, max_depth=0, visited=set(), depth=1,
                       warnings=[], truncated_flag=[False])
    assert result == []
    mock_q.assert_not_called()


def test_walk_internal_all_visited(conn):
    """Tous les IDs déjà visités → retourne []."""
    with patch('_domain.scenario_walker.db.query') as mock_q:
        result = _walk([8], conn, max_depth=3, visited={8}, depth=0,
                       warnings=[], truncated_flag=[False])
    assert result == []
    mock_q.assert_not_called()


def test_walk_internal_simple_node(conn):
    """Un élément simple, sans enfants."""
    sql_row = _make_sql_row(el_id=8, sub_id=12)
    with patch('_domain.scenario_walker.db.query', return_value=[sql_row]):
        nodes = _walk([8], conn, max_depth=3, visited=set(), depth=0,
                      warnings=[], truncated_flag=[False])
    assert len(nodes) == 1
    assert nodes[0]['element_id'] == 8
    assert nodes[0]['depth'] == 0
    assert 'children' not in nodes[0]


def test_walk_internal_with_children(conn):
    """Élément avec enfant element_id=9 (via expression type='element')."""
    row_el8 = _make_sql_row(el_id=8, sub_id=12, expr_type='element', expression='9')
    row_el9 = _make_sql_row(el_id=9, sub_id=20, expr_type='condition', expression='#123#')
    with patch('_domain.scenario_walker.db.query', side_effect=[
        [row_el8],  # _fetch_elements([8])
        [row_el9],  # _fetch_elements([9])
    ]):
        nodes = _walk([8], conn, max_depth=3, visited=set(), depth=0,
                      warnings=[], truncated_flag=[False])
    assert len(nodes) == 1
    assert 'children' in nodes[0]
    assert nodes[0]['children'][0]['element_id'] == 9


def test_walk_internal_children_empty_when_max_depth(conn):
    """Enfant hors max_depth → children retourne [] → clé 'children' absente."""
    row_el8 = _make_sql_row(el_id=8, sub_id=12, expr_type='element', expression='9')
    with patch('_domain.scenario_walker.db.query', return_value=[row_el8]):
        nodes = _walk([8], conn, max_depth=0, visited=set(), depth=0,
                      warnings=[], truncated_flag=[False])
    assert len(nodes) == 1
    assert 'children' not in nodes[0]


def test_walk_internal_truncation(conn):
    """Plus de MAX_SUB_ELEMENTS sous-éléments → troncature + avertissement."""
    # Construire 101 rows pour le même element_id=8, sub_ids distincts
    rows = [
        _make_sql_row(el_id=8, sub_id=i, expr_id=i)
        for i in range(1, MAX_SUB_ELEMENTS + 2)  # 101 rows → 101 sub_elements
    ]
    warnings: list[str] = []
    truncated_flag = [False]
    with patch('_domain.scenario_walker.db.query', return_value=rows):
        nodes = _walk([8], conn, max_depth=3, visited=set(), depth=0,
                      warnings=warnings, truncated_flag=truncated_flag)
    assert truncated_flag[0] is True
    assert len(warnings) == 1
    assert 'tronqué' in warnings[0]
    assert len(nodes[0]['sub_elements']) == MAX_SUB_ELEMENTS


def test_walk_internal_no_follow_scenario_calls(conn):
    """follow_scenario_calls=0 → pas de suivi d'appels de scénarios."""
    opts = json.dumps({'action': 'start', 'scenario_id': '99'})
    row = _make_sql_row(el_id=8, sub_id=12, expr_type='action',
                        expression='scenario', options=opts)
    with patch('_domain.scenario_walker.db.query', return_value=[row]):
        nodes = _walk([8], conn, max_depth=3, visited=set(), depth=0,
                      warnings=[], truncated_flag=[False],
                      follow_scenario_calls=0)
    expr = nodes[0]['sub_elements'][0]['expressions'][0]
    assert 'called_scenario_tree' not in expr


def test_walk_internal_follow_scenario_calls_cycle(conn):
    """Cycle inter-scénarios → avertissement dans called_scenario_tree."""
    opts = json.dumps({'action': 'start', 'scenario_id': '70'})
    row = _make_sql_row(el_id=8, sub_id=12, expr_type='action',
                        expression='scenario', options=opts)
    visited_scenarios = {70}  # scénario 70 déjà visité
    with patch('_domain.scenario_walker.db.query', return_value=[row]):
        nodes = _walk([8], conn, max_depth=3, visited=set(), depth=0,
                      warnings=[], truncated_flag=[False],
                      follow_scenario_calls=1,
                      visited_scenarios=visited_scenarios)
    expr = nodes[0]['sub_elements'][0]['expressions'][0]
    assert 'called_scenario_tree' in expr
    assert 'cycle ignoré' in expr['called_scenario_tree']['warning']


def test_walk_internal_follow_scenario_calls_success(conn):
    """Suivi d'un appel de scénario non cyclique."""
    opts = json.dumps({'action': 'start', 'scenario_id': '99'})
    row_main = _make_sql_row(el_id=8, sub_id=12, expr_type='action',
                              expression='scenario', options=opts)
    scen99_row = _make_scenario_row(scenario_id=99, name='S99', scenario_element='[]')
    with patch('_domain.scenario_walker.db.query', side_effect=[
        [row_main],     # _fetch_elements([8])
        [scen99_row],   # _fetch_scenario(99) via walk()
        # _fetch_elements([]) → not called (early return)
    ]):
        nodes = _walk([8], conn, max_depth=3, visited=set(), depth=0,
                      warnings=[], truncated_flag=[False],
                      follow_scenario_calls=1,
                      visited_scenarios={70})
    expr = nodes[0]['sub_elements'][0]['expressions'][0]
    assert 'called_scenario_tree' in expr
    assert expr['called_scenario_tree']['scenario']['id'] == 99


def test_walk_internal_visited_scenarios_none_initialized(conn):
    """visited_scenarios=None → initialisé à set() quand follow_scenario_calls > 0."""
    opts = json.dumps({'action': 'start', 'scenario_id': '99'})
    row = _make_sql_row(el_id=8, sub_id=12, expr_type='action',
                        expression='scenario', options=opts)
    scen99_row = _make_scenario_row(scenario_id=99, name='S99', scenario_element='[]')
    with patch('_domain.scenario_walker.db.query', side_effect=[
        [row],
        [scen99_row],
    ]):
        # visited_scenarios=None → _walk l'initialise à set() en interne
        nodes = _walk([8], conn, max_depth=3, visited=set(), depth=0,
                      warnings=[], truncated_flag=[False],
                      follow_scenario_calls=1,
                      visited_scenarios=None)
    expr = nodes[0]['sub_elements'][0]['expressions'][0]
    assert 'called_scenario_tree' in expr
    assert expr['called_scenario_tree']['scenario']['id'] == 99


def test_walk_internal_non_scenario_expr_skipped_in_follow(conn):
    """Expression non-scénario ignorée dans le suivi inter-scénarios."""
    row = _make_sql_row(el_id=8, sub_id=12, expr_type='condition',
                        expression='#123# == 1', options='{}')
    with patch('_domain.scenario_walker.db.query', return_value=[row]):
        nodes = _walk([8], conn, max_depth=3, visited=set(), depth=0,
                      warnings=[], truncated_flag=[False],
                      follow_scenario_calls=1,
                      visited_scenarios=set())
    expr = nodes[0]['sub_elements'][0]['expressions'][0]
    assert 'called_scenario_tree' not in expr


# ── walk (API publique) ───────────────────────────────────────────────────────


def test_walk_scenario_not_found(conn):
    with patch('_domain.scenario_walker.db.query', return_value=[]):
        result = walk(999, conn)
    assert 'error' in result
    assert result['scenario'] is None
    assert result['tree'] == []
    assert result['truncated'] is False


def test_walk_scenario_empty_elements(conn):
    scen = _make_scenario_row(70, scenario_element='[]')
    with patch('_domain.scenario_walker.db.query', return_value=[scen]):
        result = walk(70, conn)
    assert result['scenario']['id'] == 70
    assert result['tree'] == []
    assert result['truncated'] is False
    assert result['warnings'] == []


def test_walk_scenario_none_element(conn):
    """scenarioElement=None → traité comme '[]'."""
    scen = _make_scenario_row(70, scenario_element=None)
    with patch('_domain.scenario_walker.db.query', return_value=[scen]):
        result = walk(70, conn)
    assert result['tree'] == []


def test_walk_scenario_invalid_element_json(conn):
    """scenarioElement invalide → tree vide, pas d'erreur."""
    scen = _make_scenario_row(70, scenario_element='not-json')
    with patch('_domain.scenario_walker.db.query', return_value=[scen]):
        result = walk(70, conn)
    assert result['tree'] == []


def test_walk_scenario_with_tree(conn):
    """Scénario avec un élément et une expression."""
    scen = _make_scenario_row(70, scenario_element='[8]')
    sql_row = _make_sql_row(el_id=8, sub_id=12)
    with patch('_domain.scenario_walker.db.query', side_effect=[[scen], [sql_row]]):
        result = walk(70, conn)
    assert len(result['tree']) == 1
    assert result['tree'][0]['element_id'] == 8


def test_walk_default_max_depth(conn):
    assert DEFAULT_MAX_DEPTH == 3


def test_walk_visited_scenarios_first_call(conn):
    """Premier appel : _visited_scenarios initialisé à {scenario_id}."""
    scen = _make_scenario_row(70, scenario_element='[]')
    with patch('_domain.scenario_walker.db.query', return_value=[scen]):
        result = walk(70, conn)
    assert result['scenario']['id'] == 70


def test_walk_visited_scenarios_recursive_call(conn):
    """Appel récursif : _visited_scenarios passé depuis l'appelant."""
    scen = _make_scenario_row(99, scenario_element='[]')
    visited = {70}
    with patch('_domain.scenario_walker.db.query', return_value=[scen]):
        result = walk(99, conn, _visited_scenarios=visited)
    assert result['scenario']['id'] == 99
    assert 99 in visited  # ajouté par walk()


def test_walk_returns_truncated_flag(conn):
    """truncated=True quand _walk tronque un élément."""
    scen = _make_scenario_row(70, scenario_element='[8]')
    rows = [
        _make_sql_row(el_id=8, sub_id=i, expr_id=i)
        for i in range(1, MAX_SUB_ELEMENTS + 2)
    ]
    with patch('_domain.scenario_walker.db.query', side_effect=[[scen], rows]):
        result = walk(70, conn)
    assert result['truncated'] is True
    assert len(result['warnings']) > 0


def test_walk_scenario_fields_exposed(conn):
    """Vérifie que tous les champs attendus du scénario sont présents."""
    scen = _make_scenario_row(
        scenario_id=70, name='Test', isActive=1, mode='schedule',
        trigger='#cmd123#', scenario_element='[]', description='Ma desc',
    )
    with patch('_domain.scenario_walker.db.query', return_value=[scen]):
        result = walk(70, conn)
    s = result['scenario']
    assert s['id'] == 70
    assert s['name'] == 'Test'
    assert s['isActive'] == 1
    assert s['mode'] == 'schedule'
    assert s['trigger'] == '#cmd123#'
    assert s['description'] == 'Ma desc'
