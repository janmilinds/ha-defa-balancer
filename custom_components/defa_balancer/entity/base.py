"""Base entity class for defa_balancer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.defa_balancer.const import CONF_SERIAL, DOMAIN
from custom_components.defa_balancer.coordinator import DEFABalancerDataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.helpers.entity import EntityDescription


class DEFABalancerEntity(CoordinatorEntity[DEFABalancerDataUpdateCoordinator]):
    """Base entity for all DEFA Balancer entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DEFABalancerDataUpdateCoordinator,
        entity_description: EntityDescription,
    ) -> None:
        """Initialize entity properties shared by all platforms."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"

        serial = coordinator.config_entry.data.get(CONF_SERIAL, coordinator.config_entry.entry_id)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"DEFA Balancer {serial}",
            manufacturer="DEFA",
            model="Balancer",
            sw_version=str(coordinator.data.get("firmware", "unknown")) if coordinator.data else None,
        )
