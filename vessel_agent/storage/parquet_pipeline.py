"""
Parquet Storage Pipeline

Implements Parquet-based columnar storage with Hive partitioning for
time-series spatial data from Furuno sounder and GPS.

Storage pattern:
  archive_root/
    year=2026/
      month=07/
        day=24/
          vessel_id=US-AK-FVCATCHER-01.parquet

Features:
- Columnar storage (Apache Arrow + Parquet)
- Hive partitioning (year, month, day, vessel_id)
- H3 spatial indexing
- Time/Location/Source anchoring
- Snappy compression
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator
from dataclasses import dataclass, asdict
from collections import defaultdict

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False
    print("Warning: pyarrow not available. Install: pip install pyarrow")

try:
    import h3
    H3_AVAILABLE = True
except ImportError:
    H3_AVAILABLE = False
    print("Warning: h3 not available. Install: pip install h3")


@dataclass
class AcousticDataPoint:
    """Single acoustic data point with full anchoring."""
    # Time anchor
    timestamp_ns: int

    # Location anchor
    latitude: float
    longitude: float
    h3_index: str  # H3 hex cell ID
    altitude: Optional[float] = None  # Meters above MSL

    # Source anchor
    vessel_id: str = "US-AK-FVCATCHER-01"
    device_id: str = "FURUNO-FCV585"
    source_port: int = 8000

    # Acoustic data
    depth_range: float = 0.0  # Meters
    depth_bin: int = 0  # Bin number
    backscatter_db: float = -999.0  # Sv in dB
    frequency: int = 50000  # Hz (50 kHz default)

    # Vessel state
    speed_knots: Optional[float] = None
    heading: Optional[float] = None

    # Metadata
    data_quality: float = 1.0  # 0-1 confidence
    interpolation_method: Optional[str] = None


@dataclass
class GPSDataPoint:
    """GPS data point with full anchoring."""
    # Time anchor
    timestamp_ns: int

    # Location anchor
    latitude: float
    longitude: float
    h3_index: str
    altitude: Optional[float] = None

    # Source anchor
    vessel_id: str = "US-AK-FVCATCHER-01"
    device_id: str = "GPS-BU353"

    # GPS data
    speed_knots: Optional[float] = None
    heading_true: Optional[float] = None
    track_made_good: Optional[float] = None
    satellites: Optional[int] = None
    hdop: Optional[float] = None
    fix_quality: Optional[int] = None

    # Metadata
    data_quality: float = 1.0


def lat_lon_to_h3(latitude: float, longitude: float, resolution: int = 7) -> str:
    """Convert lat/lon to H3 index.

    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        resolution: H3 resolution (0-15)

    Returns:
        H3 cell ID as hex string

    Example:
        >>> lat_lon_to_h3(56.3, -134.5, 7)
        '0x8a21104523fffff'
    """
    if not H3_AVAILABLE:
        # Fallback: return mock H3 index
        return f"{resolution:02x}{'0' * 15}"

    try:
        h3_int = h3.latlng_to_cell(latitude, longitude, resolution)
        return hex(h3_int)
    except Exception as e:
        print(f"H3 conversion error: {e}")
        return f"{resolution:02x}{'0' * 15}"


class ParquetStoragePipeline:
    """Parquet storage pipeline for vessel data.

    Usage:
        pipeline = ParquetStoragePipeline(
            archive_path="C:/data/vessel_agent/archive",
            vessel_id="US-AK-FVCATCHER-01"
        )

        # Write acoustic data
        for data_point in acoustic_data:
            pipeline.write_acoustic(data_point)

        # Flush to disk
        pipeline.flush()
    """

    def __init__(
        self,
        archive_path: Path,
        vessel_id: str = "US-AK-FVCATCHER-01",
        compression: str = "snappy",
        row_group_size: int = 1000000,
        max_file_size_mb: int = 100,
        h3_resolution: int = 7,
    ):
        """Initialize Parquet storage pipeline.

        Args:
            archive_path: Root directory for archive
            vessel_id: Vessel identifier
            compression: Parquet compression codec
            row_group_size: Row group size for Parquet
            max_file_size_mb: Maximum file size before rotation
            h3_resolution: H3 resolution for spatial indexing
        """
        if not PYARROW_AVAILABLE:
            raise ImportError("pyarrow is required. Install: pip install pyarrow")

        self.archive_path = Path(archive_path)
        self.vessel_id = vessel_id
        self.compression = compression
        self.row_group_size = row_group_size
        self.max_file_size_mb = max_file_size_mb
        self.h3_resolution = h3_resolution

        # Data buffers
        self.acoustic_buffer: List[AcousticDataPoint] = []
        self.gps_buffer: List[GPSDataPoint] = []

        # Statistics
        self.stats = {
            "acoustic_points_written": 0,
            "gps_points_written": 0,
            "files_created": 0,
            "bytes_written": 0,
            "compression_ratio": 0.0,
        }

        # Ensure archive path exists
        self.archive_path.mkdir(parents=True, exist_ok=True)

    def write_acoustic(self, point: AcousticDataPoint) -> None:
        """Write acoustic data point to buffer.

        Args:
            point: Acoustic data point
        """
        # Ensure H3 index is set
        if not point.h3_index or point.h3_index == "0x0":
            point.h3_index = lat_lon_to_h3(
                point.latitude, point.longitude, self.h3_resolution
            )

        self.acoustic_buffer.append(point)

        # Auto-flush if buffer is large
        if len(self.acoustic_buffer) >= self.row_group_size:
            self.flush_acoustic()

    def write_gps(self, point: GPSDataPoint) -> None:
        """Write GPS data point to buffer.

        Args:
            point: GPS data point
        """
        # Ensure H3 index is set
        if not point.h3_index or point.h3_index == "0x0":
            point.h3_index = lat_lon_to_h3(
                point.latitude, point.longitude, self.h3_resolution
            )

        self.gps_buffer.append(point)

        # Auto-flush if buffer is large
        if len(self.gps_buffer) >= self.row_group_size:
            self.flush_gps()

    def flush_acoustic(self) -> None:
        """Flush acoustic buffer to Parquet file."""
        if not self.acoustic_buffer:
            return

        # Get partitioning info from first point
        first_point = self.acoustic_buffer[0]
        dt = datetime.fromtimestamp(first_point.timestamp_ns / 1e9)

        year = dt.year
        month = f"{dt.month:02d}"
        day = f"{dt.day:02d}"

        # Create file path with Hive partitioning
        file_path = (
            self.archive_path /
            f"year={year}" /
            f"month={month}" /
            f"day={day}" /
            f"{self.vessel_id}_acoustic.parquet"
        )

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to Arrow table
        table = self._acoustic_to_arrow(self.acoustic_buffer)

        # Write Parquet
        if file_path.exists():
            # Append to existing file
            existing_table = pq.read_table(file_path)
            combined_table = pa.concat_tables([existing_table, table])
            pq.write_table(
                combined_table,
                file_path,
                compression=self.compression,
            )
        else:
            # Create new file
            pq.write_table(
                table,
                file_path,
                compression=self.compression,
                row_group_size=self.row_group_size,
            )

        # Update stats
        points_written = len(self.acoustic_buffer)
        self.stats["acoustic_points_written"] += points_written
        self.stats["files_created"] += 1

        # Clear buffer
        self.acoustic_buffer.clear()

    def flush_gps(self) -> None:
        """Flush GPS buffer to Parquet file."""
        if not self.gps_buffer:
            return

        # Get partitioning info
        first_point = self.gps_buffer[0]
        dt = datetime.fromtimestamp(first_point.timestamp_ns / 1e9)

        year = dt.year
        month = f"{dt.month:02d}"
        day = f"{dt.day:02d}"

        # Create file path
        file_path = (
            self.archive_path /
            f"year={year}" /
            f"month={month}" /
            f"day={day}" /
            f"{self.vessel_id}_gps.parquet"
        )

        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to Arrow table
        table = self._gps_to_arrow(self.gps_buffer)

        # Write Parquet
        if file_path.exists():
            existing_table = pq.read_table(file_path)
            combined_table = pa.concat_tables([existing_table, table])
            pq.write_table(
                combined_table,
                file_path,
                compression=self.compression,
            )
        else:
            pq.write_table(
                table,
                file_path,
                compression=self.compression,
                row_group_size=self.row_group_size,
            )

        # Update stats
        points_written = len(self.gps_buffer)
        self.stats["gps_points_written"] += points_written
        self.stats["files_created"] += 1

        # Clear buffer
        self.gps_buffer.clear()

    def flush(self) -> None:
        """Flush all buffers to disk."""
        self.flush_acoustic()
        self.flush_gps()

    def _acoustic_to_arrow(self, points: List[AcousticDataPoint]) -> pa.Table:
        """Convert acoustic data points to Arrow table."""
        data = {
            "timestamp_ns": [p.timestamp_ns for p in points],
            "latitude": [p.latitude for p in points],
            "longitude": [p.longitude for p in points],
            "h3_index": [p.h3_index for p in points],
            "altitude": [p.altitude for p in points],
            "vessel_id": [p.vessel_id for p in points],
            "device_id": [p.device_id for p in points],
            "source_port": [p.source_port for p in points],
            "depth_range": [p.depth_range for p in points],
            "depth_bin": [p.depth_bin for p in points],
            "backscatter_db": [p.backscatter_db for p in points],
            "frequency": [p.frequency for p in points],
            "speed_knots": [p.speed_knots for p in points],
            "heading": [p.heading for p in points],
            "data_quality": [p.data_quality for p in points],
            "interpolation_method": [p.interpolation_method for p in points],
        }

        return pa.table(data)

    def _gps_to_arrow(self, points: List[GPSDataPoint]) -> pa.Table:
        """Convert GPS data points to Arrow table."""
        data = {
            "timestamp_ns": [p.timestamp_ns for p in points],
            "latitude": [p.latitude for p in points],
            "longitude": [p.longitude for p in points],
            "h3_index": [p.h3_index for p in points],
            "altitude": [p.altitude for p in points],
            "vessel_id": [p.vessel_id for p in points],
            "device_id": [p.device_id for p in points],
            "speed_knots": [p.speed_knots for p in points],
            "heading_true": [p.heading_true for p in points],
            "track_made_good": [p.track_made_good for p in points],
            "satellites": [p.satellites for p in points],
            "hdop": [p.hdop for p in points],
            "fix_quality": [p.fix_quality for p in points],
            "data_quality": [p.data_quality for p in points],
        }

        return pa.table(data)

    def get_stats(self) -> Dict[str, Any]:
        """Get storage pipeline statistics."""
        return self.stats.copy()

    def query_acoustic(
        self,
        start_time_ns: int,
        end_time_ns: int,
        h3_index: Optional[str] = None,
    ) -> pa.Table:
        """Query acoustic data from archive.

        Args:
            start_time_ns: Start timestamp (nanoseconds)
            end_time_ns: End timestamp (nanoseconds)
            h3_index: Optional H3 cell filter

        Returns:
            Arrow Table with results
        """
        # Convert timestamps to dates for partitioning
        start_dt = datetime.fromtimestamp(start_time_ns / 1e9)
        end_dt = datetime.fromtimestamp(end_time_ns / 1e9)

        # Collect matching files
        tables = []

        current_dt = start_dt
        while current_dt <= end_dt:
            year = current_dt.year
            month = f"{current_dt.month:02d}"
            day = f"{current_dt.day:02d}"

            file_path = (
                self.archive_path /
                f"year={year}" /
                f"month={month}" /
                f"day={day}" /
                f"{self.vessel_id}_acoustic.parquet"
            )

            if file_path.exists():
                table = pq.read_table(file_path)
                tables.append(table)

            current_dt += timedelta(days=1)

        if not tables:
            return pa.table({})

        # Combine tables
        combined = pa.concat_tables(tables)

        # Filter by time range
        mask = (
            (combined.column("timestamp_ns").to_pylist() >= start_time_ns) &
            (combined.column("timestamp_ns").to_pylist() <= end_time_ns)
        )

        # Filter by H3 if specified
        if h3_index:
            mask &= (combined.column("h3_index").to_pylist() == h3_index)

        return combined.filter(mask)


if __name__ == "__main__":
    # Test Parquet storage pipeline
    print("Testing Parquet storage pipeline...")

    from datetime import timedelta

    pipeline = ParquetStoragePipeline(
        archive_path=Path("C:/data/vessel_agent/archive"),
        vessel_id="US-AK-FVCATCHER-01",
    )

    # Create test acoustic data
    now_ns = int(datetime.now().timestamp() * 1e9)

    for i in range(10):
        point = AcousticDataPoint(
            timestamp_ns=now_ns + (i * 1_000_000_000),  # 1 second intervals
            latitude=56.3 + (i * 0.001),
            longitude=-134.5 + (i * 0.001),
            h3_index="",
            depth_range=100.0,
            depth_bin=i,
            backscatter_db=-30.0 + (i * 0.5),
            frequency=50000,
        )
        pipeline.write_acoustic(point)

    # Flush to disk
    pipeline.flush()

    # Print stats
    stats = pipeline.get_stats()
    print(f"Storage stats: {stats}")
    print("Pipeline test complete.")
