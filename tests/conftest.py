"""Shared test fixtures for DEFA Balancer integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from custom_components.defa_balancer.api import BalancerPacket
from custom_components.defa_balancer.const import (
    CONF_MULTICAST_GROUP,
    CONF_MULTICAST_PORT,
    CONF_SERIAL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MULTICAST_GROUP,
    DEFAULT_MULTICAST_PORT,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
)
from custom_components.defa_balancer.coordinator import DEFABalancerDataUpdateCoordinator
from custom_components.defa_balancer.coordinator.listeners import MockBalancerListener
from custom_components.defa_balancer.data import DEFABalancerConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from tests.test_constants import DEFAULT_MOCK_L1, DEFAULT_MOCK_L2, DEFAULT_MOCK_L3, FAKE_FIRMWARE, FAKE_SERIAL


@pytest.fixture
def mock_config_entry() -> dict[str, Any]:
    """Return a minimal config entry data dict."""
    return {
        CONF_NAME: "DEFA Balancer",
        CONF_MULTICAST_GROUP: DEFAULT_MULTICAST_GROUP,
        CONF_MULTICAST_PORT: DEFAULT_MULTICAST_PORT,
        CONF_SERIAL: FAKE_SERIAL,
        CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL_SECONDS,
    }


@pytest.fixture
def mock_packets() -> list[BalancerPacket]:
    """Return sample BalancerPacket instances for testing."""
    return [
        BalancerPacket(
            serial=FAKE_SERIAL,
            l1=DEFAULT_MOCK_L1,
            l2=DEFAULT_MOCK_L2,
            l3=DEFAULT_MOCK_L3,
            firmware=FAKE_FIRMWARE,
        ),
        BalancerPacket(
            serial=FAKE_SERIAL,
            l1=DEFAULT_MOCK_L1 + 0.1,
            l2=DEFAULT_MOCK_L2 + 0.1,
            l3=DEFAULT_MOCK_L3 + 0.1,
            firmware=FAKE_FIRMWARE,
        ),
        BalancerPacket(
            serial=FAKE_SERIAL,
            l1=DEFAULT_MOCK_L1 - 0.1,
            l2=DEFAULT_MOCK_L2 - 0.1,
            l3=DEFAULT_MOCK_L3 - 0.1,
            firmware=FAKE_FIRMWARE,
        ),
    ]


@pytest.fixture
def mock_listener(mock_packets: list[BalancerPacket]) -> MockBalancerListener:
    """Return a MockBalancerListener with sample data."""
    return MockBalancerListener(packets=mock_packets)


@pytest.fixture
async def coordinator(
    hass: HomeAssistant,
    mock_config_entry: dict[str, Any],
    mock_listener: MockBalancerListener,
) -> DEFABalancerDataUpdateCoordinator:
    """Return a DEFABalancerDataUpdateCoordinator with mock listener."""
    config_entry = MagicMock(spec=DEFABalancerConfigEntry)
    config_entry.entry_id = "test_entry_id"
    config_entry.data = mock_config_entry

    coordinator = DEFABalancerDataUpdateCoordinator(
        hass=hass,
        logger=hass.logger,
        name="DEFA Balancer",
        update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS),
        listener=mock_listener,
        config_entry=config_entry,
    )

    await coordinator.async_config_entry_first_refresh()
    return coordinator
