"""Set up DEFA Balancer integration."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_MULTICAST_GROUP,
    CONF_MULTICAST_PORT,
    CONF_SERIAL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MULTICAST_GROUP,
    DEFAULT_MULTICAST_PORT,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
    LOGGER,
)
from .coordinator import DEFABalancerDataUpdateCoordinator
from .coordinator.listeners import UDPBalancerListener
from .data import DEFABalancerData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import DEFABalancerConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]

# This integration is configured via config entries only
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration from YAML (config-entry only)."""
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DEFABalancerConfigEntry,
) -> bool:
    """Set up DEFA Balancer from a config entry."""
    listener = UDPBalancerListener(
        multicast_group=entry.data.get(CONF_MULTICAST_GROUP, DEFAULT_MULTICAST_GROUP),
        multicast_port=entry.data.get(CONF_MULTICAST_PORT, DEFAULT_MULTICAST_PORT),
        serial=entry.data.get(CONF_SERIAL),
    )
    await listener.start()

    if not await listener.wait_for_packet(timeout=5.0):
        await listener.stop()
        raise ConfigEntryNotReady(
            "No UDP packets received from DEFA Balancer – check device is powered on and reachable"
        )

    coordinator = DEFABalancerDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_SECONDS)),
        listener=listener,
        config_entry=entry,
    )

    entry.runtime_data = DEFABalancerData(
        listener=listener,
        coordinator=coordinator,
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: DEFABalancerConfigEntry,
) -> bool:
    """Unload a config entry and stop listener resources."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.listener.stop()
    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant,
    entry: DEFABalancerConfigEntry,
) -> None:
    """Reload a config entry after config changes."""
    await hass.config_entries.async_reload(entry.entry_id)
