"""Listener abstractions and UDP multicast implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
from collections import deque
from collections.abc import Iterable
import socket
import struct

from custom_components.defa_balancer.api import BalancerPacket, parse_packet
from custom_components.defa_balancer.const import LOGGER


class BalancerListener(ABC):
    """Abstract listener for Balancer packets."""

    @abstractmethod
    async def start(self) -> None:
        """Start receiving packets."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop receiving packets and release resources."""

    @abstractmethod
    def get_latest(self) -> list[BalancerPacket]:
        """Return latest packet snapshot from internal buffer."""


class _DatagramProtocol(asyncio.DatagramProtocol):
    """UDP protocol that parses incoming packets into a shared queue."""

    def __init__(self, listener: UDPBalancerListener) -> None:
        self._listener = listener

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        del addr
        packet = parse_packet(data)
        if packet is None:
            return

        if self._listener.serial and packet.serial != self._listener.serial:
            return

        self._listener.push(packet)


class UDPBalancerListener(BalancerListener):
    """Listen DEFA Balancer multicast UDP packets continuously."""

    def __init__(
        self,
        multicast_group: str,
        multicast_port: int,
        serial: str | None,
        *,
        buffer_size: int = 25,
    ) -> None:
        """Initialize listener with multicast endpoint and optional serial filter."""
        self._multicast_group = multicast_group
        self._multicast_port = multicast_port
        self.serial = serial
        self._buffer: deque[BalancerPacket] = deque(maxlen=buffer_size)
        self._transport: asyncio.DatagramTransport | None = None
        self._packet_event: asyncio.Event = asyncio.Event()

    async def start(self) -> None:
        """Open the multicast socket and start receiving datagrams."""
        if self._transport is not None:
            return

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self._multicast_port))

        mreq = struct.pack("4sL", socket.inet_aton(self._multicast_group), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.setblocking(False)

        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _DatagramProtocol(self),
            sock=sock,
        )
        self._transport = transport
        LOGGER.debug("UDP listener started for %s:%s", self._multicast_group, self._multicast_port)

    async def stop(self) -> None:
        """Close the underlying UDP transport."""
        if self._transport is None:
            return
        self._transport.close()
        self._transport = None

    def get_latest(self) -> list[BalancerPacket]:
        """Return snapshot of most recent packets."""
        return list(self._buffer)

    async def wait_for_packet(self, timeout: float) -> bool:
        """Wait up to *timeout* seconds for the first packet. Returns True if received."""
        try:
            await asyncio.wait_for(self._packet_event.wait(), timeout=timeout)
        except TimeoutError:
            return False
        else:
            return True

    def get_all_serials(self) -> list[str]:
        """Return all unique serial numbers seen in the buffer (insertion order)."""
        return list(dict.fromkeys(p.serial for p in self._buffer))

    def push(self, packet: BalancerPacket) -> None:
        """Add a parsed packet to the ring buffer and signal waiters."""
        self._buffer.append(packet)
        self._packet_event.set()


class MockBalancerListener(BalancerListener):
    """In-memory listener for tests and local development."""

    def __init__(self, packets: Iterable[BalancerPacket] | None = None) -> None:
        """Initialize with a predefined packet sequence."""
        self._packets: list[BalancerPacket] = list(packets or [])

    async def start(self) -> None:
        """No-op start."""

    async def stop(self) -> None:
        """No-op stop."""

    def get_latest(self) -> list[BalancerPacket]:
        """Return configured packets."""
        return list(self._packets)

    def get_all_serials(self) -> list[str]:
        """Return all unique serial numbers from configured packets."""
        return list(dict.fromkeys(p.serial for p in self._packets))
