"""Authentification MCP — validation des Bearer tokens (D4.1-D4.5).

Tokens stockés dans la table `config` Jeedom : plugin='holmesMcp', key='token_<user_id>'.
Résolution token → login via JOIN config ↔ user.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import structlog
import structlog.contextvars

if TYPE_CHECKING:
    import pymysql.connections

log = structlog.get_logger('holmesMcp.auth')

# Requête de chargement du store : token → login des users Jeedom actifs.
_TOKEN_QUERY = """
    SELECT c.value AS token, u.login
    FROM config c
    JOIN user u ON u.id = CAST(SUBSTRING(c.key, 7) AS UNSIGNED)
    WHERE c.plugin = 'holmesMcp'
      AND c.key LIKE 'token_%'
      AND u.enable = 1
"""


class TokenStore:
    """Map en mémoire : Bearer token → login Jeedom.

    Chargée depuis MySQL au démarrage. Thread-safe en lecture (dict Python, GIL).
    """

    def __init__(self) -> None:
        self._map: dict[str, str] = {}

    def load(self, rows: list[dict]) -> None:
        """Remplace la map depuis une liste de {'token': ..., 'login': ...}."""
        self._map = {r['token']: r['login'] for r in rows if r.get('token') and r.get('login')}
        log.info('token_store_loaded', count=len(self._map))

    def resolve(self, token: str) -> str | None:
        """Retourne le login associé au token, ou None si inconnu."""
        return self._map.get(token)

    @classmethod
    def from_db(cls, conn: pymysql.connections.Connection) -> TokenStore:
        """Construit et charge le store depuis la base Jeedom."""
        from _core.db import query as db_query

        rows = db_query(conn, _TOKEN_QUERY)
        store = cls()
        store.load(rows)
        return store


class BearerAuthMiddleware:
    """Middleware ASGI pur : valide Authorization: Bearer <token>.

    - 401 JSON si header absent ou token invalide.
    - Injecte scope['user'] = login pour les logs downstream.
    - Les scopes non-HTTP (lifespan, websocket) sont transmis sans contrôle.
    """

    def __init__(self, app, token_store: TokenStore) -> None:
        self._app = app
        self._store = token_store

    async def __call__(self, scope: dict, receive, send) -> None:
        if scope['type'] != 'http':
            await self._app(scope, receive, send)
            return

        headers = {k: v for k, v in scope.get('headers', [])}
        auth = headers.get(b'authorization', b'').decode('latin-1')

        if not auth.lower().startswith('bearer '):
            log.warning('auth_missing_header', path=scope.get('path', ''))
            await _send_401(send, 'Missing or invalid Authorization header')
            return

        token = auth[7:].strip()
        login = self._store.resolve(token)
        if login is None:
            log.warning('auth_invalid_token', path=scope.get('path', ''))
            await _send_401(send, 'Invalid token')
            return

        scope['user'] = login
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(user=login)
        log.debug('auth_ok', user=login, path=scope.get('path', ''))
        await self._app(scope, receive, send)


async def _send_401(send, detail: str) -> None:
    body = json.dumps({'error': 'Unauthorized', 'detail': detail}).encode()
    await send(
        {
            'type': 'http.response.start',
            'status': 401,
            'headers': [
                (b'content-type', b'application/json'),
                (b'content-length', str(len(body)).encode()),
                (b'www-authenticate', b'Bearer realm="Holmes MCP"'),
            ],
        }
    )
    await send({'type': 'http.response.body', 'body': body, 'more_body': False})
