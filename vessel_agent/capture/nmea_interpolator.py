"""
NMEA Interpolation Module

Implies GPS positions between 1Hz GPS updates and 15Hz sounder data.
Enables time-synchronization of acoustic data with vessel position.

Critical for: Spatial indexing (H3), data fusion, track reconstruction
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum


class SentenceType(Enum):
    """NMEA sentence types."""
    GPRMC = "RMC"  # Position, speed, heading
    GPGGA = "GGA"  # Position, altitude, satellites
    GPHDT = "HDT"  # Heading true
    GPVTG = "VTG"  # Velocity made good
    SDDPT = "DPT"  # Depth (sounder)
    SDDBT = "DBT"  # Depth below transducer


@dataclass
class GPSPosition:
    """GPS position with time."""
    timestamp_ns: int
    timestamp_dt: datetime
    latitude: float  # Decimal degrees
    longitude: float  # Decimal degrees
    altitude: Optional[float] = None  # Meters above MSL
    speed_knots: Optional[float] = None
    heading_true: Optional[float] = None  # Degrees true
    heading_magnetic: Optional[float] = None  # Degrees magnetic
    speed_over_ground: Optional[float] = None
    track_made_good: Optional[float] = None
    satellites: Optional[int] = None
    hdop: Optional[float] = None  # Horizontal dilution of precision
    fix_quality: Optional[int] = None  # 0=Invalid, 1=GPS, 2=DGPS
    magnetic_variation: Optional[float] = None


@dataclass
class InterpolatedPosition:
    """Interpolated position for a specific timestamp."""
    timestamp_ns: int
    timestamp_dt: datetime
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    speed_knots: Optional[float] = None
    heading_true: Optional[float] = None

    # Metadata
    method: str = "linear"  # Interpolation method
    age_gps_ms: float = 0  # Age of GPS data used
    confidence: float = 1.0  # Confidence score (0-1)
    reference_points: int = 0  # Number of GPS points used


@dataclass
class NMEASentence:
    """Parsed NMEA sentence."""
    raw: str
    talker: str  # GP, HC, EC, SD, etc.
    sentence_type: SentenceType
    timestamp_ns: int
    timestamp_dt: datetime
    parsed: Dict[str, Any] = field(default_factory=dict)
    checksum_valid: bool = True


def validate_nmea_checksum(sentence: str) -> bool:
    """Validate NMEA checksum.

    Args:
        sentence: NMEA sentence (including $ and checksum)

    Returns:
        True if checksum valid

    Example:
        >>> validate_nmea_checksum("$GPRMC,210230,A*47")
        True
    """
    star_idx = sentence.find("*")
    if star_idx == -1:
        return False

    provided = sentence[star_idx + 1:star_idx + 3]
    calculated = 0

    for char in sentence[1:star_idx]:
        calculated ^= ord(char)

    return f"{calculated:02X}" == provided


def parse_nmea_time(time_str: str) -> Optional[datetime]:
    """Parse NMEA time string.

    Args:
        time_str: NMEA time (HHMMSS.sss)

    Returns:
        datetime object or None if invalid
    """
    try:
        if len(time_str) < 6:
            return None

        hours = int(time_str[0:2])
        minutes = int(time_str[2:4])
        seconds = float(time_str[4:])

        # Use today's date (time only in NMEA)
        today = datetime.now().date()
        return datetime.combine(today, timedelta(hours=hours, minutes=minutes, seconds=seconds).seconds() / 3600)  # Bug, need to fix

    except (ValueError, IndexError):
        return None


def parse_nmea_date(date_str: str) -> Optional[datetime]:
    """Parse NMEA date string.

    Args:
        date_str: NMEA date (DDMMYY)

    Returns:
        datetime object (date only) or None if invalid
    """
    try:
        if len(date_str) != 6:
            return None

        day = int(date_str[0:2])
        month = int(date_str[2:4])
        year = 2000 + int(date_str[4:6])  # Y2K fix

        return datetime(year, month, day)

    except (ValueError, IndexError):
        return None


def parse_nmea_latitude(lat_str: str, hem: str) -> Optional[float]:
    """Parse NMEA latitude to decimal degrees.

    Args:
        lat_str: NMEA latitude (DDMM.MMMM)
        hem: Hemisphere (N or S)

    Returns:
        Decimal degrees or None if invalid

    Example:
        >>> parse_nmea_latitude("3855.4487", "N")
        38.924145
    """
    try:
        if not lat_str or not hem:
            return None

        # Parse DDMM.MMMM format
        degrees = float(lat_str[:2]) if len(lat_str) > 2 else 0
        minutes = float(lat_str[2:]) if len(lat_str) > 2 else 0

        decimal = degrees + minutes / 60.0

        # Apply hemisphere
        if hem.upper() == "S":
            decimal = -decimal

        return decimal

    except (ValueError, IndexError):
        return None


def parse_nmea_longitude(lon_str: str, hem: str) -> Optional[float]:
    """Parse NMEA longitude to decimal degrees.

    Args:
        lon_str: NMEA longitude (DDDMM.MMMM)
        hem: Hemisphere (E or W)

    Returns:
        Decimal degrees or None if invalid

    Example:
        >>> parse_nmea_longitude("09446.0071", "W")
        -94.766785
    """
    try:
        if not lon_str or not hem:
            return None

        # Parse DDDMM.MMMM format
        degrees = float(lon_str[:3]) if len(lon_str) > 3 else 0
        minutes = float(lon_str[3:]) if len(lon_str) > 3 else 0

        decimal = degrees + minutes / 60.0

        # Apply hemisphere
        if hem.upper() == "W":
            decimal = -decimal

        return decimal

    except (ValueError, IndexError):
        return None


def parse_rmc(sentence: str) -> Optional[GPSPosition]:
    """Parse GPRMC sentence (Recommended Minimum Navigation Information).

    Args:
        sentence: Raw GPRMC sentence

    Returns:
        GPSPosition or None if invalid

    Example:
        >>> parse_rmc("$GPRMC,210230,A,3855.4487,N,09446.0071,W,0.0,076.2,210324,,,A*47")
        GPSPosition(latitude=38.924145, longitude=-94.766785, ...)
    """
    if not validate_nmea_checksum(sentence):
        return None

    parts = sentence.split(",")
    if len(parts) < 12 or parts[0] != "$GPRMC":
        return None

    # Check status
    status = parts[2]
    if status != "A":  # A=Valid, V=Invalid
        return None

    # Parse time
    time_str = parts[1]
    dt = parse_nmea_time(time_str)
    if not dt:
        return None

    # Add date if available
    if parts[9]:  # DDMMYY
        date_part = parse_nmea_date(parts[9])
        if date_part:
            dt = datetime.combine(date_part.date(), dt.time())

    timestamp_ns = int(dt.timestamp() * 1e9)

    # Parse position
    latitude = parse_nmea_latitude(parts[3], parts[4])
    longitude = parse_nmea_longitude(parts[5], parts[6])

    if latitude is None or longitude is None:
        return None

    # Parse speed (knots)
    try:
        speed_knots = float(parts[7]) if parts[7] else None
    except ValueError:
        speed_knots = None

    # Parse track made good (degrees true)
    try:
        track_made_good = float(parts[8]) if parts[8] else None
    except ValueError:
        track_made_good = None

    # Parse magnetic variation
    mag_var = None
    if parts[10]:
        try:
            mag_var = float(parts[10])
            if parts[11] == "W":
                mag_var = -mag_var
        except ValueError:
            pass

    return GPSPosition(
        timestamp_ns=timestamp_ns,
        timestamp_dt=dt,
        latitude=latitude,
        longitude=longitude,
        speed_knots=speed_knots,
        track_made_good=track_made_good,
        magnetic_variation=mag_var,
    )


def parse_gga(sentence: str) -> Optional[GPSPosition]:
    """Parse GPGGA sentence (Global Positioning System Fix Data).

    Args:
        sentence: Raw GPGGA sentence

    Returns:
        GPSPosition or None if invalid

    Example:
        >>> parse_gga("$GPGGA,123519,4807.036,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47")
        GPSPosition(latitude=48.1176, longitude=11.516667, altitude=545.4, ...)
    """
    if not validate_nmea_checksum(sentence):
        return None

    parts = sentence.split(",")
    if len(parts) < 15 or parts[0] != "$GPGGA":
        return None

    # Parse time
    time_str = parts[1]
    dt = parse_nmea_time(time_str)
    if not dt:
        return None

    timestamp_ns = int(dt.timestamp() * 1e9)

    # Parse position
    latitude = parse_nmea_latitude(parts[2], parts[3])
    longitude = parse_nmea_longitude(parts[4], parts[5])

    if latitude is None or longitude is None:
        return None

    # Parse fix quality
    try:
        fix_quality = int(parts[6])
    except (ValueError, IndexError):
        fix_quality = None

    # Parse satellites
    try:
        satellites = int(parts[7])
    except (ValueError, IndexError):
        satellites = None

    # Parse HDOP
    try:
        hdop = float(parts[8]) if parts[8] else None
    except ValueError:
        hdop = None

    # Parse altitude
    try:
        altitude = float(parts[9]) if parts[9] else None
    except ValueError:
        altitude = None

    return GPSPosition(
        timestamp_ns=timestamp_ns,
        timestamp_dt=dt,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        satellites=satellites,
        hdop=hdop,
        fix_quality=fix_quality,
    )


class NMEAInterpolator:
    """Interpolate GPS positions for sounder timestamp synchronization.

    Problem: GPS updates at 1Hz, sounder at 15Hz.
    Solution: Interpolate positions between GPS fixes.

    Usage:
        interpolator = NMEAInterpolator(max_age_ms=2000)

        # Feed GPS data
        gps = parse_rmc(nmea_sentence)
        interpolator.add_gps_position(gps)

        # Get position for sounder timestamp
        sounder_time_ns = 1721741135000000000
        position = interpolator.get_position(sounder_time_ns)
    """

    def __init__(self, max_age_ms: float = 2000, method: str = "linear"):
        """Initialize interpolator.

        Args:
            max_age_ms: Maximum age of GPS data for interpolation (ms)
            method: Interpolation method ("linear" or "nearest")
        """
        self.max_age_ms = max_age_ms
        self.method = method

        # GPS position buffer (keeps last 10 positions)
        self.positions: List[GPSPosition] = []
        self.max_positions = 10

        # Statistics
        self.stats = {
            "total_queries": 0,
            "successful_interpolations": 0,
            "failed_interpolations": 0,
            "extrapolations": 0,  # Points outside GPS range
        }

    def add_gps_position(self, position: GPSPosition) -> None:
        """Add GPS position to buffer.

        Args:
            position: GPS position from NMEA parser
        """
        self.positions.append(position)

        # Keep buffer size limited
        if len(self.positions) > self.max_positions:
            self.positions.pop(0)

        # Sort by timestamp
        self.positions.sort(key=lambda p: p.timestamp_ns)

    def get_position(self, timestamp_ns: int) -> Optional[InterpolatedPosition]:
        """Get interpolated position for timestamp.

        Args:
            timestamp_ns: Target timestamp in nanoseconds

        Returns:
            InterpolatedPosition or None if unable to interpolate
        """
        self.stats["total_queries"] += 1

        if not self.positions:
            self.stats["failed_interpolations"] += 1
            return None

        # Find surrounding GPS positions
        before = None
        after = None

        for pos in self.positions:
            if pos.timestamp_ns <= timestamp_ns:
                before = pos
            else:
                after = pos
                break

        # Case 1: No position before (extrapolate forward)
        if before is None and after is not None:
            self.stats["extrapolations"] += 1
            return self._extrapolate(after, timestamp_ns, direction="forward")

        # Case 2: No position after (extrapolate backward)
        if after is None and before is not None:
            self.stats["extrapolations"] += 1
            return self._extrapolate(before, timestamp_ns, direction="backward")

        # Case 3: No positions at all
        if before is None and after is None:
            self.stats["failed_interpolations"] += 1
            return None

        # Case 4: Interpolate between two positions
        return self._interpolate_between(before, after, timestamp_ns)

    def _interpolate_between(
        self,
        before: GPSPosition,
        after: GPSPosition,
        target_ns: int,
    ) -> Optional[InterpolatedPosition]:
        """Interpolate between two GPS positions."""
        # Check age
        age_before_ms = (target_ns - before.timestamp_ns) / 1e6
        age_after_ms = (after.timestamp_ns - target_ns) / 1e6

        max_age = max(age_before_ms, age_after_ms)
        if max_age > self.max_age_ms:
            self.stats["failed_interpolations"] += 1
            return None

        # Calculate interpolation factor
        total_span_ns = after.timestamp_ns - before.timestamp_ns
        if total_span_ns == 0:
            return None

        factor = (target_ns - before.timestamp_ns) / total_span_ns

        # Interpolate position (linear)
        lat = before.latitude + (after.latitude - before.latitude) * factor
        lon = before.longitude + (after.longitude - before.longitude) * factor

        # Interpolate altitude if available
        alt = None
        if before.altitude is not None and after.altitude is not None:
            alt = before.altitude + (after.altitude - before.altitude) * factor

        # Interpolate heading if available
        heading = None
        if before.heading_true is not None and after.heading_true is not None:
            # Handle wraparound at 360/0
            heading = self._interpolate_angle(before.heading_true, after.heading_true, factor)

        # Interpolate speed
        speed = None
        if before.speed_knots is not None and after.speed_knots is not None:
            speed = before.speed_knots + (after.speed_knots - before.speed_knots) * factor

        # Calculate confidence
        confidence = max(0, 1 - (max_age / self.max_age_ms))

        dt = datetime.fromtimestamp(target_ns / 1e9)

        self.stats["successful_interpolations"] += 1

        return InterpolatedPosition(
            timestamp_ns=target_ns,
            timestamp_dt=dt,
            latitude=lat,
            longitude=lon,
            altitude=alt,
            speed_knots=speed,
            heading_true=heading,
            method="linear",
            age_gps_ms=max_age,
            confidence=confidence,
            reference_points=2,
        )

    def _extrapolate(
        self,
        reference: GPSPosition,
        target_ns: int,
        direction: str,
    ) -> Optional[InterpolatedPosition]:
        """Extrapolate from single GPS position."""
        age_ms = abs(target_ns - reference.timestamp_ns) / 1e6

        if age_ms > self.max_age_ms:
            self.stats["failed_interpolations"] += 1
            return None

        # Simple extrapolation using last known heading and speed
        dt_seconds = (target_ns - reference.timestamp_ns) / 1e9

        lat = reference.latitude
        lon = reference.longitude

        # Extrapolate position if we have speed and heading
        if reference.speed_knots and reference.heading_true:
            # Convert knots to m/s
            speed_ms = reference.speed_knots * 0.514444

            # Calculate distance
            distance = speed_ms * dt_seconds

            # Calculate offset (simplified)
            lat_offset = (distance * math.cos(math.radians(reference.heading_true))) / 111320
            lon_offset = (distance * math.sin(math.radians(reference.heading_true))) / (111320 * math.cos(math.radians(lat)))

            if direction == "forward":
                lat += lat_offset
                lon += lon_offset
            else:
                lat -= lat_offset
                lon -= lon_offset

        # Calculate confidence (lower for extrapolation)
        confidence = max(0, 0.5 * (1 - (age_ms / self.max_age_ms)))

        dt = datetime.fromtimestamp(target_ns / 1e9)

        self.stats["successful_interpolations"] += 1

        return InterpolatedPosition(
            timestamp_ns=target_ns,
            timestamp_dt=dt,
            latitude=lat,
            longitude=lon,
            altitude=reference.altitude,
            speed_knots=reference.speed_knots,
            heading_true=reference.heading_true,
            method="extrapolation",
            age_gps_ms=age_ms,
            confidence=confidence,
            reference_points=1,
        )

    def _interpolate_angle(self, angle1: float, angle2: float, factor: float) -> float:
        """Interpolate between two angles handling 360/0 wraparound."""
        diff = angle2 - angle1

        # Handle wraparound
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        result = angle1 + diff * factor

        # Normalize to 0-360
        while result < 0:
            result += 360
        while result >= 360:
            result -= 360

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get interpolation statistics."""
        total = self.stats["total_queries"]
        success = self.stats["successful_interpolations"]

        return {
            **self.stats,
            "success_rate_percent": (100 * success / total) if total > 0 else 0,
            "extrapolation_rate_percent": (100 * self.stats["extrapolations"] / total) if total > 0 else 0,
            "buffer_size": len(self.positions),
        }


if __name__ == "__main__":
    # Test NMEA parsing and interpolation
    print("Testing NMEA interpolation...")

    # Parse test sentences
    rmc1 = parse_rmc("$GPRMC,210230,A,3855.4487,N,09446.0071,W,0.0,076.2,210324,,,A*47")
    gga1 = parse_gga("$GPGGA,123519,4807.036,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47")

    print(f"RMC: {rmc1.latitude if rmc1 else 'N/A'}, {rmc1.longitude if rmc1 else 'N/A'}")
    print(f"GGA: {gga1.latitude if gga1 else 'N/A'}, {gga1.longitude if gga1 else 'N/A'}")

    # Test interpolation
    interpolator = NMEAInterpolator(max_age_ms=2000)

    # Add GPS positions at 1Hz
    gps1 = GPSPosition(
        timestamp_ns=1721741130000000000,
        timestamp_dt=datetime.fromtimestamp(1721741130),
        latitude=56.3,
        longitude=-134.5,
        speed_knots=8.0,
        heading_true=90.0,
    )
    interpolator.add_gps_position(gps1)

    gps2 = GPSPosition(
        timestamp_ns=1721741131000000000,  # 1 second later
        timestamp_dt=datetime.fromtimestamp(1721741131),
        latitude=56.301,
        longitude=-134.4,
        speed_knots=8.0,
        heading_true=90.0,
    )
    interpolator.add_gps_position(gps2)

    # Interpolate at 0.5 seconds
    interpolated = interpolator.get_position(1721741130500000000)

    if interpolated:
        print(f"\nInterpolated position:")
        print(f"  Latitude: {interpolated.latitude:.6f}")
        print(f"  Longitude: {interpolated.longitude:.6f}")
        print(f"  Confidence: {interpolated.confidence:.2f}")
        print(f"  Method: {interpolated.method}")

    print(f"\nInterpolation stats: {interpolator.get_stats()}")
