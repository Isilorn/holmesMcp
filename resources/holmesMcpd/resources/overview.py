"""Resource jeedom://install/overview — wrap strict de get_install_overview (D6.4)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tools import discovery

if TYPE_CHECKING:
    import pymysql.connections


def read(conn: pymysql.connections.Connection) -> dict[str, Any]:
    """Contenu de la resource jeedom://install/overview."""
    return discovery.get_install_overview(conn)
