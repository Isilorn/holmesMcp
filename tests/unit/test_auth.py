"""Tests unitaires — _core/auth.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / 'resources' / 'holmesMcpd'))

from _core.auth import BearerAuthMiddleware, TokenStore

# ── TokenStore ────────────────────────────────────────────────────────────────


def test_token_store_load_basic():
    store = TokenStore()
    store.load(
        [
            {'token': 'abc123', 'login': 'alice'},
            {'token': 'def456', 'login': 'bob'},
        ]
    )
    assert store.resolve('abc123') == 'alice'
    assert store.resolve('def456') == 'bob'


def test_token_store_resolve_unknown():
    store = TokenStore()
    store.load([{'token': 'abc123', 'login': 'alice'}])
    assert store.resolve('unknown') is None


def test_token_store_skips_empty_token():
    store = TokenStore()
    store.load(
        [
            {'token': '', 'login': 'alice'},
            {'token': None, 'login': 'bob'},
            {'token': 'valid', 'login': 'charlie'},
        ]
    )
    assert store.resolve('') is None
    assert store.resolve('valid') == 'charlie'


def test_token_store_skips_empty_login():
    store = TokenStore()
    store.load([{'token': 'abc', 'login': ''}])
    assert store.resolve('abc') is None


def test_token_store_reload_replaces_map():
    store = TokenStore()
    store.load([{'token': 'old', 'login': 'alice'}])
    store.load([{'token': 'new', 'login': 'bob'}])
    assert store.resolve('old') is None
    assert store.resolve('new') == 'bob'


# ── BearerAuthMiddleware ──────────────────────────────────────────────────────


def _make_store(token='valid-token', login='alice') -> TokenStore:
    s = TokenStore()
    s.load([{'token': token, 'login': login}])
    return s


async def _call_middleware(middleware, headers: list[tuple[bytes, bytes]], path='/mcp'):
    """Helper : simule un appel ASGI HTTP et retourne (status, body_dict)."""
    scope = {
        'type': 'http',
        'path': path,
        'headers': headers,
    }
    messages = []

    async def receive():
        return {'type': 'http.request', 'body': b''}

    async def send(msg):
        messages.append(msg)

    downstream_called = []

    async def downstream_app(scope, receive, send):
        downstream_called.append(scope.get('user'))
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})
        await send({'type': 'http.response.body', 'body': b'ok'})

    mw = middleware.__class__(downstream_app, middleware._store)
    await mw(scope, receive, send)

    status_msg = next(m for m in messages if m['type'] == 'http.response.start')
    body_msg = next(m for m in messages if m['type'] == 'http.response.body')
    body = json.loads(body_msg['body']) if body_msg['body'] != b'ok' else 'ok'
    return status_msg['status'], body, downstream_called


@pytest.mark.asyncio
async def test_middleware_valid_token():
    mw = BearerAuthMiddleware(None, _make_store())
    status, body, called = await _call_middleware(
        mw,
        [
            (b'authorization', b'Bearer valid-token'),
        ],
    )
    assert status == 200
    assert called == ['alice']


@pytest.mark.asyncio
async def test_middleware_missing_header():
    mw = BearerAuthMiddleware(None, _make_store())
    status, body, called = await _call_middleware(mw, [])
    assert status == 401
    assert body['error'] == 'Unauthorized'
    assert called == []


@pytest.mark.asyncio
async def test_middleware_invalid_token():
    mw = BearerAuthMiddleware(None, _make_store())
    status, body, called = await _call_middleware(
        mw,
        [
            (b'authorization', b'Bearer wrong-token'),
        ],
    )
    assert status == 401
    assert called == []


@pytest.mark.asyncio
async def test_middleware_not_bearer_scheme():
    mw = BearerAuthMiddleware(None, _make_store())
    status, body, called = await _call_middleware(
        mw,
        [
            (b'authorization', b'Basic dXNlcjpwYXNz'),
        ],
    )
    assert status == 401
    assert called == []


@pytest.mark.asyncio
async def test_middleware_bearer_case_insensitive():
    mw = BearerAuthMiddleware(None, _make_store())
    status, body, called = await _call_middleware(
        mw,
        [
            (b'authorization', b'BEARER valid-token'),
        ],
    )
    assert status == 200
    assert called == ['alice']


@pytest.mark.asyncio
async def test_middleware_non_http_scope_passes_through():
    """Les scopes non-HTTP (lifespan) ne sont pas bloqués."""
    downstream_called = []

    async def downstream(scope, receive, send):
        downstream_called.append(scope['type'])

    store = _make_store()
    mw = BearerAuthMiddleware(downstream, store)

    scope = {'type': 'lifespan', 'headers': []}
    await mw(scope, lambda: None, lambda m: None)
    assert downstream_called == ['lifespan']
