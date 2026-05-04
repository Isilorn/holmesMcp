"""Famille 2 — Équipements et commandes (7 tools).

Tools : list_equipments, find_equipments_advanced, get_equipment,
        find_equipment_by_name, list_commands, find_commands_advanced,
        get_command_history.
Canal : MySQL RO exclusivement (tables eqLogic, cmd, history, historyArch).
Sanitisation : sanitize_rows / wrap_result via _domain.sanitize.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from _core import db as _db
from _domain.sanitize import sanitize_rows, wrap_result

if TYPE_CHECKING:
    import pymysql.connections

_EQ_LIMIT = 100
_EQ_LIMIT_ADV = 50
_CMD_LIMIT = 200
_CMD_LIMIT_ADV = 50
_HISTORY_LIMIT = 100


def list_equipments(
    conn: pymysql.connections.Connection,
    object_id: int | None = None,
    plugin: str | None = None,
    is_enable: bool | None = None,
    limit: int = _EQ_LIMIT,
    offset: int = 0,
) -> dict[str, Any]:
    """Liste des équipements filtrables par objet, plugin ou état actif.

    Paramètres :
    - object_id : filtre sur l'objet/pièce (id de la table object)
    - plugin     : filtre sur eqType_name (ex. 'jMQTT', 'thermostat')
    - is_enable  : True = uniquement les actifs, False = uniquement les désactivés
    - limit      : nombre max de résultats (max 100)
    - offset     : décalage pour la pagination

    Pour le détail d'un équipement (commandes + config), utilisez get_equipment.
    """
    conditions: list[str] = []
    params: list[Any] = []

    if object_id is not None:
        conditions.append('object_id = %s')
        params.append(object_id)
    if plugin is not None:
        conditions.append('eqType_name = %s')
        params.append(plugin)
    if is_enable is not None:
        conditions.append('isEnable = %s')
        params.append(1 if is_enable else 0)

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
    limit = min(limit, _EQ_LIMIT)
    params += [limit, offset]

    rows = _db.query(
        conn,
        f'SELECT id, name, eqType_name, object_id, isEnable, isVisible,'
        f' logicalId, generic_type, `order`, tags'
        f' FROM eqLogic {where} ORDER BY name LIMIT %s OFFSET %s',
        params,
    )
    sanitized, filtered = sanitize_rows(rows, 'eqLogic')
    return wrap_result(
        {'equipements': sanitized, 'total': len(sanitized), 'offset': offset},
        filtered,
    )


def find_equipments_advanced(
    conn: pymysql.connections.Connection,
    name_contains: str | None = None,
    object_id: int | None = None,
    plugin: str | None = None,
    is_enable: bool | None = None,
    generic_type: str | None = None,
    tags: str | None = None,
    limit: int = _EQ_LIMIT_ADV,
) -> dict[str, Any]:
    """Recherche avancée d'équipements avec filtres combinables.

    Paramètres :
    - name_contains : fragment de nom (insensible à la casse, LIKE %fragment%)
    - object_id     : filtre sur l'objet/pièce
    - plugin        : filtre sur eqType_name
    - is_enable     : True = actifs uniquement
    - generic_type  : type générique exact (ex. 'LIGHT', 'THERMOSTAT')
    - tags          : fragment de tag (LIKE %tag%)
    - limit         : max 50 résultats

    Pour la recherche par nom seul, préférez find_equipment_by_name.
    """
    conditions: list[str] = []
    params: list[Any] = []

    if name_contains is not None:
        conditions.append('name LIKE %s')
        params.append(f'%{name_contains}%')
    if object_id is not None:
        conditions.append('object_id = %s')
        params.append(object_id)
    if plugin is not None:
        conditions.append('eqType_name = %s')
        params.append(plugin)
    if is_enable is not None:
        conditions.append('isEnable = %s')
        params.append(1 if is_enable else 0)
    if generic_type is not None:
        conditions.append('generic_type = %s')
        params.append(generic_type)
    if tags is not None:
        conditions.append('tags LIKE %s')
        params.append(f'%{tags}%')

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
    limit = min(limit, _EQ_LIMIT_ADV)
    params.append(limit)

    rows = _db.query(
        conn,
        f'SELECT id, name, eqType_name, object_id, isEnable, isVisible,'
        f' logicalId, generic_type, `order`, tags'
        f' FROM eqLogic {where} ORDER BY name LIMIT %s',
        params,
    )
    sanitized, filtered = sanitize_rows(rows, 'eqLogic')
    return wrap_result({'equipements': sanitized, 'total': len(sanitized)}, filtered)


def get_equipment(
    conn: pymysql.connections.Connection,
    equipment_id: int,
) -> dict[str, Any]:
    """Détail complet d'un équipement : structure, config sanitisée et commandes.

    Paramètres :
    - equipment_id : identifiant numérique de l'équipement (table eqLogic.id)

    Retourne l'équipement avec :
    - toutes ses métadonnées (configuration sanitisée, statut, tags)
    - la liste complète de ses commandes

    Si l'équipement n'existe pas, retourne {'error': 'Équipement non trouvé'}.
    """
    eq_rows = _db.query(
        conn,
        'SELECT id, name, eqType_name, object_id, isEnable, isVisible, logicalId,'
        ' generic_type, `order`, tags, category, timeout, comment, status, configuration'
        ' FROM eqLogic WHERE id = %s',
        (equipment_id,),
    )
    if not eq_rows:
        return {
            'error': 'Équipement non trouvé',
            'equipment_id': equipment_id,
            '_filtered_fields': [],
        }

    eq_sanitized, eq_filtered = sanitize_rows(eq_rows, 'eqLogic')

    cmd_rows = _db.query(
        conn,
        'SELECT id, name, eqLogic_id, type, subType, logicalId, generic_type,'
        ' isVisible, unite, isHistorized, display, `order`, value, configuration, template'
        ' FROM cmd WHERE eqLogic_id = %s ORDER BY `order`',
        (equipment_id,),
    )
    cmd_sanitized, cmd_filtered = sanitize_rows(cmd_rows, 'cmd')

    all_filtered = sorted(set(eq_filtered + cmd_filtered))
    return wrap_result(
        {
            'equipment': eq_sanitized[0],
            'commandes': cmd_sanitized,
            'nb_commandes': len(cmd_sanitized),
        },
        all_filtered,
    )


def find_equipment_by_name(
    conn: pymysql.connections.Connection,
    name: str,
    limit: int = 10,
) -> dict[str, Any]:
    """Recherche un équipement par son nom (partiel, insensible à la casse).

    Paramètres :
    - name  : fragment de nom à rechercher
    - limit : max de résultats (par défaut 10, max 50)

    Exemple : name='salon' trouve 'Thermostat Salon', 'Prise Salon', etc.
    """
    limit = min(limit, _EQ_LIMIT_ADV)
    rows = _db.query(
        conn,
        'SELECT id, name, eqType_name, object_id, isEnable, isVisible,'
        ' logicalId, generic_type, `order`, tags'
        ' FROM eqLogic WHERE name LIKE %s ORDER BY name LIMIT %s',
        (f'%{name}%', limit),
    )
    sanitized, filtered = sanitize_rows(rows, 'eqLogic')
    return wrap_result(
        {'equipements': sanitized, 'total': len(sanitized), 'query': name},
        filtered,
    )


def list_commands(
    conn: pymysql.connections.Connection,
    equipment_id: int,
    cmd_type: str | None = None,
    limit: int = _CMD_LIMIT,
    offset: int = 0,
) -> dict[str, Any]:
    """Liste des commandes d'un équipement.

    Paramètres :
    - equipment_id : identifiant de l'équipement (eqLogic.id)
    - cmd_type     : filtre optionnel sur le type ('info' ou 'action')
    - limit        : max 200 commandes
    - offset       : décalage pour la pagination

    Pour la recherche transverse de commandes, utilisez find_commands_advanced.
    """
    params: list[Any] = [equipment_id]
    type_clause = ''
    if cmd_type is not None:
        type_clause = ' AND type = %s'
        params.append(cmd_type)

    limit = min(limit, _CMD_LIMIT)
    params += [limit, offset]

    rows = _db.query(
        conn,
        'SELECT id, name, eqLogic_id, type, subType, logicalId, generic_type,'
        f' isVisible, unite, isHistorized, display, `order`, value, configuration, template'
        f' FROM cmd WHERE eqLogic_id = %s{type_clause} ORDER BY `order` LIMIT %s OFFSET %s',
        params,
    )
    sanitized, filtered = sanitize_rows(rows, 'cmd')
    return wrap_result(
        {
            'commandes': sanitized,
            'total': len(sanitized),
            'equipment_id': equipment_id,
            'offset': offset,
        },
        filtered,
    )


def find_commands_advanced(
    conn: pymysql.connections.Connection,
    name_contains: str | None = None,
    equipment_id: int | None = None,
    cmd_type: str | None = None,
    subtype: str | None = None,
    generic_type: str | None = None,
    is_historized: bool | None = None,
    limit: int = _CMD_LIMIT_ADV,
) -> dict[str, Any]:
    """Recherche avancée de commandes avec filtres combinables.

    Paramètres :
    - name_contains : fragment de nom (LIKE %fragment%)
    - equipment_id  : restreindre à un équipement
    - cmd_type      : 'info' ou 'action'
    - subtype       : sous-type (ex. 'numeric', 'binary', 'string', 'slider', 'message')
    - generic_type  : type générique (ex. 'TEMPERATURE', 'HUMIDITY', 'LIGHT_STATE')
    - is_historized : True = uniquement les commandes historisées
    - limit         : max 50 résultats
    """
    conditions: list[str] = []
    params: list[Any] = []

    if name_contains is not None:
        conditions.append('name LIKE %s')
        params.append(f'%{name_contains}%')
    if equipment_id is not None:
        conditions.append('eqLogic_id = %s')
        params.append(equipment_id)
    if cmd_type is not None:
        conditions.append('type = %s')
        params.append(cmd_type)
    if subtype is not None:
        conditions.append('subType = %s')
        params.append(subtype)
    if generic_type is not None:
        conditions.append('generic_type = %s')
        params.append(generic_type)
    if is_historized is not None:
        conditions.append('isHistorized = %s')
        params.append(1 if is_historized else 0)

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
    limit = min(limit, _CMD_LIMIT_ADV)
    params.append(limit)

    rows = _db.query(
        conn,
        f'SELECT id, name, eqLogic_id, type, subType, logicalId, generic_type,'
        f' isVisible, unite, isHistorized, display, `order`, value, configuration, template'
        f' FROM cmd {where} ORDER BY name LIMIT %s',
        params,
    )
    sanitized, filtered = sanitize_rows(rows, 'cmd')
    return wrap_result({'commandes': sanitized, 'total': len(sanitized)}, filtered)


def get_command_history(
    conn: pymysql.connections.Connection,
    cmd_id: int,
    limit: int = _HISTORY_LIMIT,
) -> dict[str, Any]:
    """Historique d'une commande info : récent (history) + archivé (historyArch).

    Paramètres :
    - cmd_id : identifiant de la commande (cmd.id)
    - limit  : max de lignes par table (défaut 100, max 100)

    Retourne deux listes séparées triées par datetime décroissant :
    - history_recent   : entrées de la table history (plus récentes)
    - history_archived : entrées de la table historyArch (plus anciennes)
    """
    limit = min(limit, _HISTORY_LIMIT)

    recent_rows = _db.query(
        conn,
        'SELECT id, cmd_id, datetime, value FROM history'
        ' WHERE cmd_id = %s ORDER BY datetime DESC LIMIT %s',
        (cmd_id, limit),
    )
    arch_rows = _db.query(
        conn,
        'SELECT id, cmd_id, datetime, value FROM historyArch'
        ' WHERE cmd_id = %s ORDER BY datetime DESC LIMIT %s',
        (cmd_id, limit),
    )

    recent_sanitized, recent_filtered = sanitize_rows(recent_rows, 'history')
    arch_sanitized, arch_filtered = sanitize_rows(arch_rows, 'historyArch')
    all_filtered = sorted(set(recent_filtered + arch_filtered))

    return wrap_result(
        {
            'cmd_id': cmd_id,
            'history_recent': recent_sanitized,
            'history_archived': arch_sanitized,
            'total_recent': len(recent_sanitized),
            'total_archived': len(arch_sanitized),
        },
        all_filtered,
    )
