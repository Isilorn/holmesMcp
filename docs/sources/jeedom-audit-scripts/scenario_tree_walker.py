#!/usr/bin/env python3
"""Parcours récursif d'un scénario Jeedom.

Entrée (stdin) : {
    "scenario_id": 70,
    "max_depth": 3,
    "follow_scenario_calls": 2
}
Sortie (stdout): {
    "scenario": {id, name, isActive, mode, trigger},
    "tree": [<node>, ...],
    "truncated": false,
    "warnings": []
}

Un nœud (node) :
    {
        "element_id": 8,
        "depth": 0,
        "sub_elements": [
            {
                "sub_id": 12,
                "ss_type": "if",
                "ss_subtype": "condition",
                "expressions": [
                    {"expr_id": 5, "order": 1, "type": "condition", "expression": "#15663# == 1", "options": "{}"}
                ]
            },
            ...
        ]
    }

Quand follow_scenario_calls > 0, les expressions de type action/scenario sont enrichies :
    {
        "expr_id": 6, "type": "action", "expression": "scenario",
        "options": "{\"scenario_id\": \"5\", \"action\": \"start\"}",
        "called_scenario_tree": { <résultat walk() sur scénario 5> }
    }

Usage :
    echo '{"scenario_id": 70, "follow_scenario_calls": 2}' | python3 scripts/scenario_tree_walker.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _common import credentials as _creds

DEFAULT_MAX_DEPTH = 3
MAX_SUB_ELEMENTS = 100  # au-delà : tronquer avec avertissement

_SCENARIO_SQL = (
    "SELECT id, name, isActive, mode, `trigger`, scenarioElement, description, timeout"
    " FROM scenario WHERE id = ?"
)

_ELEMENTS_SQL = (
    "SELECT"
    "  sel.id      AS element_id,"
    "  ss.id       AS sub_id,"
    "  ss.type     AS ss_type,"
    "  ss.subtype  AS ss_subtype,"
    "  expr.id     AS expr_id,"
    "  expr.`order` AS expr_order,"
    "  expr.type   AS expr_type,"
    "  expr.expression,"
    "  expr.options"
    " FROM scenarioExpression expr"
    " JOIN scenarioSubElement ss ON expr.scenarioSubElement_id = ss.id"
    " JOIN scenarioElement sel   ON ss.scenarioElement_id = sel.id"
    " WHERE sel.id IN ({placeholders})"
    " ORDER BY sel.id, ss.id, expr.`order`"
)


def _run(query: str, params: list | None = None, creds: dict | None = None) -> dict:
    import db_query as _dq
    return _dq.run(query, params=params, creds=creds)


def _fetch_scenario(scenario_id: int, creds: dict) -> dict | None:
    result = _run(_SCENARIO_SQL, params=[scenario_id], creds=creds)
    rows = result.get("rows", [])
    return rows[0] if rows else None


def _fetch_elements(element_ids: list[int], creds: dict) -> list[dict]:
    if not element_ids:
        return []
    placeholders = ", ".join(str(i) for i in element_ids)
    query = _ELEMENTS_SQL.format(placeholders=placeholders)
    result = _run(query, creds=creds)
    return result.get("rows", [])


def _group_by_element(rows: list[dict]) -> dict[int, list[dict]]:
    """Regroupe les lignes SQL par element_id → liste de sub_elements avec leurs expressions."""
    elements: dict[int, dict[int, dict]] = {}
    for row in rows:
        el_id = int(row["element_id"])
        sub_id = int(row["sub_id"])

        if el_id not in elements:
            elements[el_id] = {}
        if sub_id not in elements[el_id]:
            elements[el_id][sub_id] = {
                "sub_id": sub_id,
                "ss_type": row["ss_type"],
                "ss_subtype": row["ss_subtype"],
                "expressions": [],
            }

        elements[el_id][sub_id]["expressions"].append({
            "expr_id": int(row["expr_id"]) if row.get("expr_id") else None,
            "order": int(row["expr_order"]) if row.get("expr_order") else 0,
            "type": row["expr_type"],
            "expression": row["expression"],
            "options": row["options"],
        })

    return {
        el_id: sorted(subs.values(), key=lambda s: s["sub_id"])
        for el_id, subs in elements.items()
    }


def _child_element_ids(element_rows: list[dict]) -> list[int]:
    """Extrait les IDs des sous-éléments référencés par type='element'.

    Accepte aussi bien les dicts bruts SQL (clé 'expr_type') que les dicts
    normalisés par _group_by_element (clé 'type').
    """
    children = []
    for row in element_rows:
        if row.get("type") == "element" or row.get("expr_type") == "element":
            try:
                children.append(int(row["expression"]))
            except (ValueError, TypeError):
                pass
    return children


def _extract_scenario_call_id(expr: dict) -> int | None:
    """Retourne l'ID du scénario appelé si l'expression est un appel de scénario, sinon None.

    Détection : type="action", expression="scenario", options.scenario_id présent.
    Seul action="start" est suivi (stop/activate/deactivate n'appellent pas réellement).
    """
    if expr.get("type") != "action" or expr.get("expression") != "scenario":
        return None
    try:
        opts = json.loads(expr.get("options") or "{}")
        if opts.get("action") not in ("start", None, ""):
            return None
        sid = opts.get("scenario_id")
        return int(sid) if sid is not None else None
    except (json.JSONDecodeError, ValueError, TypeError):
        return None


def _walk(
    root_ids: list[int],
    creds: dict,
    max_depth: int,
    visited: set[int],
    depth: int,
    warnings: list[str],
    truncated_flag: list[bool],
    follow_scenario_calls: int = 0,
    visited_scenarios: set[int] | None = None,
) -> list[dict]:
    """Parcours récursif : retourne la liste des nœuds à ce niveau."""
    if depth > max_depth:
        return []

    safe_ids = [i for i in root_ids if i not in visited]
    if not safe_ids:
        return []

    visited.update(safe_ids)
    rows = _fetch_elements(safe_ids, creds)
    grouped = _group_by_element(rows)

    nodes: list[dict] = []
    for el_id in safe_ids:
        sub_elements = grouped.get(el_id, [])

        if len(sub_elements) > MAX_SUB_ELEMENTS:
            warnings.append(
                f"element {el_id} : {len(sub_elements)} sous-éléments — tronqué à {MAX_SUB_ELEMENTS}"
            )
            sub_elements = sub_elements[:MAX_SUB_ELEMENTS]
            truncated_flag[0] = True

        # Trouver les enfants de type 'element' pour la récursion
        all_expr_rows = [
            expr
            for sub in sub_elements
            for expr in sub["expressions"]
        ]
        child_ids = _child_element_ids(all_expr_rows)

        # Suivre les appels de scénarios si demandé
        if follow_scenario_calls > 0:
            if visited_scenarios is None:
                visited_scenarios = set()
            for sub in sub_elements:
                for expr in sub["expressions"]:
                    called_id = _extract_scenario_call_id(expr)
                    if called_id is None:
                        continue
                    if called_id in visited_scenarios:
                        expr["called_scenario_tree"] = {
                            "warning": f"Scénario {called_id} déjà visité — cycle ignoré"
                        }
                        continue
                    visited_scenarios.add(called_id)
                    expr["called_scenario_tree"] = walk(
                        called_id,
                        max_depth=max_depth,
                        creds=creds,
                        follow_scenario_calls=follow_scenario_calls - 1,
                        _visited_scenarios=visited_scenarios,
                    )

        node: dict = {
            "element_id": el_id,
            "depth": depth,
            "sub_elements": sub_elements,
        }

        if child_ids:
            children = _walk(
                child_ids, creds, max_depth, visited, depth + 1,
                warnings, truncated_flag,
                follow_scenario_calls=follow_scenario_calls,
                visited_scenarios=visited_scenarios,
            )
            if children:
                node["children"] = children

        nodes.append(node)

    return nodes


def walk(
    scenario_id: int,
    max_depth: int = DEFAULT_MAX_DEPTH,
    creds: dict | None = None,
    follow_scenario_calls: int = 0,
    _visited_scenarios: set[int] | None = None,
) -> dict:
    """Parcourt le scénario et retourne l'arbre structuré.

    Args:
        scenario_id            : ID du scénario Jeedom
        max_depth              : profondeur max de récursion des éléments (défaut 3)
        creds                  : credentials (chargés depuis fichier si None)
        follow_scenario_calls  : niveaux de suivi des appels inter-scénarios (0 = désactivé)
        _visited_scenarios     : usage interne — anti-cycle inter-scénarios
    """
    if creds is None:
        creds = _creds.load()

    if _visited_scenarios is None:
        _visited_scenarios = {scenario_id}
    else:
        _visited_scenarios.add(scenario_id)

    scenario = _fetch_scenario(scenario_id, creds)
    if scenario is None:
        return {
            "error": f"Scénario {scenario_id} introuvable",
            "scenario": None,
            "tree": [],
            "truncated": False,
            "warnings": [],
        }

    raw_element_ids: list[int] = []
    try:
        raw = scenario.get("scenarioElement") or "[]"
        raw_element_ids = [int(i) for i in json.loads(raw)]
    except (json.JSONDecodeError, ValueError):
        pass

    warnings: list[str] = []
    truncated_flag = [False]
    visited: set[int] = set()

    tree = _walk(
        root_ids=raw_element_ids,
        creds=creds,
        max_depth=max_depth,
        visited=visited,
        depth=0,
        warnings=warnings,
        truncated_flag=truncated_flag,
        follow_scenario_calls=follow_scenario_calls,
        visited_scenarios=_visited_scenarios,
    )

    return {
        "scenario": {
            "id": int(scenario["id"]),
            "name": scenario["name"],
            "isActive": scenario.get("isActive"),
            "mode": scenario.get("mode"),
            "trigger": scenario.get("trigger"),
            "description": scenario.get("description"),
        },
        "tree": tree,
        "truncated": truncated_flag[0],
        "warnings": warnings,
    }


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

    scenario_id = payload.get("scenario_id")
    if not isinstance(scenario_id, int):
        print(json.dumps({"error": "Clé 'scenario_id' manquante ou non-entier"}))
        sys.exit(1)

    max_depth = payload.get("max_depth", DEFAULT_MAX_DEPTH)
    follow_scenario_calls = payload.get("follow_scenario_calls", 0)
    if not isinstance(follow_scenario_calls, int) or follow_scenario_calls < 0:
        follow_scenario_calls = 0

    result = walk(scenario_id, max_depth=max_depth, follow_scenario_calls=follow_scenario_calls)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
