"""Repairs platform for defa_balancer."""

from __future__ import annotations

import voluptuous as vol

from custom_components.defa_balancer.const import (
    DEFAULT_UNAVAILABLE_TIMEOUT_SECONDS,
    ISSUE_ID_DEVICE_UNREACHABLE_PREFIX,
)
from homeassistant.components.repairs import RepairsFlow
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create a repair flow based on the issue_id."""
    if issue_id.startswith(f"{ISSUE_ID_DEVICE_UNREACHABLE_PREFIX}_"):
        return DeviceUnreachableRepairFlow(issue_id, data)

    return UnknownIssueRepairFlow(issue_id)


class DeviceUnreachableRepairFlow(RepairsFlow):
    """Handle a repair flow when the device has been unreachable."""

    def __init__(self, issue_id: str, data: dict[str, str | int | float | None] | None) -> None:
        """Store issue ID for delete and retry actions."""
        super().__init__()
        self._issue_id = issue_id
        self._entry_id = str(data.get("entry_id")) if data and data.get("entry_id") else None

    async def async_step_init(self, user_input: dict[str, str] | None = None) -> FlowResult:
        """Handle confirmation to retry setup for unreachable device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            entry_id = self._entry_id or self.handler
            entry = self.hass.config_entries.async_get_entry(entry_id)
            if entry is None:
                errors["base"] = "cannot_connect"
            else:
                await self.hass.config_entries.async_reload(entry.entry_id)

                reloaded_entry = self.hass.config_entries.async_get_entry(entry.entry_id)
                if reloaded_entry is None or reloaded_entry.state is not ConfigEntryState.LOADED:
                    errors["base"] = "cannot_connect"
                else:
                    listener = reloaded_entry.runtime_data.listener
                    packet_age = listener.get_last_packet_age()
                    if packet_age is None or packet_age > DEFAULT_UNAVAILABLE_TIMEOUT_SECONDS:
                        errors["base"] = "cannot_connect"
                    else:
                        # Issue is not deleted here; coordinator clears it automatically on recovery.
                        return self.async_create_entry(data={})

        return self.async_show_form(step_id="init", data_schema=vol.Schema({}), errors=errors)


class UnknownIssueRepairFlow(RepairsFlow):
    """Handler for unknown repair issues."""

    def __init__(self, issue_id: str) -> None:
        """Initialize the unknown issue repair flow."""
        super().__init__()
        self._issue_id = issue_id

    async def async_step_init(self, user_input: dict[str, str] | None = None) -> FlowResult:
        """Handle unknown issues."""
        if user_input is not None:
            # Just acknowledge and close
            return self.async_create_entry(data={})

        return self.async_show_form(step_id="init")
