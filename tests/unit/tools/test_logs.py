"""Tests unitaires — tools/logs.py (Famille 5, 3 tools)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from tools import logs as logs_tools

_MOCK_CONN = MagicMock()


# ---------------------------------------------------------------------------
# list_log_files
# ---------------------------------------------------------------------------


class TestListLogFiles:
    def test_empty_dirs_returns_empty(self, tmp_path):
        with patch('tools.logs._logs.list_files', return_value=[]):
            result = logs_tools.list_log_files()

        assert result['log_files'] == []
        assert result['total'] == 0

    def test_returns_files_with_metadata(self):
        files = [
            {'name': 'core', 'size_bytes': 1024, 'last_modified': '2026-05-04T10:00:00'},
            {'name': 'jMQTT', 'size_bytes': 512, 'last_modified': '2026-05-04T09:00:00'},
        ]
        with patch('tools.logs._logs.list_files', return_value=files):
            result = logs_tools.list_log_files()

        assert result['total'] == 2
        assert result['log_files'][0]['name'] == 'core'
        assert result['log_files'][1]['size_bytes'] == 512

    def test_total_matches_list_length(self):
        files = [{'name': f'log{i}', 'size_bytes': 0, 'last_modified': ''} for i in range(5)]
        with patch('tools.logs._logs.list_files', return_value=files):
            result = logs_tools.list_log_files()

        assert result['total'] == 5
        assert len(result['log_files']) == 5

    def test_delegates_to_core_list_files(self):
        with patch('tools.logs._logs.list_files', return_value=[]) as mock_lf:
            logs_tools.list_log_files()

        mock_lf.assert_called_once_with()


# ---------------------------------------------------------------------------
# tail_log
# ---------------------------------------------------------------------------


class TestTailLog:
    def test_delegates_to_core_tail(self):
        expected = {'log_file': '/var/www/html/log/core', 'lines': ['line1'], 'count': 1}
        with patch('tools.logs._logs.tail', return_value=expected) as mock_tail:
            result = logs_tools.tail_log('core', lines=50)

        mock_tail.assert_called_once_with('core', lines=50, grep=None)
        assert result == expected

    def test_passes_grep_to_core(self):
        with patch('tools.logs._logs.tail', return_value={}) as mock_tail:
            logs_tools.tail_log('core', lines=100, grep='ERROR')

        mock_tail.assert_called_once_with('core', lines=100, grep='ERROR')

    def test_lines_capped_at_500(self):
        with patch('tools.logs._logs.tail', return_value={}) as mock_tail:
            logs_tools.tail_log('core', lines=9999)

        _, kwargs = mock_tail.call_args
        assert kwargs['lines'] == logs_tools._TAIL_MAX_LINES

    def test_lines_not_capped_below_max(self):
        with patch('tools.logs._logs.tail', return_value={}) as mock_tail:
            logs_tools.tail_log('core', lines=200)

        _, kwargs = mock_tail.call_args
        assert kwargs['lines'] == 200

    def test_error_propagated_from_core(self):
        error_result = {'error': 'Fichier introuvable', 'lines': [], 'count': 0}
        with patch('tools.logs._logs.tail', return_value=error_result):
            result = logs_tools.tail_log('nonexistent')

        assert 'error' in result
        assert result['count'] == 0

    def test_invalid_log_name_propagated(self):
        error_result = {'error': 'Nom invalide', 'log_file': None, 'lines': [], 'count': 0}
        with patch('tools.logs._logs.tail', return_value=error_result):
            result = logs_tools.tail_log('../etc/passwd')

        assert 'error' in result


# ---------------------------------------------------------------------------
# get_health_summary
# ---------------------------------------------------------------------------


class TestGetHealthSummary:
    def _make_query_side_effects(
        self,
        plugins_nok=None,
        messages=None,
        crons=None,
    ):
        return [
            plugins_nok or [],
            messages or [],
            crons or [],
        ]

    def test_all_healthy_returns_empty_lists(self):
        with patch(
            'tools.logs._db.query',
            side_effect=self._make_query_side_effects(),
        ):
            result = logs_tools.get_health_summary(_MOCK_CONN)

        assert result['plugins_nok'] == []
        assert result['messages_unread'] == []
        assert result['crons_running'] == []
        assert result['summary']['plugins_nok_count'] == 0
        assert result['summary']['messages_unread_count'] == 0
        assert result['summary']['crons_running_count'] == 0
        assert result['_filtered_fields'] == []

    def test_plugins_nok_returned(self):
        plugins = [
            {'plugin': 'jMQTT', 'name': 'jMQTT', 'status': 'nok'},
            {'plugin': 'zigbee', 'name': 'Zigbee2MQTT', 'status': 'nok'},
        ]
        with patch(
            'tools.logs._db.query',
            side_effect=self._make_query_side_effects(plugins_nok=plugins),
        ):
            result = logs_tools.get_health_summary(_MOCK_CONN)

        assert len(result['plugins_nok']) == 2
        assert result['plugins_nok'][0]['plugin'] == 'jMQTT'
        assert result['summary']['plugins_nok_count'] == 2

    def test_messages_unread_returned(self):
        messages = [
            {
                'plugin': 'jMQTT',
                'logicalId': 'broker1',
                'message': 'Connexion broker perdue',
                'date': '2026-05-04 10:00:00',
            },
        ]
        with patch(
            'tools.logs._db.query',
            side_effect=self._make_query_side_effects(messages=messages),
        ):
            result = logs_tools.get_health_summary(_MOCK_CONN)

        assert len(result['messages_unread']) == 1
        assert result['messages_unread'][0]['plugin'] == 'jMQTT'
        assert result['messages_unread'][0]['message'] == 'Connexion broker perdue'
        assert result['summary']['messages_unread_count'] == 1

    def test_crons_running_returned(self):
        crons = [
            {
                'class': 'jMQTT',
                'function': 'pull',
                'schedule': '* * * * *',
            },
        ]
        with patch(
            'tools.logs._db.query',
            side_effect=self._make_query_side_effects(crons=crons),
        ):
            result = logs_tools.get_health_summary(_MOCK_CONN)

        assert len(result['crons_running']) == 1
        assert result['crons_running'][0]['class'] == 'jMQTT'
        assert result['summary']['crons_running_count'] == 1

    def test_date_none_serialized_as_none(self):
        messages = [
            {'plugin': 'core', 'logicalId': None, 'message': 'Démarrage', 'date': None},
        ]
        with patch(
            'tools.logs._db.query',
            side_effect=self._make_query_side_effects(messages=messages),
        ):
            result = logs_tools.get_health_summary(_MOCK_CONN)

        assert result['messages_unread'][0]['date'] is None

    def test_date_string_preserved(self):
        messages = [
            {'plugin': 'core', 'logicalId': None, 'message': 'OK', 'date': '2026-05-04 10:00:00'},
        ]
        with patch(
            'tools.logs._db.query',
            side_effect=self._make_query_side_effects(messages=messages),
        ):
            result = logs_tools.get_health_summary(_MOCK_CONN)

        assert result['messages_unread'][0]['date'] == '2026-05-04 10:00:00'

    def test_cron_schedule_field_present(self):
        crons = [
            {'class': 'core', 'function': 'check', 'schedule': '0 * * * *'},
        ]
        with patch(
            'tools.logs._db.query',
            side_effect=self._make_query_side_effects(crons=crons),
        ):
            result = logs_tools.get_health_summary(_MOCK_CONN)

        assert result['crons_running'][0]['schedule'] == '0 * * * *'

    def test_plugins_nok_query_targets_update_table(self):
        with patch(
            'tools.logs._db.query',
            side_effect=self._make_query_side_effects(),
        ) as mock_q:
            logs_tools.get_health_summary(_MOCK_CONN)

        first_sql = mock_q.call_args_list[0][0][1]
        assert '`update`' in first_sql
        assert "status='nok'" in first_sql

    def test_messages_query_targets_message_table(self):
        with patch(
            'tools.logs._db.query',
            side_effect=self._make_query_side_effects(),
        ) as mock_q:
            logs_tools.get_health_summary(_MOCK_CONN)

        second_sql = mock_q.call_args_list[1][0][1]
        assert 'message' in second_sql
        assert 'plugin' in second_sql

    def test_crons_query_targets_daemon_crons(self):
        with patch(
            'tools.logs._db.query',
            side_effect=self._make_query_side_effects(),
        ) as mock_q:
            logs_tools.get_health_summary(_MOCK_CONN)

        third_sql = mock_q.call_args_list[2][0][1]
        assert 'cron' in third_sql
        assert 'deamon=1' in third_sql

    def test_summary_counts_match_lists(self):
        plugins = [{'plugin': 'p1', 'name': 'P1', 'status': 'nok'}]
        messages = [
            {'plugin': 's', 'logicalId': None, 'message': 'm', 'date': '2026-05-04'},
            {'plugin': 's', 'logicalId': None, 'message': 'm2', 'date': '2026-05-04'},
        ]
        with patch(
            'tools.logs._db.query',
            side_effect=self._make_query_side_effects(plugins_nok=plugins, messages=messages),
        ):
            result = logs_tools.get_health_summary(_MOCK_CONN)

        assert result['summary']['plugins_nok_count'] == len(result['plugins_nok'])
        assert result['summary']['messages_unread_count'] == len(result['messages_unread'])
