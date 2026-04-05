"""Config flow entrypoint for Home Assistant."""

from __future__ import annotations

from .config_flow_handler import DEFABalancerConfigFlowHandler, DEFABalancerOptionsFlow


def async_get_options_flow(config_entry):
    """Return options flow handler for a config entry."""
    return DEFABalancerOptionsFlow(config_entry)


__all__ = ["DEFABalancerConfigFlowHandler", "async_get_options_flow"]
