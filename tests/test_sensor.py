"""Tests for DEFA Balancer sensor platform."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.defa_balancer.const import (
    DATA_L1,
    DATA_L1_POWER,
    DATA_L2,
    DATA_L2_POWER,
    DATA_L3,
    DATA_L3_POWER,
    DATA_TOTAL_POWER,
)
from custom_components.defa_balancer.entity import DEFABalancerEntity
from custom_components.defa_balancer.sensor.diagnostic import (
    DIAGNOSTIC_ENTITY_DESCRIPTIONS,
    DEFABalancerDiagnosticSensor,
)
from custom_components.defa_balancer.sensor.measurement import ENTITY_DESCRIPTIONS, DEFABalancerMeasurementSensor
from homeassistant.const import EntityCategory, UnitOfElectricCurrent, UnitOfPower
from tests.test_constants import FAKE_FIRMWARE, FAKE_SERIAL


def _mock_coordinator(data: dict[str, object] | None = None) -> MagicMock:
    """Create a minimal coordinator mock for entity tests."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "entry_1"
    coordinator.config_entry.data = {"serial": FAKE_SERIAL}
    coordinator.data = data
    return coordinator


@pytest.mark.unit
def test_all_seven_sensors_described() -> None:
    """Test all 7 sensors have entity descriptions."""
    assert len(ENTITY_DESCRIPTIONS) == 7


@pytest.mark.unit
def test_sensor_description_keys_complete() -> None:
    """Test sensor descriptions contain all expected keys."""
    keys = {desc.key for desc in ENTITY_DESCRIPTIONS}
    assert keys == {
        DATA_L1,
        DATA_L2,
        DATA_L3,
        DATA_L1_POWER,
        DATA_L2_POWER,
        DATA_L3_POWER,
        DATA_TOTAL_POWER,
    }


@pytest.mark.unit
def test_current_sensor_unit_of_measurement() -> None:
    """Test current sensor descriptions specify amperes."""
    for desc in ENTITY_DESCRIPTIONS[:3]:  # L1, L2, L3 current (first 3)
        assert desc.native_unit_of_measurement == UnitOfElectricCurrent.AMPERE


@pytest.mark.unit
def test_power_sensor_unit_of_measurement() -> None:
    """Test power sensor descriptions specify watts."""
    for desc in ENTITY_DESCRIPTIONS[3:]:  # L1, L2, L3, total power (last 4)
        assert desc.native_unit_of_measurement == UnitOfPower.WATT


@pytest.mark.unit
def test_sensor_precision_current_3_decimals() -> None:
    """Test current sensors have 3 decimal display precision."""
    for desc in ENTITY_DESCRIPTIONS[:3]:  # L1, L2, L3 current
        assert desc.suggested_display_precision == 3


@pytest.mark.unit
def test_sensor_precision_power_1_decimal() -> None:
    """Test power sensors have 1 decimal display precision."""
    for desc in ENTITY_DESCRIPTIONS[3:]:  # L1, L2, L3, total power
        assert desc.suggested_display_precision == 1


@pytest.mark.unit
def test_sensor_translation_keys() -> None:
    """Test all sensors use translation keys."""
    expected_keys = [
        "l1_current",
        "l2_current",
        "l3_current",
        "l1_power",
        "l2_power",
        "l3_power",
        "total_power",
    ]
    for desc, expected_key in zip(ENTITY_DESCRIPTIONS, expected_keys, strict=True):
        assert desc.translation_key == expected_key


@pytest.mark.unit
def test_sensor_is_subclass_of_base_entity() -> None:
    """Test DEFABalancerMeasurementSensor inherits from DEFABalancerEntity."""
    assert issubclass(DEFABalancerMeasurementSensor, DEFABalancerEntity)


@pytest.mark.unit
def test_sensor_native_value_returns_number_from_coordinator_data() -> None:
    """Test native_value returns numeric values from coordinator data."""
    coordinator = _mock_coordinator(data={DATA_L1: 8.5})
    entity = DEFABalancerMeasurementSensor(coordinator, ENTITY_DESCRIPTIONS[0])

    assert entity.native_value == 8.5


@pytest.mark.unit
def test_sensor_native_value_returns_none_when_data_missing() -> None:
    """Test native_value returns None when coordinator has no data."""
    coordinator = _mock_coordinator(data=None)
    entity = DEFABalancerMeasurementSensor(coordinator, ENTITY_DESCRIPTIONS[0])

    assert entity.native_value is None


@pytest.mark.unit
def test_sensor_native_value_returns_none_for_non_numeric() -> None:
    """Test native_value returns None for non-numeric coordinator values."""
    coordinator = _mock_coordinator(data={DATA_L1: "not-a-number"})
    entity = DEFABalancerMeasurementSensor(coordinator, ENTITY_DESCRIPTIONS[0])

    assert entity.native_value is None


@pytest.mark.unit
def test_entity_device_info_contains_serial_and_firmware() -> None:
    """Test base entity device_info includes expected metadata."""
    coordinator = _mock_coordinator(data={"firmware": FAKE_FIRMWARE})
    entity = DEFABalancerMeasurementSensor(coordinator, ENTITY_DESCRIPTIONS[0])

    assert entity.unique_id == "entry_1_l1"
    assert entity.device_info is not None
    assert entity.device_info["serial_number"] == FAKE_SERIAL
    assert entity.device_info["manufacturer"] == "DEFA"
    assert entity.device_info["model"] == "DEFA Balancer"
    assert entity.device_info["sw_version"] == FAKE_FIRMWARE


@pytest.mark.unit
def test_entity_device_info_firmware_none_when_coordinator_data_none() -> None:
    """Test firmware is None in device_info when coordinator has no data."""
    coordinator = _mock_coordinator(data=None)
    entity = DEFABalancerMeasurementSensor(coordinator, ENTITY_DESCRIPTIONS[0])

    assert entity.device_info is not None
    assert entity.device_info["sw_version"] is None


# --- Diagnostic sensor tests ---


@pytest.mark.unit
def test_diagnostic_entity_descriptions_count() -> None:
    """Test there are 2 diagnostic entity descriptions."""
    assert len(DIAGNOSTIC_ENTITY_DESCRIPTIONS) == 2


@pytest.mark.unit
def test_diagnostic_entity_descriptions_are_diagnostic_category() -> None:
    """Test diagnostic descriptions have EntityCategory.DIAGNOSTIC."""
    for desc in DIAGNOSTIC_ENTITY_DESCRIPTIONS:
        assert desc.entity_category == EntityCategory.DIAGNOSTIC


@pytest.mark.unit
def test_diagnostic_entity_descriptions_disabled_by_default() -> None:
    """Test diagnostic descriptions are disabled by default."""
    for desc in DIAGNOSTIC_ENTITY_DESCRIPTIONS:
        assert desc.entity_registry_enabled_default is False


@pytest.mark.unit
def test_diagnostic_sensor_native_value_returns_firmware() -> None:
    """Test diagnostic sensor returns firmware from coordinator data."""
    coordinator = _mock_coordinator(data={"firmware": FAKE_FIRMWARE, "packet_count": 42})
    entity = DEFABalancerDiagnosticSensor(coordinator, DIAGNOSTIC_ENTITY_DESCRIPTIONS[0])

    assert entity.native_value == FAKE_FIRMWARE


@pytest.mark.unit
def test_diagnostic_sensor_native_value_returns_packet_count() -> None:
    """Test diagnostic sensor returns packet_count from coordinator data."""
    coordinator = _mock_coordinator(data={"firmware": FAKE_FIRMWARE, "packet_count": 42})
    entity = DEFABalancerDiagnosticSensor(coordinator, DIAGNOSTIC_ENTITY_DESCRIPTIONS[1])

    assert entity.native_value == 42


@pytest.mark.unit
def test_diagnostic_sensor_native_value_returns_none_when_no_data() -> None:
    """Test diagnostic sensor returns None when coordinator has no data."""
    coordinator = _mock_coordinator(data=None)
    entity = DEFABalancerDiagnosticSensor(coordinator, DIAGNOSTIC_ENTITY_DESCRIPTIONS[0])

    assert entity.native_value is None


@pytest.mark.unit
def test_diagnostic_sensor_is_subclass_of_base_entity() -> None:
    """Test DEFABalancerDiagnosticSensor inherits from DEFABalancerEntity."""
    assert issubclass(DEFABalancerDiagnosticSensor, DEFABalancerEntity)
