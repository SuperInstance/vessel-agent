"""
Tests for NMEA Interpolation Module

Test suite for NMEA parsing and GPS interpolation.
"""

import pytest
from datetime import datetime

from vessel_agent.capture.nmea_interpolator import (
    validate_nmea_checksum,
    parse_nmea_time,
    parse_nmea_latitude,
    parse_nmea_longitude,
    parse_rmc,
    parse_gga,
    GPSPosition,
    InterpolatedPosition,
    NMEAInterpolator,
)


class TestNMEAValidation:
    """Tests for NMEA validation functions."""

    def test_checksum_valid(self):
        """Test checksum validation with valid sentence."""
        sentence = "$GPRMC,210230,A,3855.4487,N,09446.0071,W,0.0,076.2,210324,,,A*47"
        assert validate_nmea_checksum(sentence) is True

    def test_checksum_invalid(self):
        """Test checksum validation with invalid sentence."""
        sentence = "$GPRMC,210230,A,3855.4487,N,09446.0071,W,0.0,076.2,210324,,,A*FF"
        assert validate_nmea_checksum(sentence) is False

    def test_checksum_missing(self):
        """Test checksum validation with missing checksum."""
        sentence = "$GPRMC,210230,A,3855.4487,N,09446.0071,W,0.0,076.2,210324,,,A"
        assert validate_nmea_checksum(sentence) is False


class TestNMEAParsing:
    """Tests for NMEA parsing functions."""

    def test_parse_time_valid(self):
        """Test parsing valid NMEA time."""
        time_str = "210230.500"
        result = parse_nmea_time(time_str)
        assert result is not None
        # Should create datetime with correct time

    def test_parse_time_invalid(self):
        """Test parsing invalid NMEA time."""
        assert parse_nmea_time("") is None
        assert parse_nmea_time("abc") is None

    def test_parse_latitude_valid(self):
        """Test parsing valid NMEA latitude."""
        # Example from docs: 3855.4487,N -> 38.924145
        lat = parse_nmea_latitude("3855.4487", "N")
        assert lat == pytest.approx(38.924145, rel=0.0001)

    def test_parse_latitude_southern(self):
        """Test parsing southern hemisphere latitude."""
        lat = parse_nmea_latitude("3855.4487", "S")
        assert lat == pytest.approx(-38.924145, rel=0.0001)

    def test_parse_longitude_valid(self):
        """Test parsing valid NMEA longitude."""
        # Example from docs: 09446.0071,W -> -94.766785
        lon = parse_nmea_longitude("09446.0071", "W")
        assert lon == pytest.approx(-94.766785, rel=0.0001)

    def test_parse_longitude_eastern(self):
        """Test parsing eastern hemisphere longitude."""
        lon = parse_nmea_longitude("01131.000", "E")
        assert lon == pytest.approx(11.516667, rel=0.0001)

    def test_parse_invalid_coords(self):
        """Test parsing invalid coordinates."""
        assert parse_nmea_latitude("", "N") is None
        assert parse_nmea_longitude("", "E") is None
        assert parse_nmea_latitude("abc", "N") is None


class TestRMCParsing:
    """Tests for RMC sentence parsing."""

    def test_parse_rmc_valid(self):
        """Test parsing valid RMC sentence."""
        sentence = "$GPRMC,210230,A,3855.4487,N,09446.0071,W,0.0,076.2,210324,,,A*47"
        result = parse_rmc(sentence)

        assert result is not None
        assert isinstance(result, GPSPosition)
        assert result.latitude == pytest.approx(38.924145, rel=0.0001)
        assert result.longitude == pytest.approx(-94.766785, rel=0.0001)
        assert result.speed_knots == 0.0
        assert result.track_made_good == 76.2

    def test_parse_rmc_invalid_status(self):
        """Test parsing RMC with invalid status."""
        sentence = "$GPRMC,210230,V,3855.4487,N,09446.0071,W,0.0,076.2,210324,,,A*47"
        result = parse_rmc(sentence)

        # Status V = Invalid, should return None
        assert result is None

    def test_parse_rmc_invalid_checksum(self):
        """Test parsing RMC with invalid checksum."""
        sentence = "$GPRMC,210230,A,3855.4487,N,09446.0071,W,0.0,076.2,210324,,,A*FF"
        result = parse_rmc(sentence)

        assert result is None


class TestGGAParsing:
    """Tests for GGA sentence parsing."""

    def test_parse_gga_valid(self):
        """Test parsing valid GGA sentence."""
        sentence = "$GPGGA,123519,4807.036,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
        result = parse_gga(sentence)

        assert result is not None
        assert isinstance(result, GPSPosition)
        assert result.latitude == pytest.approx(48.1176, rel=0.0001)
        assert result.longitude == pytest.approx(11.516667, rel=0.0001)
        assert result.altitude == 545.4
        assert result.fix_quality == 1
        assert result.satellites == 8

    def test_parse_gga_no_fix(self):
        """Test parsing GGA with no fix."""
        sentence = "$GPGGA,123519,4807.036,N,01131.000,E,0,00,0.0,0.0,M,,,*47"
        result = parse_gga(sentence)

        # Should still parse but fix_quality = 0
        assert result is not None
        assert result.fix_quality == 0


class TestGPSPosition:
    """Tests for GPSPosition dataclass."""

    def test_creation(self):
        """Test creating GPS position."""
        position = GPSPosition(
            timestamp_ns=1721741135000000000,
            timestamp_dt=datetime.fromtimestamp(1721741135),
            latitude=56.3,
            longitude=-134.5,
            altitude=100.0,
            speed_knots=8.0,
            heading_true=90.0,
            satellites=8,
            hdop=1.0,
        )

        assert position.timestamp_ns == 1721741135000000000
        assert position.latitude == 56.3
        assert position.longitude == -134.5
        assert position.altitude == 100.0


class TestNMEAInterpolator:
    """Tests for NMEA interpolator."""

    def test_init(self):
        """Test interpolator initialization."""
        interpolator = NMEAInterpolator(max_age_ms=2000)

        assert interpolator.max_age_ms == 2000
        assert interpolator.method == "linear"
        assert len(interpolator.positions) == 0

    def test_add_gps_position(self):
        """Test adding GPS position."""
        interpolator = NMEAInterpolator()

        position = GPSPosition(
            timestamp_ns=1721741130000000000,
            timestamp_dt=datetime.fromtimestamp(1721741130),
            latitude=56.3,
            longitude=-134.5,
        )

        interpolator.add_gps_position(position)

        assert len(interpolator.positions) == 1

    def test_interpolate_between_positions(self):
        """Test interpolating between two positions."""
        interpolator = NMEAInterpolator(max_age_ms=2000)

        # Add two positions 1 second apart
        pos1 = GPSPosition(
            timestamp_ns=1721741130000000000,  # T=0
            timestamp_dt=datetime.fromtimestamp(1721741130),
            latitude=56.300,
            longitude=-134.500,
            speed_knots=10.0,
            heading_true=90.0,
        )

        pos2 = GPSPosition(
            timestamp_ns=1721741131000000000,  # T=1
            timestamp_dt=datetime.fromtimestamp(1721741131),
            latitude=56.301,
            longitude=-134.400,
            speed_knots=10.0,
            heading_true=90.0,
        )

        interpolator.add_gps_position(pos1)
        interpolator.add_gps_position(pos2)

        # Interpolate at T=0.5
        result = interpolator.get_position(1721741130500000000)

        assert result is not None
        assert isinstance(result, InterpolatedPosition)
        assert result.latitude == pytest.approx(56.3005, rel=0.0001)  # Midpoint
        assert result.longitude == pytest.approx(-134.450, rel=0.0001)  # Midpoint
        assert result.method == "linear"
        assert result.confidence == pytest.approx(1.0, rel=0.01)
        assert result.reference_points == 2

    def test_extrapolate_forward(self):
        """Test forward extrapolation."""
        interpolator = NMEAInterpolator(max_age_ms=2000)

        pos1 = GPSPosition(
            timestamp_ns=1721741130000000000,
            timestamp_dt=datetime.fromtimestamp(1721741130),
            latitude=56.3,
            longitude=-134.5,
            speed_knots=10.0,
            heading_true=90.0,  # East
        )

        interpolator.add_gps_position(pos1)

        # Get position 500ms in future (within max_age)
        result = interpolator.get_position(1721741130500000000)

        assert result is not None
        assert result.method == "extrapolation"
        assert result.confidence < 1.0  # Lower confidence for extrapolation
        assert result.reference_points == 1

    def test_interpolation_too_old(self):
        """Test interpolation fails when GPS too old."""
        interpolator = NMEAInterpolator(max_age_ms=100)  # 100ms max age

        pos1 = GPSPosition(
            timestamp_ns=1721741130000000000,
            timestamp_dt=datetime.fromtimestamp(1721741130),
            latitude=56.3,
            longitude=-134.5,
        )

        interpolator.add_gps_position(pos1)

        # Request position 500ms later (beyond max_age)
        result = interpolator.get_position(1721741130500000000)

        assert result is None

    def test_interpolation_no_positions(self):
        """Test interpolation fails with no positions."""
        interpolator = NMEAInterpolator()

        result = interpolator.get_position(1721741135000000000)

        assert result is None

    def test_angle_interpolation(self):
        """Test angle interpolation with wraparound."""
        interpolator = NMEAInterpolator()

        # Test wraparound: 350 -> 10 (crosses 0/360)
        result = interpolator._interpolate_angle(350.0, 10.0, 0.5)

        # Should get 0 (crossing 360/0)
        assert result == pytest.approx(0.0, abs=1.0)

    def test_stats(self):
        """Test interpolator statistics."""
        interpolator = NMEAInterpolator()

        pos1 = GPSPosition(
            timestamp_ns=1721741130000000000,
            timestamp_dt=datetime.fromtimestamp(1721741130),
            latitude=56.3,
            longitude=-134.5,
        )

        interpolator.add_gps_position(pos1)

        # Successful query
        interpolator.get_position(1721741130500000000)

        stats = interpolator.get_stats()
        assert stats["total_queries"] == 1
        assert stats["buffer_size"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
