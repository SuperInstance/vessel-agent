#!/usr/bin/env python3
"""
Vessel Agent - Capture Daemon

Main daemon entry point for vessel data capture.
Orchestrates network capture, NMEA interpolation, and Parquet storage.

Usage:
    python capture_daemon.py run      # Start capture daemon
    python capture_daemon.py status   # Show system status
    python capture_daemon.py doctor   # Validate configuration
    python capture_daemon.py once     # Single capture cycle
    python capture_daemon.py stop     # Stop capture daemon
"""

import argparse
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from vessel_agent import config
from vessel_agent.capture.network_capture import create_capture
from vessel_agent.capture.nmea_interpolator import (
    NMEAInterpolator,
    parse_rmc,
    parse_gga,
)
from vessel_agent.storage.parquet_pipeline import (
    ParquetStoragePipeline,
    AcousticDataPoint,
)
from vessel_agent.monitoring.data_quality import (
    DataQualityMonitor,
    CaptureQualityTracker,
    GPSQualityTracker,
)


class CaptureDaemon:
    """Main capture daemon orchestrating all data collection."""

    def __init__(self, mock: bool = False):
        """Initialize capture daemon.

        Args:
            mock: Use mock capture for development
        """
        self.mock = mock
        self.running = False

        # Initialize components
        print("Initializing vessel agent capture daemon...")

        # Network capture
        print(f"  - Network capture: {'MOCK' if mock else 'LIVE'}")
        self.capture = create_capture(
            interface=config.NETWORK["interface"],
            port=config.NETWORK["furuno_port"],
            mock=mock,
        )

        # NMEA interpolator
        print("  - NMEA interpolator")
        self.interpolator = NMEAInterpolator(
            max_age_ms=config.NMEA["interpolation_method"],
        )

        # Parquet storage
        print("  - Parquet storage pipeline")
        self.storage = ParquetStoragePipeline(
            archive_path=config.STORAGE["archive_path"],
            vessel_id=config.VESSEL["id"],
            h3_resolution=config.H3["resolution"],
        )

        # Quality monitoring
        print("  - Data quality monitor")
        self.quality_monitor = DataQualityMonitor(
            stats_window_seconds=config.QUALITY["stats_window_seconds"],
        )

        # Quality trackers
        self.capture_tracker = CaptureQualityTracker(self.quality_monitor)
        self.gps_tracker = GPSQualityTracker(self.quality_monitor)

        # Statistics
        self.start_time = None
        self.stats = {
            "cycles": 0,
            "packets_processed": 0,
            "storage_flushes": 0,
        }

        print("Initialization complete.\n")

    def start(self) -> None:
        """Start capture daemon."""
        if self.running:
            print("Daemon already running")
            return

        print("Starting capture daemon...")
        self.running = True
        self.start_time = time.time()
        self.capture.start()

        print(f"Daemon started at {datetime.now().isoformat()}")
        print("Capturing... (Ctrl+C to stop)")

    def stop(self) -> None:
        """Stop capture daemon."""
        if not self.running:
            return

        print("\nStopping capture daemon...")
        self.running = False
        self.capture.stop()
        self.storage.flush()

        uptime = time.time() - self.start_time if self.start_time else 0

        print(f"Daemon stopped at {datetime.now().isoformat()}")
        print(f"Uptime: {uptime:.1f} seconds")
        print(f"  Cycles: {self.stats['cycles']}")
        print(f"  Packets processed: {self.stats['packets_processed']}")
        print(f"  Storage flushes: {self.stats['storage_flushes']}")

    def run_cycle(self) -> bool:
        """Run a single capture cycle.

        Returns:
            True if cycle completed successfully
        """
        self.stats["cycles"] += 1

        # Get next packet
        packet = self.capture.get_packet(timeout=1.0)

        if packet is None:
            return False

        self.stats["packets_processed"] += 1

        # Interpolate position for packet timestamp
        position = self.interpolator.get_position(packet.metadata.timestamp_ns)

        if position is None:
            # No GPS position available yet
            return True

        # Create acoustic data point
        if packet.depth_values:
            for i, depth_value in enumerate(packet.depth_values):
                point = AcousticDataPoint(
                    timestamp_ns=packet.metadata.timestamp_ns + (i * 1_000_000),  # 1ms per bin
                    latitude=position.latitude,
                    longitude=position.longitude,
                    h3_index="",  # Will be set by storage pipeline
                    depth_range=packet.depth_range or 100.0,
                    depth_bin=i,
                    backscatter_db=float(depth_value) / 10.0,  # Convert to dB
                    frequency=packet.frequency or 50000,
                    speed_knots=position.speed_knots,
                    heading=position.heading_true,
                    data_quality=position.confidence,
                    interpolation_method=position.method,
                )

                self.storage.write_acoustic(point)

        # Periodic flush (every 100 cycles)
        if self.stats["cycles"] % 100 == 0:
            self.storage.flush()
            self.stats["storage_flushes"] += 1

            # Update capture quality stats
            capture_stats = self.capture.get_stats()
            self.capture_tracker.update_capture_stats(
                packets_captured=capture_stats["packets_captured"],
                packets_dropped=capture_stats.get("buffer_stats", {}).get("dropped_packets", 0),
                capture_rate_hz=capture_stats["capture_rate_hz"],
            )

            # Print status
            if self.stats["cycles"] % 1000 == 0:
                self.print_status()

        return True

    def run(self) -> None:
        """Run capture daemon continuously."""
        self.start()

        try:
            while self.running:
                self.run_cycle()

        except KeyboardInterrupt:
            print("\nReceived interrupt signal")
        finally:
            self.stop()

    def print_status(self) -> None:
        """Print current status."""
        uptime = time.time() - self.start_time if self.start_time else 0

        print(f"\n{'='*60}")
        print(f"Uptime: {uptime:.1f}s | Cycles: {self.stats['cycles']} | "
              f"Packets: {self.stats['packets_processed']}")
        print(f"{'='*60}")

        # Capture stats
        capture_stats = self.capture.get_stats()
        print(f"Capture Rate: {capture_stats['capture_rate_hz']:.1f} Hz")
        print(f"Data Rate: {capture_stats['data_rate_mbps']:.2f} Mbps")

        # Storage stats
        storage_stats = self.storage.get_stats()
        print(f"Acoustic Points: {storage_stats['acoustic_points_written']:,}")
        print(f"Files Created: {storage_stats['files_created']}")

        # Quality stats
        health = self.quality_monitor.get_health_score()
        print(f"Health Score: {health:.2%}")

        # Recent alerts
        alerts = self.quality_monitor.get_alerts()
        if alerts:
            print(f"\nRecent Alerts: {len(alerts)}")
            for alert in alerts[-3:]:
                print(f"  [{alert.level.value.upper()}] {alert.message}")

        print(f"{'='*60}\n")

    def validate_configuration(self) -> bool:
        """Validate system configuration.

        Returns:
            True if configuration is valid
        """
        print("Validating configuration...")

        errors = []

        # Check config
        try:
            config.validate_config()
            print("  ✓ Configuration valid")
        except Exception as e:
            errors.append(f"Configuration error: {e}")

        # Check archive path
        if not config.STORAGE["archive_path"].exists():
            try:
                config.STORAGE["archive_path"].mkdir(parents=True, exist_ok=True)
                print(f"  ✓ Archive path: {config.STORAGE['archive_path']}")
            except Exception as e:
                errors.append(f"Cannot create archive path: {e}")
        else:
            print(f"  ✓ Archive path: {config.STORAGE['archive_path']}")

        # Check log path
        if not config.LOGGING["log_path"].exists():
            try:
                config.LOGGING["log_path"].mkdir(parents=True, exist_ok=True)
                print(f"  ✓ Log path: {config.LOGGING['log_path']}")
            except Exception as e:
                errors.append(f"Cannot create log path: {e}")

        if errors:
            print("\n❌ Validation failed:")
            for error in errors:
                print(f"  - {error}")
            return False

        print("\n✅ All validation checks passed")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Vessel Agent Capture Daemon - F/V EILEEN"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    parser_run = subparsers.add_parser("run", help="Start capture daemon")
    parser_run.add_argument(
        "--mock", action="store_true", help="Use mock capture for development"
    )

    # Once command
    parser_once = subparsers.add_parser("once", help="Run single capture cycle")
    parser_once.add_argument(
        "--mock", action="store_true", help="Use mock capture for development"
    )

    # Status command
    subparsers.add_parser("status", help="Show system status")

    # Doctor command
    subparsers.add_parser("doctor", help="Validate configuration")

    # Stop command
    subparsers.add_parser("stop", help="Stop capture daemon")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Create daemon
    mock = getattr(args, "mock", False)
    daemon = CaptureDaemon(mock=mock)

    # Execute command
    if args.command == "run":
        daemon.run()

    elif args.command == "once":
        daemon.start()
        for _ in range(10):  # Run 10 cycles
            daemon.run_cycle()
        daemon.stop()
        daemon.print_status()

    elif args.command == "doctor":
        valid = daemon.validate_configuration()
        sys.exit(0 if valid else 1)

    elif args.command == "status":
        print("Status: Not implemented (use systemd/process manager)")

    elif args.command == "stop":
        print("Stop: Not implemented (use systemd/process manager)")


if __name__ == "__main__":
    main()
