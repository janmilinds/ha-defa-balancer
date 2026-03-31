"""
API package for defa_balancer.

Architecture:
    Three-layer data flow: Entities → Coordinator → API Client.
    Only the coordinator should call the API client. Entities must never
    import or call the API client directly.

Exception hierarchy:
    DEFABalancerApiClientError (base)
    ├── DEFABalancerApiClientCommunicationError (network/timeout)
    └── DEFABalancerApiClientAuthenticationError (401/403)

Coordinator exception mapping:
    ApiClientAuthenticationError → ConfigEntryAuthFailed (triggers reauth)
    ApiClientCommunicationError → UpdateFailed (auto-retry)
    ApiClientError             → UpdateFailed (auto-retry)
"""

from .client import (
    DEFABalancerApiClient,
    DEFABalancerApiClientAuthenticationError,
    DEFABalancerApiClientCommunicationError,
    DEFABalancerApiClientError,
)

__all__ = [
    "DEFABalancerApiClient",
    "DEFABalancerApiClientAuthenticationError",
    "DEFABalancerApiClientCommunicationError",
    "DEFABalancerApiClientError",
]
