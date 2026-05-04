"""Fixtures d'intégration — nécessitent une box Jeedom accessible (SSH, MySQL, API)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / 'resources' / 'holmesMcpd'))

from _core.db import connect

_DAEMON_PID_PATH = Path('/tmp/jeedom/holmesMcp/daemon.pid')
_DAEMON_APIKEY_ARG = '--jeedom-apikey'


def _read_daemon_apikey() -> str | None:
    """Lit la clé API JSON-RPC depuis la cmdline du daemon Holmes MCP en cours."""
    if not _DAEMON_PID_PATH.exists():
        return None
    try:
        pid = int(_DAEMON_PID_PATH.read_text().strip())
        cmdline = Path(f'/proc/{pid}/cmdline').read_bytes().decode().split('\x00')
        for i, arg in enumerate(cmdline):
            if arg == _DAEMON_APIKEY_ARG and i + 1 < len(cmdline):
                return cmdline[i + 1]
    except (ValueError, OSError):
        pass
    return None


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
def jeedom_apikey():
    """Clé API JSON-RPC globale Jeedom — lue depuis le daemon en cours (déjà déchiffrée).

    La clé dans la table config est chiffrée (crypt:...) par Jeedom. Le daemon reçoit
    la version déchiffrée via --jeedom-apikey. On la récupère depuis /proc/<pid>/cmdline.
    """
    key = _read_daemon_apikey()
    if not key:
        pytest.skip(
            'Clé API Jeedom introuvable — daemon holmesMcp non démarré '
            f'ou PID absent ({_DAEMON_PID_PATH})'
        )
    return key
