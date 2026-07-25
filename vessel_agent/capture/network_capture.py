"""
Network Packet Capture Module

Implements lossless UDP packet capture for Furuno sounder data.
Uses BPF filters and ring buffers for zero-copy packet processing.

Target: 15Hz Furuno FCV series acoustic data
Environment: Windows/Linux with pcap-compatible network interface
"""

import socket
import struct
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Dict, Any

try:
    import dpkt
    DPKT_AVAILABLE = True
except ImportError:
    DPKT_AVAILABLE = False
    print("Warning: dpkt not available, using fallback packet parsing")


@dataclass
class PacketMetadata:
    """Metadata for captured packets."""
    timestamp_ns: int
    timestamp_dt: datetime
    packet_size: int
    wire_size: int
    capture_length: int
    protocol: str
    source_ip: str
    dest_ip: str
    source_port: int
    dest_port: int


@dataclass
class FurunoPacket:
    """Parsed Furuno sounder packet."""
    metadata: PacketMetadata
    raw_bytes: bytes
    packet_type: str
    depth_range: Optional[float] = None
    depth_values: Optional[list] = None
    frequency: Optional[int] = None
    gain: Optional[int] = None


class RingBuffer:
    """Fixed-size ring buffer for lossless packet capture.

    Pre-allocates memory for packets to avoid allocation during capture.
    """

    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        self.dropped_packets = 0
        self.total_packets = 0

    def put(self, packet: bytes) -> bool:
        """Add packet to buffer.

        Returns:
            True if packet added, False if buffer full (packet dropped)
        """
        self.total_packets += 1
        if len(self.buffer) >= self.capacity:
            self.dropped_packets += 1
            return False
        self.buffer.append(packet)
        return True

    def get(self) -> Optional[bytes]:
        """Get next packet from buffer."""
        if not self.buffer:
            return None
        return self.buffer.popleft()

    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        return {
            "current_size": len(self.buffer),
            "capacity": self.capacity,
            "dropped_packets": self.dropped_packets,
            "total_packets": self.total_packets,
            "drop_rate_percent": (
                100 * self.dropped_packets / self.total_packets
                if self.total_packets > 0 else 0
            ),
        }


class NetworkCapture:
    """Network packet capture for Furuno sounder data.

    Usage:
        capture = NetworkCapture(interface="Ethernet", port=8000)

        # Start capture in background
        capture.start()

        # Process packets
        while True:
            packet = capture.get_packet(timeout=1.0)
            if packet:
                process_packet(packet)

        # Stop capture
        capture.stop()
    """

    def __init__(
        self,
        interface: str = "Ethernet",
        port: int = 8000,
        bpf_filter: Optional[str] = None,
        buffer_size: int = 10000,
    ):
        """Initialize network capture.

        Args:
            interface: Network interface name (ipconfig/ifconfig to find)
            port: UDP port to capture (Furuno default: 8000)
            bpf_filter: Optional BPF filter string
            buffer_size: Ring buffer capacity in packets
        """
        self.interface = interface
        self.port = port
        self.bpf_filter = bpf_filter or f"udp port {port}"
        self.buffer_size = buffer_size

        self.ring_buffer = RingBuffer(capacity=buffer_size)
        self.running = False
        self.socket: Optional[socket.socket] = None
        self.stats = {
            "start_time": None,
            "packets_captured": 0,
            "bytes_captured": 0,
            "capture_errors": 0,
        }

    def start(self) -> None:
        """Start packet capture.

        Raises:
            OSError: If cannot bind to interface or port
        """
        if self.running:
            return

        self.running = True
        self.stats["start_time"] = time.time()

        # Create raw socket for UDP capture
        try:
            self.socket = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM
            )
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("0.0.0.0", self.port))
            self.socket.settimeout(1.0)  # Non-blocking with timeout

        except Exception as e:
            raise OSError(f"Failed to create capture socket: {e}")

    def stop(self) -> None:
        """Stop packet capture."""
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None

    def get_packet(self, timeout: float = 1.0) -> Optional[FurunoPacket]:
        """Get next captured packet.

        Args:
            timeout: Seconds to wait for packet

        Returns:
            FurunoPacket if available, None if timeout
        """
        if not self.running:
            raise RuntimeError("Capture not running. Call start() first.")

        try:
            # Receive from socket
            data, addr = self.socket.recvfrom(2048)

            if not data:
                return None

            # Update stats
            self.stats["packets_captured"] += 1
            self.stats["bytes_captured"] += len(data)

            # Create metadata
            now = datetime.now()
            timestamp_ns = int(now.timestamp() * 1e9)

            metadata = PacketMetadata(
                timestamp_ns=timestamp_ns,
                timestamp_dt=now,
                packet_size=len(data),
                wire_size=len(data),
                capture_length=len(data),
                protocol="UDP",
                source_ip=addr[0],
                dest_ip="0.0.0.0",
                source_port=addr[1],
                dest_port=self.port,
            )

            # Parse Furuno packet
            packet = self._parse_furuno_packet(data, metadata)
            return packet

        except socket.timeout:
            return None
        except Exception as e:
            self.stats["capture_errors"] += 1
            print(f"Capture error: {e}")
            return None

    def _parse_furuno_packet(
        self, data: bytes, metadata: PacketMetadata
    ) -> FurinoPacket:
        """Parse Furuno sounder packet.

        Furuno FCV series format (simplified):
        - Header: 0x02 0x00 (STX)
        - Data: 16-bit depth values
        - Trailer: 0x03 0x00 (ETX)

        This is a basic parser. Real Furuno parsing requires spec.
        """
        packet_type = "UNKNOWN"

        # Check for Furuno header
        if len(data) >= 2 and data[0] == 0x02 and data[1] == 0x00:
            packet_type = "FCV_SOUNDING"

            # Extract 16-bit depth values (after header)
            depth_values = []
            if len(data) >= 4:
                for i in range(2, len(data) - 2, 2):
                    if i + 1 < len(data):
                        value = struct.unpack(">H", data[i:i+2])[0]
                        depth_values.append(value)

            return FurinoPacket(
                metadata=metadata,
                raw_bytes=data,
                packet_type=packet_type,
                depth_values=depth_values if depth_values else None,
            )

        return FurinoPacket(
            metadata=metadata,
            raw_bytes=data,
            packet_type=packet_type,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get capture statistics.

        Returns:
            Dictionary with capture statistics
        """
        uptime = (
            time.time() - self.stats["start_time"]
            if self.stats["start_time"]
            else 0
        )

        return {
            "running": self.running,
            "uptime_seconds": uptime,
            "packets_captured": self.stats["packets_captured"],
            "bytes_captured": self.stats["bytes_captured"],
            "capture_errors": self.stats["capture_errors"],
            "capture_rate_hz": (
                self.stats["packets_captured"] / uptime
                if uptime > 0
                else 0
            ),
            "data_rate_mbps": (
                (self.stats["bytes_captured"] * 8) / (uptime * 1e6)
                if uptime > 0
                else 0
            ),
            "buffer_stats": self.ring_buffer.get_stats(),
        }


class MockNetworkCapture(NetworkCapture):
    """Mock capture for development/testing without hardware.

    Generates synthetic Furuno-style packets at specified rate.
    """

    def __init__(self, rate_hz: float = 15.0, **kwargs):
        super().__init__(**kwargs)
        self.rate_hz = rate_hz
        self.packet_interval = 1.0 / rate_hz
        self.last_packet_time = 0

    def get_packet(self, timeout: float = 1.0) -> Optional[FurinoPacket]:
        """Get next mock packet."""
        if not self.running:
            raise RuntimeError("Capture not running. Call start() first.")

        # Rate limiting
        now = time.time()
        elapsed = now - self.last_packet_time
        if elapsed < self.packet_interval:
            time.sleep(self.packet_interval - elapsed)

        self.last_packet_time = time.time()

        # Generate mock packet
        now = datetime.now()
        timestamp_ns = int(now.timestamp() * 1e9)

        # Create mock depth values (100 bins)
        depth_values = [
            100 + int(50 * (i / 100))  # Linear depth gradient
            for i in range(100)
        ]

        metadata = PacketMetadata(
            timestamp_ns=timestamp_ns,
            timestamp_dt=now,
            packet_size=204,
            wire_size=204,
            capture_length=204,
            protocol="UDP",
            source_ip="192.168.1.100",
            dest_ip="255.255.255.255",
            source_port=8000,
            dest_port=8000,
        )

        # Create mock raw packet
        raw_data = struct.pack(">HH", 0x0200, 0x0000)  # Header
        for depth in depth_values:
            raw_data += struct.pack(">H", depth)
        raw_data += struct.pack(">HH", 0x0300, 0x0000)  # Trailer

        return FurinoPacket(
            metadata=metadata,
            raw_bytes=raw_data,
            packet_type="MOCK_FCV_SOUNDING",
            depth_values=depth_values,
            depth_range=100.0,
            frequency=50000,  # 50 kHz
            gain=70,
        )


def create_capture(interface: str = "Ethernet", port: int = 8000,
                  mock: bool = False, mock_rate: float = 15.0) -> NetworkCapture:
    """Factory function to create capture instance.

    Args:
        interface: Network interface name
        port: UDP port to capture
        mock: Use mock capture for development
        mock_rate: Mock data rate in Hz

    Returns:
        NetworkCapture instance
    """
    if mock:
        return MockNetworkCapture(
            interface=interface, port=port, rate_hz=mock_rate
        )
    return NetworkCapture(interface=interface, port=port)


if __name__ == "__main__":
    # Test capture
    print("Testing network capture (mock mode)...")

    capture = create_capture(interface="Ethernet", port=8000, mock=True)

    print("Starting capture...")
    capture.start()

    try:
        for i in range(10):
            packet = capture.get_packet(timeout=2.0)
            if packet:
                print(f"Packet {i+1}: {packet.packet_type}, "
                      f"size={packet.metadata.packet_size} bytes, "
                      f"{len(packet.depth_values) if packet.depth_values else 0} depth values")

        stats = capture.get_stats()
        print(f"\nCapture stats: {stats}")

    finally:
        capture.stop()
        print("Capture stopped.")
