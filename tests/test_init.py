"""Tests for DEFA Balancer integration setup lifecycle."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.defa_balancer import (
    CONF_MULTICAST_GROUP,
    CONF_MULTICAST_PORT,
    CONF_SERIAL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MULTICAST_GROUP,
    DEFAULT_MULTICAST_PORT,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from test_constants import FAKE_SERIAL


def _mock_entry() -> MockConfigEntry:
    """Create a config entry for tests."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_MULTICAST_GROUP: DEFAULT_MULTICAST_GROUP,
            CONF_MULTICAST_PORT: DEFAULT_MULTICAST_PORT,
            CONF_SERIAL: FAKE_SERIAL,
            CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL_SECONDS,
        },
        entry_id="entry_test",
    )


@pytest.mark.unit
async def test_async_setup_returns_true(hass: HomeAssistant) -> None:
    """Test config-entry-only async_setup returns True."""
    assert await async_setup(hass, {}) is True


@pytest.mark.unit
async def test_async_setup_entry_success(hass: HomeAssistant) -> None:
    """Test async_setup_entry creates runtime data and forwards platforms."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    listener = MagicMock()
    listener.start = AsyncMock()
    listener.wait_for_packet = AsyncMock(return_value=True)
    listener.stop = AsyncMock()

    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with (
        patch("custom_components.defa_balancer.UDPBalancerListener", return_value=listener),
        patch("custom_components.defa_balancer.DEFABalancerDataUpdateCoordinator", return_value=coordinator),
        patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock(return_value=True)) as forward,
    ):
        assert await async_setup_entry(hass, entry) is True

    listener.start.assert_awaited_once()
    listener.wait_for_packet.assert_awaited_once_with(timeout=5.0)
    coordinator.async_config_entry_first_refresh.assert_awaited_once()
    forward.assert_awaited_once()

    assert entry.runtime_data.listener is listener
    assert entry.runtime_data.coordinator is coordinator


@pytest.mark.unit
async def test_async_setup_entry_raises_not_ready_when_no_packets(hass: HomeAssistant) -> None:
    """Test async_setup_entry raises ConfigEntryNotReady and stops listener."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    listener = MagicMock()
    listener.start = AsyncMock()
    listener.wait_for_packet = AsyncMock(return_value=False)
    listener.stop = AsyncMock()

    with (
        patch("custom_components.defa_balancer.UDPBalancerListener", return_value=listener),
        pytest.raises(ConfigEntryNotReady, match="No data received from DEFA Balancer"),
    ):
        await async_setup_entry(hass, entry)

    listener.stop.assert_awaited_once()


@pytest.mark.unit
async def test_async_unload_entry_stops_listener_on_success(hass: HomeAssistant) -> None:
    """Test async_unload_entry stops listener when unload succeeds."""
    entry = _mock_entry()
    listener = MagicMock()
    listener.stop = AsyncMock()
    entry.runtime_data = SimpleNamespace(listener=listener)

    with patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True)):
        assert await async_unload_entry(hass, entry) is True

    listener.stop.assert_awaited_once()


@pytest.mark.unit
async def test_async_unload_entry_does_not_stop_listener_on_failure(hass: HomeAssistant) -> None:
    """Test async_unload_entry does not stop listener when unload fails."""
    entry = _mock_entry()
    listener = MagicMock()
    listener.stop = AsyncMock()
    entry.runtime_data = SimpleNamespace(listener=listener)

    with patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=False)):
        assert await async_unload_entry(hass, entry) is False

    listener.stop.assert_not_awaited()
