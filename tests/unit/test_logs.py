"""Tests unitaires — _core/logs.py"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / 'resources' / 'holmesMcpd'))

from _core.logs import resolve_log_path, tail, validate_log_name

# ── validate_log_name ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    'name',
    [
        'core',
        'jMQTT',
        'my-plugin',
        'my_plugin',
        'scenarioLog/scenario70.log',
        'plugin123',
    ],
)
def test_validate_valid_names(name):
    validate_log_name(name)  # ne doit pas lever


@pytest.mark.parametrize(
    'name',
    [
        '../etc/passwd',
        '../../secret',
        'foo/bar/baz',
        'foo/../bar',
        '',
        'foo bar',
        '/absolute/path',
    ],
)
def test_validate_invalid_names(name):
    with pytest.raises(ValueError):
        validate_log_name(name)


# ── resolve_log_path ──────────────────────────────────────────────────────────


def test_resolve_finds_first_existing(tmp_path):
    log_dir1 = tmp_path / 'dir1'
    log_dir2 = tmp_path / 'dir2'
    log_dir1.mkdir()
    log_dir2.mkdir()
    (log_dir2 / 'core').write_text('line1\nline2\n')

    result = resolve_log_path('core', [log_dir1, log_dir2])
    assert result == log_dir2 / 'core'


def test_resolve_returns_none_when_missing(tmp_path):
    result = resolve_log_path('core', [tmp_path / 'nonexistent'])
    assert result is None


def test_resolve_prefers_first_dir(tmp_path):
    dir1 = tmp_path / 'd1'
    dir2 = tmp_path / 'd2'
    dir1.mkdir()
    dir2.mkdir()
    (dir1 / 'core').write_text('from dir1')
    (dir2 / 'core').write_text('from dir2')

    result = resolve_log_path('core', [dir1, dir2])
    assert result == dir1 / 'core'


# ── tail ──────────────────────────────────────────────────────────────────────


def _make_log(tmp_path, name='core', content='line1\nline2\nline3\n'):
    log_dir = tmp_path / 'log'
    log_dir.mkdir(exist_ok=True)
    (log_dir / name).write_text(content)
    return [log_dir]


def test_tail_returns_all_lines(tmp_path):
    dirs = _make_log(tmp_path, content='a\nb\nc\n')
    result = tail('core', lines=10, log_dirs=dirs)
    assert result['lines'] == ['a', 'b', 'c']
    assert result['count'] == 3
    assert 'error' not in result


def test_tail_limits_lines(tmp_path):
    content = '\n'.join(str(i) for i in range(100))
    dirs = _make_log(tmp_path, content=content)
    result = tail('core', lines=5, log_dirs=dirs)
    assert result['count'] == 5
    assert result['lines'] == ['95', '96', '97', '98', '99']


def test_tail_grep_filters(tmp_path):
    dirs = _make_log(tmp_path, content='[ERROR] bad\n[INFO] ok\n[ERROR] fail\n')
    result = tail('core', lines=100, grep='ERROR', log_dirs=dirs)
    assert result['count'] == 2
    assert all('ERROR' in line for line in result['lines'])


def test_tail_grep_case_insensitive(tmp_path):
    dirs = _make_log(tmp_path, content='ERROR here\nerror there\nok\n')
    result = tail('core', lines=100, grep='error', log_dirs=dirs)
    assert result['count'] == 2


def test_tail_file_not_found(tmp_path):
    result = tail('core', log_dirs=[tmp_path / 'nonexistent'])
    assert 'error' in result
    assert result['count'] == 0
    assert result['lines'] == []


def test_tail_invalid_name():
    result = tail('../etc/passwd')
    assert 'error' in result
    assert result['count'] == 0


def test_tail_returns_log_file_path(tmp_path):
    dirs = _make_log(tmp_path)
    result = tail('core', log_dirs=dirs)
    assert result['log_file'] is not None
    assert 'core' in result['log_file']


def test_tail_subdirectory_log(tmp_path):
    log_dir = tmp_path / 'log'
    sub = log_dir / 'scenarioLog'
    sub.mkdir(parents=True)
    (sub / 'scenario70.log').write_text('event1\nevent2\n')
    result = tail('scenarioLog/scenario70.log', log_dirs=[log_dir])
    assert result['count'] == 2
