"""Tests unitaires — resources/health.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from resources import health

_MOCK_CONN = MagicMock()


class TestReadHealth:
    def test_delegates_to_get_health_summary(self):
        expected = {
            'plugins_nok': [],
            'messages_unread': [],
            'crons_running': [],
            'summary': {'plugins_nok': 0, 'messages_unread': 0, 'crons_running': 0},
        }
        with patch('resources.health.logs_tools.get_health_summary', return_value=expected) as mock:
            result = health.read(_MOCK_CONN)
        mock.assert_called_once_with(_MOCK_CONN)
        assert result == expected

    def test_returns_dict(self):
        with patch('resources.health.logs_tools.get_health_summary', return_value={'ok': True}):
            result = health.read(_MOCK_CONN)
        assert isinstance(result, dict)

    def test_passes_connection_through(self):
        conn = MagicMock()
        with patch('resources.health.logs_tools.get_health_summary', return_value={}) as mock:
            health.read(conn)
        mock.assert_called_once_with(conn)
