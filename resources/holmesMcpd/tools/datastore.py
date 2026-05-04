"""Famille 4 — Variables / dataStore (2 tools).

Tools : list_datastore_variables, get_datastore_variable.
Canal : MySQL RO exclusivement (table dataStore).
Sanitisation : sanitize_rows / wrap_result via _domain.sanitize.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from _core import db as _db
from _domain.sanitize import sanitize_rows, wrap_result

if TYPE_CHECKING:
    import pymysql.connections

_DATASTORE_LIMIT = 200


def list_datastore_variables(
    conn: pymysql.connections.Connection,
    var_type: str | None = None,
    link_id: int | None = None,
    key_pattern: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Variables persistantes Jeedom (table dataStore).

    Paramètres :
    - var_type    : filtre exact sur le type ('global' pour variables globales,
                    'scenario' pour variables scénario)
    - link_id     : filtre sur l'identifiant lié (ex. scenario_id pour type='scenario',
                    0 pour les variables globales)
    - key_pattern : filtre LIKE sur le nom de variable (ex. 'meteo%', '%temp%')
    - limit       : nombre max de résultats (max 200)
    - offset      : décalage pour la pagination

    Les variables globales ont type='global' et link_id=0.
    Les variables de scénario ont type='scenario' et link_id=<scenario_id>.
    """
    conditions: list[str] = []
    params: list[Any] = []

    if var_type is not None:
        conditions.append('type=%s')
        params.append(var_type)
    if link_id is not None:
        conditions.append('link_id=%s')
        params.append(link_id)
    if key_pattern is not None:
        conditions.append('`key` LIKE %s')
        params.append(key_pattern)

    where = (' WHERE ' + ' AND '.join(conditions)) if conditions else ''
    limit = min(limit, _DATASTORE_LIMIT)
    params.extend([limit, offset])

    rows = _db.query(
        conn,
        f'SELECT id, type, link_id, `key`, value FROM dataStore{where}'
        ' ORDER BY type, `key` LIMIT %s OFFSET %s',
        tuple(params),
    )
    sanitized, filtered = sanitize_rows(rows, 'dataStore')
    return wrap_result({'variables': sanitized, 'total': len(sanitized)}, filtered)


def get_datastore_variable(
    conn: pymysql.connections.Connection,
    key: str,
    var_type: str | None = None,
    link_id: int | None = None,
) -> dict[str, Any]:
    """Valeur courante d'une variable dataStore par nom de clé.

    Paramètres :
    - key      : nom exact de la variable (ex. 'temperature_salon', 'alarme_active')
    - var_type : restreindre au type ('global' ou 'scenario') si plusieurs variables
                 partagent le même nom
    - link_id  : restreindre à un scenario_id si var_type='scenario'

    Retourne {'error': ...} si la variable n'existe pas.
    Si plusieurs variables correspondent (même nom, types différents), retourne la liste.
    """
    conditions: list[str] = ['`key`=%s']
    params: list[Any] = [key]

    if var_type is not None:
        conditions.append('type=%s')
        params.append(var_type)
    if link_id is not None:
        conditions.append('link_id=%s')
        params.append(link_id)

    where = ' WHERE ' + ' AND '.join(conditions)
    rows = _db.query(
        conn,
        f'SELECT id, type, link_id, `key`, value FROM dataStore{where} LIMIT 20',
        tuple(params),
    )

    if not rows:
        return {'error': f'Variable {key!r} introuvable', '_filtered_fields': []}

    sanitized, filtered = sanitize_rows(rows, 'dataStore')
    return wrap_result({'key': key, 'variables': sanitized, 'total': len(sanitized)}, filtered)
