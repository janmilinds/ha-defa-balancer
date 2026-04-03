"""Tests for DEFA Balancer coordinator."""

from __future__ import annotations

from datetime import timedelta
import logging
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.defa_balancer.api import BalancerPacket
from custom_components.defa_balancer.const import (
    CONF_SERIAL,
    DATA_L1,
    DATA_L1_POWER,
    DATA_L2,
    DATA_L2_POWER,
    DATA_L3,
    DATA_L3_POWER,
    DATA_TOTAL_POWER,
    DEFAULT_OFFLINE_REPAIRS_THRESHOLD_SECONDS,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
    ISSUE_ID_DEVICE_UNREACHABLE_PREFIX,
)
from custom_components.defa_balancer.coordinator import DEFABalancerDataUpdateCoordinator
from custom_components.defa_balancer.coordinator.listeners import MockBalancerListener
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import UpdateFailed
from tests.test_constants import FAKE_FIRMWARE, FAKE_SERIAL

_LOGGER = logging.getLogger(__name__)


def _make_config_entry(**kwargs: object) -> MockConfigEntry:
    """Create a MockConfigEntry for defa_balancer."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SERIAL: FAKE_SERIAL, **kwargs},
        entry_id="test_entry_id",
    )


def _make_coordinator(
    hass: HomeAssistant,
    listener: MockBalancerListener,
    config_entry: MockConfigEntry,
) -> DEFABalancerDataUpdateCoordinator:
    """Instantiate coordinator with given fixtures."""
    return DEFABalancerDataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        name="test",
        update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS),
        listener=listener,
        config_entry=config_entry,  # type: ignore[arg-type]
    )


@pytest.mark.unit
async def test_coordinator_aggregates_currents(hass: HomeAssistant, mock_packets: list[BalancerPacket]) -> None:
    """Test coordinator calculates average of L1/L2/L3 currents."""
    config_entry = _make_config_entry()
    config_entry.add_to_hass(hass)
    listener = MockBalancerListener(packets=mock_packets)
    coordinator = _make_coordinator(hass, listener, config_entry)

    await coordinator.async_refresh()

    # Mock packets: L1=[8.5, 8.6, 8.4], L2=[7.2, 7.3, 7.1], L3=[6.9, 7.0, 6.8]
    # Expected averages: L1=8.5, L2=7.2, L3=6.9
    assert coordinator.data[DATA_L1] == pytest.approx(8.5, abs=0.001)
    assert coordinator.data[DATA_L2] == pytest.approx(7.2, abs=0.001)
    assert coordinator.data[DATA_L3] == pytest.approx(6.9, abs=0.001)


@pytest.mark.unit
async def test_coordinator_calculates_power(hass: HomeAssistant, mock_packets: list[BalancerPacket]) -> None:
    """Test coordinator calculates power for each phase and total."""
    config_entry = _make_config_entry()
    config_entry.add_to_hass(hass)
    listener = MockBalancerListener(packets=mock_packets)
    coordinator = _make_coordinator(hass, listener, config_entry)

    await coordinator.async_refresh()

    # power = current * voltage (default 230V)
    assert DATA_L1_POWER in coordinator.data
    assert DATA_L2_POWER in coordinator.data
    assert DATA_L3_POWER in coordinator.data
    assert DATA_TOTAL_POWER in coordinator.data

    # Total should equal sum of phases (within floating point tolerance)
    total = coordinator.data[DATA_TOTAL_POWER]
    phase_sum = coordinator.data[DATA_L1_POWER] + coordinator.data[DATA_L2_POWER] + coordinator.data[DATA_L3_POWER]
    assert total == pytest.approx(phase_sum, abs=0.1)


@pytest.mark.unit
async def test_coordinator_fails_no_packets(hass: HomeAssistant) -> None:
    """Test coordinator raises UpdateFailed when no packets available."""
    config_entry = _make_config_entry()
    config_entry.add_to_hass(hass)
    listener = MockBalancerListener(packets=[])
    coordinator = _make_coordinator(hass, listener, config_entry)

    with pytest.raises(UpdateFailed, match="No data received"):
        await coordinator._async_update_data()


@pytest.mark.unit
async def test_coordinator_stale_timeout_triggers(hass: HomeAssistant, mock_packets: list[BalancerPacket]) -> None:
    """Test coordinator raises UpdateFailed when packet age exceeds timeout."""
    config_entry = _make_config_entry()
    config_entry.add_to_hass(hass)
    listener = MockBalancerListener(packets=mock_packets)
    coordinator = _make_coordinator(hass, listener, config_entry)

    # Simulate packets being old (20 seconds ago, over the 15s threshold)
    with (
        patch.object(listener, "get_last_packet_age", return_value=20.0),
        pytest.raises(UpdateFailed, match="No data received in the last"),
    ):
        await coordinator._async_update_data()


@pytest.mark.unit
async def test_coordinator_rounds_currents_to_3_decimals(
    hass: HomeAssistant, mock_packets: list[BalancerPacket]
) -> None:
    """Test coordinator rounds currents to 3 decimal places."""
    config_entry = _make_config_entry()
    config_entry.add_to_hass(hass)
    # Single packet with exact value to verify rounding
    packet = BalancerPacket(serial=FAKE_SERIAL, l1=8.54321, l2=7.23456, l3=6.87654, firmware=FAKE_FIRMWARE)
    listener = MockBalancerListener(packets=[packet])
    coordinator = _make_coordinator(hass, listener, config_entry)

    await coordinator.async_refresh()

    l1 = coordinator.data[DATA_L1]
    assert l1 == round(8.54321, 3)


@pytest.mark.unit
async def test_coordinator_rounds_power_to_1_decimal(hass: HomeAssistant, mock_packets: list[BalancerPacket]) -> None:
    """Test coordinator rounds power to 1 decimal place."""
    config_entry = _make_config_entry()
    config_entry.add_to_hass(hass)
    packet = BalancerPacket(serial=FAKE_SERIAL, l1=8.54321, l2=7.23456, l3=6.87654, firmware=FAKE_FIRMWARE)
    listener = MockBalancerListener(packets=[packet])
    coordinator = _make_coordinator(hass, listener, config_entry)

    await coordinator.async_refresh()

    l1_power = coordinator.data[DATA_L1_POWER]
    # 8.54321 * 230 = 1964.9383 -> rounded to 1 decimal = 1964.9
    assert l1_power == round(8.54321 * 230, 1)


@pytest.mark.unit
async def test_coordinator_uses_phase_voltage_230(
    hass: HomeAssistant,
) -> None:
    """Test coordinator multiplies current by 230V for power."""
    config_entry = _make_config_entry()
    config_entry.add_to_hass(hass)
    packet = BalancerPacket(serial=FAKE_SERIAL, l1=1.0, l2=1.0, l3=1.0, firmware=FAKE_FIRMWARE)
    listener = MockBalancerListener(packets=[packet])
    coordinator = _make_coordinator(hass, listener, config_entry)

    await coordinator.async_refresh()

    # With 1A per phase and 230V: each phase power should be 230W
    assert coordinator.data[DATA_L1_POWER] == pytest.approx(230.0, abs=0.1)
    assert coordinator.data[DATA_L2_POWER] == pytest.approx(230.0, abs=0.1)
    assert coordinator.data[DATA_L3_POWER] == pytest.approx(230.0, abs=0.1)
    assert coordinator.data[DATA_TOTAL_POWER] == pytest.approx(690.0, abs=0.1)


@pytest.mark.unit
async def test_coordinator_creates_unreachable_issue_after_threshold(
    hass: HomeAssistant,
    mock_packets: list[BalancerPacket],
) -> None:
    """Test warning issue is created after continuous offline period."""
    config_entry = _make_config_entry()
    config_entry.add_to_hass(hass)
    listener = MockBalancerListener(packets=mock_packets)
    coordinator = _make_coordinator(hass, listener, config_entry)

    issue_id = f"{ISSUE_ID_DEVICE_UNREACHABLE_PREFIX}_{config_entry.entry_id}"

    with (
        patch.object(listener, "get_last_packet_age", return_value=20.0),
        patch("custom_components.defa_balancer.coordinator.base.monotonic", side_effect=[100.0, 161.0]),
        pytest.raises(UpdateFailed),
    ):
        await coordinator._async_update_data()

    with (
        patch.object(listener, "get_last_packet_age", return_value=20.0),
        patch("custom_components.defa_balancer.coordinator.base.monotonic", return_value=161.0),
        pytest.raises(UpdateFailed),
    ):
        await coordinator._async_update_data()

    issue = ir.async_get(hass).async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.translation_key == "device_unreachable"
    assert issue.severity == ir.IssueSeverity.ERROR
    assert issue.is_persistent is True


@pytest.mark.unit
async def test_coordinator_clears_unreachable_issue_on_recovery(
    hass: HomeAssistant,
    mock_packets: list[BalancerPacket],
) -> None:
    """Test warning issue is deleted after device recovers."""
    config_entry = _make_config_entry()
    config_entry.add_to_hass(hass)
    listener = MockBalancerListener(packets=mock_packets)
    coordinator = _make_coordinator(hass, listener, config_entry)

    issue_id = f"{ISSUE_ID_DEVICE_UNREACHABLE_PREFIX}_{config_entry.entry_id}"

    with (
        patch.object(listener, "get_last_packet_age", return_value=20.0),
        patch(
            "custom_components.defa_balancer.coordinator.base.monotonic",
            side_effect=[200.0, 200.0 + DEFAULT_OFFLINE_REPAIRS_THRESHOLD_SECONDS],
        ),
        pytest.raises(UpdateFailed),
    ):
        await coordinator._async_update_data()

    with (
        patch.object(listener, "get_last_packet_age", return_value=20.0),
        patch(
            "custom_components.defa_balancer.coordinator.base.monotonic",
            return_value=200.0 + DEFAULT_OFFLINE_REPAIRS_THRESHOLD_SECONDS,
        ),
        pytest.raises(UpdateFailed),
    ):
        await coordinator._async_update_data()

    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is not None

    with patch.object(listener, "get_last_packet_age", return_value=1.0):
        await coordinator._async_update_data()

    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None


@pytest.mark.unit
async def test_coordinator_clears_existing_issue_on_recovery_even_if_flag_not_set(
    hass: HomeAssistant,
    mock_packets: list[BalancerPacket],
) -> None:
    """Test stale existing issue is cleared on recovery after restart/reload."""
    config_entry = _make_config_entry()
    config_entry.add_to_hass(hass)
    listener = MockBalancerListener(packets=mock_packets)
    coordinator = _make_coordinator(hass, listener, config_entry)

    issue_id = f"{ISSUE_ID_DEVICE_UNREACHABLE_PREFIX}_{config_entry.entry_id}"
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        data={"entry_id": config_entry.entry_id},
        is_fixable=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key="device_unreachable",
    )

    # Simulate restart/reload case where issue exists but runtime flag is reset.
    coordinator._offline_issue_created = False

    with patch.object(listener, "get_last_packet_age", return_value=1.0):
        await coordinator._async_update_data()

    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None


@pytest.mark.unit
async def test_coordinator_initializes_issue_flag_from_registry(
    hass: HomeAssistant,
    mock_packets: list[BalancerPacket],
) -> None:
    """Test coordinator picks up pre-existing unreachable issue after restart."""
    config_entry = _make_config_entry()
    config_entry.add_to_hass(hass)
    issue_id = f"{ISSUE_ID_DEVICE_UNREACHABLE_PREFIX}_{config_entry.entry_id}"

    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        data={"entry_id": config_entry.entry_id},
        is_fixable=True,
        is_persistent=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key="device_unreachable",
    )

    listener = MockBalancerListener(packets=mock_packets)
    coordinator = _make_coordinator(hass, listener, config_entry)

    assert coordinator._offline_issue_created is True
