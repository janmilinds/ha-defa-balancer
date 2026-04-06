"""Options flow for DEFA Balancer."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries

from .schemas import get_options_schema


class DEFABalancerOptionsFlow(config_entries.OptionsFlow):
    """
    Handle options for DEFA Balancer config entries.

    This class manages the options that users can modify after initial setup.
    Currently, the only supported option is `phase_voltage`.

    The options flow always starts with async_step_init and provides a single
    form for the configurable options.

    For more information:
    https://developers.home-assistant.io/docs/config_entries_options_flow_handler
    """

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Manage the options for the integration.

        The only configurable option is `phase_voltage` (integer volts).

        Args:
            user_input: The user input from the options form, or None for initial display.

        Returns:
            The config flow result, either showing a form or creating an options entry.

        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=get_options_schema(self.config_entry.options),
        )


__all__ = ["DEFABalancerOptionsFlow"]
