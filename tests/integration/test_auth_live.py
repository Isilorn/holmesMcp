"""Tests d'intégration — _core/auth.py sur box réelle."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / 'resources' / 'holmesMcpd'))

from _core.auth import TokenStore

pytestmark = pytest.mark.integration


def test_token_store_from_db_loads(db_conn):
    """TokenStore.from_db() ne doit pas lever d'exception, même si vide."""
    store = TokenStore.from_db(db_conn)
    assert isinstance(store, TokenStore)


def test_token_store_resolve_unknown(db_conn):
    """Un token inconnu retourne None — pas d'exception."""
    store = TokenStore.from_db(db_conn)
    assert store.resolve('token_qui_nexiste_pas_12345') is None
