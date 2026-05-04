"""Resource jeedom://install/health — wrap strict de get_health_summary (D6.4)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tools import logs as logs_tools

if TYPE_CHECKING:
    import pymysql.connections


def read(conn: pymysql.connections.Connection) -> dict[str, Any]:
    """Contenu de la resource jeedom://install/health."""
    return logs_tools.get_health_summary(conn)
