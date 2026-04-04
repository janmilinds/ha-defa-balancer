"""DEFA Balancer diagnostic sensors."""

from __future__ import annotations

from typing import Any

from custom_components.defa_balancer.const import DATA_FIRMWARE, DATA_PACKET_COUNT
from custom_components.defa_balancer.entity import DEFABalancerEntity
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory

DIAGNOSTIC_ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key=DATA_FIRMWARE,
        translation_key="firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=DATA_PACKET_COUNT,
        translation_key="packet_count",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


class DEFABalancerDiagnosticSensor(SensorEntity, DEFABalancerEntity):
    """DEFA Balancer diagnostic sensor for non-numeric values."""

    @property
    def native_value(self) -> Any | None:
        """Return diagnostic sensor value from coordinator data."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self.entity_description.key)
