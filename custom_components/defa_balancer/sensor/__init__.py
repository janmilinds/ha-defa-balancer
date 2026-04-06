"""Sensor platform for defa_balancer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.defa_balancer.const import PARALLEL_UPDATES as PARALLEL_UPDATES

from .diagnostic import DIAGNOSTIC_ENTITY_DESCRIPTIONS, DEFABalancerDiagnosticSensor
from .measurement import ENTITY_DESCRIPTIONS, DEFABalancerMeasurementSensor

if TYPE_CHECKING:
    from custom_components.defa_balancer.data import DEFABalancerConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DEFABalancerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DEFA Balancer sensors."""
    coordinator = entry.runtime_data.coordinator

    entities: list[DEFABalancerMeasurementSensor | DEFABalancerDiagnosticSensor] = [
        DEFABalancerMeasurementSensor(coordinator=coordinator, entity_description=desc) for desc in ENTITY_DESCRIPTIONS
    ]
    entities.extend(
        DEFABalancerDiagnosticSensor(coordinator=coordinator, entity_description=desc)
        for desc in DIAGNOSTIC_ENTITY_DESCRIPTIONS
    )

    async_add_entities(entities)
