#!/usr/bin/env python3
"""Entrypoint daemon Holmes MCP.

Pattern Jeedom : script lancé par deamon_start() côté PHP, surveillé via PID file.
Ref : doc.jeedom.com/fr_FR/dev/daemon_plugin
"""

import argparse
import logging
import os
import signal
import sys
from pathlib import Path

# ── CLI (pattern Jeedom — arguments passés par deamon_start() en PHP) ─────────
_parser = argparse.ArgumentParser(description='Holmes MCP daemon')
_parser.add_argument('--loglevel', default='info', choices=['debug', 'info', 'warning', 'error'])
_parser.add_argument(
    '--socketport', default=55000, type=int, help='Port socket interne Jeedom (PHP→daemon)'
)
_parser.add_argument('--apikey', required=True, help='Clé API plugin Jeedom (callbacks daemon→PHP)')
_parser.add_argument(
    '--jeedom-apikey',
    required=True,
    dest='jeedom_apikey',
    help='Clé API JSON-RPC globale Jeedom (appels API localhost)',
)
_parser.add_argument('--port', default=8765, type=int, help="Port HTTP d'écoute MCP")
_parser.add_argument('--pid', required=True, help='Chemin du fichier PID')
_parser.add_argument('--callback', default='', help='URL callback daemon→PHP (jeeholmesMcp.php)')
ARGS = _parser.parse_args()

# ── Structlog (D9.1 — JSON Lines vers stdout redirigé dans le log Jeedom) ─────
import structlog  # noqa: E402

_LOG_LEVEL = getattr(logging, ARGS.loglevel.upper(), logging.INFO)
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(_LOG_LEVEL),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
log = structlog.get_logger('holmesMcp')

# ── PID file ──────────────────────────────────────────────────────────────────
_PID_PATH = Path(ARGS.pid)


def _write_pid() -> None:
    _PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PID_PATH.write_text(str(os.getpid()))
    log.info('pid_written', pid=os.getpid(), path=str(_PID_PATH))


def _remove_pid() -> None:
    _PID_PATH.unlink(missing_ok=True)


# ── Signal handlers ───────────────────────────────────────────────────────────
def _handle_shutdown(signum, frame) -> None:
    log.info('daemon_shutdown', signal=signum)
    _remove_pid()
    sys.exit(0)


signal.signal(signal.SIGTERM, _handle_shutdown)
signal.signal(signal.SIGINT, _handle_shutdown)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    log.info('daemon_start', port=ARGS.port, pid_path=str(_PID_PATH))
    _write_pid()

    # pydantic_settings cherche .env dans le CWD — se placer dans le répertoire du daemon
    # pour éviter une PermissionError si PHP lance depuis un répertoire inaccessible à www-data
    os.chdir(Path(__file__).parent)

    try:
        import uvicorn
        from _core.auth import BearerAuthMiddleware, TokenStore
        from _core.db import connect
        from mcp_server import build_mcp

        # Chargement du store de tokens depuis la DB Jeedom
        conn = connect()
        token_store = TokenStore.from_db(conn)
        conn.close()

        # Construction du serveur MCP
        mcp = build_mcp(ARGS)

        # Récupération de l'app ASGI Streamable HTTP et ajout du middleware auth
        mcp_asgi = mcp.streamable_http_app()
        authed_app = BearerAuthMiddleware(mcp_asgi, token_store=token_store)

        log.info('daemon_listening', host='0.0.0.0', port=ARGS.port, path='/mcp')
        uvicorn.run(authed_app, host='0.0.0.0', port=ARGS.port, log_config=None)

    except Exception:
        log.exception('daemon_fatal_error')
        _remove_pid()
        sys.exit(1)


if __name__ == '__main__':
    main()
