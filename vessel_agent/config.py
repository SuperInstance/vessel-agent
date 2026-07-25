"""
Vessel Agent Configuration

Configuration for F/V EILEEN data capture system.
Edit this file to match your vessel's hardware setup.
"""

from pathlib import Path
from typing import Dict, Any

# ============================================================================
# VESSEL CONFIGURATION
# ============================================================================

VESSEL: Dict[str, Any] = {
    "id": "US-AK-FVCATCHER-01",
    "name": "EILEEN",
    "home_port": "Southeast Alaska",
    "length_ft": 51,
    "primary_fishery": "Power Trolling",
}

# ============================================================================
# NETWORK CAPTURE CONFIGURATION
# ============================================================================

NETWORK = {
    # Network interface for Furuno sounder capture
    # Use 'ipconfig' (Windows) or 'ifconfig' (Linux/Mac) to find
    "interface": "Ethernet",

    # Furuno FCV-295/585/600 series UDP broadcast
    "furuno_port": 8000,
    "furuno_address": "255.255.255.255",  # UDP broadcast

    # BPF filter for kernel-level packet capture
    # Captures UDP traffic on Furuno port
    "bpf_filter": f"udp port {8000}",

    # Ring buffer size (packets)
    "ring_buffer_size": 10000,

    # Zero-copy parser settings
    "max_packet_size": 2048,
}

# ============================================================================
# NMEA CONFIGURATION
# ============================================================================

NMEA = {
    # Serial port for GPS/NMEA input
    # Use Windows Device Manager or 'ls /dev/tty.*' (Mac) to find
    "port": "COM3",  # Windows: "COM3", Linux: "/dev/ttyUSB0", Mac: "/dev/tty.usbserial"
    "baudrate": 4800,
    "timeout": 1.0,

    # NMEA sentences to parse
    "enabled_sentences": [
        "GPRMC",  # Position, speed, heading
        "GPGGA",  # Position, altitude, satellites
        "GPHDT",  # Heading true
        "GPVTG",  # Velocity made good
        "SDDPT",  # Depth (sounder)
        "SDDBT",  # Depth below transducer
    ],

    # Interpolation settings (15Hz sounder -> 1Hz GPS)
    "interpolation_method": "linear",
    "max_interpolation_age_ms": 2000,  # Max age of GPS for interpolation
}

# ============================================================================
# STORAGE CONFIGURATION
# ============================================================================

STORAGE = {
    # Archive root directory
    "archive_path": Path("C:/data/vessel_agent/archive"),

    # Parquet file settings
    "parquet_compression": "snappy",  # Options: None, "snappy", "gzip", "brotli"
    "row_group_size": 1000000,  # Rows per Parquet row group

    # Hive partitioning scheme
    # Creates: archive_root/year=2026/month=07/day=24/vessel_id=*.parquet
    "partitioning": ["year", "month", "day", "vessel_id"],

    # File rotation
    "max_file_size_mb": 100,
    "rotation_interval_minutes": 60,

    # Retention policy
    "retention_days": 365,  # Keep data for 1 year
}

# ============================================================================
# QUALITY MONITORING CONFIGURATION
# ============================================================================

QUALITY = {
    # Data quality thresholds
    "packet_loss_threshold_percent": 0.1,  # Alert if > 0.1% packet loss
    "capture_rate_threshold_percent": 99.9,  # Alert if < 99.9% capture rate
    "gps_fix_required": True,  # Require valid GPS fix
    "min_satellites": 4,  # Minimum satellites for good fix

    # Alert settings
    "alert_cooldown_seconds": 300,  # Don't spam alerts
    "log_quality_metrics": True,

    # Statistics window
    "stats_window_seconds": 60,
}

# ============================================================================
# TIMEZERO PROFESSIONAL INTEGRATION
# ============================================================================

TIMEZERO = {
    "enabled": True,
    "process_name": "TimeZero.exe",

    # TZ Pro shared memory/communication
    "nmea_output_port": 60001,  # TZ Pro NMEA output
    "nmea_input_port": 60002,   # TZ Pro NMEA input

    # Furuno FCV series integration
    "furuno_sounder_port": 7000,
}

# ============================================================================
# SPATIAL INDEXING (H3)
# ============================================================================

H3 = {
    "resolution": 7,  # H3 resolution (0-15, 7 ≈ 5km hex cells)
    # Resolution guide:
    # 0: 1100km, 1: 418km, 2: 158km, 3: 60km, 4: 23km, 5: 8.6km
    # 6: 3.2km, 7: 1.2km, 8: 445m, 9: 168m, 10: 63m
}

# ============================================================================
# AGENT SYSTEM CONFIGURATION
# ============================================================================

AGENT = {
    "enabled": True,
    "model": "deepseek-chat",  # Or other LLM
    "max_tokens": 4096,
    "temperature": 0.7,
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOGGING = {
    "level": "INFO",  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    "log_path": Path("C:/data/vessel_agent/logs"),
    "max_log_size_mb": 10,
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

# ============================================================================
# DEVELOPMENT/DEBUGGING
# ============================================================================

DEBUG = {
    "mock_mode": False,  # Set True for development without hardware
    "mock_data_rate_hz": 15,  # Mock data rate
    "verbose_packet_logging": False,  # Log every packet (large logs!)
    "profile_performance": False,  # Enable performance profiling
}

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config() -> bool:
    """Validate configuration settings.

    Returns:
        True if configuration is valid, raises ValueError if not.
    """
    errors = []

    # Check archive path exists or can be created
    try:
        STORAGE["archive_path"].mkdir(parents=True, exist_ok=True)
    except Exception as e:
        errors.append(f"Cannot create archive path: {e}")

    # Check logging path
    try:
        LOGGING["log_path"].mkdir(parents=True, exist_ok=True)
    except Exception as e:
        errors.append(f"Cannot create log path: {e}")

    # Validate H3 resolution
    if not 0 <= H3["resolution"] <= 15:
        errors.append(f"H3 resolution must be 0-15, got {H3['resolution']}")

    # Validate NMEA baudrate
    if NMEA["baudrate"] not in [4800, 9600, 19200, 38400]:
        errors.append(f"NMEA baudrate should be 4800/9600/19200/38400, got {NMEA['baudrate']}")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

    return True


# Auto-validate on import
try:
    validate_config()
except Exception as e:
    print(f"Configuration error: {e}")
