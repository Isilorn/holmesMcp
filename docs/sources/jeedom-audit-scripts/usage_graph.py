#!/usr/bin/env python3
"""Graphe d'usage — trouve tout ce qui référence une cmd, eqLogic, ou scénario.

Entrée (stdin) : {"target_type": "cmd|eqLogic|scenario", "target_id": 15663}
Sortie (stdout): {
    "target": {...},
    "references": {
        "triggers": [...],
        "conditions": [...],
        "actions": [...],
        "plugin_consumers": [],
        "datastore_refs": [...],
        "scenario_calls": [...]
    },
    "false_positive_warnings": [...]
}

Usage :
    echo '{"target_type": "cmd", "target_id": 15663}' | python3 scripts/usage_graph.py
    echo '{"target_type": "eqLogic", "target_id": 186}' | python3 scripts/usage_graph.py
    echo '{"target_type": "scenario", "target_id": 70}' | python3 scripts/usage_graph.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _common import credentials as _creds
import db_query as _db

# ── Requêtes SQL ───────────────────────────────────────────────────────────────

_CMD_INFO = (
    "SELECT c.id, c.name, c.type, c.subType, c.eqLogic_id, e.name AS eqLogic_name"
    " FROM cmd c"
    " JOIN eqLogic e ON e.id = c.eqLogic_id"
    " WHERE c.id = ?"
)

_EQLOGIC_INFO = (
    "SELECT id, name, eqType_name, isEnable FROM eqLogic WHERE id = ?"
)

_SCENARIO_INFO = (
    "SELECT id, name, isActive, mode FROM scenario WHERE id = ?"
)

_EQLOGIC_CMD_IDS = (
    "SELECT id FROM cmd WHERE eqLogic_id = ?"
)

_TRIGGER_REFS = (
    "SELECT DISTINCT id, name FROM scenario WHERE `trigger` LIKE ?"
)

# Remontée expression → scénario : scenarioElement n'a pas de scenario_id,
# le lien est stocké dans scenario.scenarioElement (JSON array d'entiers).
# LIKE '%N%' est sûr sur des IDs >100 ; les petits IDs (<10) peuvent générer
# des faux positifs — signalés dans false_positive_warnings si détectés.
_EXPR_REFS = """
SELECT DISTINCT
    s.id        AS scenario_id,
    s.name      AS scenario_name,
    ss.type     AS ss_type,
    ss.subtype  AS ss_subtype
FROM scenarioExpression expr
JOIN scenarioSubElement ss  ON ss.id  = expr.scenarioSubElement_id
JOIN scenarioElement    sel ON sel.id = ss.scenarioElement_id
JOIN scenario           s   ON s.scenarioElement LIKE CONCAT('%', sel.id, '%')
WHERE expr.expression LIKE ?
  AND ss.type != 'code'
"""

_CODE_REFS = """
SELECT DISTINCT
    s.id   AS scenario_id,
    s.name AS scenario_name
FROM scenarioExpression expr
JOIN scenarioSubElement ss  ON ss.id  = expr.scenarioSubElement_id
JOIN scenarioElement    sel ON sel.id = ss.scenarioElement_id
JOIN scenario           s   ON s.scenarioElement LIKE CONCAT('%', sel.id, '%')
WHERE ss.type = 'code'
  AND expr.expression LIKE ?
"""

_SCENARIO_CALLERS = """
SELECT DISTINCT
    s.id   AS scenario_id,
    s.name AS scenario_name
FROM scenarioExpression expr
JOIN scenarioSubElement ss  ON ss.id  = expr.scenarioSubElement_id
JOIN scenarioElement    sel ON sel.id = ss.scenarioElement_id
JOIN scenario           s   ON s.scenarioElement LIKE CONCAT('%', sel.id, '%')
WHERE expr.expression = 'scenario'
  AND expr.options LIKE ?
"""

_DATASTORE_REFS = (
    "SELECT id, name, type FROM dataStore WHERE value LIKE ?"
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _q(sql: str, params: list, creds: dict) -> list[dict]:
    result = _db.run(sql, params=params, creds=creds)
    return result.get("rows", [])


def _scenario_ref(row: dict) -> dict:
    return {"id": int(row["scenario_id"]), "name": row["scenario_name"]}


def _classify_expr_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Sépare les références en conditions et actions selon ss_subtype."""
    conditions: list[dict] = []
    actions: list[dict] = []
    seen_cond: set[int] = set()
    seen_act: set[int] = set()

    for row in rows:
        ref = _scenario_ref(row)
        sid = ref["id"]
        subtype = (row.get("ss_subtype") or "").lower()

        if subtype == "condition":
            if sid not in seen_cond:
                conditions.append(ref)
                seen_cond.add(sid)
        else:
            if sid not in seen_act:
                actions.append(ref)
                seen_act.add(sid)

    return conditions, actions


def _refs_for_cmd_id(cmd_id: int, creds: dict) -> tuple[list, list, list, list, list[str]]:
    """Retourne (triggers, conditions, actions, datastore_refs, fp_warnings)."""
    pattern = f"%#{cmd_id}#%"

    trigger_rows = _q(_TRIGGER_REFS, [pattern], creds)
    triggers = [{"id": int(r["id"]), "name": r["name"]} for r in trigger_rows]

    expr_rows = _q(_EXPR_REFS, [pattern], creds)
    conditions, actions = _classify_expr_rows(expr_rows)

    datastore_rows = _q(_DATASTORE_REFS, [pattern], creds)
    datastore_refs = [
        {"id": int(r["id"]), "name": r["name"], "type": r["type"]}
        for r in datastore_rows
    ]

    fp_warnings: list[str] = []
    code_rows = _q(_CODE_REFS, [f"%{cmd_id}%"], creds)
    if code_rows:
        scenario_names = ", ".join(
            f"{r['scenario_name']} (#{r['scenario_id']})" for r in code_rows
        )
        fp_warnings.append(
            f"ID {cmd_id} apparaît dans des blocs 'code' PHP (faux positifs possibles) : "
            f"{scenario_names}"
        )

    return triggers, conditions, actions, datastore_refs, fp_warnings


# ── Points d'entrée par target_type ───────────────────────────────────────────


def _resolve_cmd(target_id: int, creds: dict) -> dict:
    rows = _q(_CMD_INFO, [target_id], creds)
    if not rows:
        return {"error": f"Commande introuvable : id={target_id}"}

    r = rows[0]
    target = {
        "type": "cmd",
        "id": int(r["id"]),
        "name": r["name"],
        "cmd_type": r["type"],
        "cmd_subtype": r["subType"],
        "eqLogic_id": int(r["eqLogic_id"]),
        "eqLogic_name": r["eqLogic_name"],
    }

    triggers, conditions, actions, ds_refs, fp = _refs_for_cmd_id(target_id, creds)

    return {
        "target": target,
        "references": {
            "triggers": triggers,
            "conditions": conditions,
            "actions": actions,
            "plugin_consumers": [],
            "datastore_refs": ds_refs,
            "scenario_calls": [],
        },
        "false_positive_warnings": fp,
    }


def _resolve_eqlogic(target_id: int, creds: dict) -> dict:
    rows = _q(_EQLOGIC_INFO, [target_id], creds)
    if not rows:
        return {"error": f"eqLogic introuvable : id={target_id}"}

    r = rows[0]
    target = {
        "type": "eqLogic",
        "id": int(r["id"]),
        "name": r["name"],
        "plugin": r["eqType_name"],
        "isEnable": r["isEnable"],
    }

    cmd_rows = _q(_EQLOGIC_CMD_IDS, [target_id], creds)
    cmd_ids = [int(cr["id"]) for cr in cmd_rows]

    all_triggers: list[dict] = []
    all_conditions: list[dict] = []
    all_actions: list[dict] = []
    all_ds: list[dict] = []
    all_fp: list[str] = []

    seen_t: set[int] = set()
    seen_c: set[int] = set()
    seen_a: set[int] = set()

    for cid in cmd_ids:
        t, c, a, ds, fp = _refs_for_cmd_id(cid, creds)
        for ref in t:
            if ref["id"] not in seen_t:
                all_triggers.append(ref)
                seen_t.add(ref["id"])
        for ref in c:
            if ref["id"] not in seen_c:
                all_conditions.append(ref)
                seen_c.add(ref["id"])
        for ref in a:
            if ref["id"] not in seen_a:
                all_actions.append(ref)
                seen_a.add(ref["id"])
        all_ds.extend(ds)
        all_fp.extend(fp)

    return {
        "target": target,
        "references": {
            "triggers": all_triggers,
            "conditions": all_conditions,
            "actions": all_actions,
            "plugin_consumers": [],
            "datastore_refs": all_ds,
            "scenario_calls": [],
        },
        "false_positive_warnings": all_fp,
    }


def _resolve_scenario(target_id: int, creds: dict) -> dict:
    rows = _q(_SCENARIO_INFO, [target_id], creds)
    if not rows:
        return {"error": f"Scénario introuvable : id={target_id}"}

    r = rows[0]
    target = {
        "type": "scenario",
        "id": int(r["id"]),
        "name": r["name"],
        "isActive": r["isActive"],
        "mode": r["mode"],
    }

    options_pattern = f'%"scenario_id":"{target_id}"%'
    caller_rows = _q(_SCENARIO_CALLERS, [options_pattern], creds)
    callers = [_scenario_ref(r) for r in caller_rows]

    return {
        "target": target,
        "references": {
            "triggers": [],
            "conditions": [],
            "actions": [],
            "plugin_consumers": [],
            "datastore_refs": [],
            "scenario_calls": callers,
        },
        "false_positive_warnings": [],
    }


# ── API publique ───────────────────────────────────────────────────────────────


def run(
    target_type: str,
    target_id: int,
    creds: dict | None = None,
) -> dict:
    """Construit le graphe d'usage pour une cible donnée."""
    if creds is None:
        creds = _creds.load()

    if target_type == "cmd":
        return _resolve_cmd(target_id, creds)
    if target_type == "eqLogic":
        return _resolve_eqlogic(target_id, creds)
    if target_type == "scenario":
        return _resolve_scenario(target_id, creds)

    return {"error": f"target_type inconnu : {target_type!r} — valeurs : cmd, eqLogic, scenario"}


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"error": "Entrée vide — fournir JSON sur stdin"}))
        sys.exit(1)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"JSON invalide : {exc}"}))
        sys.exit(1)

    target_type = payload.get("target_type", "").strip()
    target_id_raw = payload.get("target_id")

    if not target_type:
        print(json.dumps({"error": "Clé 'target_type' manquante ou vide"}))
        sys.exit(1)

    if target_id_raw is None:
        print(json.dumps({"error": "Clé 'target_id' manquante"}))
        sys.exit(1)

    try:
        target_id = int(target_id_raw)
    except (TypeError, ValueError):
        print(json.dumps({"error": f"'target_id' doit être un entier, reçu : {target_id_raw!r}"}))
        sys.exit(1)

    result = run(target_type, target_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
