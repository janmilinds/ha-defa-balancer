"""Diagnostics support for defa_balancer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from custom_components.defa_balancer.const import DOMAIN, ISSUE_ID_DEVICE_UNREACHABLE_PREFIX
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.redact import async_redact_data

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import DEFABalancerConfigEntry

TO_REDACT = {"entry_id", "serial"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: DEFABalancerConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    issue_registry = ir.async_get(hass)
    expected_issue_id = f"{ISSUE_ID_DEVICE_UNREACHABLE_PREFIX}_{entry.entry_id}"
    issue = issue_registry.async_get_issue(DOMAIN, expected_issue_id)
    issues = [issue] if issue and (not issue.data or issue.data.get("entry_id") == entry.entry_id) else []

    entry_payload = {
        "entry_id": entry.entry_id,
        "domain": entry.domain,
        "title": entry.title,
        "data": dict(entry.data),
        "options": dict(entry.options),
    }

    return {
        "entry": async_redact_data(entry_payload, TO_REDACT),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_exception": str(coordinator.last_exception) if coordinator.last_exception else None,
            "packet_age_seconds": entry.runtime_data.listener.get_last_packet_age(),
            "update_interval": str(coordinator.update_interval),
            "data": coordinator.data,
        },
        "issues": [
            {
                "issue_id": issue.issue_id,
                "severity": issue.severity,
                "translation_key": issue.translation_key,
                "is_fixable": issue.is_fixable,
                "data": async_redact_data(issue.data or {}, TO_REDACT),
            }
            for issue in issues
        ],
    }
