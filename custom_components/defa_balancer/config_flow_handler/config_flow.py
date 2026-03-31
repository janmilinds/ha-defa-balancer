"""Config flow for DEFA Balancer."""

from __future__ import annotations

from typing import Any

from custom_components.defa_balancer.config_flow_handler.schemas import get_user_schema
from custom_components.defa_balancer.const import CONF_MULTICAST_GROUP, CONF_MULTICAST_PORT, DOMAIN
from homeassistant import config_entries


class DEFABalancerConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle DEFA Balancer config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle user initiated setup flow."""
        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_MULTICAST_GROUP]}:{user_input[CONF_MULTICAST_PORT]}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="DEFA Balancer", data=user_input)

        return self.async_show_form(step_id="user", data_schema=get_user_schema())


__all__ = ["DEFABalancerConfigFlowHandler"]
