"""Famille 5 — Logs et diagnostic (3 tools).

Tools : list_log_files, tail_log, get_health_summary.
Canaux :
  - list_log_files : lecture fichiers locaux via _core/logs
  - tail_log       : lecture fichiers locaux via _core/logs
  - get_health_summary : MySQL RO (tables update, message, cron)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from _core import db as _db
from _core import logs as _logs

if TYPE_CHECKING:
    import pymysql.connections

_TAIL_MAX_LINES = 500


def list_log_files() -> dict[str, Any]:
    """Liste des fichiers de log Jeedom disponibles avec taille et date de modification.

    Retourne tous les logs accessibles dans les répertoires Jeedom connus
    (/var/www/html/log et /usr/share/nginx/www/jeedom/log).
    Le champ name est utilisable directement avec tail_log.
    Les fichiers de sous-répertoires (ex. scenarioLog/scenario70.log) sont inclus.
    """
    files = _logs.list_files()
    return {'log_files': files, 'total': len(files)}


def tail_log(
    log_name: str,
    lines: int = 100,
    grep: str | None = None,
) -> dict[str, Any]:
    """Tail d'un log Jeedom avec grep optionnel.

    Paramètres :
    - log_name : nom du fichier de log (ex. 'core', 'jMQTT', 'scenarioLog/scenario70.log')
                 Utiliser list_log_files pour connaître les logs disponibles.
    - lines    : nombre de lignes à retourner depuis la fin (défaut 100, max 500)
    - grep     : filtre optionnel — seules les lignes contenant ce texte sont retournées
                 (insensible à la casse)

    Retourne {'log_file': ..., 'lines': [...], 'count': N}.
    Retourne {'error': ..., 'lines': [], 'count': 0} si le log est introuvable.
    """
    lines = min(lines, _TAIL_MAX_LINES)
    return _logs.tail(log_name, lines=lines, grep=grep)


def get_health_summary(conn: pymysql.connections.Connection) -> dict[str, Any]:
    """Résumé de santé Jeedom : daemons KO, messages système récents, crons daemon actifs,
    commandes mortes et qualité d'historique.

    Interroge cinq sources MySQL :
    - Plugins avec daemon en panne (table update, status='nok')
    - 20 messages système les plus récents (table message)
    - Crons de type daemon actifs et activés (table cron, deamon=1 AND enable=1)
    - Commandes mortes : commandes dont l'équipement est désactivé ou supprimé (LIMIT 200)
    - Qualité historique : nombre de commandes info historisées sans aucune donnée

    Aucune donnée sensible — résumé diagnostique sans credentials.
    Si toutes les listes sont vides et les comptages à zéro, l'installation est saine.
    """
    plugins_nok_rows = _db.query(
        conn,
        'SELECT logicalId AS plugin, name, status FROM `update`'
        " WHERE type='plugin' AND status='nok' ORDER BY name",
    )

    messages_rows = _db.query(
        conn,
        'SELECT plugin, logicalId, `message`, `date` FROM message ORDER BY `date` DESC LIMIT 20',
    )

    crons_rows = _db.query(
        conn,
        'SELECT class, `function`, schedule FROM cron WHERE deamon=1 AND enable=1 ORDER BY class',
    )

    dead_cmd_rows = _db.query(
        conn,
        'SELECT c.id, c.name, c.eqLogic_id'
        ' FROM cmd c'
        ' LEFT JOIN eqLogic e ON c.eqLogic_id = e.id'
        ' WHERE e.id IS NULL OR e.isEnable = 0'
        ' ORDER BY c.eqLogic_id LIMIT 200',
    )

    history_quality_rows = _db.query(
        conn,
        'SELECT COUNT(*) AS cmd_info_sans_historique'
        ' FROM cmd c'
        " WHERE c.type = 'info'"
        ' AND c.isHistorized = 1'
        ' AND NOT EXISTS (SELECT 1 FROM history h WHERE h.cmd_id = c.id)',
    )

    plugins_nok = [dict(r) for r in plugins_nok_rows]
    messages = [
        {
            'plugin': r['plugin'],
            'logicalId': r['logicalId'],
            'message': r['message'],
            'date': str(r['date']) if r['date'] is not None else None,
        }
        for r in messages_rows
    ]
    crons_running = [
        {
            'class': r['class'],
            'function': r['function'],
            'schedule': r['schedule'],
        }
        for r in crons_rows
    ]
    dead_commands = [
        {'id': r['id'], 'name': r['name'], 'eqLogic_id': r['eqLogic_id']}
        for r in dead_cmd_rows
    ]
    historized_without_data = int(
        history_quality_rows[0]['cmd_info_sans_historique']
        if history_quality_rows
        else 0
    )

    return {
        'plugins_nok': plugins_nok,
        'messages_unread': messages,
        'crons_running': crons_running,
        'dead_commands': dead_commands,
        'summary': {
            'plugins_nok_count': len(plugins_nok),
            'messages_unread_count': len(messages),
            'crons_running_count': len(crons_running),
            'dead_commands_count': len(dead_commands),
            'historized_cmds_without_data': historized_without_data,
        },
        '_filtered_fields': [],
    }
