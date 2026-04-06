"""Tests for DEFA Balancer config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.defa_balancer.api import BalancerPacket
from custom_components.defa_balancer.config_flow_handler.config_flow import DEFABalancerConfigFlowHandler
from custom_components.defa_balancer.const import CONF_SERIAL, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from tests.test_constants import FAKE_DUPLICATE_SERIAL, FAKE_SERIAL


class _FakeScanListener:
    """Minimal scan listener for config flow e2e tests."""

    def __init__(self) -> None:
        self.start = AsyncMock()
        self.stop = AsyncMock()

    def get_all_serials(self) -> list[str]:
        """Return a single discovered serial."""
        return [FAKE_SERIAL]


class _FakeUDPListener:
    """Minimal setup listener used after config flow entry creation."""

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


def _mock_listener() -> MagicMock:
    """Return a MagicMock UDPBalancerListener with awaitable start/stop."""
    listener = MagicMock()
    listener.start = AsyncMock()
    listener.stop = AsyncMock()
    listener.get_all_serials.return_value = []
    listener.get_latest.return_value = []
    return listener


async def _poll_until_done(hass: HomeAssistant, result: dict, max_steps: int = 5) -> dict:
    """Poll an in-progress flow until it reaches a non-progress step."""
    for _ in range(max_steps):
        if result["type"] not in (FlowResultType.SHOW_PROGRESS, FlowResultType.SHOW_PROGRESS_DONE):
            break
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
    return result


@pytest.mark.unit
async def test_config_flow_user_step_starts_scanning(hass: HomeAssistant, enable_custom_integrations: None) -> None:
    """Test user step immediately starts scanning progress."""

    async def instant_scan(self) -> list[str]:
        return []

    with (
        patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.UDPBalancerListener",
            return_value=_mock_listener(),
        ),
        patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.DEFABalancerConfigFlowHandler._do_scan",
            instant_scan,
        ),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})

        # The flow skips the form and goes straight to scanning progress
        assert result["type"] in (FlowResultType.SHOW_PROGRESS, FlowResultType.SHOW_PROGRESS_DONE)


@pytest.mark.unit
async def test_config_flow_no_device_shows_retry_menu(hass: HomeAssistant, enable_custom_integrations: None) -> None:
    """Test retry menu appears when no device is found."""
    with patch(
        "custom_components.defa_balancer.config_flow_handler.config_flow.UDPBalancerListener",
        return_value=_mock_listener(),
    ):

        async def empty_scan(self) -> list[str]:
            return []

        with patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.DEFABalancerConfigFlowHandler._do_scan",
            empty_scan,
        ):
            result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            result = await _poll_until_done(hass, result)

            # After scan completes with no devices, show retry menu
            assert result["type"] in (FlowResultType.MENU, FlowResultType.FORM)


@pytest.mark.unit
async def test_config_flow_device_found_shows_select_form(
    hass: HomeAssistant, enable_custom_integrations: None
) -> None:
    """Test device selection form appears when device is found."""
    mock_serial = FAKE_SERIAL

    with patch(
        "custom_components.defa_balancer.config_flow_handler.config_flow.UDPBalancerListener",
        return_value=_mock_listener(),
    ):

        async def one_device_scan(self) -> list[str]:
            return [mock_serial]

        with patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.DEFABalancerConfigFlowHandler._do_scan",
            one_device_scan,
        ):
            result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            result = await _poll_until_done(hass, result)

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "select"


@pytest.mark.unit
async def test_config_flow_select_creates_entry_with_serial(
    hass: HomeAssistant, enable_custom_integrations: None
) -> None:
    """Test selecting a device creates the config entry with correct serial."""
    mock_serial = FAKE_SERIAL

    with patch(
        "custom_components.defa_balancer.config_flow_handler.config_flow.UDPBalancerListener",
        return_value=_mock_listener(),
    ):

        async def one_device_scan(self) -> list[str]:
            return [mock_serial]

        with patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.DEFABalancerConfigFlowHandler._do_scan",
            one_device_scan,
        ):
            result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            result = await _poll_until_done(hass, result)
            assert result["step_id"] == "select"

            result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_SERIAL: mock_serial})
            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["data"][CONF_SERIAL] == mock_serial


@pytest.mark.unit
async def test_config_flow_duplicate_serial_menu(hass: HomeAssistant, enable_custom_integrations: None) -> None:
    """Test that all found serials already configured shows dedicated menu."""
    mock_serial = FAKE_DUPLICATE_SERIAL
    existing_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SERIAL: mock_serial},
        unique_id=mock_serial,
    )
    existing_entry.add_to_hass(hass)

    with patch(
        "custom_components.defa_balancer.config_flow_handler.config_flow.UDPBalancerListener",
        return_value=_mock_listener(),
    ):

        async def duplicate_scan(self) -> list[str]:
            return [mock_serial]

        with patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.DEFABalancerConfigFlowHandler._do_scan",
            duplicate_scan,
        ):
            result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            result = await _poll_until_done(hass, result)

            assert result["type"] == FlowResultType.MENU
            assert result["step_id"] == "already_configured"


@pytest.mark.unit
async def test_config_flow_listener_start_failure_shows_connection_error(
    hass: HomeAssistant, enable_custom_integrations: None
) -> None:
    """Test listener startup OSError routes flow to connection_error step."""
    listener = _mock_listener()
    listener.start = AsyncMock(side_effect=OSError)

    with patch(
        "custom_components.defa_balancer.config_flow_handler.config_flow.UDPBalancerListener",
        return_value=listener,
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        assert result["type"] == FlowResultType.SHOW_PROGRESS_DONE

        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "connection_error"


@pytest.mark.unit
async def test_config_flow_scan_exception_shows_retry(hass: HomeAssistant, enable_custom_integrations: None) -> None:
    """Test scan task raising exception shows retry menu (no crash)."""
    with patch(
        "custom_components.defa_balancer.config_flow_handler.config_flow.UDPBalancerListener",
        return_value=_mock_listener(),
    ):

        async def failing_scan(self) -> list[str]:
            raise RuntimeError("unexpected failure")

        with patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.DEFABalancerConfigFlowHandler._do_scan",
            failing_scan,
        ):
            result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            result = await _poll_until_done(hass, result)

            assert result["type"] in (FlowResultType.MENU, FlowResultType.FORM)


@pytest.mark.integration
async def test_e2e_config_flow_create_entry_and_setup(
    hass: HomeAssistant,
    enable_custom_integrations: None,
) -> None:
    """E2E: config flow creates an entry that loads the integration successfully."""
    scan_listener = _FakeScanListener()
    setup_listener = _FakeUDPListener(
        packets=[
            BalancerPacket(serial=FAKE_SERIAL, l1=8.5, l2=7.2, l3=6.9, firmware="4.0.0"),
        ]
    )

    async def one_device_scan(self) -> list[str]:
        return [FAKE_SERIAL]

    with (
        patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.UDPBalancerListener",
            return_value=scan_listener,
        ),
        patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.DEFABalancerConfigFlowHandler._do_scan",
            one_device_scan,
        ),
        patch("custom_components.defa_balancer.UDPBalancerListener", return_value=setup_listener),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await _poll_until_done(hass, result)

        assert result["type"] == FlowResultType.FORM
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_SERIAL: FAKE_SERIAL})
        assert result["type"] == FlowResultType.CREATE_ENTRY

        entry = hass.config_entries.async_entries(DOMAIN)[0]
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED


@pytest.mark.integration
async def test_e2e_config_flow_connection_error_then_retry_success(
    hass: HomeAssistant,
    enable_custom_integrations: None,
) -> None:
    """E2E: a failed flow does not block a subsequent successful setup attempt."""
    failing_scan_listener = _FakeScanListener()
    failing_scan_listener.start = AsyncMock(side_effect=OSError)
    successful_scan_listener = _FakeScanListener()
    setup_listener = _FakeUDPListener(
        packets=[
            BalancerPacket(serial=FAKE_SERIAL, l1=8.5, l2=7.2, l3=6.9, firmware="4.0.0"),
        ]
    )

    async def one_device_scan(self) -> list[str]:
        return [FAKE_SERIAL]

    with (
        patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.UDPBalancerListener",
            side_effect=[failing_scan_listener, successful_scan_listener],
        ),
        patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.DEFABalancerConfigFlowHandler._do_scan",
            one_device_scan,
        ),
        patch("custom_components.defa_balancer.UDPBalancerListener", return_value=setup_listener),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await _poll_until_done(hass, result)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "connection_error"

        # Start a fresh user flow after the failed attempt.
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await _poll_until_done(hass, result)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "select"

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_SERIAL: FAKE_SERIAL})
        assert result["type"] == FlowResultType.CREATE_ENTRY

        entry = hass.config_entries.async_entries(DOMAIN)[0]
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED
        successful_scan_listener.stop.assert_awaited_once()


@pytest.mark.unit
async def test_config_flow_connection_error_form_retry_to_user(
    hass: HomeAssistant, enable_custom_integrations: None
) -> None:
    """Test that submitting the connection_error form restarts scanning."""
    failing_listener = _mock_listener()
    failing_listener.start = AsyncMock(side_effect=OSError)
    success_listener = _mock_listener()

    async def one_device_scan(self) -> list[str]:
        return [FAKE_SERIAL]

    with (
        patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.UDPBalancerListener",
            side_effect=[failing_listener, success_listener],
        ),
        patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.DEFABalancerConfigFlowHandler._do_scan",
            one_device_scan,
        ),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await _poll_until_done(hass, result)
        assert result["step_id"] == "connection_error"
        assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.unit
async def test_config_flow_already_configured_menu(hass: HomeAssistant, enable_custom_integrations: None) -> None:
    """Test dedicated already_configured menu when all devices exist."""
    existing = MockConfigEntry(domain=DOMAIN, data={CONF_SERIAL: FAKE_SERIAL}, unique_id=FAKE_SERIAL)
    existing.add_to_hass(hass)

    async def one_device_scan(self) -> list[str]:
        return [FAKE_SERIAL]

    with (
        patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.UDPBalancerListener",
            return_value=_mock_listener(),
        ),
        patch(
            "custom_components.defa_balancer.config_flow_handler.config_flow.DEFABalancerConfigFlowHandler._do_scan",
            one_device_scan,
        ),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await _poll_until_done(hass, result)
        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "already_configured"


@pytest.mark.unit
async def test_config_flow_async_remove_cancels_task_and_stops_listener(
    hass: HomeAssistant, enable_custom_integrations: None
) -> None:
    """Test async_remove cleans up scan task and listener."""
    flow = DEFABalancerConfigFlowHandler()
    flow.hass = hass

    # Simulate an in-progress scan task
    mock_task = MagicMock()
    mock_task.done.return_value = False
    flow._scan_task = mock_task

    # Simulate an active listener
    listener = _mock_listener()
    flow._listener = listener

    flow.async_remove()

    mock_task.cancel.assert_called_once()
    assert flow._scan_task is None
    assert flow._listener is None
