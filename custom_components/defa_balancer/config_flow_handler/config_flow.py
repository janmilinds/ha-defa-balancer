"""Config flow for DEFA Balancer."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol

from custom_components.defa_balancer.const import (
    CONF_MULTICAST_GROUP,
    CONF_MULTICAST_PORT,
    CONF_SERIAL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MULTICAST_GROUP,
    DEFAULT_MULTICAST_PORT,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
    SCAN_TIMEOUT_INITIAL,
    SCAN_TIMEOUT_RETRY,
)
from custom_components.defa_balancer.coordinator.listeners import UDPBalancerListener
from homeassistant import config_entries
from homeassistant.helpers.selector import SelectOptionDict, SelectSelector, SelectSelectorConfig

from .options_flow import DEFABalancerOptionsFlow


class DEFABalancerConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle DEFA Balancer config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow state."""
        self._listener: UDPBalancerListener | None = None
        self._detected_serials: list[str] = []
        self._scan_task: asyncio.Task[list[str]] | None = None
        self._scan_error: str | None = None

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> DEFABalancerOptionsFlow:
        """Get the options flow for this handler."""
        return DEFABalancerOptionsFlow()

    def async_remove(self) -> None:
        """Clean up background task and listener when the flow is dismissed."""
        if self._scan_task is not None and not self._scan_task.done():
            self._scan_task.cancel()
            self._scan_task = None
        if self._listener is not None:
            self.hass.async_create_task(self._listener.stop())
            self._listener = None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Start scanning, or create entry for a pre-selected serial.

        When called with a pre-selected serial (from multi-device setup),
        skip scanning and create the entry directly.
        """
        if self._scan_task is not None and not self._scan_task.done():
            self._scan_task.cancel()
        self._scan_task = None
        await self._stop_listener()
        return await self.async_step_scanning()

    async def async_step_scanning(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage the background scan task.

        This step ONLY returns async_show_progress or async_show_progress_done
        to satisfy HA's progress state machine rules.
        """
        if self._scan_task is None:
            try:
                self._listener = UDPBalancerListener(
                    DEFAULT_MULTICAST_GROUP,
                    DEFAULT_MULTICAST_PORT,
                    serial=None,
                )
                await self._listener.start()
            except OSError:
                self._scan_error = "cannot_connect"
                return self.async_show_progress_done(next_step_id="connection_error")
            self._scan_task = self.hass.async_create_task(self._do_scan())

        if not self._scan_task.done():
            return self.async_show_progress(
                step_id="scanning",
                progress_action="scanning",
                progress_task=self._scan_task,
            )

        try:
            serials = self._scan_task.result()
        except Exception:  # noqa: BLE001
            serials = []
        self._scan_task = None

        if not serials:
            await self._stop_listener()
            return self.async_show_progress_done(next_step_id="retry")

        await self._stop_listener()
        self._detected_serials = serials
        return self.async_show_progress_done(next_step_id="select")

    async def async_step_select(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Let user choose which discovered device(s) to set up."""
        already_configured = {entry.unique_id for entry in self.hass.config_entries.async_entries(DOMAIN)}
        available = [s for s in self._detected_serials if s not in already_configured]

        if not available:
            return await self.async_step_already_configured()

        if user_input is not None:
            serial: str = user_input[CONF_SERIAL]
            await self.async_set_unique_id(serial)
            self._abort_if_unique_id_configured(description_placeholders={"serial": serial})
            return self.async_create_entry(
                title=f"DEFA Balancer {serial}",
                data={
                    CONF_MULTICAST_GROUP: DEFAULT_MULTICAST_GROUP,
                    CONF_MULTICAST_PORT: DEFAULT_MULTICAST_PORT,
                    CONF_SERIAL: serial,
                    CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL_SECONDS,
                },
            )

        options = [SelectOptionDict(value=s, label=f"DEFA Balancer \u2013 {s}") for s in available]
        return self.async_show_form(
            step_id="select",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SERIAL): SelectSelector(SelectSelectorConfig(options=options, multiple=False)),
                }
            ),
            description_placeholders={"count": str(len(available))},
        )

    async def async_step_retry(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Show retry screen with a custom scan-again button."""
        return self.async_show_menu(
            step_id="retry",
            menu_options=["user"],
        )

    async def async_step_already_configured(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Show menu when discovered devices are already configured."""
        return self.async_show_menu(
            step_id="already_configured",
            menu_options=["user"],
        )

    async def async_step_connection_error(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Show a recoverable error when multicast listener startup fails."""
        if user_input is not None:
            self._scan_error = None
            return await self.async_step_user()

        return self.async_show_form(
            step_id="connection_error",
            data_schema=vol.Schema({}),
            errors={"base": self._scan_error or "cannot_connect"},
        )

    async def _do_scan(self) -> list[str]:
        """Run the full two-phase scan: 2s initial, then auto-extend 8s.

        Always waits the full window so multiple devices can be discovered.
        Returns list of unique serial numbers found, empty if none.
        """
        if self._listener is None:
            return []

        await asyncio.sleep(SCAN_TIMEOUT_INITIAL)
        serials = self._listener.get_all_serials()
        if serials:
            return serials

        await asyncio.sleep(SCAN_TIMEOUT_RETRY)
        return self._listener.get_all_serials()

    async def _stop_listener(self) -> None:
        """Stop and discard the active listener."""
        if self._listener is not None:
            await self._listener.stop()
            self._listener = None


__all__ = ["DEFABalancerConfigFlowHandler"]
