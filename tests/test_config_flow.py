"""Tests for DEFA Balancer config flow."""

from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

# Add custom_components to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.defa_balancer.const import CONF_SERIAL, DOMAIN
from test_constants import FAKE_DUPLICATE_SERIAL, FAKE_SERIAL


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
    with patch(
        "custom_components.defa_balancer.config_flow_handler.config_flow.UDPBalancerListener",
        return_value=_mock_listener(),
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
async def test_config_flow_duplicate_serial_aborts(hass: HomeAssistant, enable_custom_integrations: None) -> None:
    """Test that all found serials already configured causes abort."""
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

            assert result["type"] == FlowResultType.ABORT
            assert result["reason"] == "already_configured"
