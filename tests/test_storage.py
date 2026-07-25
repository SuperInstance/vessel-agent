"""
Tests for Parquet Storage Module

Test suite for Parquet storage pipeline.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from vessel_agent.storage.parquet_pipeline import (
    lat_lon_to_h3,
    AcousticDataPoint,
    GPSDataPoint,
    ParquetStoragePipeline,
)


class TestH3Conversion:
    """Tests for H3 conversion functions."""

    @patch('vessel_agent.storage.parquet_pipeline.H3_AVAILABLE', False)
    def test_lat_lon_to_h3_fallback(self):
        """Test H3 conversion fallback when h3 not available."""
        h3 = lat_lon_to_h3(56.3, -134.5, 7)
        # Should return fallback format
        assert h3 is not None
        assert isinstance(h3, str)


class TestAcousticDataPoint:
    """Tests for AcousticDataPoint dataclass."""

    def test_creation(self):
        """Test creating acoustic data point."""
        point = AcousticDataPoint(
            timestamp_ns=1721741135000000000,
            latitude=56.3,
            longitude=-134.5,
            h3_index="0x8a21104523fffff",
            depth_range=100.0,
            depth_bin=50,
            backscatter_db=-30.0,
            frequency=50000,
            speed_knots=8.0,
            heading=90.0,
        )

        assert point.timestamp_ns == 1721741135000000000
        assert point.latitude == 56.3
        assert point.longitude == -134.5
        assert point.h3_index == "0x8a21104523fffff"
        assert point.depth_range == 100.0
        assert point.backscatter_db == -30.0


class TestGPSDataPoint:
    """Tests for GPSDataPoint dataclass."""

    def test_creation(self):
        """Test creating GPS data point."""
        point = GPSDataPoint(
            timestamp_ns=1721741135000000000,
            latitude=56.3,
            longitude=-134.5,
            h3_index="0x8a21104523fffff",
            altitude=100.0,
            speed_knots=8.0,
            heading_true=90.0,
            satellites=8,
            hdop=1.0,
            fix_quality=1,
        )

        assert point.timestamp_ns == 1721741135000000000
        assert point.latitude == 56.3
        assert point.longitude == -134.5
        assert point.altitude == 100.0
        assert point.satellites == 8


class TestParquetStoragePipeline:
    """Tests for Parquet storage pipeline."""

    @patch('vessel_agent.storage.parquet_pipeline.PYARROW_AVAILABLE', True)
    def test_init(self, tmp_path):
        """Test storage pipeline initialization."""
        pipeline = ParquetStoragePipeline(
            archive_path=tmp_path,
            vessel_id="US-AK-FVCATCHER-01",
        )

        assert pipeline.archive_path == tmp_path
        assert pipeline.vessel_id == "US-AK-FVCATCHER-01"
        assert len(pipeline.acoustic_buffer) == 0
        assert len(pipeline.gps_buffer) == 0

    @patch('vessel_agent.storage.parquet_pipeline.PYARROW_AVAILABLE', True)
    def test_write_acoustic(self, tmp_path):
        """Test writing acoustic data."""
        pipeline = ParquetStoragePipeline(
            archive_path=tmp_path,
            vessel_id="US-AK-FVCATCHER-01",
        )

        point = AcousticDataPoint(
            timestamp_ns=1721741135000000000,
            latitude=56.3,
            longitude=-134.5,
            h3_index="",
            depth_range=100.0,
            depth_bin=50,
            backscatter_db=-30.0,
        )

        pipeline.write_acoustic(point)

        assert len(pipeline.acoustic_buffer) == 1

    @patch('vessel_agent.storage.parquet_pipeline.PYARROW_AVAILABLE', True)
    def test_write_gps(self, tmp_path):
        """Test writing GPS data."""
        pipeline = ParquetStoragePipeline(
            archive_path=tmp_path,
            vessel_id="US-AK-FVCATCHER-01",
        )

        point = GPSDataPoint(
            timestamp_ns=1721741135000000000,
            latitude=56.3,
            longitude=-134.5,
            h3_index="",
            altitude=100.0,
            speed_knots=8.0,
        )

        pipeline.write_gps(point)

        assert len(pipeline.gps_buffer) == 1

    @patch('vessel_agent.storage.parquet_pipeline.PYARROW_AVAILABLE', True)
    def test_h3_auto_fill(self, tmp_path):
        """Test H3 index auto-fill on write."""
        pipeline = ParquetStoragePipeline(
            archive_path=tmp_path,
            vessel_id="US-AK-FVCATCHER-01",
            h3_resolution=7,
        )

        point = AcousticDataPoint(
            timestamp_ns=1721741135000000000,
            latitude=56.3,
            longitude=-134.5,
            h3_index="",  # Empty H3
            depth_range=100.0,
            depth_bin=50,
            backscatter_db=-30.0,
        )

        pipeline.write_acoustic(point)

        # H3 should be auto-filled
        assert pipeline.acoustic_buffer[0].h3_index != ""


class TestParquetStorageIntegration:
    """Integration tests for Parquet storage."""

    @patch('vessel_agent.storage.parquet_pipeline.PYARROW_AVAILABLE', False)
    def test_pyarrow_not_available(self):
        """Test error when pyarrow not available."""
        with pytest.raises(ImportError):
            ParquetStoragePipeline(
                archive_path=Path("C:/data/archive"),
                vessel_id="US-AK-FVCATCHER-01",
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
