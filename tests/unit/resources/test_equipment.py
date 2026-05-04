"""Tests unitaires — resources/equipment.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from resources import equipment as res_equipment

_MOCK_CONN = MagicMock()
_PATCH = 'resources.equipment.equipments_tools.get_equipment'

_EQUIPMENT_RESULT = {
    'id': 10,
    'name': 'Thermostat Salon',
    'eqType_name': 'thermostat',
    'isEnable': 1,
    'commands': [{'id': 101, 'name': 'Température', 'type': 'info', 'currentValue': '21.5'}],
}


class TestReadEquipment:
    def test_delegates_to_get_equipment(self):
        with patch(_PATCH, return_value=_EQUIPMENT_RESULT) as mock:
            result = res_equipment.read(_MOCK_CONN, 10, 'apikey')
        mock.assert_called_once_with(_MOCK_CONN, 10, 'apikey')
        assert result == _EQUIPMENT_RESULT

    def test_returns_dict(self):
        with patch(_PATCH, return_value={'id': 1}):
            result = res_equipment.read(_MOCK_CONN, 1, '')
        assert isinstance(result, dict)

    def test_error_propagated(self):
        error = {'error': 'Équipement non trouvé'}
        with patch(_PATCH, return_value=error):
            result = res_equipment.read(_MOCK_CONN, 999, '')
        assert result.get('error') == 'Équipement non trouvé'

    def test_apikey_empty_by_default(self):
        with patch(_PATCH, return_value={}) as mock:
            res_equipment.read(_MOCK_CONN, 1)
        _, _, apikey_passed = mock.call_args[0]
        assert apikey_passed == ''
