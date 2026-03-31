#!/usr/bin/env python3
"""Send mock DEFA Balancer UDP multicast packets for local development.

This utility mimics a DEFA Balancer by broadcasting 54-byte payloads to the
integration multicast endpoint (default: 234.222.250.1:57082).

Usage
-----
Basic (single device, 2 packets/s):
    python3 script/mock_balancer.py --serial AB12CD34

Custom phase currents and jitter:
    python3 script/mock_balancer.py --serial AB12CD34 --l1 8500 --l2 7200 --l3 9100 --jitter 0.05

Run two devices simultaneously (open two terminals):
    python3 script/mock_balancer.py --serial AB12CD34 --rate 2 --jitter 0.05
    python3 script/mock_balancer.py --serial EF56BA78 --rate 2 --jitter 0.05

Time-limited run (stop after 30 s):
    timeout 30s python3 script/mock_balancer.py --serial AB12CD34

Arguments:
---------
--serial     Device serial number, e.g. AB12CD34 (required)
--group      Multicast group IP  (default: 234.222.250.1)
--port       Multicast port      (default: 57082)
--rate       Packets per second  (default: 2.0)
--l1         L1 phase current in mA (default: 8000)
--l2         L2 phase current in mA (default: 7500)
--l3         L3 phase current in mA (default: 8200)
--jitter     Random current jitter fraction 0–1 (default: 0.0)
--firmware   Firmware version string (default: 4.0.0)
--source-port UDP source port; 0 lets the OS pick a free port (default: 0)

Notes:
-----
- Packets are 54 bytes, little-endian, matching the DEFA Balancer wire format.
- SO_REUSEADDR is set so multiple instances can run in parallel.
- Stop with Ctrl+C.
"""

from __future__ import annotations

import argparse
import random
import socket
import struct
import time

PACKET_LENGTH = 54
DEFAULT_GROUP = "234.222.250.1"
DEFAULT_PORT = 57082
DEFAULT_RATE = 2.0
DEFAULT_FIRMWARE = "4.0.0"

FIXED_14_18 = bytes.fromhex("43 9d 01 00 00")
FIXED_21_22 = bytes.fromhex("05 00")
FIXED_29 = bytes([0x02])
FIXED_30_32 = b"D01"


def _encode_u24_le(value: int) -> bytes:
    if value < 0 or value > 0xFFFFFF:
        raise ValueError(f"u24 out of range: {value}")
    return bytes((value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF))


def build_packet(
    *,
    serial: str,
    sequence: int,
    counter: int,
    l1_amp: float,
    l2_amp: float,
    l3_amp: float,
    firmware: str,
) -> bytes:
    """Build one 54-byte DEFA-like payload."""
    packet = bytearray(PACKET_LENGTH)

    identifier = f"L4{serial}".encode("ascii", errors="ignore")[:11]
    packet[0:11] = identifier.ljust(11, b"\x00")

    packet[11] = sequence & 0xFF
    packet[12:14] = struct.pack("<H", counter & 0xFFFF)
    packet[14:19] = FIXED_14_18

    l1_ma = max(0, min(int(l1_amp * 1000), 0xFFFF))
    l2_ma = max(0, min(int(l2_amp * 1000), 0xFFFFFF))
    l3_ma = max(0, min(int(l3_amp * 1000), 0xFFFFFF))

    packet[19:21] = struct.pack("<H", l1_ma)
    packet[21:23] = FIXED_21_22
    packet[23:26] = _encode_u24_le(l2_ma)
    packet[26:29] = _encode_u24_le(l3_ma)
    packet[29:30] = FIXED_29
    packet[30:33] = FIXED_30_32

    firmware_bytes = firmware.encode("ascii", errors="ignore")[:5]
    packet[33:38] = firmware_bytes.ljust(5, b"\x00")
    packet[38:54] = b"\x00" * 16

    return bytes(packet)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the mock sender."""
    parser = argparse.ArgumentParser(description="Mock DEFA Balancer multicast sender")
    parser.add_argument("--group", default=DEFAULT_GROUP, help="Multicast group")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Multicast port")
    parser.add_argument(
        "--source-port",
        type=int,
        default=4568,
        help="UDP source port (DEFA devices commonly use 4568)",
    )
    parser.add_argument(
        "--serial",
        default="AB12CD34",
        help="Device serial in packet prefix L4<serial>",
    )
    parser.add_argument("--firmware", default=DEFAULT_FIRMWARE, help="Firmware string (max 5 chars)")
    parser.add_argument("--rate", type=float, default=DEFAULT_RATE, help="Packets per second")
    parser.add_argument("--l1", type=float, default=8.5, help="L1 current in amps")
    parser.add_argument("--l2", type=float, default=7.2, help="L2 current in amps")
    parser.add_argument("--l3", type=float, default=6.9, help="L3 current in amps")
    parser.add_argument(
        "--jitter",
        type=float,
        default=0.15,
        help="Random amp jitter (+/-) applied per phase to simulate live data",
    )
    return parser.parse_args()


def main() -> int:
    """Run the mock sender loop until interrupted."""
    args = parse_args()
    interval = 1.0 / args.rate if args.rate > 0 else 0.5

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    try:
        sock.bind(("", args.source_port))
        bound_port = args.source_port
    except OSError:
        sock.bind(("", 0))
        bound_port = sock.getsockname()[1]

    sequence = 255
    counter = 0

    print(
        f"Sending mock DEFA Balancer packets to {args.group}:{args.port} "
        f"from source port {bound_port} (serial={args.serial})"
    )
    print("Press Ctrl+C to stop")

    try:
        while True:
            l1 = max(0.0, args.l1 + random.uniform(-args.jitter, args.jitter))
            l2 = max(0.0, args.l2 + random.uniform(-args.jitter, args.jitter))
            l3 = max(0.0, args.l3 + random.uniform(-args.jitter, args.jitter))

            payload = build_packet(
                serial=args.serial,
                sequence=sequence,
                counter=counter,
                l1_amp=l1,
                l2_amp=l2,
                l3_amp=l3,
                firmware=args.firmware,
            )
            sock.sendto(payload, (args.group, args.port))

            sequence = (sequence - 1) & 0xFF
            counter = (counter + 1) & 0xFFFF
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped mock sender")
    finally:
        sock.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
