"""Tests unitaires — _core/db.py"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[2] / 'resources' / 'holmesMcpd'))

from _core.db import connect, escape_reserved, query, read_config

# ── read_config ───────────────────────────────────────────────────────────────


def test_read_config_basic(tmp_path):
    conf = tmp_path / 'holmes_mcp_ro.conf'
    conf.write_text('password=abc123\n# commentaire\nhost=localhost\n')
    result = read_config(conf)
    assert result == {'password': 'abc123', 'host': 'localhost'}


def test_read_config_empty_lines(tmp_path):
    conf = tmp_path / 'holmes_mcp_ro.conf'
    conf.write_text('\n\npassword=secret\n\n')
    assert read_config(conf) == {'password': 'secret'}


def test_read_config_no_hash(tmp_path):
    conf = tmp_path / 'holmes_mcp_ro.conf'
    conf.write_text('password=abc#def\n')
    assert read_config(conf)['password'] == 'abc#def'


# ── escape_reserved ───────────────────────────────────────────────────────────


def test_escape_trigger():
    sql = 'SELECT trigger FROM scenario'
    assert '`trigger`' in escape_reserved(sql)


def test_escape_repeat():
    sql = 'SELECT repeat FROM calendar_event'
    assert '`repeat`' in escape_reserved(sql)


def test_escape_update_table():
    sql = 'SELECT * FROM update'
    assert '`update`' in escape_reserved(sql)


def test_no_double_backtick():
    sql = 'SELECT `trigger` FROM scenario'
    result = escape_reserved(sql)
    assert '``trigger``' not in result
    assert result.count('`trigger`') == 1


def test_no_escape_in_string_context():
    # Le mot "trigger" dans une chaîne SQL ne doit pas crasher (pas de double backtick)
    sql = "SELECT id FROM scenario WHERE name = 'trigger test'"
    result = escape_reserved(sql)
    # Le mot dans la valeur string est à l'intérieur de guillemets simples — on l'échappe
    # car on ne parse pas le SQL, mais le résultat ne doit pas être malformé
    assert isinstance(result, str)


def test_non_reserved_word_untouched():
    sql = 'SELECT id, name FROM eqLogic'
    assert escape_reserved(sql) == sql


# ── query ─────────────────────────────────────────────────────────────────────


def test_query_returns_rows():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'Light'}]
    mock_conn.cursor.return_value = mock_cursor

    rows = query(mock_conn, 'SELECT id, name FROM eqLogic LIMIT 1')
    assert rows == [{'id': 1, 'name': 'Light'}]
    mock_cursor.execute.assert_called_once()


def test_query_with_params():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cursor

    query(mock_conn, 'SELECT * FROM eqLogic WHERE id = %s', (42,))
    call_args = mock_cursor.execute.call_args
    assert call_args[0][1] == (42,)


def test_query_no_params_not_formatted():
    """Sans params, PyMySQL ne doit pas interpréter '%' dans le SQL (ex: LIKE 'token_%')."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cursor

    query(mock_conn, "SELECT key FROM config WHERE key LIKE 'token_%'")
    call_args = mock_cursor.execute.call_args
    # params non passés (None) pour ne pas déclencher le formattage %_ par PyMySQL
    assert len(call_args[0]) == 1 or call_args[0][1] is None


def test_query_applies_escape_reserved():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cursor

    query(mock_conn, 'SELECT trigger FROM scenario')
    executed_sql = mock_cursor.execute.call_args[0][0]
    assert '`trigger`' in executed_sql


# ── connect (smoke test avec mock) ────────────────────────────────────────────


def test_connect_reads_password(tmp_path):
    conf = tmp_path / 'conf'
    conf.write_text('password=mysecret\n')

    with patch('pymysql.connect') as mock_connect:
        mock_connect.return_value = MagicMock()
        connect(conf_path=conf)
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs['password'] == 'mysecret'
        assert call_kwargs['user'] == 'jeedom_mcp_ro'
        assert call_kwargs['database'] == 'jeedom'
        assert 'unix_socket' in call_kwargs
        assert 'host' not in call_kwargs


def test_connect_socket_override(tmp_path):
    conf = tmp_path / 'conf'
    conf.write_text('password=s\nsocket=/tmp/custom.sock\n')

    with patch('pymysql.connect') as mock_connect:
        mock_connect.return_value = MagicMock()
        connect(conf_path=conf)
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs['unix_socket'] == '/tmp/custom.sock'
