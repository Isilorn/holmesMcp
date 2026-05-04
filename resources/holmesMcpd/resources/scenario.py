"""Resource jeedom://scenario/{id} — combine describe_scenario + get_scenario_log (D6.2)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tools import scenarios as scenarios_tools

if TYPE_CHECKING:
    import pymysql.connections

_LOG_LINES = 50


def read(
    conn: pymysql.connections.Connection,
    scenario_id: int,
    apikey: str = '',
) -> dict[str, Any]:
    """Contenu de la resource jeedom://scenario/{scenario_id}.

    Combine describe_scenario (description LLM-friendly + état runtime) et
    les 50 dernières lignes du log du dernier run.
    """
    result = scenarios_tools.describe_scenario(conn, scenario_id, apikey)
    log_data = scenarios_tools.get_scenario_log(conn, scenario_id, lines=_LOG_LINES)
    return {**result, 'last_run_log': log_data}
