"""Resource jeedom://logs/today — wrap de tail_log sur le log core Jeedom (D6.2)."""

from __future__ import annotations

from typing import Any

from tools import logs as logs_tools

_LOG_NAME = 'http'
_LINES = 500


def read() -> dict[str, Any]:
    """Contenu de la resource jeedom://logs/today.

    Retourne les 500 dernières lignes du log core Jeedom ('http').
    Approximation best-effort de l'activité du jour — aucun filtrage
    temporel appliqué (tail sur le fichier courant).
    """
    return logs_tools.tail_log(_LOG_NAME, lines=_LINES, grep=None)
