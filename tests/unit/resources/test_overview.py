"""Tests unitaires — resources/overview.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from resources import overview

_MOCK_CONN = MagicMock()
_PATCH = 'resources.overview.discovery.get_install_overview'


class TestReadOverview:
    def test_delegates_to_get_install_overview(self):
        expected = {'jeedom_version': '4.5.3', 'equipements': {'total': 217, 'actifs': 180}}
        with patch(_PATCH, return_value=expected) as mock:
            result = overview.read(_MOCK_CONN)
        mock.assert_called_once_with(_MOCK_CONN)
        assert result == expected

    def test_returns_dict(self):
        with patch(_PATCH, return_value={'ok': True}):
            result = overview.read(_MOCK_CONN)
        assert isinstance(result, dict)

    def test_passes_connection_through(self):
        conn = MagicMock()
        with patch(_PATCH, return_value={}) as mock:
            overview.read(conn)
        mock.assert_called_once_with(conn)
