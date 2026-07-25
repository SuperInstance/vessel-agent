# Vessel Agent System - Student Guide

**For Clever High School Students Interested in How It Works**

---

## Hey There, Future Engineer!

So you're curious about how this vessel-agent system works? Maybe you're thinking about:
- Marine biology
- Computer science
- Engineering
- Oceanography
- Or you just like knowing how things work

You're in the right place. This guide explains the system in a way that doesn't assume you're an expert, but also doesn't treat you like a beginner.

---

## The Big Picture: What Are We Doing?

### The Problem

Imagine you're a marine biologist studying fish in the ocean. You have some questions:

1. **Where do the fish hang out?**
2. **How do their locations change over time?**
3. **What environmental factors affect them?**
4. **Can we predict where they'll be tomorrow?**

To answer these, you need data. **Lots of data.**

### The Solution

This system is like a **time machine for ocean data**:

- **Records everything** the fish finder sees
- **Records where** the boat is (GPS)
- **Records when** this happened (timestamp)
- **Links it all together** so you can ask questions later

**Then it helps you find patterns** that humans would miss.

---

## How It Works: The Architecture

### The Three-Layer System

```
┌─────────────────────────────────────────────────────────────┐
│                     LAYER 1: CAPTURE                         │
│                                                               │
│    Fish Finder → Network Packets → Ring Buffer              │
│                                                               │
│    "Listen to everything, save it all"                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     LAYER 2: PROCESS                         │
│                                                               │
│    GPS Interpolation → Spatial Index → Metadata             │
│                                                               │
│    "Make sense of the raw data"                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     LAYER 3: ANALYZE                         │
│                                                               │
│    Queries → Visualizations → Patterns → Predictions        │
│                                                               │
│    "Answer questions from the data"                        │
└─────────────────────────────────────────────────────────────┘
```

### Real-World Analogy

Think of it like a **library system**:

**Layer 1 (Capture) = Getting Books**
- You collect books (data packets)
- Organize them on shelves (storage)
- Make sure nothing gets lost (redundancy)

**Layer 2 (Process) = Cataloging**
- Create card catalog (indexing)
- Organize by topic (spatial grouping)
- Cross-reference books (linking data)

**Layer 3 (Analyze) = Research**
- Look up specific topics (queries)
- Find connections between books (patterns)
- Write new insights (predictions)

---

## The Technology: Behind the Scenes

### What Programming Language? Why?

**We chose Python** for the backend. Here's why:

**Pros:**
- ✅ Easy to read and write (looks like English)
- ✅ Huge ecosystem of libraries
- ✅ Great for data science (NumPy, Pandas)
- ✅ Fast enough for what we need

**Cons:**
- ❌ Not the fastest (but we don't need fastest)
- ❌ Global Interpreter Lock (GIL) limits parallelism

**Real Talk:** At 15 packets per second, Python is **plenty fast**. We'd need 15,000 packets/second to hit Python's limits.

### What About TypeScript?

**We use TypeScript** for the user interface. Here's why:

**Pros:**
- ✅ Type safety (catches bugs before running)
- ✅ Great for interactive UIs
- ✅ Real-time updates (WebSocket)
- ✅ Works in browsers AND desktop (Electron)

**Cons:**
- ❌ Single-threaded (Node.js)
- ❌ Not great for heavy number-crunching

**Perfect division:** Python for heavy lifting, TypeScript for pretty pictures.

---

## Key Concepts: The Building Blocks

### 1. Network Packet Capture

**What:** Listening to data flowing through network cables

**How:**
```python
# Open a "socket" (like a phone connection)
socket.bind(("0.0.0.0", 8000))  # Listen on port 8000

# Wait for data
data, addr = socket.recvfrom(2048)  # Get up to 2048 bytes

# Save it
ring_buffer.write(data)
```

**Why:** Your fish finder sends data over the network. We need to catch it.

**Cool Fact:** At 15 Hz (15 times per second), we get 66 milliseconds between packets. That's **forever** in computer time.

### 2. Ring Buffers

**What:** A circular queue that never grows

**How:**
```python
class RingBuffer:
    def __init__(self, size):
        self.buffer = [None] * size  # Pre-allocate
        self.write_idx = 0
        self.read_idx = 0

    def write(self, item):
        self.buffer[self.write_idx % size] = item
        self.write_idx += 1

    def read(self):
        item = self.buffer[self.read_idx % size]
        self.read_idx += 1
        return item
```

**Why:** Pre-allocated memory = no garbage collection = consistent performance.

**Cool Fact:** When write_idx catches up to read_idx, old data gets overwritten (hence "ring").

### 3. GPS Interpolation

**The Problem:**
- GPS updates 1 time per second (1 Hz)
- Fish finder updates 15 times per second (15 Hz)
- **Mismatch!**

**The Solution:**
```python
# We have GPS positions at t=0 and t=1
# Need position at t=0.5, t=0.67, t=0.73, etc.

# Linear interpolation
position = (
    gps_t0 * (1 - fraction) +
    gps_t1 * fraction
)
```

**Why:** Sounder data needs accurate position for each ping.

**Cool Fact:** At 10 knots, your boat moves 0.17 feet in 66 milliseconds. Good enough!

### 4. Spatial Indexing (H3)

**What:** Divide Earth into hexagonal cells

**Why:** Fast spatial queries

**How:**
```python
import h3

lat, lon = 56.3, -134.5
resolution = 7  # Different sizes (0-15)

h3_index = h3.latlng_to_cell(lat, lon, resolution)
# Returns: 0x8a21104523fffff (hexagonal cell ID)
```

**Cool Fact:** Each resolution 7 hex cell is about 1.2 km across. Perfect for fishing spots!

### 5. Time/Location/Source Anchoring

**The Golden Rule:** Every data point must have three anchors:

```python
data_point = {
    "timestamp_ns": 1721741135000000000,  # WHEN (nanoseconds)
    "latitude": 56.3,                       # WHERE (GPS)
    "longitude": -134.5,
    "h3_index": "0x8a21104523fffff",        # WHERE (hex cell)
    "vessel_id": "US-AK-FVCATCHER-01",      # WHO (source)
    "device_id": "FURUNO-FCV585",           # WHAT (instrument)
}
```

**Why:** Without all three, data is useless.

---

## The Code: How It's Organized

### Project Structure

```
vessel-agent/
├── vessel_agent/          # Main package
│   ├── capture/            # Network capture & NMEA
│   │   ├── network_capture.py
│   │   └── nmea_interpolator.py
│   ├── storage/            # Parquet storage
│   │   └── parquet_pipeline.py
│   └── monitoring/         # Data quality
│       └── data_quality.py
├── tests/                  # Test suite
├── capture_daemon.py       # Main entry point
└── requirements.txt        # Dependencies
```

### Key Files Explained

**network_capture.py (410 lines)**
- Captures UDP packets from fish finder
- Uses ring buffer for zero-loss
- Parses Furuno protocol

**nmea_interpolator.py (669 lines)**
- Parses NMEA sentences from GPS
- Interpolates positions between updates
- Calculates headings, speeds

**parquet_pipeline.py (486 lines)**
- Writes data to Parquet files (columnar storage)
- Organizes by date (Hive partitioning)
- Adds H3 spatial index

**capture_daemon.py (345 lines)**
- Main program that coordinates everything
- Runs in background
- Handles start/stop

---

## The Math: It's Not That Scary

### Linear Interpolation

**Given:** Two GPS positions 1 second apart
**Need:** Position 0.5 seconds between them

```python
# Simple weighted average
def interpolate(pos1, pos2, fraction):
    return pos1 * (1 - fraction) + pos2 * fraction

# Example:
# At t=0: (56.300, -134.500)
# At t=1: (56.301, -134.400)
# At t=0.5: (56.3005, -134.450)  # Midpoint
```

### Geographic Distance

**How far apart are two points?**

```python
import math

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates."""
    R = 6371  # Earth's radius in km

    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c  # Distance in km
```

### Backscatter (Sv) Calculation

**Converting raw sounder data to meaningful values:**

```python
def raw_to_sv(raw_value, gain, range):
    """
    Convert raw ADC value to volume scattering strength (Sv).

    Sv = 20 * log10(power) - calibration
    """
    voltage = raw_value / 65535  # 16-bit ADC
    power = voltage ** 2
    sv = 20 * math.log10(power) + gain - range
    return sv
```

**What it means:** Higher Sv = more stuff in water (fish, plankton, etc.)

---

## The Data: What We Actually Record

### Acoustic Data Point

```python
{
    "timestamp_ns": 1721741135000000000,     # Exact time
    "latitude": 56.300,                       # Exact position
    "longitude": -134.500,
    "h3_index": "0x8a21104523fffff",        # Hex cell
    "depth_range": 100.0,                     # Depth range (m)
    "depth_bin": 50,                          # Which depth bin
    "backscatter_db": -30.0,                 # Signal strength
    "frequency": 50000,                      # 50 kHz
    "vessel_id": "US-AK-FVCATCHER-01",       # Your boat
    "data_quality": 1.0                      # Confidence (0-1)
}
```

### GPS Data Point

```python
{
    "timestamp_ns": 1721741135000000000,
    "latitude": 56.300,
    "longitude": -134.500,
    "altitude": 100.0,                       # Above sea level
    "speed_knots": 8.0,                      # Boat speed
    "heading_true": 90.0,                    # Direction
    "satellites": 8,                         # GPS quality
    "fix_quality": 1                         # 1=GPS, 2=DGPS
}
```

---

## Performance: How Fast Is Fast Enough?

### The 15 Hz Challenge

**Requirement:** Process 15 packets per second

**Reality:**
- Time between packets: 66.67 ms
- Python processing time: 5-10 ms
- **Headroom:** 6-13× what we need

### Performance Budget

```
Total Budget: 66.67 ms (between packets)
├── Socket receive: 1-2 ms
├── Packet parsing: 0.5-1 ms
├── GPS interpolation: 0.1-0.5 ms
├── Metadata add: 0.1-0.5 ms
├── Buffer write: 0.1-0.5 ms
└── Total used: 2-5 ms

Remaining: 61+ ms (plenty of headroom)
```

**Conclusion:** We could handle 100× more packets before breaking a sweat.

---

## Challenges: Things We Had to Solve

### Challenge 1: Packet Loss

**Problem:** Network packets can get dropped

**Solution:** Ring buffer with overflow detection

```python
if not ring_buffer.write(packet):
    packet_drops += 1
    if packet_drops > threshold:
        alert("Packet loss too high!")
```

### Challenge 2: GPS Interpolation Age

**Problem:** GPS data gets old as we interpolate

**Solution:** Track interpolation age, reject if too old

```python
age_ms = (current_time - gps_time) * 1000
if age_ms > 2000:  # 2 seconds
    position = None  # Too old, don't use
```

### Challenge 3: Data Quality

**Problem:** How do we know data is good?

**Solution:** Quality monitoring with alerts

```python
class DataQualityMonitor:
    def check_packet_loss(self, rate):
        if rate > 0.1:  # More than 0.1%
            alert("Packet loss high!")

    def check_gps_quality(self, n_sats):
        if n_sats < 4:
            alert("Poor GPS fix!")
```

---

## The Future: Where This Could Go

### Level 1 (Current): Raw Data Recording

**What we do now:**
- Record everything
- Save to disk
- Query later

### Level 2 (Next): Feature Extraction

**What's next:**
- Identify fish marks automatically
- Classify bottom type
- Detect thermoclines
- Calculate biomass estimates

### Level 3 (Future): Prediction

**What's coming:**
- Predict where fish will be
- Recommend fishing spots
- Suggest optimal timing
- Estimate catch rates

---

## Hands-On: Try It Yourself

### Experiment 1: Parse NMEA Sentence

NMEA sentences look like this:
```
$GPRMC,210230,A,3855.4487,N,09446.0071,W,0.0,076.2,210324,,,A*47
```

**Breakdown:**
- `GPRMC`: Recommended Minimum sentence
- `210230`: Time (21:02:30 UTC)
- `A`: Status (A=Valid, V=Invalid)
- `3855.4487,N`: Latitude 38°55.4487' N
- `09446.0071,W`: Longitude 094°46.0071' W
- `0.0`: Speed over ground (knots)
- `076.2`: Track made good (degrees)
- `210324`: Date (21 March 2024)
- `*47`: Checksum

**Your Turn:** Write a parser!

```python
def parse_rmc(sentence):
    parts = sentence.split(',')
    return {
        "time": parts[1],
        "status": parts[2],
        "latitude": float(parts[3][:2]) + float(parts[3][2:]) / 60,
        "longitude": float(parts[5][:3]) + float(parts[5][3:]) / 60,
    }
```

### Experiment 2: Calculate Distance

**Problem:** How far did the boat travel?

```python
import math

def distance_traveled(positions):
    total = 0
    for i in range(1, len(positions)):
        total += haversine(
            positions[i-1].lat, positions[i-1].lon,
            positions[i].lat, positions[i].lon
        )
    return total
```

### Experiment 3: Find Patterns

**Problem:** When are fish most active?

```python
def find_activity_pattern(data):
    """Find time of day with most fish marks."""
    hourly_counts = [0] * 24

    for point in data:
        hour = (point.timestamp_ns // 1_000_000_000) % 86400 // 3600
        if point.backscatter_db > -30:  # Fish mark?
            hourly_counts[hour] += 1

    peak_hour = hourly_counts.index(max(hourly_counts))
    return peak_hour
```

---

## Learning Path: How to Get From Here

### If You're Interested in Marine Science

**Study these:**
- **Biology:** Fish behavior, habitat preferences
- **Oceanography:** Tides, currents, temperature
- **Statistics:** Pattern recognition, significance testing
- **GIS:** Mapping, spatial analysis

**This system gives you real data to work with!**

### If You're Interested in Computer Science

**Study these:**
- **Programming:** Python, TypeScript, SQL
- **Databases:** Parquet, spatial indexing, queries
- **Networks:** UDP, sockets, protocols
- **Algorithms:** Interpolation, search, optimization

**This system shows real-world application!**

### If You're Interested in Engineering

**Study these:**
- **Signal Processing:** FFT, filtering, Sv calculations
- **Systems:** Real-time processing, reliability
- **Data:** Compression, storage, quality control
- **User Experience:** Visualization, interfaces

**This system has all these challenges!**

---

## The Philosophy: Why This Matters

### The Non-Renewable Resource Principle

**"Acoustic signatures of 2026 cannot be recreated in 2031."**

**What this means:**
- Models will get better
- Computers will get faster
- But you can never go back and record 2026 again

**Implication:** Record everything now, analyze later.

### The Foundation First Principle

**"Level 0 must be bulletproof before Level 1 begins."**

**What this means:**
- Get raw data recording perfect
- Then worry about processing
- Then worry about analysis
- Then worry about prediction

**Implication:** Don't rush. Build solid foundations.

---

## Your Turn: How to Contribute

### Ideas for Projects

**For Beginners:**
1. Write a parser for a different NMEA sentence type
2. Create a visualization of boat tracks
3. Calculate total distance traveled per trip

**For Intermediate:**
1. Implement a simple fish mark detector
2. Create a tide pattern analyzer
3. Build a catch predictor

**For Advanced:**
1. Implement machine learning classification
2. Create real-time 3D visualization
3. Build a fishing spot recommender

### Skills You'll Learn

**Technical Skills:**
- Python programming
- Data structures (buffers, queues, indexes)
- Algorithms (search, interpolation, clustering)
- Database design and queries

**Domain Skills:**
- Marine ecology
- Fish behavior
- Oceanographic processes
- Commercial fishing practices

**Soft Skills:**
- Problem decomposition
- System thinking
- Data-driven decision making
- Technical communication

---

## Real-World Impact

### Why This Matters

**For Fisheries Management:**
- Better data = better decisions
- Sustainable harvests
- Healthy fisheries

**For Science:**
- Real-world data for research
- Understanding ecosystems
- Publishing findings

**For Your Future:**
- Portfolio-worthy projects
- Real skills, not just theory
- Connections to marine industry

---

## Next Steps

### If You Want to Learn More

**Read These:**
- USER_GUIDE_NON_TECHNICAL.md (Simple overview)
- USER_GUIDE_MARINER.md (Professional use)
- USER_GUIDE_ENGINEER.md (Technical details)

**Try These:**
- Clone the repository
- Run the tests
- Add a feature

**Ask These:**
- Questions about how things work
- Ideas for improvements
- Ways to contribute

---

## The Bottom Line

**This system is real. It solves real problems. And it was built by people like you learning by doing.**

**You could:**
- Understand it fully
- Improve it significantly
- Use it as a foundation for your own projects
- Build something even better

**The ocean is full of questions. This system helps find answers.**

---

## Challenge Questions

### Easy
1. What is a ring buffer and why do we use it?
2. Why do we need GPS interpolation?
3. What does H3 spatial indexing do?

### Medium
4. At 15 Hz, how much time do we have between packets?
5. Why is Python fast enough for this application?
6. What are the three anchors every data point must have?

### Hard
7. Design a better interpolation algorithm
8. How would you handle 100 boats instead of 1?
9. What's the bottleneck if we go to 150 Hz?

### Expert
10. Implement a fish mark classifier
11. Build a catch prediction model
12. Create a real-time 3D visualization

---

**Good luck, future engineer!** 🚀

---

*Student Guide v1.0.0*
*For: Clever High School Students*
*Last Updated: 2026-07-24*
*Vessel: F/V EILEEN*
