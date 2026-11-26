"""Shared test fixtures for DEFA Balancer integration."""

from collections.abc import Generator
from datetime import timedelta
import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.defa_balancer.api import BalancerPacket
from custom_components.defa_balancer.const import (
    CONF_MULTICAST_GROUP,
    CONF_MULTICAST_PORT,
    CONF_SERIAL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MULTICAST_GROUP,
    DEFAULT_MULTICAST_PORT,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
)
from custom_components.defa_balancer.coordinator import DEFABalancerDataUpdateCoordinator
from custom_components.defa_balancer.coordinator.listeners import MockBalancerListener
from custom_components.defa_balancer.data import DEFABalancerConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from tests.test_constants import DEFAULT_MOCK_L1, DEFAULT_MOCK_L2, DEFAULT_MOCK_L3, FAKE_FIRMWARE, FAKE_SERIAL


@pytest.fixture(autouse=True)
def fail_on_deprecation_report(caplog: pytest.LogCaptureFixture) -> Generator[None]:
    """Fail a test when Home Assistant logs a deprecation this integration caused."""
    yield
    reports = [
        message
        for record in [*caplog.get_records("setup"), *caplog.get_records("call")]
        if record.levelno >= logging.WARNING
        and DOMAIN in (message := record.getMessage())
        and message.startswith(("Detected that custom integration", "The deprecated"))
    ]
    assert not reports, "\n".join(reports)


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
        logger=logging.getLogger(__name__),
        name="DEFA Balancer",
        update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS),
        listener=mock_listener,
        config_entry=config_entry,
    )

    await coordinator.async_config_entry_first_refresh()
    return coordinator


@pytest.fixture
def config_entry(mock_config_entry: dict[str, Any]) -> MockConfigEntry:
    """Return a config entry for this integration, not yet added to hass."""
    return MockConfigEntry(domain=DOMAIN, title="DEFA Balancer", unique_id=FAKE_SERIAL, data=mock_config_entry)


@pytest.fixture
def mock_api(mock_listener: MockBalancerListener) -> Generator[MockBalancerListener]:
    """Replace the UDP listener setup creates with one that replays the sample packets."""
    mock_listener.wait_for_packet = AsyncMock(return_value=True)  # type: ignore[attr-defined] - UDP-only method
    with patch("custom_components.defa_balancer.UDPBalancerListener", return_value=mock_listener):
        yield mock_listener


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_api: MockBalancerListener,
    config_entry: MockConfigEntry,
) -> MockConfigEntry:
    """Set up the integration from a config entry and return the loaded entry."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
