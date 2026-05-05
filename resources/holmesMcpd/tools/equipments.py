"""Famille 2 — Équipements et commandes (8 tools).

Tools : list_equipments, find_equipments_advanced, get_equipment,
        find_equipment_by_name, list_commands, find_commands_advanced,
        get_command_history, find_command_usages.
Canal : MySQL RO exclusivement (tables eqLogic, cmd, history, historyArch,
        scenario, scenarioExpression, scenarioSubElement, scenarioElement, dataStore).
        Enrichissement runtime : API JSON-RPC (currentValue, collectDate) via _core/api.
Sanitisation : sanitize_rows / wrap_result via _domain.sanitize.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from _core import api as _api
from _core import db as _db
from _domain.sanitize import sanitize_rows, wrap_result

if TYPE_CHECKING:
    import pymysql.connections

_EQ_LIMIT = 100
_EQ_LIMIT_ADV = 50
_CMD_LIMIT = 200
_CMD_LIMIT_ADV = 50
_HISTORY_LIMIT = 100
_CMD_USAGES_LIMIT = 50


# ── Helpers runtime API ───────────────────────────────────────────────────────


def _fetch_cmd_runtime_map(apikey: str, equipment_id: int) -> dict[int, dict]:
    """One call to eqLogic::fullById → {cmd_id: {currentValue, collectDate}}. Returns {} on error.
    """
    if not apikey:
        return {}
    resp = _api.call(apikey, 'eqLogic::fullById', {'id': equipment_id})
    result = resp.get('result')
    if not isinstance(result, dict):
        return {}
    cmds = result.get('cmds', [])
    if not isinstance(cmds, list):
        return {}
    mapping: dict[int, dict] = {}
    for cmd in cmds:
        try:
            cid = int(cmd.get('id', 0))
            if cid:
                mapping[cid] = {
                    'currentValue': cmd.get('currentValue'),
                    'collectDate': cmd.get('collectDate'),
                }
        except (TypeError, ValueError):
            pass
    return mapping


def _inject_cmd_runtime(cmds: list[dict], runtime_map: dict[int, dict]) -> None:
    """Injects currentValue/collectDate for info cmds in place."""
    for cmd in cmds:
        if cmd.get('type') != 'info':
            continue
        cid = cmd.get('id')
        if cid is not None and cid in runtime_map:
            rt = runtime_map[cid]
            cmd['currentValue'] = rt['currentValue']
            cmd['collectDate'] = rt['collectDate']


# ── Tools ─────────────────────────────────────────────────────────────────────


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
    apikey: str = '',
) -> dict[str, Any]:
    """Détail complet d'un équipement : structure, config sanitisée, commandes et valeurs courantes.

    Paramètres :
    - equipment_id : identifiant numérique de l'équipement (table eqLogic.id)
    - apikey       : clé API JSON-RPC Jeedom (enrichit currentValue + collectDate si fournie)

    Retourne l'équipement avec :
    - toutes ses métadonnées (configuration sanitisée, statut, tags)
    - la liste complète de ses commandes
    - pour les commandes de type info : currentValue et collectDate (via API JSON-RPC)

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

    runtime_map = _fetch_cmd_runtime_map(apikey, equipment_id)
    if runtime_map:
        _inject_cmd_runtime(cmd_sanitized, runtime_map)

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
    apikey: str = '',
) -> dict[str, Any]:
    """Liste des commandes d'un équipement avec valeurs courantes.

    Paramètres :
    - equipment_id : identifiant de l'équipement (eqLogic.id)
    - cmd_type     : filtre optionnel sur le type ('info' ou 'action')
    - limit        : max 200 commandes
    - offset       : décalage pour la pagination
    - apikey       : clé API JSON-RPC Jeedom (enrichit currentValue + collectDate si fournie)

    Pour les commandes de type info, currentValue et collectDate sont ajoutés
    via l'API JSON-RPC (données runtime absentes de MySQL).
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

    runtime_map = _fetch_cmd_runtime_map(apikey, equipment_id)
    if runtime_map:
        _inject_cmd_runtime(sanitized, runtime_map)

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
        'SELECT cmd_id, datetime, value FROM history'
        ' WHERE cmd_id = %s ORDER BY datetime DESC LIMIT %s',
        (cmd_id, limit),
    )
    arch_rows = _db.query(
        conn,
        'SELECT cmd_id, datetime, value FROM historyArch'
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


def find_command_usages(
    conn: pymysql.connections.Connection,
    cmd_id: int,
    limit: int = _CMD_USAGES_LIMIT,
) -> dict[str, Any]:
    """Retourne tous les endroits où une commande est référencée dans l'installation.

    Paramètres :
    - cmd_id : identifiant de la commande (cmd.id)
    - limit  : max de résultats par catégorie (défaut 50, max 50)

    Retourne trois catégories :
    - triggers    : scénarios qui ont cette commande en déclencheur (champ trigger)
    - expressions : scénarios qui l'utilisent dans conditions ou actions
    - datastore   : variables dataStore dont la valeur référence cette commande

    Le pattern de recherche est #cmdId# (format de référence Jeedom).
    Pour explorer les expressions détaillées, utilisez get_scenario_structure(scenario_id).
    """
    limit = min(limit, _CMD_USAGES_LIMIT)
    pattern = f'%#{cmd_id}#%'

    trigger_rows = _db.query(
        conn,
        'SELECT id, name, isActive, `trigger`'
        ' FROM scenario WHERE `trigger` LIKE %s LIMIT %s',
        (pattern, limit),
    )
    trigger_sanitized, trigger_filtered = sanitize_rows(trigger_rows, 'scenario')

    expr_rows = _db.query(
        conn,
        'SELECT DISTINCT s.id, s.name, s.isActive,'
        ' expr.type AS expr_type, expr.expression'
        ' FROM scenarioExpression expr'
        ' JOIN scenarioSubElement ss ON expr.scenarioSubElement_id = ss.id'
        ' JOIN scenarioElement sel   ON ss.scenarioElement_id = sel.id'
        ' JOIN scenario s            ON JSON_CONTAINS(s.scenarioElement, CAST(sel.id AS JSON))'
        ' WHERE expr.expression LIKE %s'
        ' LIMIT %s',
        (pattern, limit),
    )
    expr_sanitized, expr_filtered = sanitize_rows(expr_rows)

    datastore_rows = _db.query(
        conn,
        'SELECT `key`, value, type, link_id'
        ' FROM dataStore WHERE value LIKE %s LIMIT %s',
        (pattern, limit),
    )
    datastore_sanitized, datastore_filtered = sanitize_rows(datastore_rows, 'dataStore')

    all_filtered = sorted(set(trigger_filtered + expr_filtered + datastore_filtered))

    return wrap_result(
        {
            'cmd_id': cmd_id,
            'triggers': trigger_sanitized,
            'expressions': expr_sanitized,
            'datastore': datastore_sanitized,
            'total_triggers': len(trigger_sanitized),
            'total_expressions': len(expr_sanitized),
            'total_datastore': len(datastore_sanitized),
        },
        all_filtered,
    )
