"""Tests unitaires — resources/logs_today.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from resources import logs_today

_TAIL_RESULT = {
    'log_file': '/var/log/jeedom/http',
    'lines': ['line1', 'line2', 'line3'],
    'count': 3,
}


class TestReadLogsToday:
    def test_delegates_to_tail_log(self):
        with patch('resources.logs_today.logs_tools.tail_log', return_value=_TAIL_RESULT) as mock:
            result = logs_today.read()
        mock.assert_called_once_with('http', lines=500, grep=None)
        assert result == _TAIL_RESULT

    def test_returns_dict(self):
        with patch('resources.logs_today.logs_tools.tail_log', return_value=_TAIL_RESULT):
            result = logs_today.read()
        assert isinstance(result, dict)

    def test_uses_http_log(self):
        with patch('resources.logs_today.logs_tools.tail_log', return_value={}) as mock:
            logs_today.read()
        log_name = mock.call_args[0][0]
        assert log_name == 'http'

    def test_requests_500_lines(self):
        with patch('resources.logs_today.logs_tools.tail_log', return_value={}) as mock:
            logs_today.read()
        assert mock.call_args[1]['lines'] == 500

    def test_no_grep_filter(self):
        with patch('resources.logs_today.logs_tools.tail_log', return_value={}) as mock:
            logs_today.read()
        assert mock.call_args[1]['grep'] is None

    def test_error_log_propagated(self):
        error = {'error': 'Log introuvable', 'lines': [], 'count': 0}
        with patch('resources.logs_today.logs_tools.tail_log', return_value=error):
            result = logs_today.read()
        assert result.get('error') == 'Log introuvable'
