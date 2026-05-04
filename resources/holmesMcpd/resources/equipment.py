"""Resource jeedom://equipment/{id} — wrap strict de get_equipment (D6.4)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tools import equipments as equipments_tools

if TYPE_CHECKING:
    import pymysql.connections


def read(
    conn: pymysql.connections.Connection,
    equipment_id: int,
    apikey: str = '',
) -> dict[str, Any]:
    """Contenu de la resource jeedom://equipment/{equipment_id}."""
    return equipments_tools.get_equipment(conn, equipment_id, apikey)
