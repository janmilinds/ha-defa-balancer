"""Config flow schemas for DEFA Balancer.

Schemas for the options flow that allows users to modify settings
after initial configuration.

This module contains reusable probatio schemas used by the config and
options flows. Export small helper functions so callers can compute defaults
before requesting the schema.
"""

from collections.abc import Mapping
from typing import Any

import probatio

from custom_components.defa_balancer.const import CONF_PHASE_VOLTAGE, DEFAULT_PHASE_VOLTAGE
from homeassistant.helpers import selector


def get_options_schema(defaults: Mapping[str, Any] | None = None) -> probatio.Schema:
    """
    Get schema for options flow.

    Args:
        defaults: Optional dictionary of current option values.

    Returns:
        Voluptuous schema for options configuration.

    """
    defaults = defaults or {}
    return probatio.Schema(
        {
            probatio.Optional(
                CONF_PHASE_VOLTAGE, default=defaults.get(CONF_PHASE_VOLTAGE, DEFAULT_PHASE_VOLTAGE)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=100,
                    max=250,
                    step=1,
                    unit_of_measurement="V",
                    mode=selector.NumberSelectorMode.BOX,
                ),
            ),
        },
    )


__all__ = [
    "get_options_schema",
]
