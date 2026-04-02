"""Tests for listener edge cases."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from custom_components.defa_balancer.api import BalancerPacket
from custom_components.defa_balancer.coordinator.listeners import (
    MockBalancerListener,
    UDPBalancerListener,
    _DatagramProtocol,
)
from test_constants import FAKE_FIRMWARE, FAKE_SERIAL


def _packet(serial: str = FAKE_SERIAL, l1: float = 1.0, l2: float = 1.0, l3: float = 1.0) -> BalancerPacket:
    """Create a simple packet fixture."""
    return BalancerPacket(serial=serial, l1=l1, l2=l2, l3=l3, firmware=FAKE_FIRMWARE)


@pytest.mark.unit
def test_mock_listener_get_all_serials_unique_order() -> None:
    """Mock listener should return unique serials in insertion order."""
    packets = [_packet("A1"), _packet("B2"), _packet("A1"), _packet("C3")]
    listener = MockBalancerListener(packets)

    assert listener.get_all_serials() == ["A1", "B2", "C3"]


@pytest.mark.unit
async def test_udp_listener_wait_for_packet_timeout_returns_false() -> None:
    """wait_for_packet should return False when timeout expires."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=None)

    assert await listener.wait_for_packet(timeout=0.01) is False


@pytest.mark.unit
async def test_udp_listener_wait_for_packet_returns_true_after_push() -> None:
    """wait_for_packet should return True when a packet is pushed."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=None)

    asyncio.get_running_loop().call_soon(listener.push, _packet())

    assert await listener.wait_for_packet(timeout=0.2) is True


@pytest.mark.unit
async def test_udp_listener_ring_buffer_respects_maxlen() -> None:
    """Listener ring buffer should only keep the latest N packets."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=None, buffer_size=2)

    listener.push(_packet(l1=1.0))
    listener.push(_packet(l1=2.0))
    listener.push(_packet(l1=3.0))

    latest = listener.get_latest()
    assert len(latest) == 2
    assert latest[0].l1 == 2.0
    assert latest[1].l1 == 3.0


@pytest.mark.unit
def test_udp_listener_get_last_packet_age_none_without_packets() -> None:
    """get_last_packet_age should return None when no packet has been received."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=None)

    assert listener.get_last_packet_age() is None


@pytest.mark.unit
async def test_udp_listener_get_last_packet_age_after_push() -> None:
    """get_last_packet_age should return a non-negative age after push."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=None)
    listener.push(_packet())

    await asyncio.sleep(0)
    age = listener.get_last_packet_age()

    assert age is not None
    assert age >= 0


@pytest.mark.unit
async def test_udp_listener_get_latest_returns_copy() -> None:
    """get_latest should return a snapshot copy and not expose internal deque."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=None)
    listener.push(_packet(l1=1.0))

    latest = listener.get_latest()
    latest.append(_packet(l1=99.0))

    assert len(listener.get_latest()) == 1


@pytest.mark.unit
def test_datagram_protocol_ignores_invalid_packet() -> None:
    """Protocol should ignore datagrams that fail parsing."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=None)
    listener.push = MagicMock()  # type: ignore[method-assign]
    protocol = _DatagramProtocol(listener)

    with patch("custom_components.defa_balancer.coordinator.listeners.parse_packet", return_value=None):
        protocol.datagram_received(b"invalid", ("127.0.0.1", 1234))

    listener.push.assert_not_called()


@pytest.mark.unit
def test_datagram_protocol_filters_non_matching_serial() -> None:
    """Protocol should drop packets whose serial does not match filter."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=FAKE_SERIAL)
    listener.push = MagicMock()  # type: ignore[method-assign]
    protocol = _DatagramProtocol(listener)

    with patch(
        "custom_components.defa_balancer.coordinator.listeners.parse_packet",
        return_value=_packet(serial="OTHER123"),
    ):
        protocol.datagram_received(b"packet", ("127.0.0.1", 1234))

    listener.push.assert_not_called()


@pytest.mark.unit
def test_datagram_protocol_pushes_matching_packet() -> None:
    """Protocol should push packets when serial matches or no filter is set."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=FAKE_SERIAL)
    listener.push = MagicMock()  # type: ignore[method-assign]
    protocol = _DatagramProtocol(listener)
    packet = _packet(serial=FAKE_SERIAL)

    with patch("custom_components.defa_balancer.coordinator.listeners.parse_packet", return_value=packet):
        protocol.datagram_received(b"packet", ("127.0.0.1", 1234))

    listener.push.assert_called_once_with(packet)
