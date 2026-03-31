"""DataUpdateCoordinator for DEFA Balancer multicast data."""

from __future__ import annotations

from datetime import timedelta
from logging import Logger
from typing import TYPE_CHECKING

from custom_components.defa_balancer.const import (
    DATA_FIRMWARE,
    DATA_L1,
    DATA_L1_POWER,
    DATA_L2,
    DATA_L2_POWER,
    DATA_L3,
    DATA_L3_POWER,
    DATA_PACKET_COUNT,
    DATA_TOTAL_POWER,
    DEFAULT_PHASE_VOLTAGE,
)
from custom_components.defa_balancer.coordinator.listeners import BalancerListener
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

if TYPE_CHECKING:
    from custom_components.defa_balancer.data import DEFABalancerConfigEntry


class DEFABalancerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, float | int | str]]):
    """Coordinate packet aggregation for entity updates."""

    config_entry: DEFABalancerConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        logger: Logger,
        name: str,
        update_interval: timedelta,
        listener: BalancerListener,
        config_entry: DEFABalancerConfigEntry,
    ) -> None:
        """Initialize coordinator instance."""
        super().__init__(
            hass=hass,
            logger=logger,
            name=name,
            update_interval=update_interval,
            config_entry=config_entry,
        )
        self._listener = listener

    async def _async_update_data(self) -> dict[str, float | int | str]:
        """Aggregate latest packet values for sensors."""
        packets = self._listener.get_latest()
        if not packets:
            raise UpdateFailed("No packets received")

        packet_count = len(packets)
        l1 = sum(packet.l1 for packet in packets) / packet_count
        l2 = sum(packet.l2 for packet in packets) / packet_count
        l3 = sum(packet.l3 for packet in packets) / packet_count

        l1_power = l1 * DEFAULT_PHASE_VOLTAGE
        l2_power = l2 * DEFAULT_PHASE_VOLTAGE
        l3_power = l3 * DEFAULT_PHASE_VOLTAGE

        return {
            DATA_L1: round(l1, 3),
            DATA_L2: round(l2, 3),
            DATA_L3: round(l3, 3),
            DATA_L1_POWER: round(l1_power, 1),
            DATA_L2_POWER: round(l2_power, 1),
            DATA_L3_POWER: round(l3_power, 1),
            DATA_TOTAL_POWER: round(l1_power + l2_power + l3_power, 1),
            DATA_FIRMWARE: packets[-1].firmware,
            DATA_PACKET_COUNT: packet_count,
        }
