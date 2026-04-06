"""Tests for DEFA Balancer options flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.defa_balancer.api import BalancerPacket
from custom_components.defa_balancer.const import (
    CONF_MULTICAST_GROUP,
    CONF_MULTICAST_PORT,
    CONF_PHASE_VOLTAGE,
    CONF_SERIAL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MULTICAST_GROUP,
    DEFAULT_MULTICAST_PORT,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from tests.test_constants import FAKE_SERIAL


class _FakeUDPListener:
    """Minimal listener for setup tests."""

    def __init__(self, packets: list[BalancerPacket]) -> None:
        self._packets = packets
        self.packet_age = 0.0
        self.start = AsyncMock()
        self.stop = AsyncMock()
        self.wait_for_packet = AsyncMock(return_value=True)

    def get_latest(self) -> list[BalancerPacket]:
        return list(self._packets)

    def get_last_packet_age(self) -> float | None:
        if not self._packets:
            return None
        return self.packet_age


def _mock_entry() -> MockConfigEntry:
    """Create a loaded config entry for options tests."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_MULTICAST_GROUP: DEFAULT_MULTICAST_GROUP,
            CONF_MULTICAST_PORT: DEFAULT_MULTICAST_PORT,
            CONF_SERIAL: FAKE_SERIAL,
            CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL_SECONDS,
        },
        entry_id="options_test_entry",
        unique_id=FAKE_SERIAL,
    )


@pytest.mark.unit
async def test_options_flow_shows_form(hass: HomeAssistant, enable_custom_integrations: None) -> None:
    """Test options flow init step shows form with phase_voltage field."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    listener = _FakeUDPListener(packets=[BalancerPacket(serial=FAKE_SERIAL, l1=8.5, l2=7.2, l3=6.9, firmware="4.0.0")])

    with patch("custom_components.defa_balancer.UDPBalancerListener", return_value=listener):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


@pytest.mark.unit
async def test_options_flow_saves_phase_voltage(hass: HomeAssistant, enable_custom_integrations: None) -> None:
    """Test options flow saves phase_voltage to entry options."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    listener = _FakeUDPListener(packets=[BalancerPacket(serial=FAKE_SERIAL, l1=8.5, l2=7.2, l3=6.9, firmware="4.0.0")])

    with patch("custom_components.defa_balancer.UDPBalancerListener", return_value=listener):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_PHASE_VOLTAGE: 120},
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_PHASE_VOLTAGE] == 120
