# Vessel Agent System - Implementation Guide

**Vessel:** F/V EILEEN (51' Commercial Fishing Vessel)
**Home Port:** Southeast Alaska
**Methodology:** BMAD (Bottom-up, Multi-level, Agile Development)

---

## Quick Start - 30 Minutes to Running System

### Prerequisites

- Python 3.10 or higher
- Windows (primary) or Linux
- Administrator access (for network capture)

### Step 1: Install Dependencies (5 minutes)

```bash
# Clone repository
git clone https://github.com/SuperInstance/vessel-agent.git
cd vessel-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure System (2 minutes)

Edit `vessel_agent/config.py` to match your vessel:

```python
VESSEL = {
    "id": "US-AK-FVCATCHER-01",  # Your vessel ID
    "name": "EILEEN",             # Vessel name
    "home_port": "Southeast Alaska",
}

NETWORK = {
    "interface": "Ethernet",  # Check with ipconfig/ifconfig
    "furuno_port": 8000,      # Furuno default UDP port
}

STORAGE = {
    "archive_path": Path("C:/data/vessel_agent/archive"),
}
```

### Step 3: Validate Configuration (1 minute)

```bash
python capture_daemon.py doctor
```

Expected output:
```
Validating configuration...
  ✓ Configuration valid
  ✓ Archive path: C:\data\vessel_agent\archive
  ✓ Log path: C:\data\vessel_agent\logs

✅ All validation checks passed
```

### Step 4: Test Capture (3 minutes)

```bash
# Test with mock data (no hardware required)
python capture_daemon.py once --mock
```

Expected output:
```
Testing network capture (mock mode)...
Starting capture...
Capture Rate: 15.0 Hz
Storage stats: {'acoustic_points_written': 1000, ...}
Capture stopped.
```

### Step 5: Run Live Capture (ongoing)

```bash
# Start live capture (requires Furuno sounder + GPS)
python capture_daemon.py run
```

---

## Architecture

### Module Structure

```
vessel-agent/
├── vessel_agent/
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Vessel configuration
│   ├── capture/                 # Network capture & NMEA
│   │   ├── __init__.py
│   │   ├── network_capture.py   # UDP packet capture
│   │   └── nmea_interpolator.py # GPS interpolation
│   ├── storage/                 # Parquet storage
│   │   ├── __init__.py
│   │   └── parquet_pipeline.py  # Parquet writing
│   └── monitoring/              # Data quality
│       ├── __init__.py
│       └── data_quality.py     # Quality monitoring
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_network_capture.py
│   ├── test_nmea_interpolator.py
│   ├── test_storage.py
│   └── test_quality_monitoring.py
├── capture_daemon.py            # Main entry point
├── requirements.txt             # Runtime dependencies
└── requirements-dev.txt          # Development dependencies
```

### Data Flow

```
PHYSICAL LAYER
  Furuno Sounder → UDP Packets → Network Card
  GPS/NMEA → Serial/UDP → NMEA Parser
        ↓
CAPTURE LAYER
  BPF Filter → Ring Buffer → Zero-Copy Parser
        ↓
INTERPOLATION LAYER
  GPS Interpolator → Position for each packet
        ↓
STORAGE LAYER
  Parquet Writer → Hive Partitioning → Disk
        ↓
QUALITY LAYER
  Data Quality Monitor → Alerts
```

---

## Core Components

### 1. Network Capture (`network_capture.py`)

Captures UDP packets from Furuno sounder at 15Hz.

```python
from vessel_agent.capture.network_capture import create_capture

# Create capture instance
capture = create_capture(interface="Ethernet", port=8000, mock=False)

# Start capture
capture.start()

# Get packets
packet = capture.get_packet(timeout=1.0)
if packet:
    print(f"Depth values: {len(packet.depth_values)} bins")

# Stop capture
capture.stop()
```

**Key Features:**
- Ring buffer for lossless capture
- BPF filters for kernel-level packet interception
- Zero-copy packet processing
- Mock mode for development

### 2. NMEA Interpolation (`nmea_interpolator.py`)

Interpolates GPS positions between 1Hz updates and 15Hz sounder data.

```python
from vessel_agent.capture.nmea_interpolator import (
    NMEAInterpolator,
    parse_rmc,
    GPSPosition,
)

# Create interpolator
interpolator = NMEAInterpolator(max_age_ms=2000)

# Add GPS positions
gps = parse_rmc("$GPRMC,210230,A,3855.4487,N,09446.0071,W,...")
interpolator.add_gps_position(gps)

# Get position for sounder timestamp
sounder_time_ns = 1721741135000000000
position = interpolator.get_position(sounder_time_ns)

print(f"Interpolated: {position.latitude}, {position.longitude}")
print(f"Confidence: {position.confidence}")
```

**Key Features:**
- Linear interpolation between GPS fixes
- Extrapolation for edge cases
- Confidence scoring
- Wraparound handling for headings

### 3. Parquet Storage (`parquet_pipeline.py`)

Columnar storage with Hive partitioning and H3 spatial indexing.

```python
from vessel_agent.storage.parquet_pipeline import (
    ParquetStoragePipeline,
    AcousticDataPoint,
)

# Create storage pipeline
pipeline = ParquetStoragePipeline(
    archive_path=Path("C:/data/archive"),
    vessel_id="US-AK-FVCATCHER-01",
)

# Write data
point = AcousticDataPoint(
    timestamp_ns=1721741135000000000,
    latitude=56.3,
    longitude=-134.5,
    h3_index="0x8a21104523fffff",
    depth_range=100.0,
    depth_bin=50,
    backscatter_db=-30.0,
)
pipeline.write_acoustic(point)

# Flush to disk
pipeline.flush()
```

**Key Features:**
- Apache Arrow + Parquet
- Hive partitioning (year/month/day/vessel_id)
- H3 spatial indexing
- Snappy compression

### 4. Quality Monitoring (`data_quality.py`)

Monitors data quality and generates alerts.

```python
from vessel_agent.monitoring.data_quality import (
    DataQualityMonitor,
    CaptureQualityTracker,
)

# Create monitor
monitor = DataQualityMonitor()

# Set thresholds
monitor.set_threshold("packet_loss_rate", 0.1, AlertLevel.ERROR)
monitor.set_threshold("capture_rate_hz", 14.0, AlertLevel.WARNING, "below")

# Update metrics
monitor.update_metric("packet_loss_rate", 0.05)
monitor.update_metric("capture_rate_hz", 15.0)

# Check alerts
alerts = monitor.get_alerts()
for alert in alerts:
    print(f"[{alert.level.value}] {alert.message}")
```

**Key Features:**
- Configurable thresholds
- Alert cooldown
- Health scoring
- Rolling statistics

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Module

```bash
pytest tests/test_network_capture.py -v
pytest tests/test_nmea_interpolator.py -v
pytest tests/test_storage.py -v
pytest tests/test_quality_monitoring.py -v
```

### Run with Coverage

```bash
pytest --cov=vessel_agent tests/
```

---

## Configuration

### Vessel Configuration

Edit `vessel_agent/config.py`:

```python
VESSEL = {
    "id": "US-AK-FVCATCHER-01",
    "name": "EILEEN",
    "home_port": "Southeast Alaska",
    "length_ft": 51,
    "primary_fishery": "Power Trolling",
}
```

### Network Configuration

```python
NETWORK = {
    "interface": "Ethernet",        # Network interface
    "furuno_port": 8000,           # Furuno UDP port
    "bpf_filter": "udp port 8000", # BPF filter
    "ring_buffer_size": 10000,     # Ring buffer size
}
```

### NMEA Configuration

```python
NMEA = {
    "port": "COM3",              # Serial port
    "baudrate": 4800,            # Baud rate
    "interpolation_method": "linear",
    "max_interpolation_age_ms": 2000,
}
```

### Storage Configuration

```python
STORAGE = {
    "archive_path": Path("C:/data/vessel_agent/archive"),
    "parquet_compression": "snappy",
    "row_group_size": 1000000,
    "partitioning": ["year", "month", "day", "vessel_id"],
    "retention_days": 365,
}
```

---

## Troubleshooting

### "No module named 'pyarrow'"

```bash
pip install pyarrow
```

### "Permission denied" on network interface

Run as Administrator:
```bash
# Windows
# Right-click Command Prompt → Run as Administrator

# Linux
sudo python capture_daemon.py run
```

### "Cannot create archive path"

Create directory manually:
```bash
mkdir -p C:/data/vessel_agent/archive
mkdir -p C:/data/vessel_agent/logs
```

### Low capture rate

Check network interface:
```bash
# Windows
ipconfig

# Linux
ifconfig
```

Update `config.py` with correct interface name.

---

## Performance Tuning

### Capture Rate

If losing packets at 15Hz:
- Increase ring buffer: `ring_buffer_size`: 20000
- Use dedicated network interface
- Disable Wi-Fi if using Ethernet

### Storage Performance

If storage lagging:
- Increase row group size: `row_group_size`: 2000000
- Use faster disk (SSD)
- Reduce compression: `parquet_compression`: None

### Interpolation Age

If interpolation failing:
- Increase max age: `max_interpolation_age_ms`: 5000
- Check GPS update rate (should be 1Hz)
- Validate NMEA sentences

---

## BMAD Development

### Level 0 (Current) - Raw Bits

**Focus:** Lossless packet capture, NMEA parsing, Parquet storage

**Success Criteria:**
- Capture rate: >99.9%
- Packet loss: <0.1%
- Query performance: <1s for any day

### Level 1 - Physical Tensors

**Next:** Normalization, calibration, H3 indexing

**Success Criteria:**
- Position error: <5m at 10 knots
- Depth precision: <0.5m
- Sv calibration: <1dB variance

### Level 2 - Analytical Features

**Future:** Feature extraction, classification, pattern mining

**Success Criteria:**
- Species accuracy: >70% for 3 species
- Biomass precision: >80%
- Bottom classification: >85%

---

## Contributing

### Adding New Features

1. Update schema in `vessel_agent_memory_schema.json`
2. Implement in appropriate module
3. Add tests in `tests/`
4. Update documentation

### Testing Standards

- All new code must have tests
- Test coverage >80%
- All tests must pass before commit

### Code Style

- Use Black formatter: `black vessel_agent/`
- Follow PEP 8 guidelines
- Add docstrings to all functions

---

## License

MIT License - See LICENSE file

---

## Contact

**Vessel:** F/V EILEEN
**Captain:** Casey
**Location:** Southeast Alaska
**Repository:** https://github.com/SuperInstance/vessel-agent

---

*Implementation Guide v1.0.0*
*Last Updated: 2026-07-24*
*Status: Phase 0 - Data Capture Emergency*
