"""Tests unitaires — _core/api.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / 'resources' / 'holmesMcpd'))

from _core.api import call, is_blacklisted

# ── is_blacklisted ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    'method',
    [
        'cmd::execCmd',
        'scenario::changeState',
        'datastore::save',
        'interact::tryToReply',
    ],
)
def test_blacklist_exact_match(method):
    assert is_blacklisted(method) is True


@pytest.mark.parametrize(
    'method',
    [
        'eqLogic::save',
        'cmd::delete',
        'plugin::remove',
        'jeedom::update',
        'user::add',
        'scenario::create',
    ],
)
def test_blacklist_verb_match(method):
    assert is_blacklisted(method) is True


@pytest.mark.parametrize(
    'method',
    [
        'eqLogic::byId',
        'cmd::byId',
        'scenario::byId',
        'jeedom::version',
        'ping',
        'eqLogic::all',
        'plugin::listPlugin',
    ],
)
def test_not_blacklisted(method):
    assert is_blacklisted(method) is False


# ── call — blacklisted ────────────────────────────────────────────────────────


def test_call_blacklisted_returns_error():
    result = call(apikey='key', method='cmd::execCmd')
    assert 'error' in result
    assert result.get('code') == 'api::forbidden::method'


# ── call — HTTP success ───────────────────────────────────────────────────────


def _mock_urlopen(payload: dict):
    """Retourne un context manager simulant urlopen avec le payload JSON donné."""
    body = json.dumps(payload).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_call_success_scalar():
    rpc_response = {'jsonrpc': '2.0', 'result': 'ok', 'id': 1}
    with patch('urllib.request.urlopen', return_value=_mock_urlopen(rpc_response)):
        result = call(apikey='key', method='ping')
    assert result == {'result': 'ok', '_filtered_fields': []}


def test_call_success_dict():
    rpc_response = {'jsonrpc': '2.0', 'result': {'id': 5, 'name': 'Light'}, 'id': 1}
    with patch('urllib.request.urlopen', return_value=_mock_urlopen(rpc_response)):
        result = call(apikey='key', method='eqLogic::byId', params={'id': 5})
    assert result['result'] == {'id': 5, 'name': 'Light'}
    assert result['_filtered_fields'] == []


def test_call_rpc_error():
    rpc_response = {
        'jsonrpc': '2.0',
        'error': {'code': -32601, 'message': 'Method not found'},
        'id': 1,
    }
    with patch('urllib.request.urlopen', return_value=_mock_urlopen(rpc_response)):
        result = call(apikey='key', method='unknown::method')
    assert 'error' in result
    assert result['code'] == -32601


def test_call_transport_error_retries():
    import urllib.error

    call_count = {'n': 0}

    def mock_urlopen(req, timeout):
        call_count['n'] += 1
        if call_count['n'] < 2:
            raise urllib.error.URLError('Connection refused')
        return _mock_urlopen({'jsonrpc': '2.0', 'result': 'ok', 'id': 1})

    with patch('urllib.request.urlopen', side_effect=mock_urlopen):
        result = call(apikey='key', method='ping')
    assert result == {'result': 'ok', '_filtered_fields': []}
    assert call_count['n'] == 2


def test_call_transport_error_both_fail():
    import urllib.error

    with patch('urllib.request.urlopen', side_effect=urllib.error.URLError('refused')):
        result = call(apikey='key', method='ping')
    assert 'error' in result
    assert '_filtered_fields' not in result


def test_call_timeout():
    with patch('urllib.request.urlopen', side_effect=TimeoutError()):
        result = call(apikey='key', method='ping', timeout=1)
    assert 'error' in result
    assert 'Timeout' in result['error']
