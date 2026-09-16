#!/usr/bin/env python3
"""Entrypoint daemon Holmes MCP.

Pattern Jeedom : script lancé par deamon_start() côté PHP, surveillé via PID file.
Ref : doc.jeedom.com/fr_FR/dev/daemon_plugin
"""

import argparse
import asyncio
import logging
import os
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


# ── Watchdog CLOSE-WAIT (Level 2) ─────────────────────────────────────────────
async def _watchdog_close_wait(port: int) -> None:
    """Nettoie les sockets CLOSE-WAIT laissés par des clients MCP déconnectés abruptement.

    Bug FastMCP : StreamableHTTPServerTransport ne ferme pas les sockets quand le client
    envoie un FIN mid-SSE-stream. Les sockets restent en CLOSE-WAIT avec données en Recv-Q,
    epoll les signale en boucle → spin CPU. Ce watchdog les nettoie toutes les 15 s.
    """
    while True:
        await asyncio.sleep(15)
        inodes = _find_close_wait_inodes(port)
        if not inodes:
            continue
        log.warning('close_wait_cleanup', count=len(inodes), port=port)
        _close_sockets_by_inode(inodes)


def _find_close_wait_inodes(port: int) -> set[int]:
    close_wait = 8
    inodes: set[int] = set()
    try:
        with open('/proc/self/net/tcp') as f:
            for line in f.readlines()[1:]:
                parts = line.split()
                if len(parts) < 10:
                    continue
                local_port = int(parts[1].split(':')[1], 16)
                state = int(parts[3], 16)
                inode = int(parts[9])
                if local_port == port and state == close_wait:
                    inodes.add(inode)
    except OSError:
        pass
    return inodes


def _close_sockets_by_inode(inodes: set[int]) -> None:
    loop = asyncio.get_running_loop()
    closed = 0
    for entry in Path('/proc/self/fd').iterdir():
        try:
            target = os.readlink(entry)
            if 'socket:[' not in target:
                continue
            inode = int(target[8:-1])
            if inode not in inodes:
                continue
            fd = int(entry.name)
            try:
                loop.remove_reader(fd)
            except Exception:
                pass
            try:
                loop.remove_writer(fd)
            except Exception:
                pass
            os.close(fd)
            closed += 1
        except OSError:
            pass
    if closed:
        log.info('close_wait_sockets_closed', closed=closed)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    log.info('daemon_start', port=ARGS.port, pid_path=str(_PID_PATH))
    _write_pid()

    # pydantic_settings cherche .env dans le CWD — se placer dans le répertoire du daemon
    # pour éviter une PermissionError si PHP lance depuis un répertoire inaccessible à www-data
    os.chdir(Path(__file__).parent)

    try:
        import uvicorn
        from _core.activity import McpActivityLogger
        from _core.auth import BearerAuthMiddleware, TokenStore
        from _core.db import connect
        from mcp_server import build_mcp

        # Chargement du store de tokens depuis la DB Jeedom
        conn = connect()
        token_store = TokenStore.from_db(conn)
        conn.close()

        # Construction du serveur MCP
        mcp = build_mcp(ARGS)

        # Pile middleware : BearerAuth → McpActivityLogger → FastMCP ASGI
        mcp_asgi = mcp.streamable_http_app()
        activity_logged = McpActivityLogger(mcp_asgi)
        authed_app = BearerAuthMiddleware(activity_logged, token_store=token_store)

        log.info('daemon_listening', host='0.0.0.0', port=ARGS.port, path='/mcp')

        # uvicorn installe ses propres handlers SIGTERM/SIGINT sur la boucle asyncio.
        # On lance le watchdog CLOSE-WAIT dans la même boucle que uvicorn via asyncio.run().
        async def _serve() -> None:
            asyncio.create_task(_watchdog_close_wait(ARGS.port))
            config = uvicorn.Config(authed_app, host='0.0.0.0', port=ARGS.port, log_config=None)
            server = uvicorn.Server(config)
            await server.serve()

        asyncio.run(_serve())

    except Exception:
        log.exception('daemon_fatal_error')
        raise
    finally:
        log.info('daemon_shutdown')
        _remove_pid()


if __name__ == '__main__':
    main()
