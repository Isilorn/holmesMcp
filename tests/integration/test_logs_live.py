"""Tests d'intégration — _core/logs.py sur box réelle."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / 'resources' / 'holmesMcpd'))

from _core.logs import resolve_log_path, tail

pytestmark = pytest.mark.integration

_LOG_ROOT = Path('/var/www/html/log')


def _log_root_present():
    return _LOG_ROOT.is_dir()


@pytest.fixture(autouse=True)
def require_log_dir():
    if not _log_root_present():
        pytest.skip('Répertoire /var/www/html/log absent — pas sur box Jeedom')


def test_log_holmesmcp_resolves():
    path = resolve_log_path('holmesMcp')
    assert path is not None, 'Log holmesMcp introuvable dans /var/www/html/log'
    assert path.is_file()


def test_log_tail_holmesmcp_returns_lines():
    result = tail('holmesMcp', lines=10)
    assert 'error' not in result
    assert result['log_file'] is not None
    assert isinstance(result['lines'], list)


def test_log_tail_grep():
    result = tail('holmesMcp', lines=500, grep='ERROR')
    assert 'error' not in result
    assert isinstance(result['lines'], list)


def test_log_invalid_traversal_rejected():
    result = tail('../etc/passwd')
    assert 'error' in result


def test_log_invalid_double_slash_rejected():
    result = tail('a//b')
    assert 'error' in result


def test_log_unknown_name_returns_error():
    result = tail('log_qui_nexiste_vraiment_pas_xyz123')
    assert 'error' in result
    assert result['count'] == 0
