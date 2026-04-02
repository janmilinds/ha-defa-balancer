"""Tests for DEFA Balancer packet parsing."""

from __future__ import annotations

import pytest

from custom_components.defa_balancer.api import parse_packet
from tests.test_constants import FAKE_FIRMWARE, FAKE_SERIAL


def _build_packet(
    *,
    serial: str = FAKE_SERIAL,
    l1_ma: int = 1211,
    l2_ma: int = 801,
    l3_ma: int = 780,
    firmware: str = FAKE_FIRMWARE,
) -> bytes:
    """Build a synthetic 54-byte DEFA-like packet with safe test data."""
    packet = bytearray(54)
    packet[0:11] = f"L4{serial}".encode("ascii")[:11].ljust(11, b"\x00")
    packet[19] = 0x41
    packet[20:22] = int(l1_ma).to_bytes(2, "little")
    packet[23:26] = int(l2_ma).to_bytes(3, "little")
    packet[26:29] = int(l3_ma).to_bytes(3, "little")
    packet[33:38] = firmware.encode("ascii")[:5].ljust(5, b"\x00")
    return bytes(packet)


@pytest.mark.unit
def test_parse_packet_valid() -> None:
    """Test parsing a valid 54-byte DEFA packet."""
    packet_data = _build_packet(l1_ma=1211, l2_ma=801, l3_ma=780)

    packet = parse_packet(packet_data)

    assert packet is not None
    assert packet.serial == FAKE_SERIAL
    assert packet.l1 == pytest.approx(1.211, abs=0.01)  # ~1.2 A (not 46 A)
    assert packet.l2 == pytest.approx(0.801, abs=0.01)  # ~0.8 A
    assert packet.l3 == pytest.approx(0.780, abs=0.01)  # ~0.78 A
    assert packet.firmware == FAKE_FIRMWARE


@pytest.mark.unit
def test_parse_packet_different_currents() -> None:
    """Test packet with varying L1/L2/L3 currents."""
    packet_data = _build_packet(l1_ma=2500, l2_ma=1600, l3_ma=900)

    packet = parse_packet(packet_data)
    assert packet is not None
    # Verify all three phases are extracted
    assert packet.l1 > 0
    assert packet.l2 > 0
    assert packet.l3 > 0
    # All should be A roughly the same magnitude (single-phase-like distribution)
    assert packet.l1 < 30
    assert packet.l2 < 30
    assert packet.l3 < 30


@pytest.mark.unit
def test_parse_packet_firmware_extraction() -> None:
    """Test firmware version is correctly extracted."""
    packet_data = _build_packet(firmware=FAKE_FIRMWARE)

    packet = parse_packet(packet_data)
    assert packet is not None
    assert packet.firmware == FAKE_FIRMWARE


@pytest.mark.unit
def test_parse_packet_serial_extraction() -> None:
    """Test serial number is correctly extracted."""
    packet_data = _build_packet(serial=FAKE_SERIAL)

    packet = parse_packet(packet_data)
    assert packet is not None
    assert packet.serial == FAKE_SERIAL


@pytest.mark.unit
def test_parse_packet_invalid_length() -> None:
    """Test parsing with invalid packet length returns None."""
    short_data = _build_packet()[:11]  # Too short

    packet = parse_packet(short_data)
    assert packet is None


@pytest.mark.unit
def test_parse_packet_empty() -> None:
    """Test parsing empty data returns None."""
    packet = parse_packet(b"")
    assert packet is None
