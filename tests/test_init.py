"""Tests for DEFA Balancer integration setup lifecycle."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.defa_balancer import (
    CONF_MULTICAST_GROUP,
    CONF_MULTICAST_PORT,
    CONF_SERIAL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MULTICAST_GROUP,
    DEFAULT_MULTICAST_PORT,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
    async_reload_entry,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.defa_balancer.api import BalancerPacket
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
from homeassistant.util.dt import utcnow
from tests.test_constants import FAKE_SERIAL


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


class _FakeUDPListener:
    """Minimal listener used for integration-style setup tests."""

    def __init__(self, packets: list[BalancerPacket]) -> None:
        self._packets = packets
        self.packet_age = 0.0
        self.start = AsyncMock()
        self.stop = AsyncMock()
        self.wait_for_packet = AsyncMock(return_value=True)

    def get_latest(self) -> list[BalancerPacket]:
        """Return latest packets snapshot."""
        return list(self._packets)

    def get_last_packet_age(self) -> float | None:
        """Return packet freshness for coordinator checks."""
        if not self._packets:
            return None
        return self.packet_age


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


@pytest.mark.integration
async def test_e2e_setup_entry_creates_sensor_entities(
    hass: HomeAssistant,
    enable_custom_integrations: None,
) -> None:
    """E2E: config entry setup creates 7 sensor entities with valid states."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    listener = _FakeUDPListener(
        packets=[
            BalancerPacket(serial=FAKE_SERIAL, l1=8.5, l2=7.2, l3=6.9, firmware="4.0.0"),
        ]
    )

    with patch("custom_components.defa_balancer.UDPBalancerListener", return_value=listener):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert len(entities) == 7

    for entity in entities:
        assert hass.states.get(entity.entity_id) is not None


@pytest.mark.integration
async def test_e2e_refresh_updates_sensor_state(
    hass: HomeAssistant,
    enable_custom_integrations: None,
) -> None:
    """E2E: coordinator refresh updates all 7 sensor state values."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    listener = _FakeUDPListener(
        packets=[
            BalancerPacket(serial=FAKE_SERIAL, l1=8.5, l2=7.2, l3=6.9, firmware="4.0.0"),
        ]
    )

    with patch("custom_components.defa_balancer.UDPBalancerListener", return_value=listener):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        registry = er.async_get(hass)
        entities = er.async_entries_for_config_entry(registry, entry.entry_id)

        def _state(suffix: str) -> float:
            entity = next(e for e in entities if e.unique_id.endswith(suffix))
            return float(hass.states.get(entity.entity_id).state)  # type: ignore[union-attr]

        # Initial values: l1=8.5, l2=7.2, l3=6.9, voltage=230V
        assert _state("_l1") == pytest.approx(8.5, abs=0.001)
        assert _state("_l2") == pytest.approx(7.2, abs=0.001)
        assert _state("_l3") == pytest.approx(6.9, abs=0.001)
        assert _state("_l1_power") == pytest.approx(1955.0, abs=0.1)
        assert _state("_l2_power") == pytest.approx(1656.0, abs=0.1)
        assert _state("_l3_power") == pytest.approx(1587.0, abs=0.1)
        assert _state("_total_power") == pytest.approx(5198.0, abs=0.1)

        # Update l1 only — only l1, l1_power and total_power should change
        listener._packets = [
            BalancerPacket(serial=FAKE_SERIAL, l1=9.1, l2=7.2, l3=6.9, firmware="4.0.0"),
        ]
        await entry.runtime_data.coordinator.async_request_refresh()
        await hass.async_block_till_done()

        assert _state("_l1") == pytest.approx(9.1, abs=0.001)
        assert _state("_l2") == pytest.approx(7.2, abs=0.001)
        assert _state("_l3") == pytest.approx(6.9, abs=0.001)
        assert _state("_l1_power") == pytest.approx(2093.0, abs=0.1)
        assert _state("_l2_power") == pytest.approx(1656.0, abs=0.1)
        assert _state("_l3_power") == pytest.approx(1587.0, abs=0.1)
        assert _state("_total_power") == pytest.approx(5336.0, abs=0.1)


@pytest.mark.integration
async def test_e2e_unload_entry_removes_sensor_states(
    hass: HomeAssistant,
    enable_custom_integrations: None,
) -> None:
    """E2E: unloading config entry removes entity states and stops listener."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    listener = _FakeUDPListener(
        packets=[
            BalancerPacket(serial=FAKE_SERIAL, l1=8.5, l2=7.2, l3=6.9, firmware="4.0.0"),
        ]
    )

    with patch("custom_components.defa_balancer.UDPBalancerListener", return_value=listener):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        registry = er.async_get(hass)
        entities = er.async_entries_for_config_entry(registry, entry.entry_id)
        entity_ids = [entity.entity_id for entity in entities]
        assert entity_ids

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        assert state is None or state.state == "unavailable"

    listener.stop.assert_awaited_once()


@pytest.mark.integration
async def test_e2e_stale_data_marks_entities_unavailable(
    hass: HomeAssistant,
    enable_custom_integrations: None,
) -> None:
    """E2E: stale coordinator data marks entities unavailable."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    listener = _FakeUDPListener(
        packets=[
            BalancerPacket(serial=FAKE_SERIAL, l1=8.5, l2=7.2, l3=6.9, firmware="4.0.0"),
        ]
    )

    with patch("custom_components.defa_balancer.UDPBalancerListener", return_value=listener):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        registry = er.async_get(hass)
        entities = er.async_entries_for_config_entry(registry, entry.entry_id)
        l1_entity = next(item for item in entities if item.unique_id.endswith("_l1"))

        listener.packet_age = 20.0
        await entry.runtime_data.coordinator.async_request_refresh()
        await hass.async_block_till_done()

        state = hass.states.get(l1_entity.entity_id)
        assert state is not None
        assert state.state == "unavailable"


@pytest.mark.integration
async def test_e2e_fresh_data_restores_entities_from_unavailable(
    hass: HomeAssistant,
    enable_custom_integrations: None,
) -> None:
    """E2E: fresh coordinator data restores entities after a stale-data failure."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    listener = _FakeUDPListener(
        packets=[
            BalancerPacket(serial=FAKE_SERIAL, l1=8.5, l2=7.2, l3=6.9, firmware="4.0.0"),
        ]
    )

    with patch("custom_components.defa_balancer.UDPBalancerListener", return_value=listener):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        registry = er.async_get(hass)
        entities = er.async_entries_for_config_entry(registry, entry.entry_id)
        l1_entity = next(item for item in entities if item.unique_id.endswith("_l1"))

        listener.packet_age = 20.0
        await entry.runtime_data.coordinator.async_request_refresh()
        await hass.async_block_till_done()

        unavailable_state = hass.states.get(l1_entity.entity_id)
        assert unavailable_state is not None
        assert unavailable_state.state == "unavailable"

        # Prepare fresh data and advance time past the coordinator's update
        # interval so the next scheduled refresh picks up the recovery.
        listener.packet_age = 0.0
        listener._packets = [
            BalancerPacket(serial=FAKE_SERIAL, l1=9.3, l2=7.4, l3=7.0, firmware="4.0.0"),
        ]
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS + 1))
        await hass.async_block_till_done()

        assert entry.runtime_data.coordinator.last_update_success is True
        assert entry.runtime_data.coordinator.data is not None
        assert entry.runtime_data.coordinator.data["l1"] == pytest.approx(9.3, abs=0.001)

        recovered_state = hass.states.get(l1_entity.entity_id)
        assert recovered_state is not None
        assert recovered_state.state != "unavailable"
        assert float(recovered_state.state) == pytest.approx(9.3, abs=0.001)


@pytest.mark.integration
async def test_e2e_reload_entry_recreates_runtime_objects(
    hass: HomeAssistant,
    enable_custom_integrations: None,
) -> None:
    """E2E: reloading entry stops old listener and creates a new one."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    first_listener = _FakeUDPListener(
        packets=[
            BalancerPacket(serial=FAKE_SERIAL, l1=8.5, l2=7.2, l3=6.9, firmware="4.0.0"),
        ]
    )
    second_listener = _FakeUDPListener(
        packets=[
            BalancerPacket(serial=FAKE_SERIAL, l1=9.0, l2=7.5, l3=7.1, firmware="4.0.0"),
        ]
    )

    with patch(
        "custom_components.defa_balancer.UDPBalancerListener",
        side_effect=[first_listener, second_listener],
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.runtime_data.listener is first_listener

        await async_reload_entry(hass, entry)
        await hass.async_block_till_done()

        assert first_listener.stop.await_count >= 1
        assert second_listener.start.await_count == 1
        assert entry.runtime_data.listener is second_listener


@pytest.mark.integration
async def test_e2e_setup_retry_recovery(
    hass: HomeAssistant,
    enable_custom_integrations: None,
) -> None:
    """E2E: setup failure followed by successful reload puts entry in LOADED state."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    # First listener: wait_for_packet returns False → ConfigEntryNotReady
    failing_listener = MagicMock()
    failing_listener.start = AsyncMock()
    failing_listener.stop = AsyncMock()
    failing_listener.wait_for_packet = AsyncMock(return_value=False)

    # Second listener: succeeds normally
    recovery_listener = _FakeUDPListener(
        packets=[
            BalancerPacket(serial=FAKE_SERIAL, l1=8.5, l2=7.2, l3=6.9, firmware="4.0.0"),
        ]
    )

    with patch(
        "custom_components.defa_balancer.UDPBalancerListener",
        side_effect=[failing_listener, recovery_listener],
    ):
        # First attempt fails: entry enters SETUP_RETRY
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state.name == "SETUP_RETRY"

        failing_listener.stop.assert_awaited_once()

        # Recovery: reload succeeds
        await async_reload_entry(hass, entry)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED

        recovery_listener.start.assert_awaited_once()
        assert entry.runtime_data.listener is recovery_listener
