"""Tests d'intégration — _core/api.py sur box réelle (JSON-RPC localhost)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / 'resources' / 'holmesMcpd'))

from _core.api import call

pytestmark = pytest.mark.integration


def test_api_blacklist_save_blocked(jeedom_apikey):
    result = call(jeedom_apikey, 'eqLogic::save')
    assert 'error' in result
    blocked = 'blacklist' in result.get('error', '').lower()
    assert blocked or result.get('code') == 'api::forbidden::method'


def test_api_blacklist_exec_blocked(jeedom_apikey):
    result = call(jeedom_apikey, 'cmd::execCmd')
    assert 'error' in result


def test_api_version(jeedom_apikey):
    """Appel lecture seule : version Jeedom."""
    result = call(jeedom_apikey, 'version')
    # Soit on obtient un résultat, soit une erreur RPC (méthode inconnue selon version)
    # Dans tous les cas, pas d'erreur de transport ni de blacklist
    assert result.get('code') != 'api::forbidden::method', 'version ne doit pas être blacklistée'


def test_api_eqlogic_all_returns_list(jeedom_apikey):
    """eqLogic::all — base du D6.3 (mesure taille réponse).

    Skip si la clé API est stockée chiffrée (crypt:) — PHP décrypte en runtime,
    mais le user RO MySQL récupère la forme opaque. La mesure D6.3 se fait via SQL.
    """
    import json
    import time

    if jeedom_apikey.startswith('crypt:'):
        pytest.skip('Clé API chiffrée (crypt:) — mesure D6.3 via SQL (test_db_live.py)')

    t0 = time.monotonic()
    result = call(jeedom_apikey, 'eqLogic::all')
    elapsed = time.monotonic() - t0

    assert 'result' in result, f'Erreur inattendue : {result}'
    items = result['result']
    payload_bytes = len(json.dumps(items).encode())
    print(f'\n[D6.3] eqLogic::all → {len(items)} items, {payload_bytes} bytes, {elapsed:.3f}s')
    assert elapsed < 10, f'Réponse trop lente : {elapsed:.1f}s'
