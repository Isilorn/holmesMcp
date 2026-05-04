"""Tests unitaires — resources/scenario.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from resources import scenario as res_scenario

_MOCK_CONN = MagicMock()
_PATCH_DESC = 'resources.scenario.scenarios_tools.describe_scenario'
_PATCH_LOG = 'resources.scenario.scenarios_tools.get_scenario_log'

_DESCRIBE_RESULT = {
    'id': 42,
    'name': 'Réveil Salon',
    'description': 'Allume la lumière du salon',
    'state': 'stop',
    'lastLaunch': '2026-05-04 08:00:00',
}
_LOG_RESULT = {
    'log_file': 'scenarioLog/scenario42.log',
    'lines': ['2026-05-04 08:00:01 [INFO] Scénario démarré'],
    'count': 1,
}


class TestReadScenario:
    def test_combines_describe_and_log(self):
        with (
            patch(_PATCH_DESC, return_value=_DESCRIBE_RESULT) as m_desc,
            patch(_PATCH_LOG, return_value=_LOG_RESULT) as m_log,
        ):
            result = res_scenario.read(_MOCK_CONN, 42, 'apikey')

        m_desc.assert_called_once_with(_MOCK_CONN, 42, 'apikey')
        m_log.assert_called_once_with(_MOCK_CONN, 42, lines=50)
        assert result['id'] == 42
        assert result['name'] == 'Réveil Salon'
        assert 'last_run_log' in result
        assert result['last_run_log'] == _LOG_RESULT

    def test_describe_fields_preserved(self):
        with (
            patch(_PATCH_DESC, return_value=dict(_DESCRIBE_RESULT)),
            patch(_PATCH_LOG, return_value=_LOG_RESULT),
        ):
            result = res_scenario.read(_MOCK_CONN, 42, '')

        for key in _DESCRIBE_RESULT:
            assert key in result

    def test_error_from_describe_propagated(self):
        error_result = {'error': 'Scénario non trouvé'}
        with (
            patch(_PATCH_DESC, return_value=error_result),
            patch(_PATCH_LOG, return_value={'error': 'Not found'}),
        ):
            result = res_scenario.read(_MOCK_CONN, 99, '')
        assert result.get('error') == 'Scénario non trouvé'

    def test_apikey_empty_by_default(self):
        with (
            patch(_PATCH_DESC, return_value={}) as m_desc,
            patch(_PATCH_LOG, return_value={}),
        ):
            res_scenario.read(_MOCK_CONN, 1)
        _, _, apikey_passed = m_desc.call_args[0]
        assert apikey_passed == ''

    def test_log_lines_capped_at_50(self):
        with (
            patch(_PATCH_DESC, return_value={}),
            patch(_PATCH_LOG, return_value={}) as m_log,
        ):
            res_scenario.read(_MOCK_CONN, 1, '')
        assert m_log.call_args[1]['lines'] == 50
