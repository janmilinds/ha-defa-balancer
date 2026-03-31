"""
Custom types for defa_balancer.

This module defines the runtime data structure attached to each config entry.
Access pattern: entry.runtime_data.client / entry.runtime_data.coordinator

The DEFABalancerConfigEntry type alias is used throughout the integration
for type-safe access to the config entry's runtime data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import DEFABalancerApiClient
    from .coordinator import DEFABalancerDataUpdateCoordinator


type DEFABalancerConfigEntry = ConfigEntry[DEFABalancerData]


@dataclass
class DEFABalancerData:
    """Runtime data for defa_balancer config entries.

    Stored as entry.runtime_data after successful setup.
    Provides typed access to the API client and coordinator instances.
    """

    client: DEFABalancerApiClient
    coordinator: DEFABalancerDataUpdateCoordinator
    integration: Integration
