"""Tests for DEFA Balancer diagnostics."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.defa_balancer.diagnostics import async_get_config_entry_diagnostics
from homeassistant.core import HomeAssistant
from tests.test_constants import FAKE_FIRMWARE, FAKE_SERIAL


def _mock_entry(serial: str = FAKE_SERIAL) -> MagicMock:
    """Return a mock config entry with runtime data."""
    entry = MagicMock()
    entry.entry_id = "diag_entry_id"
    entry.domain = "defa_balancer"
    entry.title = f"DEFA Balancer {serial}"
    entry.data = {"serial": serial, "multicast_group": "234.222.250.1", "multicast_port": 57082}
    entry.options = {}

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.last_exception = None
    coordinator.update_interval = "0:00:10"
    coordinator.data = {"l1": 8.5, "firmware": FAKE_FIRMWARE}

    listener = MagicMock()
    listener.get_last_packet_age.return_value = 2.3

    entry.runtime_data.coordinator = coordinator
    entry.runtime_data.listener = listener
    return entry


@pytest.mark.unit
async def test_diagnostics_returns_expected_structure(hass: HomeAssistant) -> None:
    """Test diagnostics returns the expected top-level keys."""
    entry = _mock_entry()
    result = await async_get_config_entry_diagnostics(hass, entry)

    assert "entry" in result
    assert "coordinator" in result


@pytest.mark.unit
async def test_diagnostics_redacts_serial(hass: HomeAssistant) -> None:
    """Test that serial is redacted in entry data."""
    entry = _mock_entry()
    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["entry"]["data"]["serial"] == "**REDACTED**"


@pytest.mark.unit
async def test_diagnostics_redacts_serial_in_title(hass: HomeAssistant) -> None:
    """Test that serial embedded in the title is also redacted."""
    entry = _mock_entry()
    result = await async_get_config_entry_diagnostics(hass, entry)

    assert FAKE_SERIAL not in result["entry"]["title"]
    assert "**REDACTED**" in result["entry"]["title"]


@pytest.mark.unit
async def test_diagnostics_includes_coordinator_data(hass: HomeAssistant) -> None:
    """Test coordinator section contains expected fields."""
    entry = _mock_entry()
    result = await async_get_config_entry_diagnostics(hass, entry)

    coord = result["coordinator"]
    assert coord["last_update_success"] is True
    assert coord["last_exception"] is None
    assert coord["packet_age_seconds"] == 2.3
    assert coord["data"]["l1"] == 8.5


@pytest.mark.unit
async def test_diagnostics_with_last_exception(hass: HomeAssistant) -> None:
    """Test diagnostics when coordinator has a last_exception."""
    entry = _mock_entry()
    entry.runtime_data.coordinator.last_exception = RuntimeError("test error")
    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["coordinator"]["last_exception"] == "test error"
