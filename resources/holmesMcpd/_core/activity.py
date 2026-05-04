"""Middleware ASGI de logging d'activité MCP — observabilité des tool calls.

Intercepte les requêtes JSON-RPC tools/call, mesure la durée et émet un log
structuré 'tool_call'. L'utilisateur est injecté automatiquement via
structlog.contextvars (alimenté par BearerAuthMiddleware).
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable

import structlog

log = structlog.get_logger('holmesMcp.activity')

_MAX_PARAM_VAL = 40   # longueur max d'une valeur de paramètre dans le résumé
_MAX_PARAMS_STR = 150  # longueur max du résumé complet


def _summarize_params(params: dict) -> str:
    """Résume un dict de paramètres en chaîne courte pour les logs."""
    if not params:
        return ''
    parts = []
    for k, v in list(params.items())[:5]:
        sv = str(v)
        if len(sv) > _MAX_PARAM_VAL:
            sv = sv[:_MAX_PARAM_VAL - 3] + '...'
        parts.append(f'{k}={sv}')
    result = ', '.join(parts)
    if len(result) > _MAX_PARAMS_STR:
        result = result[:_MAX_PARAMS_STR - 3] + '...'
    return result


class McpActivityLogger:
    """Middleware ASGI : enregistre chaque appel tool MCP avec timing et statut.

    Positionné après BearerAuthMiddleware pour que structlog contextvars soit
    alimenté avec l'utilisateur courant.
    """

    def __init__(self, app) -> None:
        self._app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope.get('type') != 'http':
            await self._app(scope, receive, send)
            return

        chunks: list[bytes] = []
        while True:
            msg = await receive()
            chunks.append(msg.get('body', b''))
            if not msg.get('more_body', False):
                break
        body = b''.join(chunks)

        tool_name: str | None = None
        tool_params: dict = {}
        if body:
            try:
                payload = json.loads(body)
                if isinstance(payload, dict) and payload.get('method') == 'tools/call':
                    p = payload.get('params') or {}
                    tool_name = p.get('name')
                    tool_params = p.get('arguments') or {}
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass

        body_sent = False

        async def _buffered_receive():
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {'type': 'http.request', 'body': body, 'more_body': False}
            return {'type': 'http.request', 'body': b'', 'more_body': False}

        start = time.perf_counter()
        exc_raised: BaseException | None = None
        try:
            await self._app(scope, _buffered_receive, send)
        except BaseException as exc:
            exc_raised = exc
            raise
        finally:
            if tool_name:
                ms = round((time.perf_counter() - start) * 1000)
                params_summary = _summarize_params(tool_params)
                if exc_raised is not None:
                    log.error(
                        'tool_call',
                        tool=tool_name,
                        params_summary=params_summary,
                        duration_ms=ms,
                        status='error',
                        error=str(exc_raised),
                    )
                else:
                    log.info(
                        'tool_call',
                        tool=tool_name,
                        params_summary=params_summary,
                        duration_ms=ms,
                        status='ok',
                    )
