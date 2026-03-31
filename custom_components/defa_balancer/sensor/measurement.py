"""DEFA Balancer current and power sensors."""

from __future__ import annotations

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
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import UnitOfElectricCurrent, UnitOfPower

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key=DATA_L1,
        translation_key="l1_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
    ),
    SensorEntityDescription(
        key=DATA_L2,
        translation_key="l2_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
    ),
    SensorEntityDescription(
        key=DATA_L3,
        translation_key="l3_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
    ),
    SensorEntityDescription(
        key=DATA_L1_POWER,
        translation_key="l1_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key=DATA_L2_POWER,
        translation_key="l2_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key=DATA_L3_POWER,
        translation_key="l3_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key=DATA_TOTAL_POWER,
        translation_key="total_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
)


class DEFABalancerMeasurementSensor(SensorEntity, DEFABalancerEntity):
    """DEFA Balancer sensor backed by coordinator data."""

    @property
    def native_value(self) -> float | int | None:
        """Return sensor value from coordinator data."""
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get(self.entity_description.key)
        if isinstance(value, (float, int)):
            return value
        return None
