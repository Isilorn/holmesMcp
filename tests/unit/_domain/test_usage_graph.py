"""Tests unitaires _domain/usage_graph.py — couverture 100% obligatoire.

Structure :
  - _scenario_ref : conversion row → dict
  - _classify_expr_rows : condition / action / déduplication
  - _refs_for_cmd_id : triggers, conditions, actions, datastore, code fp
  - _resolve_cmd : cmd trouvée / introuvable
  - _resolve_eqlogic : eqLogic trouvée / introuvable / 0 cmds / cmds avec dédup
  - _resolve_scenario : scénario trouvé / introuvable / avec callers
  - resolve : dispatch par target_type + type inconnu
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from _domain.usage_graph import (
    _classify_expr_rows,
    _refs_for_cmd_id,
    _resolve_cmd,
    _resolve_eqlogic,
    _resolve_scenario,
    _scenario_ref,
    resolve,
)


# ── Fixture commune ───────────────────────────────────────────────────────────


@pytest.fixture
def conn():
    return MagicMock()


# ── _scenario_ref ─────────────────────────────────────────────────────────────


def test_scenario_ref_converts_types():
    row = {'scenario_id': '5', 'scenario_name': 'Test scénario'}
    assert _scenario_ref(row) == {'id': 5, 'name': 'Test scénario'}


def test_scenario_ref_int_id():
    row = {'scenario_id': 42, 'scenario_name': 'S42'}
    assert _scenario_ref(row) == {'id': 42, 'name': 'S42'}


# ── _classify_expr_rows ───────────────────────────────────────────────────────


def test_classify_empty():
    cond, act = _classify_expr_rows([])
    assert cond == [] and act == []


def test_classify_single_condition():
    rows = [{'scenario_id': '1', 'scenario_name': 'S1', 'ss_type': 'if', 'ss_subtype': 'condition'}]
    cond, act = _classify_expr_rows(rows)
    assert cond == [{'id': 1, 'name': 'S1'}]
    assert act == []


def test_classify_single_action():
    rows = [{'scenario_id': '2', 'scenario_name': 'S2', 'ss_type': 'action', 'ss_subtype': 'action'}]
    cond, act = _classify_expr_rows(rows)
    assert cond == []
    assert act == [{'id': 2, 'name': 'S2'}]


def test_classify_none_subtype_falls_to_action():
    rows = [{'scenario_id': '3', 'scenario_name': 'S3', 'ss_type': 'action', 'ss_subtype': None}]
    cond, act = _classify_expr_rows(rows)
    assert cond == []
    assert len(act) == 1


def test_classify_dedup_condition():
    rows = [
        {'scenario_id': '1', 'scenario_name': 'S1', 'ss_type': 'if', 'ss_subtype': 'condition'},
        {'scenario_id': '1', 'scenario_name': 'S1', 'ss_type': 'if', 'ss_subtype': 'condition'},
    ]
    cond, _ = _classify_expr_rows(rows)
    assert len(cond) == 1


def test_classify_dedup_action():
    rows = [
        {'scenario_id': '2', 'scenario_name': 'S2', 'ss_type': 'action', 'ss_subtype': 'action'},
        {'scenario_id': '2', 'scenario_name': 'S2', 'ss_type': 'action', 'ss_subtype': 'action'},
    ]
    _, act = _classify_expr_rows(rows)
    assert len(act) == 1


def test_classify_mixed():
    rows = [
        {'scenario_id': '1', 'scenario_name': 'S1', 'ss_type': 'if', 'ss_subtype': 'condition'},
        {'scenario_id': '2', 'scenario_name': 'S2', 'ss_type': 'action', 'ss_subtype': 'action'},
    ]
    cond, act = _classify_expr_rows(rows)
    assert len(cond) == 1 and len(act) == 1


# ── _refs_for_cmd_id ─────────────────────────────────────────────────────────


def test_refs_no_refs(conn):
    with patch('_domain.usage_graph.db.query', side_effect=[[], [], [], []]):
        triggers, cond, act, ds, fp = _refs_for_cmd_id(100, conn)
    assert triggers == [] and cond == [] and act == [] and ds == [] and fp == []


def test_refs_with_trigger(conn):
    with patch('_domain.usage_graph.db.query', side_effect=[
        [{'id': '5', 'name': 'S5'}],  # _TRIGGER_REFS
        [],                             # _EXPR_REFS
        [],                             # _DATASTORE_REFS
        [],                             # _CODE_REFS
    ]):
        triggers, _, _, _, _ = _refs_for_cmd_id(100, conn)
    assert triggers == [{'id': 5, 'name': 'S5'}]


def test_refs_with_datastore(conn):
    with patch('_domain.usage_graph.db.query', side_effect=[
        [],
        [],
        [{'id': '1', 'name': 'DS1', 'type': 'scenario'}],
        [],
    ]):
        _, _, _, ds, _ = _refs_for_cmd_id(100, conn)
    assert ds == [{'id': 1, 'name': 'DS1', 'type': 'scenario'}]


def test_refs_code_rows_generates_fp_warning(conn):
    with patch('_domain.usage_graph.db.query', side_effect=[
        [],
        [],
        [],
        [{'scenario_id': '8', 'scenario_name': 'ScénD'}],
    ]):
        _, _, _, _, fp = _refs_for_cmd_id(100, conn)
    assert len(fp) == 1
    assert 'ScénD' in fp[0]
    assert '100' in fp[0]


def test_refs_multiple_code_rows_in_fp(conn):
    with patch('_domain.usage_graph.db.query', side_effect=[
        [],
        [],
        [],
        [
            {'scenario_id': '8', 'scenario_name': 'ScénD'},
            {'scenario_id': '9', 'scenario_name': 'ScénE'},
        ],
    ]):
        _, _, _, _, fp = _refs_for_cmd_id(100, conn)
    assert 'ScénD' in fp[0] and 'ScénE' in fp[0]


# ── _resolve_cmd ──────────────────────────────────────────────────────────────


def test_resolve_cmd_not_found(conn):
    with patch('_domain.usage_graph.db.query', return_value=[]):
        result = _resolve_cmd(999, conn)
    assert 'error' in result
    assert '999' in result['error']


def test_resolve_cmd_found_minimal(conn):
    cmd_row = [{'id': 15663, 'name': 'BLE présent', 'type': 'info', 'subType': 'binary',
                'eqLogic_id': 186, 'eqLogic_name': 'Présence Géraud'}]
    with patch('_domain.usage_graph.db.query', side_effect=[
        cmd_row, [], [], [], [],
    ]):
        result = _resolve_cmd(15663, conn)
    assert result['target']['id'] == 15663
    assert result['target']['type'] == 'cmd'
    assert result['target']['eqLogic_id'] == 186
    assert result['references']['triggers'] == []
    assert result['false_positive_warnings'] == []


def test_resolve_cmd_found_with_all_refs(conn):
    cmd_row = [{'id': 100, 'name': 'Cmd', 'type': 'info', 'subType': 'numeric',
                'eqLogic_id': 10, 'eqLogic_name': 'EQ'}]
    with patch('_domain.usage_graph.db.query', side_effect=[
        cmd_row,
        [{'id': '5', 'name': 'ScénA'}],
        [{'scenario_id': '6', 'scenario_name': 'ScénB', 'ss_type': 'if', 'ss_subtype': 'condition'}],
        [{'id': '1', 'name': 'DS1', 'type': 'scenario'}],
        [{'scenario_id': '8', 'scenario_name': 'ScénD'}],
    ]):
        result = _resolve_cmd(100, conn)
    assert len(result['references']['triggers']) == 1
    assert len(result['references']['conditions']) == 1
    assert len(result['references']['datastore_refs']) == 1
    assert len(result['false_positive_warnings']) == 1


# ── _resolve_eqlogic ─────────────────────────────────────────────────────────


def test_resolve_eqlogic_not_found(conn):
    with patch('_domain.usage_graph.db.query', return_value=[]):
        result = _resolve_eqlogic(999, conn)
    assert 'error' in result


def test_resolve_eqlogic_no_cmds(conn):
    eq_row = [{'id': 186, 'name': 'Présence', 'eqType_name': 'BLEA', 'isEnable': 1}]
    with patch('_domain.usage_graph.db.query', side_effect=[eq_row, []]):
        result = _resolve_eqlogic(186, conn)
    assert result['target']['id'] == 186
    assert result['target']['plugin'] == 'BLEA'
    assert result['references']['triggers'] == []


def test_resolve_eqlogic_dedup_triggers(conn):
    eq_row = [{'id': 10, 'name': 'EQ', 'eqType_name': 'Plugin', 'isEnable': 1}]
    cmd_ids = [{'id': 101}, {'id': 102}]
    trigger_101 = [{'id': '1', 'name': 'S1'}, {'id': '2', 'name': 'S2'}]
    trigger_102 = [{'id': '1', 'name': 'S1'}, {'id': '3', 'name': 'S3'}]
    with patch('_domain.usage_graph.db.query', side_effect=[
        eq_row, cmd_ids,
        trigger_101, [], [], [],
        trigger_102, [], [], [],
    ]):
        result = _resolve_eqlogic(10, conn)
    trigger_ids = {r['id'] for r in result['references']['triggers']}
    assert trigger_ids == {1, 2, 3}


def test_resolve_eqlogic_dedup_conditions(conn):
    eq_row = [{'id': 20, 'name': 'EQ2', 'eqType_name': 'P', 'isEnable': 1}]
    cmd_ids = [{'id': 201}, {'id': 202}]
    cond_row = [{'scenario_id': '5', 'scenario_name': 'S5', 'ss_type': 'if', 'ss_subtype': 'condition'}]
    with patch('_domain.usage_graph.db.query', side_effect=[
        eq_row, cmd_ids,
        [], cond_row, [], [],
        [], cond_row, [], [],
    ]):
        result = _resolve_eqlogic(20, conn)
    assert len(result['references']['conditions']) == 1


def test_resolve_eqlogic_dedup_actions(conn):
    eq_row = [{'id': 30, 'name': 'EQ3', 'eqType_name': 'P', 'isEnable': 1}]
    cmd_ids = [{'id': 301}, {'id': 302}]
    act_row = [{'scenario_id': '6', 'scenario_name': 'S6', 'ss_type': 'action', 'ss_subtype': 'action'}]
    with patch('_domain.usage_graph.db.query', side_effect=[
        eq_row, cmd_ids,
        [], act_row, [], [],
        [], act_row, [], [],
    ]):
        result = _resolve_eqlogic(30, conn)
    assert len(result['references']['actions']) == 1


def test_resolve_eqlogic_aggregates_datastore_and_fp(conn):
    eq_row = [{'id': 40, 'name': 'EQ4', 'eqType_name': 'P', 'isEnable': 1}]
    cmd_ids = [{'id': 401}]
    ds_rows = [{'id': '7', 'name': 'DS7', 'type': 'scenario'}]
    code_rows = [{'scenario_id': '9', 'scenario_name': 'ScénX'}]
    with patch('_domain.usage_graph.db.query', side_effect=[
        eq_row, cmd_ids,
        [], [], ds_rows, code_rows,
    ]):
        result = _resolve_eqlogic(40, conn)
    assert len(result['references']['datastore_refs']) == 1
    assert len(result['false_positive_warnings']) == 1


# ── _resolve_scenario ─────────────────────────────────────────────────────────


def test_resolve_scenario_not_found(conn):
    with patch('_domain.usage_graph.db.query', return_value=[]):
        result = _resolve_scenario(999, conn)
    assert 'error' in result


def test_resolve_scenario_no_callers(conn):
    scen_row = [{'id': 70, 'name': 'Scénario test', 'isActive': 1, 'mode': 'schedule'}]
    with patch('_domain.usage_graph.db.query', side_effect=[scen_row, []]):
        result = _resolve_scenario(70, conn)
    assert result['target']['id'] == 70
    assert result['target']['type'] == 'scenario'
    assert result['references']['scenario_calls'] == []
    assert result['false_positive_warnings'] == []


def test_resolve_scenario_with_callers(conn):
    scen_row = [{'id': 5, 'name': 'S5', 'isActive': 1, 'mode': 'trigger'}]
    caller_rows = [{'scenario_id': '10', 'scenario_name': 'S10'}]
    with patch('_domain.usage_graph.db.query', side_effect=[scen_row, caller_rows]):
        result = _resolve_scenario(5, conn)
    assert result['references']['scenario_calls'] == [{'id': 10, 'name': 'S10'}]


# ── resolve (dispatch) ────────────────────────────────────────────────────────


def test_resolve_dispatches_cmd(conn):
    cmd_row = [{'id': 1, 'name': 'C', 'type': 'info', 'subType': 'binary',
                'eqLogic_id': 1, 'eqLogic_name': 'EQ'}]
    with patch('_domain.usage_graph.db.query', side_effect=[cmd_row, [], [], [], []]):
        result = resolve('cmd', 1, conn)
    assert result['target']['type'] == 'cmd'


def test_resolve_dispatches_eqlogic(conn):
    eq_row = [{'id': 1, 'name': 'EQ', 'eqType_name': 'P', 'isEnable': 1}]
    with patch('_domain.usage_graph.db.query', side_effect=[eq_row, []]):
        result = resolve('eqLogic', 1, conn)
    assert result['target']['type'] == 'eqLogic'


def test_resolve_dispatches_scenario(conn):
    scen_row = [{'id': 1, 'name': 'S', 'isActive': 1, 'mode': 'trigger'}]
    with patch('_domain.usage_graph.db.query', side_effect=[scen_row, []]):
        result = resolve('scenario', 1, conn)
    assert result['target']['type'] == 'scenario'


def test_resolve_unknown_target_type(conn):
    result = resolve('foobar', 1, conn)
    assert 'error' in result
    assert 'foobar' in result['error']
