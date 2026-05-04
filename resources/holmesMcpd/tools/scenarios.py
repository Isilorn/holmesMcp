"""Famille 3 — Scénarios (7 tools).

Tools : list_scenarios, find_scenarios_advanced, get_scenario,
        get_scenario_structure, describe_scenario,
        find_scenario_dependencies, get_scenario_log.
Canal : MySQL RO (tables scenario, scenarioElement, scenarioSubElement,
        scenarioExpression) + _domain walker/graph/cmd_refs + _core/logs.
Sanitisation : sanitize_rows / wrap_result via _domain.sanitize.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from _core import db as _db
from _core import logs as _logs
from _domain import cmd_refs as _cmd_refs
from _domain import scenario_walker as _walker
from _domain import usage_graph as _usage_graph
from _domain.sanitize import sanitize_rows, wrap_result

if TYPE_CHECKING:
    import pymysql.connections

_SCEN_LIMIT = 100
_SCEN_LIMIT_ADV = 50
_LOG_LINES = 100

_ID_RE = re.compile(r'#(\d+)#')

_SCEN_COLS = (
    'id, name, `group`, isActive, mode, `trigger`, lastLaunch, timeout, description, state'
)


def list_scenarios(
    conn: pymysql.connections.Connection,
    group: str | None = None,
    is_active: bool | None = None,
    limit: int = _SCEN_LIMIT,
    offset: int = 0,
) -> dict[str, Any]:
    """Liste des scénarios filtrables par groupe ou état d'activation.

    Paramètres :
    - group     : filtre exact sur le groupe du scénario
    - is_active : True = uniquement les actifs, False = uniquement les désactivés
    - limit     : nombre max de résultats (max 100)
    - offset    : décalage pour la pagination

    Pour le détail d'un scénario (déclencheurs, structure), utilisez get_scenario.
    """
    conditions: list[str] = []
    params: list[Any] = []

    if group is not None:
        conditions.append('`group` = %s')
        params.append(group)
    if is_active is not None:
        conditions.append('isActive = %s')
        params.append(1 if is_active else 0)

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
    limit = min(limit, _SCEN_LIMIT)
    params += [limit, offset]

    rows = _db.query(
        conn,
        f'SELECT {_SCEN_COLS} FROM scenario {where} ORDER BY name LIMIT %s OFFSET %s',
        params,
    )
    sanitized, filtered = sanitize_rows(rows, 'scenario')
    return wrap_result(
        {'scenarios': sanitized, 'total': len(sanitized), 'offset': offset},
        filtered,
    )


def find_scenarios_advanced(
    conn: pymysql.connections.Connection,
    name_contains: str | None = None,
    group: str | None = None,
    is_active: bool | None = None,
    trigger_type: str | None = None,
    limit: int = _SCEN_LIMIT_ADV,
) -> dict[str, Any]:
    """Recherche avancée de scénarios avec filtres combinables.

    Paramètres :
    - name_contains : fragment de nom (insensible à la casse, LIKE %fragment%)
    - group         : filtre exact sur le groupe
    - is_active     : True = actifs uniquement
    - trigger_type  : fragment dans le champ trigger (ex. 'schedule', 'event')
    - limit         : max 50 résultats
    """
    conditions: list[str] = []
    params: list[Any] = []

    if name_contains is not None:
        conditions.append('name LIKE %s')
        params.append(f'%{name_contains}%')
    if group is not None:
        conditions.append('`group` = %s')
        params.append(group)
    if is_active is not None:
        conditions.append('isActive = %s')
        params.append(1 if is_active else 0)
    if trigger_type is not None:
        conditions.append('`trigger` LIKE %s')
        params.append(f'%{trigger_type}%')

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
    limit = min(limit, _SCEN_LIMIT_ADV)
    params.append(limit)

    rows = _db.query(
        conn,
        f'SELECT {_SCEN_COLS} FROM scenario {where} ORDER BY name LIMIT %s',
        params,
    )
    sanitized, filtered = sanitize_rows(rows, 'scenario')
    return wrap_result({'scenarios': sanitized, 'total': len(sanitized)}, filtered)


def get_scenario(
    conn: pymysql.connections.Connection,
    scenario_id: int,
) -> dict[str, Any]:
    """Détail complet d'un scénario : métadonnées, déclencheurs, dernier run.

    Paramètres :
    - scenario_id : identifiant numérique du scénario (table scenario.id)

    Retourne les métadonnées complètes du scénario (sanitisées).
    Pour l'arbre structurel, utilisez get_scenario_structure.
    Pour la description LLM-friendly, utilisez describe_scenario.
    Si le scénario n'existe pas, retourne {'error': 'Scénario non trouvé'}.
    """
    rows = _db.query(
        conn,
        f'SELECT {_SCEN_COLS} FROM scenario WHERE id = %s',
        (scenario_id,),
    )
    if not rows:
        return {
            'error': 'Scénario non trouvé',
            'scenario_id': scenario_id,
            '_filtered_fields': [],
        }

    sanitized, filtered = sanitize_rows(rows, 'scenario')
    return wrap_result({'scenario': sanitized[0]}, filtered)


def get_scenario_structure(
    conn: pymysql.connections.Connection,
    scenario_id: int,
    max_depth: int = 3,
    follow_scenario_calls: int = 0,
) -> dict[str, Any]:
    """Arbre structurel brut d'un scénario (machine-friendly).

    Paramètres :
    - scenario_id           : identifiant du scénario
    - max_depth             : profondeur max de récursion des éléments (défaut 3)
    - follow_scenario_calls : niveaux de suivi des appels inter-scénarios (0 = désactivé)

    Retourne l'arbre de scenarioElement/scenarioSubElement/scenarioExpression.
    Pour une description lisible avec résolution des #[O][E][C]#, utilisez describe_scenario.
    """
    return _walker.walk(
        scenario_id,
        conn,
        max_depth=max_depth,
        follow_scenario_calls=follow_scenario_calls,
    )


def describe_scenario(
    conn: pymysql.connections.Connection,
    scenario_id: int,
) -> dict[str, Any]:
    """Description LLM-friendly d'un scénario avec résolution systématique des #[O][E][C]#.

    Paramètres :
    - scenario_id : identifiant du scénario

    Résout automatiquement toutes les références #cmdId# en #[Objet][Équipement][Commande]#
    dans les déclencheurs et les expressions du scénario.
    Pour l'arbre brut (machine-friendly), utilisez get_scenario_structure.
    """
    tree_result = _walker.walk(scenario_id, conn, follow_scenario_calls=0)

    if tree_result.get('scenario') is None:
        return tree_result

    scenario = tree_result['scenario']
    trigger_text = scenario.get('trigger', '') or ''

    texts: list[str] = []
    if trigger_text:
        texts.append(trigger_text)

    def _collect(nodes: list[dict]) -> None:
        for node in nodes:
            for sub in node.get('sub_elements', []):
                for expr in sub.get('expressions', []):
                    for field in ('expression', 'options'):
                        val = expr.get(field)
                        if val and isinstance(val, str):
                            texts.append(val)
            _collect(node.get('children', []))

    _collect(tree_result.get('tree', []))

    combined = '\n'.join(texts)
    resolved_result = _cmd_refs.resolve(combined, conn)
    mapping: dict[str, str] = resolved_result.get('mapping', {})

    def _resolve_text(text: str | None) -> str | None:
        if not text:
            return text

        def _replacer(m: re.Match) -> str:
            cid = m.group(1)
            return f'#{mapping[cid]}#' if cid in mapping else f'#ID_NON_RÉSOLU:{cid}#'

        return _ID_RE.sub(_replacer, text)

    def _humanize(nodes: list[dict]) -> list[dict]:
        result = []
        for node in nodes:
            human_node: dict[str, Any] = {
                'element_id': node['element_id'],
                'depth': node['depth'],
                'sub_elements': [],
            }
            for sub in node.get('sub_elements', []):
                human_sub: dict[str, Any] = {
                    'sub_id': sub['sub_id'],
                    'ss_type': sub['ss_type'],
                    'ss_subtype': sub['ss_subtype'],
                    'expressions': [],
                }
                for expr in sub.get('expressions', []):
                    human_expr = dict(expr)
                    for field in ('expression', 'options'):
                        val = expr.get(field)
                        if val and isinstance(val, str):
                            resolved = _resolve_text(val)
                            if resolved != val:
                                human_expr[f'{field}_resolved'] = resolved
                    human_sub['expressions'].append(human_expr)
                human_node['sub_elements'].append(human_sub)
            if node.get('children'):
                human_node['children'] = _humanize(node['children'])
            result.append(human_node)
        return result

    return {
        'scenario': {
            **scenario,
            'trigger_resolved': _resolve_text(trigger_text),
        },
        'blocks': _humanize(tree_result.get('tree', [])),
        'cmd_mapping': mapping,
        'unresolved_cmd_ids': resolved_result.get('unresolved', []),
        'truncated': tree_result.get('truncated', False),
        'warnings': tree_result.get('warnings', []),
    }


def find_scenario_dependencies(
    conn: pymysql.connections.Connection,
    scenario_id: int,
) -> dict[str, Any]:
    """Graphe d'usage d'un scénario : qui l'appelle, qui est appelé par lui.

    Paramètres :
    - scenario_id : identifiant du scénario

    Retourne les scénarios qui appellent ce scénario (via scenario/start).
    """
    return _usage_graph.resolve('scenario', scenario_id, conn)


def get_scenario_log(
    conn: pymysql.connections.Connection,
    scenario_id: int,
    lines: int = _LOG_LINES,
) -> dict[str, Any]:
    """Log du dernier run d'un scénario.

    Paramètres :
    - scenario_id : identifiant du scénario
    - lines       : nombre de lignes à retourner (défaut 100, max 500)

    Les logs de scénario sont stockés dans scenarioLog/scenario<id>.log.
    Retourne {'error': ...} si le fichier n'existe pas.
    """
    lines = min(lines, 500)
    log_name = f'scenarioLog/scenario{scenario_id}.log'
    return _logs.tail(log_name, lines=lines)
