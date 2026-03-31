"""Diagnostics support for defa_balancer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.redact import async_redact_data

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import DEFABalancerConfigEntry

TO_REDACT = {"serial"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: DEFABalancerConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator

    return {
        "entry": {
            "entry_id": entry.entry_id,
            "domain": entry.domain,
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
            "data": coordinator.data,
        },
    }
