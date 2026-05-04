"""Bootstrap du serveur MCP Holmes.

Construit l'instance FastMCP et enregistre les tools/resources.
J3-1 : Famille 1 — 4 tools découverte d'install.
J3-2 : Famille 2 — 7 tools équipements/commandes (à venir).
J3-3 : Famille 3 — 7 tools scénarios (à venir).
J5   : Famille 4-6 + query_sql + 5 resources (à venir).
"""

from __future__ import annotations

import argparse

import structlog
from _core import db as _db
from mcp.server.fastmcp import FastMCP
from tools import discovery

log = structlog.get_logger('holmesMcp.server')

_INSTRUCTIONS = (
    'Holmes observe, déduit, raconte. '
    'Il expose votre installation Jeedom en lecture seule : équipements, commandes, '
    'scénarios, plugins, logs. '
    'Il ne modifie jamais votre installation. '
    'Posez vos questions sur votre maison connectée.'
)


def build_mcp(args: argparse.Namespace) -> FastMCP:
    """Construit et retourne l'instance FastMCP configurée."""
    mcp = FastMCP(
        name='Holmes MCP',
        instructions=_INSTRUCTIONS,
        host='0.0.0.0',
        port=args.port,
    )

    _register_family1(mcp)

    log.info('mcp_initialized', families=[1], tools=4)
    return mcp


def _register_family1(mcp: FastMCP) -> None:
    """Famille 1 — Découverte d'install (4 tools)."""

    @mcp.tool()
    def get_install_overview() -> dict:
        """Snapshot général de l'installation Jeedom.

        Retourne la version Jeedom, les comptages globaux d'équipements (actifs/total),
        scénarios (actifs/total), plugins, objets et commandes.
        """
        conn = _db.connect()
        try:
            return discovery.get_install_overview(conn)
        finally:
            conn.close()

    @mcp.tool()
    def list_objects() -> dict:
        """Hiérarchie des objets/pièces Jeedom.

        Retourne la liste des objets triée par ordre d'affichage, avec leur père
        (father_id) pour reconstituer la hiérarchie pièces/sous-pièces.
        isVisible indique si l'objet est affiché dans le dashboard.
        """
        conn = _db.connect()
        try:
            return discovery.list_objects(conn)
        finally:
            conn.close()

    @mcp.tool()
    def list_plugins() -> dict:
        """Plugins installés avec version et état.

        Retourne la liste des plugins installés sur cette box Jeedom.
        Le champ state indique si le daemon du plugin est opérationnel (ok/nok).
        logical_id est l'identifiant technique du plugin (ex. 'jMQTT', 'holmesMcp').
        """
        conn = _db.connect()
        try:
            return discovery.list_plugins(conn)
        finally:
            conn.close()

    @mcp.tool()
    def get_config(plugin: str, key_pattern: str | None = None) -> dict:
        """Configuration Jeedom par namespace plugin (sanitisée).

        Paramètres :
        - plugin      : namespace du plugin dans la table config
                        (ex. 'core', 'jMQTT', 'holmesMcp', 'agenda')
        - key_pattern : filtre LIKE optionnel sur la colonne key
                        (ex. 'mqtt%', '%port%') — None retourne toutes les clés

        Les valeurs dont la clé est sensible (token, password, apikey…) sont
        automatiquement masquées (***FILTERED***). La clé reste visible.
        Limite : 200 entrées par appel.
        """
        conn = _db.connect()
        try:
            return discovery.get_config(conn, plugin, key_pattern)
        finally:
            conn.close()
