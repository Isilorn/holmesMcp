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
_parser.add_argument('--loglevel',   default='info',
                     choices=['debug', 'info', 'warning', 'error'])
_parser.add_argument('--socketport', default=55000, type=int,
                     help='Port socket interne Jeedom (PHP→daemon)')
_parser.add_argument('--apikey',     required=True,
                     help='Clé API plugin Jeedom (pour callbacks daemon→PHP)')
_parser.add_argument('--port',       default=8765, type=int,
                     help='Port HTTP d\'écoute MCP')
_parser.add_argument('--pid',        required=True,
                     help='Chemin du fichier PID')
_parser.add_argument('--callback',   default='',
                     help='URL callback daemon→PHP (jeeholmesMcp.php)')
ARGS = _parser.parse_args()

# ── Logging stdlib (structlog intégré à partir de J1 — D9.1) ──────────────────
_LOG_LEVEL = getattr(logging, ARGS.loglevel.upper(), logging.INFO)
logging.basicConfig(
    level=_LOG_LEVEL,
    format='[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)
log = logging.getLogger('holmesMcp')

# ── PID file ──────────────────────────────────────────────────────────────────
_PID_PATH = Path(ARGS.pid)


def _write_pid() -> None:
    _PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PID_PATH.write_text(str(os.getpid()))
    log.info('PID %d écrit dans %s', os.getpid(), _PID_PATH)


def _remove_pid() -> None:
    _PID_PATH.unlink(missing_ok=True)


# ── Signal handlers ───────────────────────────────────────────────────────────
def _handle_shutdown(signum, frame) -> None:
    log.info('Signal %d reçu — arrêt propre du daemon Holmes MCP', signum)
    _remove_pid()
    sys.exit(0)


signal.signal(signal.SIGTERM, _handle_shutdown)
signal.signal(signal.SIGINT, _handle_shutdown)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    log.info('=== Holmes MCP daemon démarrage (port=%d, pid=%s) ===', ARGS.port, _PID_PATH)
    _write_pid()

    try:
        from mcp_server import build_mcp
        mcp = build_mcp(ARGS)

        # Transport : Streamable HTTP (spec MCP 2025-03-26+, ADR-0003)
        # SDK 1.27.0 : host/port passés au constructeur FastMCP, pas à run()
        log.info('Démarrage serveur MCP Streamable HTTP sur 0.0.0.0:%d/mcp', ARGS.port)
        mcp.run(transport='streamable-http')

    except Exception:
        log.exception('Erreur fatale — arrêt daemon Holmes MCP')
        _remove_pid()
        sys.exit(1)


if __name__ == '__main__':
    main()
