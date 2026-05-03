"""Bootstrap du serveur MCP Holmes.

Construit l'instance FastMCP et enregistre les tools/resources.
POC J0 : un seul tool `hello` pour valider l'intégration complète.
J3+ : import des modules tools/ et resources/ au fur et à mesure.
"""

from __future__ import annotations

import argparse

import structlog
from mcp.server.fastmcp import FastMCP

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

    _register_poc_tools(mcp)

    log.info('mcp_initialized', tool='hello')
    return mcp


def _register_poc_tools(mcp: FastMCP) -> None:
    """Tools POC J0 — remplacés par les 25 tools V1 à partir de J3."""

    @mcp.tool()
    def hello(name: str = 'Jeedom') -> str:
        """[POC J0] Vérifie que le serveur MCP Holmes est opérationnel.

        Retourne un message de confirmation. Ce tool est temporaire et sera
        remplacé par les 25 tools V1 à partir du jalon J3.
        """
        return (
            f'Holmes MCP opérationnel — serveur connecté à {name}. '
            'POC J0 validé. Les 25 tools V1 seront disponibles à partir du jalon J3.'
        )
