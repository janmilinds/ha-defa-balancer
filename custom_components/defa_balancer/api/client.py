"""Packet models and parser for DEFA Balancer UDP data."""

from __future__ import annotations

from dataclasses import dataclass

from custom_components.defa_balancer.const import PACKET_LENGTH


@dataclass(slots=True, frozen=True)
class BalancerPacket:
    """Parsed DEFA Balancer payload values."""

    serial: str
    l1: float
    l2: float
    l3: float
    firmware: str


def parse_packet(data: bytes) -> BalancerPacket | None:
    """
    Parse a raw UDP packet into a BalancerPacket.

    Data packet structure of notable fields:

    | Offset | Length | Type      | Description                                      |
    |--------|--------|-----------|--------------------------------------------------|
    | 0-10   | 11     | ASCII     | Serial number (right-aligned, padded with nulls) |
    | 20-21  | 2      | uint16 LE | L1 current in mA                                 |
    | 23-25  | 3      | uint24 LE | L2 current in mA                                 |
    | 26-28  | 3      | uint24 LE | L3 current in mA                                 |
    | 33-37  | 5      | ASCII     | Firmware version (padded with nulls)             |

    Args:
        data: The raw bytes received from the DEFA Balancer device.

    Returns:
        A BalancerPacket instance if parsing is successful, None otherwise.

    """

    if len(data) != PACKET_LENGTH:
        return None

    serial_raw = data[0:11].decode("ascii", errors="ignore").rstrip("\x00")
    # Use the fixed serial length from the right side to support optional/variable prefixes.
    serial = serial_raw[-9:]

    # Byte 19 is a status marker in observed packets; L1 is at 20-21.
    l1_ma = int.from_bytes(data[20:22], "little")
    l2_ma = int.from_bytes(data[23:26], "little")
    l3_ma = int.from_bytes(data[26:29], "little")
    firmware = data[33:38].decode("ascii", errors="ignore").rstrip("\x00")

    return BalancerPacket(
        serial=serial,
        l1=l1_ma / 1000,
        l2=l2_ma / 1000,
        l3=l3_ma / 1000,
        firmware=firmware,
    )
