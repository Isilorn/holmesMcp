"""Tests unitaires — _core/activity.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / 'resources' / 'holmesMcpd'))

from _core.activity import McpActivityLogger, _summarize_params

# ── _summarize_params ─────────────────────────────────────────────────────────


def test_summarize_empty():
    assert _summarize_params({}) == ''


def test_summarize_none():
    assert _summarize_params(None) == ''  # type: ignore[arg-type]


def test_summarize_simple():
    result = _summarize_params({'limit': 10, 'offset': 0})
    assert 'limit=10' in result
    assert 'offset=0' in result


def test_summarize_truncates_long_value():
    long_val = 'SELECT * FROM eqLogic WHERE id IN (1,2,3,4,5,6,7,8,9,10,11,12)'
    result = _summarize_params({'sql': long_val})
    assert len(result) <= 160
    assert '...' in result


def test_summarize_max_five_params():
    params = {f'k{i}': i for i in range(10)}
    result = _summarize_params(params)
    # At most 5 key=val pairs
    assert result.count('=') <= 5


def test_summarize_total_length_capped():
    params = {f'key{i}': 'x' * 50 for i in range(5)}
    result = _summarize_params(params)
    assert len(result) <= 153  # 150 + '...'


# ── McpActivityLogger — helpers ───────────────────────────────────────────────

def _make_scope(path: str = '/mcp', scope_type: str = 'http') -> dict:
    return {'type': scope_type, 'path': path, 'headers': []}


async def _make_receive(body: bytes):
    called = [False]

    async def receive():
        if not called[0]:
            called[0] = True
            return {'type': 'http.request', 'body': body, 'more_body': False}
        return {'type': 'http.request', 'body': b'', 'more_body': False}

    return receive


async def _noop_send(msg):
    pass


def _tool_call_body(tool: str, arguments: dict | None = None) -> bytes:
    return json.dumps({
        'jsonrpc': '2.0',
        'method': 'tools/call',
        'params': {'name': tool, 'arguments': arguments or {}},
        'id': 1,
    }).encode()


def _non_tool_body(method: str = 'tools/list') -> bytes:
    return json.dumps({'jsonrpc': '2.0', 'method': method, 'id': 1}).encode()


# ── McpActivityLogger — test pass-through ─────────────────────────────────────


@pytest.mark.asyncio
async def test_non_http_scope_passes_through():
    received_scope = {}

    async def inner(scope, receive, send):
        received_scope.update(scope)

    middleware = McpActivityLogger(inner)
    scope = _make_scope(scope_type='lifespan')
    receive = await _make_receive(b'')
    await middleware(scope, receive, _noop_send)
    assert received_scope['type'] == 'lifespan'


@pytest.mark.asyncio
async def test_non_tool_call_passes_body_through(structlog_caplog):
    body_received = []

    async def inner(scope, receive, send):
        msg = await receive()
        body_received.append(msg.get('body', b''))

    body = _non_tool_body('tools/list')
    middleware = McpActivityLogger(inner)
    receive = await _make_receive(body)
    await middleware(_make_scope(), receive, _noop_send)
    assert body_received[0] == body


@pytest.mark.asyncio
async def test_non_tool_call_does_not_log_tool_call(structlog_caplog):
    async def inner(scope, receive, send):
        await receive()

    middleware = McpActivityLogger(inner)
    receive = await _make_receive(_non_tool_body())
    await middleware(_make_scope(), receive, _noop_send)

    tool_events = [e for e in structlog_caplog if e.get('event') == 'tool_call']
    assert tool_events == []


# ── McpActivityLogger — tool_call logging ─────────────────────────────────────


@pytest.mark.asyncio
async def test_tool_call_logged_on_success(structlog_caplog):
    async def inner(scope, receive, send):
        await receive()

    middleware = McpActivityLogger(inner)
    receive = await _make_receive(_tool_call_body('list_scenarios', {'is_active': True}))
    await middleware(_make_scope(), receive, _noop_send)

    events = [e for e in structlog_caplog if e.get('event') == 'tool_call']
    assert len(events) == 1
    ev = events[0]
    assert ev['tool'] == 'list_scenarios'
    assert ev['status'] == 'ok'
    assert 'duration_ms' in ev
    assert isinstance(ev['duration_ms'], int)
    assert 'is_active=True' in ev['params_summary']


@pytest.mark.asyncio
async def test_tool_call_body_forwarded_to_inner(structlog_caplog):
    body_received = []

    async def inner(scope, receive, send):
        msg = await receive()
        body_received.append(msg.get('body', b''))

    body = _tool_call_body('get_install_overview')
    middleware = McpActivityLogger(inner)
    receive = await _make_receive(body)
    await middleware(_make_scope(), receive, _noop_send)
    assert body_received[0] == body


@pytest.mark.asyncio
async def test_tool_call_logged_on_exception(structlog_caplog):
    async def inner(scope, receive, send):
        await receive()
        raise RuntimeError('boom')

    middleware = McpActivityLogger(inner)
    receive = await _make_receive(_tool_call_body('query_sql', {'sql': 'SELECT 1'}))
    with pytest.raises(RuntimeError):
        await middleware(_make_scope(), receive, _noop_send)

    events = [e for e in structlog_caplog if e.get('event') == 'tool_call']
    assert len(events) == 1
    ev = events[0]
    assert ev['tool'] == 'query_sql'
    assert ev['status'] == 'error'
    assert 'boom' in ev['error']


@pytest.mark.asyncio
async def test_tool_call_duration_ms_is_non_negative(structlog_caplog):
    async def inner(scope, receive, send):
        await receive()

    middleware = McpActivityLogger(inner)
    receive = await _make_receive(_tool_call_body('get_install_overview'))
    await middleware(_make_scope(), receive, _noop_send)

    ev = next(e for e in structlog_caplog if e.get('event') == 'tool_call')
    assert ev['duration_ms'] >= 0


@pytest.mark.asyncio
async def test_tool_call_no_arguments_empty_params_summary(structlog_caplog):
    async def inner(scope, receive, send):
        await receive()

    body = json.dumps({
        'jsonrpc': '2.0',
        'method': 'tools/call',
        'params': {'name': 'get_install_overview'},  # no 'arguments' key
        'id': 1,
    }).encode()

    middleware = McpActivityLogger(inner)
    receive = await _make_receive(body)
    await middleware(_make_scope(), receive, _noop_send)

    ev = next(e for e in structlog_caplog if e.get('event') == 'tool_call')
    assert ev['params_summary'] == ''


@pytest.mark.asyncio
async def test_invalid_json_body_does_not_log_tool_call(structlog_caplog):
    async def inner(scope, receive, send):
        await receive()

    middleware = McpActivityLogger(inner)
    receive = await _make_receive(b'not json at all')
    await middleware(_make_scope(), receive, _noop_send)

    tool_events = [e for e in structlog_caplog if e.get('event') == 'tool_call']
    assert tool_events == []


@pytest.mark.asyncio
async def test_empty_body_does_not_log_tool_call(structlog_caplog):
    async def inner(scope, receive, send):
        await receive()

    middleware = McpActivityLogger(inner)
    receive = await _make_receive(b'')
    await middleware(_make_scope(), receive, _noop_send)

    tool_events = [e for e in structlog_caplog if e.get('event') == 'tool_call']
    assert tool_events == []


# ── conftest fixture inline ───────────────────────────────────────────────────


@pytest.fixture
def structlog_caplog():
    import structlog.testing

    with structlog.testing.capture_logs() as cap:
        yield cap
