"""Fixtures d'intégration — nécessitent une box Jeedom accessible (SSH, MySQL, API)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / 'resources' / 'holmesMcpd'))

from _core.db import connect, query


@pytest.fixture(scope='session')
def db_conn():
    """Connexion PyMySQL read-only vers la base Jeedom réelle.

    Skipped automatiquement si /etc/holmes_mcp_ro.conf est absent (pas sur box).
    """
    conf = Path('/etc/holmes_mcp_ro.conf')
    if not conf.exists():
        pytest.skip('Box Jeedom non accessible — /etc/holmes_mcp_ro.conf absent')
    conn = connect()
    yield conn
    conn.close()


@pytest.fixture(scope='session')
def jeedom_apikey(db_conn):
    """Clé API JSON-RPC globale Jeedom lue depuis la base."""
    rows = query(db_conn, "SELECT value FROM config WHERE plugin='core' AND `key`='api'")
    if not rows:
        pytest.skip('Clé API Jeedom introuvable dans config (plugin=core, key=api)')
    return rows[0]['value']
