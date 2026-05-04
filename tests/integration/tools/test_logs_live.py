"""Tests d'intégration live — tools/logs.py (Famille 5, 3 tools)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from tools import logs as logs_tools

pytestmark = pytest.mark.integration

_HOLMES_LOG_NAME = 'holmesMcp'


# ---------------------------------------------------------------------------
# list_log_files
# ---------------------------------------------------------------------------


class TestListLogFilesLive:
    def test_structure(self):
        result = logs_tools.list_log_files()
        assert 'log_files' in result
        assert 'total' in result
        assert isinstance(result['log_files'], list)

    def test_au_moins_un_log(self):
        result = logs_tools.list_log_files()
        assert result['total'] >= 1, 'Aucun fichier de log trouvé'

    def test_total_coherent(self):
        result = logs_tools.list_log_files()
        assert result['total'] == len(result['log_files'])

    def test_champs_log(self):
        result = logs_tools.list_log_files()
        if result['total'] == 0:
            pytest.skip('Aucun log disponible')
        log = result['log_files'][0]
        assert 'name' in log, 'Champ name manquant'

    def test_holmes_log_present(self):
        result = logs_tools.list_log_files()
        names = [f['name'] for f in result['log_files']]
        assert _HOLMES_LOG_NAME in names, f'{_HOLMES_LOG_NAME!r} absent de la liste : {names[:10]}'


# ---------------------------------------------------------------------------
# tail_log
# ---------------------------------------------------------------------------


class TestTailLogLive:
    def test_structure_holmes_log(self):
        result = logs_tools.tail_log(_HOLMES_LOG_NAME)
        assert 'log_file' in result or 'error' in result

    def test_holmes_log_accessible(self):
        result = logs_tools.tail_log(_HOLMES_LOG_NAME, lines=10)
        assert 'error' not in result, f'Erreur inattendue : {result.get("error")}'
        assert 'lines' in result
        assert 'count' in result
        assert isinstance(result['lines'], list)

    def test_lines_cap(self):
        result = logs_tools.tail_log(_HOLMES_LOG_NAME, lines=5)
        assert 'error' not in result
        assert result['count'] <= 5

    def test_lines_max_500(self):
        result = logs_tools.tail_log(_HOLMES_LOG_NAME, lines=1000)
        assert 'error' not in result
        assert result['count'] <= 500

    def test_grep_filtre(self):
        result = logs_tools.tail_log(_HOLMES_LOG_NAME, lines=200, grep='holmes')
        if result.get('count', 0) == 0:
            pytest.skip('Aucune ligne avec "holmes" dans le log')
        for line in result['lines']:
            assert 'holmes' in line.lower(), (
                f'Ligne sans "holmes" dans le résultat filtré : {line!r}'
            )

    def test_log_inexistant(self):
        result = logs_tools.tail_log('__log_inexistant_xyz_holmes__')
        assert 'error' in result
        assert result.get('count', 0) == 0
        assert result.get('lines', []) == []

    def test_log_first_available(self, first_log_name):
        result = logs_tools.tail_log(first_log_name, lines=5)
        assert 'error' not in result, f'Erreur sur {first_log_name!r} : {result.get("error")}'


# ---------------------------------------------------------------------------
# get_health_summary
# ---------------------------------------------------------------------------


class TestGetHealthSummaryLive:
    def test_structure(self, db_conn):
        result = logs_tools.get_health_summary(db_conn)
        assert 'plugins_nok' in result
        assert 'messages_unread' in result
        assert 'crons_running' in result
        assert 'summary' in result
        assert '_filtered_fields' in result

    def test_listes_sont_listes(self, db_conn):
        result = logs_tools.get_health_summary(db_conn)
        assert isinstance(result['plugins_nok'], list)
        assert isinstance(result['messages_unread'], list)
        assert isinstance(result['crons_running'], list)

    def test_summary_coherent(self, db_conn):
        result = logs_tools.get_health_summary(db_conn)
        summary = result['summary']
        assert summary['plugins_nok_count'] == len(result['plugins_nok'])
        assert summary['messages_unread_count'] == len(result['messages_unread'])
        assert summary['crons_running_count'] == len(result['crons_running'])

    def test_summary_champs(self, db_conn):
        result = logs_tools.get_health_summary(db_conn)
        summary = result['summary']
        for key in ('plugins_nok_count', 'messages_unread_count', 'crons_running_count'):
            assert key in summary, f'Clé manquante dans summary : {key}'
            assert isinstance(summary[key], int)
            assert summary[key] >= 0

    def test_champs_message_si_present(self, db_conn):
        result = logs_tools.get_health_summary(db_conn)
        for msg in result['messages_unread']:
            for field in ('plugin', 'logicalId', 'message', 'date'):
                assert field in msg, f'Champ manquant dans message : {field}'

    def test_champs_cron_si_present(self, db_conn):
        result = logs_tools.get_health_summary(db_conn)
        for cron in result['crons_running']:
            for field in ('class', 'function', 'schedule'):
                assert field in cron, f'Champ manquant dans cron : {field}'

    def test_pas_de_filtrage_inattendu(self, db_conn):
        result = logs_tools.get_health_summary(db_conn)
        assert result['_filtered_fields'] == []
