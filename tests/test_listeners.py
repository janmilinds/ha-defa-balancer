"""Tests for listener edge cases."""

from __future__ import annotations

import asyncio
import socket

import pytest

from custom_components.defa_balancer.api import BalancerPacket, parse_packet
from custom_components.defa_balancer.coordinator.listeners import (
    MockBalancerListener,
    UDPBalancerListener,
    _DatagramProtocol,
)
from tests.test_constants import FAKE_FIRMWARE, FAKE_SERIAL


def _packet(serial: str = FAKE_SERIAL, l1: float = 1.0, l2: float = 1.0, l3: float = 1.0) -> BalancerPacket:
    """Create a simple packet fixture."""
    return BalancerPacket(serial=serial, l1=l1, l2=l2, l3=l3, firmware=FAKE_FIRMWARE)


def _build_packet_bytes(
    *,
    serial: str = FAKE_SERIAL,
    l1_ma: int = 8500,
    l2_ma: int = 7200,
    l3_ma: int = 6900,
    firmware: str = FAKE_FIRMWARE,
) -> bytes:
    """Build a parsable 54-byte DEFA-like UDP payload."""
    packet = bytearray(54)
    packet[0:11] = f"L4{serial}".encode("ascii")[:11].ljust(11, b"\x00")
    packet[19] = 0x41
    packet[20:22] = int(l1_ma).to_bytes(2, "little")
    packet[23:26] = int(l2_ma).to_bytes(3, "little")
    packet[26:29] = int(l3_ma).to_bytes(3, "little")
    packet[33:38] = firmware.encode("ascii")[:5].ljust(5, b"\x00")
    return bytes(packet)


@pytest.mark.unit
def test_mock_listener_get_all_serials_unique_order() -> None:
    """Mock listener should return unique serials in insertion order."""
    packets = [_packet("A1"), _packet("B2"), _packet("A1"), _packet("C3")]
    listener = MockBalancerListener(packets)

    assert listener.get_all_serials() == ["A1", "B2", "C3"]


@pytest.mark.unit
async def test_udp_listener_get_all_serials_unique_order() -> None:
    """UDP listener should return unique serials in insertion order after pushes."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=None)

    # Push packets with duplicate serials
    listener.push(_packet("A1"))
    listener.push(_packet("B2"))
    listener.push(_packet("A1"))
    listener.push(_packet("C3"))

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
def test_parse_packet_returns_none_for_invalid_data() -> None:
    """parse_packet should return None for data that cannot be decoded."""
    assert parse_packet(b"invalid") is None
    assert parse_packet(b"") is None
    assert parse_packet(b"\x00" * 10) is None


@pytest.mark.unit
async def test_listener_push_buffers_any_packet() -> None:
    """push() should unconditionally buffer the given packet."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=FAKE_SERIAL)
    packet = _packet(serial=FAKE_SERIAL)

    listener.push(packet)

    packets = listener.get_latest()
    assert len(packets) == 1
    assert packets[0] is packet


@pytest.mark.unit
def test_listener_serial_attribute_is_set() -> None:
    """Listener should store the serial filter for protocol-level filtering."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=FAKE_SERIAL)
    assert listener.serial == FAKE_SERIAL

    listener_no_filter = UDPBalancerListener("234.222.250.1", 57082, serial=None)
    assert listener_no_filter.serial is None


@pytest.mark.unit
def test_mock_listener_get_last_packet_age_with_packets() -> None:
    """MockBalancerListener.get_last_packet_age returns 0.0 when packets exist."""
    listener = MockBalancerListener([_packet()])
    assert listener.get_last_packet_age() == 0.0


@pytest.mark.unit
def test_mock_listener_get_last_packet_age_without_packets() -> None:
    """MockBalancerListener.get_last_packet_age returns None when empty."""
    listener = MockBalancerListener()
    assert listener.get_last_packet_age() is None


@pytest.mark.unit
async def test_udp_listener_start_is_idempotent() -> None:
    """Calling start() twice should not create a second transport."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=None)
    # Simulate transport already set
    listener._transport = object()  # type: ignore[assignment]
    await listener.start()
    # Should return early without replacing the transport
    assert listener._transport is not None


@pytest.mark.unit
async def test_udp_listener_stop_is_idempotent() -> None:
    """Calling stop() when no transport exists should be a no-op."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=None)
    assert listener._transport is None
    await listener.stop()
    assert listener._transport is None


@pytest.mark.unit
def test_datagram_protocol_ignores_unparsable_data() -> None:
    """Protocol should silently discard data that parse_packet returns None for."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial=None)
    protocol = _DatagramProtocol(listener)
    protocol.datagram_received(b"garbage", ("127.0.0.1", 9999))
    assert listener.get_latest() == []


@pytest.mark.unit
def test_datagram_protocol_filters_by_serial() -> None:
    """Protocol should drop packets with non-matching serial."""
    listener = UDPBalancerListener("234.222.250.1", 57082, serial="WANTED1234567")
    protocol = _DatagramProtocol(listener)
    # Build a valid packet with a different serial
    packet_bytes = _build_packet_bytes(serial="OTHER1234")
    protocol.datagram_received(packet_bytes, ("127.0.0.1", 9999))
    assert listener.get_latest() == []


@pytest.mark.integration
@pytest.mark.enable_socket
async def test_udp_listener_receives_real_multicast_packet(socket_enabled: None) -> None:
    """Listener should receive and parse a real UDP multicast datagram."""
    del socket_enabled
    multicast_group = "239.255.0.10"

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as temp_sock:
        temp_sock.bind(("", 0))
        multicast_port = temp_sock.getsockname()[1]

    listener = UDPBalancerListener(multicast_group, multicast_port, serial=FAKE_SERIAL)
    try:
        await listener.start()
    except OSError:
        pytest.skip("Multicast not available in this environment")

    try:
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

        try:
            sender.sendto(_build_packet_bytes(), (multicast_group, multicast_port))

            received = await listener.wait_for_packet(timeout=1.0)
            if not received:
                pytest.skip("Multicast datagram not received; environment likely blocks multicast traffic")

            assert received is True
            packets = listener.get_latest()
            assert len(packets) == 1
            assert packets[0].serial == FAKE_SERIAL
            assert packets[0].l1 == pytest.approx(8.5, abs=0.001)
            assert packets[0].l2 == pytest.approx(7.2, abs=0.001)
            assert packets[0].l3 == pytest.approx(6.9, abs=0.001)
            assert packets[0].firmware == FAKE_FIRMWARE
        finally:
            sender.close()
    finally:
        await listener.stop()
