"""Config flow schemas for DEFA Balancer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from custom_components.defa_balancer.const import (
    CONF_MULTICAST_GROUP,
    CONF_MULTICAST_PORT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MULTICAST_GROUP,
    DEFAULT_MULTICAST_PORT,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
)
from homeassistant.helpers import selector


def get_user_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    """Get schema for user setup (multicast settings)."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_MULTICAST_GROUP,
                default=defaults.get(CONF_MULTICAST_GROUP, DEFAULT_MULTICAST_GROUP),
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                ),
            ),
            vol.Required(
                CONF_MULTICAST_PORT,
                default=defaults.get(CONF_MULTICAST_PORT, DEFAULT_MULTICAST_PORT),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=65535,
                    mode=selector.NumberSelectorMode.BOX,
                    step=1,
                ),
            ),
            vol.Required(
                CONF_UPDATE_INTERVAL,
                default=defaults.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_SECONDS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=120,
                    mode=selector.NumberSelectorMode.BOX,
                    step=1,
                ),
            ),
        },
    )


__all__ = ["get_user_schema"]
