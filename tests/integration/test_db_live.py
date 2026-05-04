"""Tests d'intégration — _core/db.py sur box réelle."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / 'resources' / 'holmesMcpd'))

from _core.db import query

pytestmark = pytest.mark.integration


def test_db_connect(db_conn):
    assert db_conn is not None


def test_db_select_1(db_conn):
    rows = query(db_conn, 'SELECT 1 AS n')
    assert rows == [{'n': 1}]


def test_db_tables_exist(db_conn):
    rows = query(db_conn, 'SHOW TABLES')
    table_names = {list(r.values())[0] for r in rows}
    for required in ('config', 'user', 'eqLogic'):
        assert required in table_names, f'Table manquante : {required}'


def test_db_query_eqlogic_count(db_conn):
    rows = query(db_conn, 'SELECT COUNT(*) AS n FROM eqLogic')
    count = rows[0]['n']
    assert isinstance(count, int)
    print(f'\n[D6.3] eqLogic total: {count}')


def test_db_query_cmd_count(db_conn):
    rows = query(db_conn, 'SELECT COUNT(*) AS n FROM cmd')
    count = rows[0]['n']
    assert isinstance(count, int)
    print(f'\n[D6.3] cmd total: {count}')


def test_db_query_scenario_count(db_conn):
    rows = query(db_conn, 'SELECT COUNT(*) AS n FROM scenario')
    count = rows[0]['n']
    assert isinstance(count, int)
    print(f'\n[D6.3] scenario total: {count}')


def test_db_query_object_count(db_conn):
    rows = query(db_conn, 'SELECT COUNT(*) AS n FROM object')
    count = rows[0]['n']
    assert isinstance(count, int)
    print(f'\n[D6.3] object total: {count}')
