# Vessel Agent - Performance Requirements Analysis

**Vessel:** F/V EILEEN (51' Commercial Fishing Vessel)
**Context:** Phase 0 - Data Capture Emergency
**Purpose:** Define precise performance requirements to guide architecture decisions

---

## Critical Performance Requirements

### 1. Network Packet Capture

**Source:** Furuno FCV-585/FCV-600/FCV-295 Sounder
**Rate:** 15 Hz (approximately 15 packets/second)
**Protocol:** UDP broadcast on port 8000
**Packet Size:** ~200-300 bytes per packet

**Requirements:**
| Metric | Requirement | Priority | Rationale |
|--------|-------------|----------|-----------|
| Packet Loss | <0.1% | P0 | Acoustic data non-renewable |
| Capture Latency | <10ms (p99) | P1 | GPS interpolation age |
| Processing Time | <50ms per packet | P1 | Keep up with 15Hz rate |
| Uptime | >99% during operations | P0 | Fishing season limited |

**Analysis:**
- At 15 Hz, we have ~66ms between packets
- Processing budget: 66ms - safety margin = ~50ms
- Current Python implementation: Should be feasible
- Bottleneck risk: Python GIL, memory allocation

---

### 2. NMEA GPS Parsing

**Source:** GPS receiver (BU-353, Furuno GP1871F)
**Rate:** 1 Hz (1 update per second)
**Protocol:** NMEA 0183 over serial/UDP
**Sentences:** GPRMC, GPGGA, GPHDT, GPVTG

**Requirements:**
| Metric | Requirement | Priority | Rationale |
|--------|-------------|----------|-----------|
| Parse Latency | <100ms | P2 | Not time-critical |
| Checksum Validation | 100% | P0 | Data integrity |
| Interpolation Age | <2000ms | P1 | Position accuracy |
| Interpolation Error | <5m at 10 knots | P1 | Acceptable accuracy |

**Analysis:**
- At 1 Hz, NMEA parsing is NOT performance-critical
- Python pynmea2 adequate
- Interpolation more critical than parsing

---

### 3. GPS Interpolation

**Purpose:** Synchronize 15Hz sounder with 1Hz GPS
**Method:** Linear interpolation between GPS fixes

**Requirements:**
| Metric | Requirement | Priority | Rationale |
|--------|-------------|----------|-----------|
| Interpolation Rate | 15 Hz | P0 | Match sounder rate |
| Position Error | <5m at 10 knots | P1 | Species habitat accuracy |
| Calculation Time | <5ms | P2 | Not CPU intensive |
| Memory Overhead | <100MB | P2 | Keep position buffer |

**Analysis:**
- Linear interpolation: O(1) per query
- Buffer size: 10 positions = trivial
- Python performance: Adequate
- Bottleneck: None identified

---

### 4. Parquet Storage

**Write Rate:** ~1.3M points/day (15 Hz × 86400s)
**Data Size:** ~300-500 bytes per point (with anchors)
**Daily Volume:** ~400-650 MB/day uncompressed

**Requirements:**
| Metric | Requirement | Priority | Rationale |
|--------|-------------|----------|-----------|
| Write Latency | <1s (batch) | P2 | Not real-time critical |
| Compression Ratio | >5:1 | P1 | Storage efficiency |
| Query Performance | <1s per day | P1 | User experience |
| File Rotation | Hourly | P2 | Manageable file sizes |

**Analysis:**
- Parquet with Snappy: ~80% compression ratio
- Daily storage: ~80-130 MB/day (compressed)
- Python pyarrow: Performant enough
- Bottleneck: None for vessel-scale data

---

### 5. Data Quality Monitoring

**Metrics Tracked:** Packet loss, capture rate, GPS quality, interpolation confidence
**Update Rate:** 1 Hz (rolling statistics)

**Requirements:**
| Metric | Requirement | Priority | Rationale |
|--------|-------------|----------|-----------|
| Alert Latency | <10s | P2 | Human response time |
| Stats Window | 60s rolling | P2 | Meaningful averages |
| Memory Overhead | <50MB | P3 | Trivial |

**Analysis:**
- Monitoring NOT performance-critical
- Python adequate
- Future: Can be separate service

---

## Performance Ceiling Analysis

### Upper Bounds (Theoretical Limits)

**Network:**
- Gigabit Ethernet: 125 MB/s = ~416,000 packets/s (at 300 bytes)
- Our requirement: 15 packets/s
- **Headroom: 27,000×**

**CPU:**
- Packet processing: ~1-10 ms per packet (Python)
- Our budget: 66 ms per packet
- **Headroom: 6-60×**

**Memory:**
- Ring buffer (10,000 packets): ~3 MB
- Position buffer (10 positions): ~1 KB
- Acoustic buffer (1,000 points): ~300 KB
- **Total: <5 MB working set**

**Storage:**
- Write rate: ~400 MB/day
- Disk speed: 100+ MB/s (SSD)
- **Headroom: 21,600× daily write time**

### Conclusion: Performance NOT the Bottleneck

**Key Finding:** The vessel-agent workload is **NOT performance-constrained** for single-vessel deployment.

**Evidence:**
- 15 Hz packet rate is trivial for modern hardware
- Python overhead negligible at this scale
- Storage requirements modest (<100 GB/year)
- Memory footprint tiny (<100 MB)

**Implication:** Language choice should prioritize **developer experience, deployment simplicity, and ecosystem maturity** over raw performance.

---

## Scalability Analysis

### Current Scale: Single Vessel

| Metric | Value | Assessment |
|--------|-------|------------|
| Vessels | 1 | Trivial |
| Packet Rate | 15 Hz | Trivial |
| Daily Storage | ~100 MB | Trivial |
| CPU Utilization | <5% | Massive headroom |
| Memory Usage | <100 MB | Massive headroom |

**Verdict:** Python fully adequate.

---

### Future Scale: Fleet (10 vessels)

| Metric | Value | Assessment |
|--------|-------|------------|
| Vessels | 10 | Manageable |
| Packet Rate | 150 Hz | Still trivial |
| Daily Storage | ~1 GB | Still trivial |
| CPU Utilization | <10% | Massive headroom |
| Memory Usage | <500 MB | Massive headroom |

**Verdict:** Python still adequate. Single server can handle.

---

### Future Scale: Regional (100 vessels)

| Metric | Value | Assessment |
|--------|-------|------------|
| Vessels | 100 | Requiring scaling |
| Packet Rate | 1500 Hz | Approaching limits |
| Daily Storage | ~10 GB | Need compression |
| CPU Utilization | ~50% | Adequate |
| Memory Usage | <5 GB | Adequate |

**Verdict:** Python may need optimization:
- Cython for critical paths
- Separate processes per vessel
- Distributed storage

---

### Future Scale: National (1000+ vessels)

| Metric | Value | Assessment |
|--------|-------|------------|
| Vessels | 1000+ | Distributed system |
| Packet Rate | 15,000 Hz | Beyond single machine |
| Daily Storage | ~100 GB | Need distributed storage |
| CPU Utilization | >100% | Need distributed processing |
| Memory Usage | >50 GB | Need distributed memory |

**Verdict:** Need fundamental redesign:
- Rust for critical paths
- Distributed architecture
- Separate capture, processing, storage

---

## Recommendations

### For Current Phase (Single Vessel)

**Recommendation:** Stay with Python

**Rationale:**
- Performance requirements trivial at current scale
- Developer experience superior
- Ecosystem mature (pyarrow, pynmea2, pytest)
- Deployment simple (pip, venv)

**Optimization Priority:** Low
- Focus on correctness, not performance
- Measure before optimizing
- Profile to find actual bottlenecks

---

### For Near Future (10 vessels)

**Recommendation:** Python with monitoring

**Rationale:**
- Still within Python capabilities
- Add performance monitoring
- Identify scaling bottlenecks
- Plan migration path if needed

**Preparation:**
- Modular architecture for easy extraction
- Document performance budgets
- Benchmark current implementation

---

### For Long Term (100+ vessels)

**Recommendation:** Hybrid architecture

**Components:**
- **Rust:** Critical capture path (packet capture ring buffer)
- **Python:** Orchestration and business logic
- **Go:** Distributed services (if needed)
- **Julia:** Scientific computing (acoustic analysis)

**Migration Strategy:**
1. Profile Python implementation
2. Identify hotspots
3. Extract critical paths to Rust (PyO3)
4. Benchmark hybrid vs pure Python
5. Migrate incrementally

---

## Performance Testing Plan

### Baseline Measurement

**Tests:**
1. Packet capture rate (sustained 15 Hz for 1 hour)
2. Packet loss percentage (<0.1%)
3. NMEA parsing latency (<100ms p99)
4. Interpolation accuracy (<5m error)
5. Parquet write throughput (<1s per batch)

**Tools:**
- pytest-benchmark for microbenchmarks
- pytest for integration tests
- custom load generators

### Stress Testing

**Tests:**
1. Sustained 150 Hz (10× load)
2. Memory allocation profiling
3. CPU utilization profiling
4. Disk I/O profiling
5. Concurrent operation with other processes

**Tools:**
- memory_profiler
- cProfile
- iostat
- perf (Linux)

### Regression Testing

**Tests:**
1. Benchmark suite run on every commit
2. Performance degradation alerts
3. Compare vs baseline

**Tools:**
- pytest-benchmark
- continuous integration
- performance trend monitoring

---

## Conclusion

**Primary Finding:** The vessel-agent system is **NOT performance-constrained** at current scale (single vessel).

**Implication:** Language choice should prioritize:

1. **Developer Experience** (Python wins)
2. **Deployment Simplicity** (Python wins)
3. **Ecosystem Maturity** (Python wins)
4. **Correctness** (all adequate)

**Future-Proofing:**
- Design modular architecture for easy extraction
- Document performance budgets
- Monitor actual usage
- Migrate hotspots to Rust when needed

**Recommendation:** Continue with Python for Phase 0. Re-evaluate when approaching 10+ vessels or identified bottlenecks.

---

*Document Version: 1.0.0*
*Created: 2026-07-24*
*Author: Performance Analysis Team*
*Status: Requirements Defined*
