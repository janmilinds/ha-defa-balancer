"""Runtime data types for defa_balancer config entries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import BalancerListener, DEFABalancerDataUpdateCoordinator


type DEFABalancerConfigEntry = ConfigEntry[DEFABalancerData]


@dataclass
class DEFABalancerData:
    """Runtime objects for one config entry."""

    listener: BalancerListener
    coordinator: DEFABalancerDataUpdateCoordinator
