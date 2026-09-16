"""Graphe d'usage Jeedom — trouve tout ce qui référence une cmd, eqLogic, ou scénario.

Dérivé de jeedom-audit/usage_graph.py — db_query.py → _core/db.py (PyMySQL local).
"""

from __future__ import annotations

import structlog
from _core import db

from _domain import scenario_tree as _tree

log = structlog.get_logger('holmesMcp.domain.usage_graph')

# ── SQL ───────────────────────────────────────────────────────────────────────

_CMD_INFO = (
    'SELECT c.id, c.name, c.type, c.subType, c.eqLogic_id, e.name AS eqLogic_name'
    ' FROM cmd c'
    ' JOIN eqLogic e ON e.id = c.eqLogic_id'
    ' WHERE c.id = %s'
)

_EQLOGIC_INFO = 'SELECT id, name, eqType_name, isEnable FROM eqLogic WHERE id = %s'

_SCENARIO_INFO = 'SELECT id, name, isActive, mode FROM scenario WHERE id = %s'

_EQLOGIC_CMD_IDS = 'SELECT id FROM cmd WHERE eqLogic_id = %s'

_TRIGGER_REFS = 'SELECT DISTINCT id, name FROM scenario WHERE `trigger` LIKE %s'

# Le rattachement expression → scénario est RÉCURSIF (ADR-0023, _domain/scenario_tree).
# Le JOIN `LIKE CONCAT('%', sel.id, '%')` qui vivait ici inventait des rattachements
# (élément 1 → 23 scénarios) ET manquait les éléments imbriqués, soit 69 % d'entre eux.
_EXPR_REFS = (
    _tree.ancestors_cte(seed_where="x.expression LIKE %s AND ss.type != 'code'")
    + """SELECT DISTINCT
    s.id        AS scenario_id,
    s.name      AS scenario_name,
    ss.type     AS ss_type,
    ss.subtype  AS ss_subtype
FROM anc a
"""
    + _tree.ROOT_JOIN
    + '\n'
    + _tree.SUBELEMENT_JOIN
    + '\n'
)

_CODE_REFS = (
    _tree.ancestors_cte(seed_where="ss.type = 'code' AND x.expression LIKE %s")
    + """SELECT DISTINCT
    s.id   AS scenario_id,
    s.name AS scenario_name
FROM anc a
"""
    + _tree.ROOT_JOIN
    + '\n'
)

_SCENARIO_CALLERS = (
    _tree.ancestors_cte(seed_where="x.expression = 'scenario' AND x.options LIKE %s")
    + """SELECT DISTINCT
    s.id   AS scenario_id,
    s.name AS scenario_name
FROM anc a
"""
    + _tree.ROOT_JOIN
    + '\n'
)

_DATASTORE_REFS = 'SELECT id, name, type FROM dataStore WHERE value LIKE %s'


# ── Helpers ───────────────────────────────────────────────────────────────────


def _scenario_ref(row: dict) -> dict:
    return {'id': int(row['scenario_id']), 'name': row['scenario_name']}


def _classify_expr_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Sépare les références en conditions et actions selon ss_subtype."""
    conditions: list[dict] = []
    actions: list[dict] = []
    seen_cond: set[int] = set()
    seen_act: set[int] = set()

    for row in rows:
        ref = _scenario_ref(row)
        sid = ref['id']
        subtype = (row.get('ss_subtype') or '').lower()

        if subtype == 'condition':
            if sid not in seen_cond:
                conditions.append(ref)
                seen_cond.add(sid)
        else:
            if sid not in seen_act:
                actions.append(ref)
                seen_act.add(sid)

    return conditions, actions


def _refs_for_cmd_id(
    cmd_id: int,
    conn,
) -> tuple[list, list, list, list, list[str]]:
    """Retourne (triggers, conditions, actions, datastore_refs, fp_warnings)."""
    pattern = f'%#{cmd_id}#%'

    trigger_rows = db.query(conn, _TRIGGER_REFS, (pattern,))
    triggers = [{'id': int(r['id']), 'name': r['name']} for r in trigger_rows]

    expr_rows = db.query(conn, _EXPR_REFS, (pattern,))
    conditions, actions = _classify_expr_rows(expr_rows)

    datastore_rows = db.query(conn, _DATASTORE_REFS, (pattern,))
    datastore_refs = [
        {'id': int(r['id']), 'name': r['name'], 'type': r['type']} for r in datastore_rows
    ]

    fp_warnings: list[str] = []
    code_rows = db.query(conn, _CODE_REFS, (f'%{cmd_id}%',))
    if code_rows:
        names = ', '.join(f'{r["scenario_name"]} (#{r["scenario_id"]})' for r in code_rows)
        fp_warnings.append(
            f"ID {cmd_id} apparaît dans des blocs 'code' PHP (faux positifs possibles) : {names}"
        )

    return triggers, conditions, actions, datastore_refs, fp_warnings


# ── Résolutions par target_type ───────────────────────────────────────────────


def _resolve_cmd(target_id: int, conn) -> dict:
    rows = db.query(conn, _CMD_INFO, (target_id,))
    if not rows:
        return {'error': f'Commande introuvable : id={target_id}'}

    r = rows[0]
    target = {
        'type': 'cmd',
        'id': int(r['id']),
        'name': r['name'],
        'cmd_type': r['type'],
        'cmd_subtype': r['subType'],
        'eqLogic_id': int(r['eqLogic_id']),
        'eqLogic_name': r['eqLogic_name'],
    }

    triggers, conditions, actions, ds_refs, fp = _refs_for_cmd_id(target_id, conn)

    return {
        'target': target,
        'references': {
            'triggers': triggers,
            'conditions': conditions,
            'actions': actions,
            'plugin_consumers': [],
            'datastore_refs': ds_refs,
            'scenario_calls': [],
        },
        'false_positive_warnings': fp,
    }


def _resolve_eqlogic(target_id: int, conn) -> dict:
    rows = db.query(conn, _EQLOGIC_INFO, (target_id,))
    if not rows:
        return {'error': f'eqLogic introuvable : id={target_id}'}

    r = rows[0]
    target = {
        'type': 'eqLogic',
        'id': int(r['id']),
        'name': r['name'],
        'plugin': r['eqType_name'],
        'isEnable': r['isEnable'],
    }

    cmd_rows = db.query(conn, _EQLOGIC_CMD_IDS, (target_id,))
    cmd_ids = [int(cr['id']) for cr in cmd_rows]

    all_triggers: list[dict] = []
    all_conditions: list[dict] = []
    all_actions: list[dict] = []
    all_ds: list[dict] = []
    all_fp: list[str] = []

    seen_t: set[int] = set()
    seen_c: set[int] = set()
    seen_a: set[int] = set()

    for cid in cmd_ids:
        t, c, a, ds, fp = _refs_for_cmd_id(cid, conn)
        for ref in t:
            if ref['id'] not in seen_t:
                all_triggers.append(ref)
                seen_t.add(ref['id'])
        for ref in c:
            if ref['id'] not in seen_c:
                all_conditions.append(ref)
                seen_c.add(ref['id'])
        for ref in a:
            if ref['id'] not in seen_a:
                all_actions.append(ref)
                seen_a.add(ref['id'])
        all_ds.extend(ds)
        all_fp.extend(fp)

    return {
        'target': target,
        'references': {
            'triggers': all_triggers,
            'conditions': all_conditions,
            'actions': all_actions,
            'plugin_consumers': [],
            'datastore_refs': all_ds,
            'scenario_calls': [],
        },
        'false_positive_warnings': all_fp,
    }


def _resolve_scenario(target_id: int, conn) -> dict:
    rows = db.query(conn, _SCENARIO_INFO, (target_id,))
    if not rows:
        return {'error': f'Scénario introuvable : id={target_id}'}

    r = rows[0]
    target = {
        'type': 'scenario',
        'id': int(r['id']),
        'name': r['name'],
        'isActive': r['isActive'],
        'mode': r['mode'],
    }

    options_pattern = f'%"scenario_id":"{target_id}"%'
    caller_rows = db.query(conn, _SCENARIO_CALLERS, (options_pattern,))
    callers = [_scenario_ref(r) for r in caller_rows]

    return {
        'target': target,
        'references': {
            'triggers': [],
            'conditions': [],
            'actions': [],
            'plugin_consumers': [],
            'datastore_refs': [],
            'scenario_calls': callers,
        },
        'false_positive_warnings': [],
    }


# ── API publique ──────────────────────────────────────────────────────────────


def resolve(target_type: str, target_id: int, conn) -> dict:
    """Construit le graphe d'usage pour une cible donnée.

    Args:
        target_type : 'cmd' | 'eqLogic' | 'scenario'
        target_id   : ID Jeedom de la cible
        conn        : connexion PyMySQL (db.connect())
    """
    log.debug('usage_graph_resolve', target_type=target_type, target_id=target_id)

    if target_type == 'cmd':
        return _resolve_cmd(target_id, conn)
    if target_type == 'eqLogic':
        return _resolve_eqlogic(target_id, conn)
    if target_type == 'scenario':
        return _resolve_scenario(target_id, conn)

    return {'error': f'target_type inconnu : {target_type!r} — valeurs : cmd, eqLogic, scenario'}
