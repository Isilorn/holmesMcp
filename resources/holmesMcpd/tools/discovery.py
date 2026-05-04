"""Famille 1 — Découverte d'install (4 tools).

Tools : get_install_overview, list_objects, list_plugins, get_config.
Canal : MySQL RO exclusivement (données structurelles).
Sanitisation : sanitize_rows / _sanitize_config_row via _domain.sanitize.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from _core import db as _db
from _domain.sanitize import sanitize_rows, wrap_result

if TYPE_CHECKING:
    import pymysql.connections

_CONFIG_LIMIT = 200
_OBJECTS_LIMIT = 500
_PLUGINS_LIMIT = 200


def get_install_overview(conn: pymysql.connections.Connection) -> dict[str, Any]:
    """Snapshot général de l'installation Jeedom.

    Retourne la version Jeedom, les comptages globaux d'équipements (actifs/total),
    scénarios (actifs/total), plugins, objets et commandes.
    Aucune donnée sensible — pas de sanitisation requise sur les comptages.
    """
    version_rows = _db.query(
        conn,
        "SELECT value FROM config WHERE plugin='core' AND `key`='version'",
    )
    version: str = version_rows[0]['value'] if version_rows else 'inconnu'

    eq_total: int = _db.query(conn, 'SELECT COUNT(*) AS n FROM eqLogic')[0]['n']
    eq_active: int = _db.query(conn, 'SELECT COUNT(*) AS n FROM eqLogic WHERE isEnable=1')[0]['n']
    scen_total: int = _db.query(conn, 'SELECT COUNT(*) AS n FROM scenario')[0]['n']
    scen_active: int = _db.query(conn, 'SELECT COUNT(*) AS n FROM scenario WHERE isActive=1')[0][
        'n'
    ]
    plugin_count: int = _db.query(
        conn, "SELECT COUNT(*) AS n FROM `update` WHERE type='plugin'"
    )[0]['n']
    object_count: int = _db.query(conn, 'SELECT COUNT(*) AS n FROM object')[0]['n']
    cmd_count: int = _db.query(conn, 'SELECT COUNT(*) AS n FROM cmd')[0]['n']

    return {
        'jeedom_version': version,
        'equipements': {'total': eq_total, 'actifs': eq_active},
        'scenarios': {'total': scen_total, 'actifs': scen_active},
        'plugins': plugin_count,
        'objets': object_count,
        'commandes': cmd_count,
        '_filtered_fields': [],
    }


def list_objects(conn: pymysql.connections.Connection) -> dict[str, Any]:
    """Hiérarchie des objets/pièces Jeedom.

    Retourne la liste des objets triée par ordre d'affichage, avec leur père
    (father_id) pour reconstituer la hiérarchie pièces/sous-pièces.
    isVisible indique si l'objet est affiché dans le dashboard.
    """
    rows = _db.query(
        conn,
        'SELECT id, name, father_id, isVisible, position FROM object ORDER BY position LIMIT %s',
        (_OBJECTS_LIMIT,),
    )
    sanitized, filtered = sanitize_rows(rows, 'object')
    return wrap_result({'objects': sanitized, 'total': len(sanitized)}, filtered)


def list_plugins(conn: pymysql.connections.Connection) -> dict[str, Any]:
    """Plugins installés avec version et état.

    Retourne la liste des plugins installés sur cette box Jeedom.
    Le champ state indique si le daemon du plugin est opérationnel (ok/nok).
    logical_id est l'identifiant technique du plugin (ex. 'jMQTT', 'holmesMcp').
    """
    rows = _db.query(
        conn,
        'SELECT id, name, localVersion AS version, status AS state, logicalId AS logical_id'
        " FROM `update` WHERE type='plugin' ORDER BY name LIMIT %s",
        (_PLUGINS_LIMIT,),
    )
    sanitized, filtered = sanitize_rows(rows, 'plugin')
    return wrap_result({'plugins': sanitized, 'total': len(sanitized)}, filtered)


def get_config(
    conn: pymysql.connections.Connection,
    plugin: str | None = None,
    key_pattern: str | None = None,
) -> dict[str, Any]:
    """Configuration Jeedom par namespace plugin (sanitisée).

    Paramètres :
    - plugin      : namespace du plugin dans la table config
                    (ex. 'core', 'jMQTT', 'holmesMcp', 'agenda').
                    None ou '*' retourne tous les namespaces.
    - key_pattern : filtre LIKE optionnel sur la colonne key
                    (ex. 'mqtt%', '%port%') — None retourne toutes les clés

    Les valeurs dont la clé est sensible (token, password, apikey…) sont
    automatiquement masquées (***FILTERED***). La clé reste visible pour
    que le LLM puisse expliquer à l'utilisateur que le champ existe.
    Limite : 200 entrées par appel.
    """
    all_plugins = plugin is None or plugin == '*'

    if all_plugins and key_pattern:
        rows = _db.query(
            conn,
            'SELECT plugin, `key`, value FROM config'
            ' WHERE `key` LIKE %s ORDER BY plugin, `key` LIMIT %s',
            (key_pattern, _CONFIG_LIMIT),
        )
    elif all_plugins:
        rows = _db.query(
            conn,
            'SELECT plugin, `key`, value FROM config ORDER BY plugin, `key` LIMIT %s',
            (_CONFIG_LIMIT,),
        )
    elif key_pattern:
        rows = _db.query(
            conn,
            'SELECT plugin, `key`, value FROM config'
            ' WHERE plugin=%s AND `key` LIKE %s ORDER BY `key` LIMIT %s',
            (plugin, key_pattern, _CONFIG_LIMIT),
        )
    else:
        rows = _db.query(
            conn,
            'SELECT plugin, `key`, value FROM config WHERE plugin=%s ORDER BY `key` LIMIT %s',
            (plugin, _CONFIG_LIMIT),
        )
    sanitized, filtered = sanitize_rows(rows, 'config')
    return wrap_result(
        {
            'plugin': plugin if not all_plugins else '*',
            'key_pattern': key_pattern,
            'config': sanitized,
            'total': len(sanitized),
        },
        filtered,
    )
