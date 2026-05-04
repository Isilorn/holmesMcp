"""Résolution batch de #cmdId# → #[Objet][Équipement][Commande]# dans du texte.

Dérivé de jeedom-audit/resolve_cmd_refs.py — db_query.py → _core/db.py (PyMySQL local).
"""

from __future__ import annotations

import re

import structlog
from _core import db

log = structlog.get_logger('holmesMcp.domain.cmd_refs')

_ID_PATTERN = re.compile(r'#(\d+)#')

_RESOLVE_SQL = (
    'SELECT c.id, COALESCE(o.name, \'\') AS objet, e.name AS equipement, c.name AS commande'
    ' FROM cmd c'
    ' JOIN eqLogic e ON c.eqLogic_id = e.id'
    ' LEFT JOIN object o ON e.object_id = o.id'
    ' WHERE c.id IN ({placeholders})'
)


def _fetch_names(ids: list[int], conn) -> dict[int, str]:
    """Requête SQL batch → {cmd_id: '[O][E][C]'}."""
    placeholders = ', '.join(['%s'] * len(ids))
    sql = _RESOLVE_SQL.format(placeholders=placeholders)
    rows = db.query(conn, sql, tuple(ids))
    result: dict[int, str] = {}
    for row in rows:
        cmd_id = int(row['id'])
        label = (
            f"[{row.get('objet') or ''}]"
            f"[{row.get('equipement') or ''}]"
            f"[{row.get('commande') or ''}]"
        )
        result[cmd_id] = label
    log.debug('cmd_refs_fetched', found=len(result), requested=len(ids))
    return result


def resolve(text: str, conn) -> dict:
    """Résout tous les #cmdId# numériques dans *text* via une requête SQL batch.

    Returns:
        resolved   : texte avec #ID# remplacés par #[O][E][C]# ou #ID_NON_RÉSOLU:X#
        mapping    : {str(id): "[O][E][C]"} pour les IDs résolus
        unresolved : IDs absents de la DB (liste d'entiers triée)
    """
    ids_found = {int(m.group(1)) for m in _ID_PATTERN.finditer(text)}

    if not ids_found:
        return {'resolved': text, 'mapping': {}, 'unresolved': []}

    mapping = _fetch_names(list(ids_found), conn)

    str_mapping: dict[str, str] = {str(k): v for k, v in mapping.items()}
    unresolved = sorted(i for i in ids_found if i not in mapping)

    def _replacer(m: re.Match) -> str:
        cmd_id = int(m.group(1))
        if cmd_id in mapping:
            return f'#{mapping[cmd_id]}#'
        return f'#ID_NON_RÉSOLU:{cmd_id}#'

    return {
        'resolved': _ID_PATTERN.sub(_replacer, text),
        'mapping': str_mapping,
        'unresolved': unresolved,
    }
