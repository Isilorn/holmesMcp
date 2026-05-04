"""Famille 6 — Recherche transverse (1 tool).

Tool : search_text.
Canal : MySQL RO (jointures eqLogic / cmd / scenario / scenarioExpression).
Sanitisation : sanitize_rows via _domain.sanitize.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from _core import db as _db
from _domain.sanitize import sanitize_rows, wrap_result

if TYPE_CHECKING:
    import pymysql.connections

_SEARCH_LIMIT_EACH = 50
_SEARCH_MIN_LEN = 2


def search_text(
    conn: pymysql.connections.Connection,
    text: str,
    limit: int = 20,
) -> dict[str, Any]:
    """Recherche d'une chaîne dans les noms d'équipements, commandes, scénarios et expressions.

    Paramètre :
    - text  : texte à rechercher (minimum 2 caractères, insensible à la casse)
    - limit : nombre max de résultats par catégorie (défaut 20, max 50)

    Retourne quatre catégories :
    - equipements : équipements dont le nom contient text
    - commandes   : commandes dont le nom contient text
    - scenarios   : scénarios dont le nom contient text
    - expressions : expressions de scénarios dont le texte contient text
                    (utile pour retrouver les scénarios qui utilisent une commande donnée)

    Exemple : search_text('salon') retrouve l'équipement 'Prise Salon',
    la commande 'Lumière Salon ON', le scénario 'Réveil Salon', etc.
    """
    if not text or len(text) < _SEARCH_MIN_LEN:
        return {
            'error': f'Texte trop court — minimum {_SEARCH_MIN_LEN} caractères',
            '_filtered_fields': [],
        }

    limit = min(limit, _SEARCH_LIMIT_EACH)
    pattern = f'%{text}%'

    eq_rows = _db.query(
        conn,
        'SELECT id, name, eqType_name, object_id, isEnable, isVisible'
        ' FROM eqLogic WHERE name LIKE %s ORDER BY name LIMIT %s',
        (pattern, limit),
    )
    eq_sanitized, eq_filtered = sanitize_rows(eq_rows, 'eqLogic')

    cmd_rows = _db.query(
        conn,
        'SELECT id, name, eqLogic_id, type, subType, generic_type'
        ' FROM cmd WHERE name LIKE %s ORDER BY name LIMIT %s',
        (pattern, limit),
    )
    cmd_sanitized, cmd_filtered = sanitize_rows(cmd_rows, 'cmd')

    scen_rows = _db.query(
        conn,
        'SELECT id, name, `group`, isActive, mode'
        ' FROM scenario WHERE name LIKE %s ORDER BY name LIMIT %s',
        (pattern, limit),
    )
    scen_sanitized, scen_filtered = sanitize_rows(scen_rows, 'scenario')

    expr_rows = _db.query(
        conn,
        'SELECT id, subElement_id, type, expression'
        ' FROM scenarioExpression WHERE expression LIKE %s ORDER BY id LIMIT %s',
        (pattern, limit),
    )
    expr_sanitized, expr_filtered = sanitize_rows(expr_rows, 'scenarioExpression')

    all_filtered = list(
        dict.fromkeys(eq_filtered + cmd_filtered + scen_filtered + expr_filtered)
    )

    return wrap_result(
        {
            'query': text,
            'equipements': eq_sanitized,
            'commandes': cmd_sanitized,
            'scenarios': scen_sanitized,
            'expressions': expr_sanitized,
            'totals': {
                'equipements': len(eq_sanitized),
                'commandes': len(cmd_sanitized),
                'scenarios': len(scen_sanitized),
                'expressions': len(expr_sanitized),
            },
        },
        all_filtered,
    )
