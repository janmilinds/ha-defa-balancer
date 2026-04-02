"""Tests for DEFA Balancer sensor platform."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

from homeassistant.const import UnitOfElectricCurrent, UnitOfPower

# Add custom_components to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.defa_balancer.const import (
    DATA_L1,
    DATA_L1_POWER,
    DATA_L2,
    DATA_L2_POWER,
    DATA_L3,
    DATA_L3_POWER,
    DATA_TOTAL_POWER,
)
from custom_components.defa_balancer.entity.base import DEFABalancerEntity
from custom_components.defa_balancer.sensor.measurement import ENTITY_DESCRIPTIONS, DEFABalancerMeasurementSensor


@pytest.mark.unit
def test_all_seven_sensors_described() -> None:
    """Test all 7 sensors have entity descriptions."""
    assert len(ENTITY_DESCRIPTIONS) == 7


@pytest.mark.unit
def test_sensor_description_keys_in_order() -> None:
    """Test sensor descriptions have expected keys in order."""
    keys = [desc.key for desc in ENTITY_DESCRIPTIONS]
    assert keys == [
        DATA_L1,
        DATA_L2,
        DATA_L3,
        DATA_L1_POWER,
        DATA_L2_POWER,
        DATA_L3_POWER,
        DATA_TOTAL_POWER,
    ]


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
