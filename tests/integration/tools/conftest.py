"""Fixtures d'intégration spécifiques aux tools — nécessitent une box Jeedom."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from _core.db import query


@pytest.fixture(scope='session')
def first_equipment(db_conn):
    """Premier équipement actif sur la box (id)."""
    rows = query(db_conn, 'SELECT id FROM eqLogic WHERE isEnable=1 ORDER BY id LIMIT 1')
    if not rows:
        pytest.skip('Aucun équipement actif sur la box')
    return rows[0]['id']


@pytest.fixture(scope='session')
def first_scenario(db_conn):
    """Premier scénario disponible sur la box (id)."""
    rows = query(db_conn, 'SELECT id FROM scenario ORDER BY id LIMIT 1')
    if not rows:
        pytest.skip('Aucun scénario sur la box')
    return rows[0]['id']


@pytest.fixture(scope='session')
def first_historized_cmd(db_conn):
    """Première commande info historisée disponible sur la box (id)."""
    rows = query(
        db_conn,
        "SELECT id FROM cmd WHERE type='info' AND isHistorized=1 ORDER BY id LIMIT 1",
    )
    if not rows:
        pytest.skip('Aucune commande historisée sur la box')
    return rows[0]['id']
