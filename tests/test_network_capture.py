"""
Tests for Network Capture Module

Test suite for network packet capture functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from vessel_agent.capture.network_capture import (
    RingBuffer,
    PacketMetadata,
    FurinoPacket,
    NetworkCapture,
    MockNetworkCapture,
    create_capture,
)


class TestRingBuffer:
    """Tests for RingBuffer class."""

    def test_init(self):
        """Test ring buffer initialization."""
        buffer = RingBuffer(capacity=100)
        assert buffer.capacity == 100
        assert buffer.dropped_packets == 0
        assert buffer.total_packets == 0

    def test_put(self):
        """Test putting packets into buffer."""
        buffer = RingBuffer(capacity=3)

        # Add packets
        assert buffer.put(b"packet1") is True
        assert buffer.put(b"packet2") is True
        assert buffer.put(b"packet3") is True

        # Buffer should be full now
        assert buffer.put(b"packet4") is True  # Ring overwrites
        assert buffer.dropped_packets == 1

    def test_get(self):
        """Test getting packets from buffer."""
        buffer = RingBuffer(capacity=10)

        # Empty buffer returns None
        assert buffer.get() is None

        # Add and retrieve
        buffer.put(b"packet1")
        assert buffer.get() == b"packet1"

        # Buffer empty again
        assert buffer.get() is None

    def test_stats(self):
        """Test buffer statistics."""
        buffer = RingBuffer(capacity=2)

        buffer.put(b"p1")
        buffer.put(b"p2")
        buffer.put(b"p3")  # Drops p1

        stats = buffer.get_stats()
        assert stats["current_size"] == 2
        assert stats["capacity"] == 2
        assert stats["dropped_packets"] == 1
        assert stats["total_packets"] == 3
        assert stats["drop_rate_percent"] == pytest.approx(33.33, rel=0.01)


class TestPacketMetadata:
    """Tests for PacketMetadata dataclass."""

    def test_creation(self):
        """Test creating packet metadata."""
        metadata = PacketMetadata(
            timestamp_ns=1721741135000000000,
            timestamp_dt=datetime.fromtimestamp(1721741135),
            packet_size=1024,
            wire_size=1024,
            capture_length=1024,
            protocol="UDP",
            source_ip="192.168.1.100",
            dest_ip="255.255.255.255",
            source_port=8000,
            dest_port=8000,
        )

        assert metadata.timestamp_ns == 1721741135000000000
        assert metadata.protocol == "UDP"
        assert metadata.packet_size == 1024


class TestFurinoPacket:
    """Tests for FurinoPacket dataclass."""

    def test_creation(self):
        """Test creating Furuno packet."""
        metadata = PacketMetadata(
            timestamp_ns=1721741135000000000,
            timestamp_dt=datetime.fromtimestamp(1721741135),
            packet_size=204,
            wire_size=204,
            capture_length=204,
            protocol="UDP",
            source_ip="192.168.1.100",
            dest_ip="255.255.255.255",
            source_port=8000,
            dest_port=8000,
        )

        packet = FurinoPacket(
            metadata=metadata,
            raw_bytes=b"\x02\x00\x00\x00\x03\x00",
            packet_type="FCV_SOUNDING",
            depth_values=[100, 101, 102],
            frequency=50000,
        )

        assert packet.packet_type == "FCV_SOUNDING"
        assert len(packet.depth_values) == 3
        assert packet.frequency == 50000


class TestNetworkCapture:
    """Tests for NetworkCapture class."""

    def test_init(self):
        """Test network capture initialization."""
        capture = NetworkCapture(
            interface="Ethernet",
            port=8000,
            buffer_size=1000,
        )

        assert capture.interface == "Ethernet"
        assert capture.port == 8000
        assert capture.buffer_size == 1000
        assert capture.bpf_filter == "udp port 8000"
        assert not capture.running

    def test_stop_without_start(self):
        """Test stopping without starting is safe."""
        capture = NetworkCapture(port=8000)
        capture.stop()  # Should not raise


class TestMockNetworkCapture:
    """Tests for MockNetworkCapture class."""

    def test_init(self):
        """Test mock capture initialization."""
        mock = MockNetworkCapture(rate_hz=15.0, port=8000)

        assert mock.rate_hz == 15.0
        assert mock.packet_interval == pytest.approx(1/15, rel=0.01)

    def test_get_packet(self):
        """Test getting mock packet."""
        mock = MockNetworkCapture(rate_hz=15.0, port=8000)
        mock.start()

        packet = mock.get_packet(timeout=1.0)

        assert packet is not None
        assert packet.packet_type == "MOCK_FCV_SOUNDING"
        assert packet.depth_values is not None
        assert len(packet.depth_values) == 100
        assert packet.frequency == 50000

        mock.stop()

    def test_packet_rate(self):
        """Test mock packet rate limiting."""
        import time

        mock = MockNetworkCapture(rate_hz=10.0, port=8000)  # 10 Hz = 100ms interval
        mock.start()

        start = time.time()
        packets = []

        for _ in range(5):
            packet = mock.get_packet(timeout=1.0)
            packets.append(packet)

        elapsed = time.time() - start
        mock.stop()

        # Should take ~500ms for 5 packets at 10 Hz
        assert elapsed >= pytest.approx(0.4, abs=0.15)  # Allow some variance
        assert len(packets) == 5


class TestCreateCapture:
    """Tests for create_capture factory function."""

    def test_create_live_capture(self):
        """Test creating live capture."""
        capture = create_capture(interface="Ethernet", port=8000, mock=False)

        assert isinstance(capture, NetworkCapture)
        assert not isinstance(capture, MockNetworkCapture)

    def test_create_mock_capture(self):
        """Test creating mock capture."""
        capture = create_capture(interface="Ethernet", port=8000, mock=True)

        assert isinstance(capture, MockNetworkCapture)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
