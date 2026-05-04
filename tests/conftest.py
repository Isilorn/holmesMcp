"""Configuration pytest commune — fixtures partagées entre unit et integration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).parent / 'fixtures' / 'synthetic'


@pytest.fixture
def synthetic_tokens() -> list[dict]:
    return json.loads((_FIXTURES / 'config_tokens.json').read_text())


@pytest.fixture
def synthetic_eqlogics() -> list[dict]:
    return json.loads((_FIXTURES / 'eqlogics.json').read_text())


@pytest.fixture
def synthetic_log_path() -> Path:
    return _FIXTURES / 'log_sample.txt'
