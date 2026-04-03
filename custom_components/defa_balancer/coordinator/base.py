"""DataUpdateCoordinator for DEFA Balancer multicast data."""

from __future__ import annotations

from datetime import timedelta
from logging import Logger
from time import monotonic
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
    DEFAULT_OFFLINE_REPAIRS_THRESHOLD_SECONDS,
    DEFAULT_PHASE_VOLTAGE,
    DEFAULT_UNAVAILABLE_TIMEOUT_SECONDS,
    DOMAIN,
    ISSUE_ID_DEVICE_UNREACHABLE_PREFIX,
)
from custom_components.defa_balancer.coordinator.listeners import BalancerListener
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
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
        self._offline_since: float | None = None
        self._offline_issue_created = ir.async_get(hass).async_get_issue(DOMAIN, self._offline_issue_id) is not None

    @property
    def _offline_issue_id(self) -> str:
        """Return issue ID scoped to the config entry."""
        return f"{ISSUE_ID_DEVICE_UNREACHABLE_PREFIX}_{self.config_entry.entry_id}"

    def _track_unavailable_state(self) -> None:
        """Track continuous offline state and create an error issue if needed."""
        now = monotonic()
        if self._offline_since is None:
            self._offline_since = now

        if self._offline_issue_created:
            return

        if now - self._offline_since < DEFAULT_OFFLINE_REPAIRS_THRESHOLD_SECONDS:
            return

        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self._offline_issue_id,
            data={"entry_id": self.config_entry.entry_id},
            is_fixable=False,
            is_persistent=True,
            severity=ir.IssueSeverity.ERROR,
            translation_key="device_unreachable",
        )
        self._offline_issue_created = True

    def _clear_unavailable_state(self) -> None:
        """Clear offline tracking and remove existing error issue on recovery."""
        self._offline_since = None
        ir.async_delete_issue(
            self.hass,
            DOMAIN,
            self._offline_issue_id,
        )
        self._offline_issue_created = False

    async def _async_update_data(self) -> dict[str, float | int | str]:
        """Aggregate latest packet values for sensors."""
        packets = self._listener.get_latest()
        if not packets:
            self._track_unavailable_state()
            raise UpdateFailed("No data received")

        last_packet_age = self._listener.get_last_packet_age()
        if last_packet_age is None or last_packet_age > DEFAULT_UNAVAILABLE_TIMEOUT_SECONDS:
            self._track_unavailable_state()
            if last_packet_age is None:
                raise UpdateFailed(f"No data received in the last {DEFAULT_UNAVAILABLE_TIMEOUT_SECONDS} seconds")

            raise UpdateFailed(
                f"No data received in the last {DEFAULT_UNAVAILABLE_TIMEOUT_SECONDS} "
                f"seconds (latest data {last_packet_age:.1f}s ago)"
            )

        self._clear_unavailable_state()

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
