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

    entry_payload = {
        "entry_id": entry.entry_id,
        "domain": entry.domain,
        "title": entry.title,
        "data": dict(entry.data),
        "options": dict(entry.options),
    }

    # Ensure serial in the title is redacted (title may contain the serial).
    serial_in_entry = (entry_payload.get("data") or {}).get("serial")
    if serial_in_entry and isinstance(entry_payload.get("title"), str):
        entry_payload["title"] = entry_payload["title"].replace(serial_in_entry, "**REDACTED**")

    return {
        "entry": async_redact_data(entry_payload, TO_REDACT),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_exception": str(coordinator.last_exception) if coordinator.last_exception else None,
            "packet_age_seconds": entry.runtime_data.listener.get_last_packet_age(),
            "update_interval": str(coordinator.update_interval),
            "data": coordinator.data,
        },
    }
