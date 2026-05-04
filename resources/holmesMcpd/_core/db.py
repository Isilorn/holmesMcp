"""Accès MySQL read-only — driver PyMySQL (D4bis.1-D4bis.4).

Dérivé de jeedom-audit/db_query.py — logique escape conservée, SSH → driver local.
Ref jeedom-audit : db_query.py @ commit à préciser en J1-2 (D7.4).
"""

from __future__ import annotations

import re
from pathlib import Path

import pymysql
import pymysql.cursors
import structlog

log = structlog.get_logger('holmesMcp.db')

_CONF_PATH = Path('/etc/holmes_mcp_ro.conf')
_DB_SOCKET = '/run/mysqld/mysqld.sock'
_DB_USER = 'jeedom_mcp_ro'
_DB_NAME = 'jeedom'

# Mots réservés MySQL/MariaDB utilisés comme noms de colonnes/tables dans Jeedom :
# `trigger` dans scenario.trigger, `repeat` dans calendar_event.repeat,
# `update` comme nom de table (versions plugins/core).
_RESERVED_RE = re.compile(r'\b(trigger|repeat|update)\b', re.IGNORECASE)


def read_config(conf_path: Path = _CONF_PATH) -> dict[str, str]:
    """Parse /etc/holmes_mcp_ro.conf (format key=value, commentaires # ignorés)."""
    cfg: dict[str, str] = {}
    for line in conf_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, _, v = line.partition('=')
            cfg[k.strip()] = v.strip()
    return cfg


def connect(conf_path: Path = _CONF_PATH) -> pymysql.connections.Connection:
    """Ouvre une connexion PyMySQL read-only vers la base Jeedom via unix socket.

    Unix socket requis : le user jeedom_mcp_ro est GRANT @'localhost' (socket uniquement,
    comme le fait le client C MySQL / PHP — '127.0.0.1' TCP serait refusé).
    """
    cfg = read_config(conf_path)
    password = cfg.get('password', '')
    socket = cfg.get('socket', _DB_SOCKET)
    conn = pymysql.connect(
        unix_socket=socket,
        user=_DB_USER,
        password=password,
        database=_DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=5,
    )
    log.debug('db_connected', socket=socket, user=_DB_USER, db=_DB_NAME)
    return conn


def escape_reserved(sql: str) -> str:
    """Ajoute des backticks autour des mots réservés MySQL non encore quotés."""

    def _replacer(m: re.Match) -> str:
        start = m.start()
        if start > 0 and sql[start - 1] == '`':
            return m.group()
        return f'`{m.group()}`'

    return _RESERVED_RE.sub(_replacer, sql)


def query(
    conn: pymysql.connections.Connection,
    sql: str,
    params: tuple | list | None = None,
) -> list[dict]:
    """Exécute un SELECT et retourne les lignes sous forme de liste de dicts.

    Lève pymysql.Error en cas d'erreur SQL — le caller gère.
    """
    sql = escape_reserved(sql)
    with conn.cursor() as cur:
        # Ne passer params que s'il est non vide : PyMySQL formate les `%` du SQL
        # même avec un tuple vide (), ce qui casse les clauses LIKE 'token_%'.
        cur.execute(sql, params if params else None)
        rows = list(cur.fetchall())
    log.debug('db_query_ok', rows=len(rows))
    return rows
