# Vessel Agent System - Agent Onboarding Guide

**Vessel:** F/V EILEEN (51' Commercial Fishing Vessel)
**Home Port:** Southeast Alaska
**Primary Fishery:** Power Trolling
**Methodology:** BMAD (Bottom-up, Multi-level, Agile Development)
**Development Start:** July 2026
**Planning Horizon:** 2031 (5-year vision)

---

## Table of Contents

1. [Agent Orientation](#agent-orientation)
2. [Knowledge Base Navigation](#knowledge-base-navigation)
3. [Development Workflow](#development-workflow)
4. [Session Continuity](#session-continuity)
5. [Common Tasks](#common-tasks)
6. [Quality Standards](#quality-standards)

---

## Agent Orientation

### Project Purpose and Context

**The Mission:** Transform F/V EILEEN into an intelligent fishing vessel that captures, analyzes, and learns from every fishing operation. Build a system that scales from one vessel to an entire fleet, providing both real-time operational intelligence and long-term strategic insights.

**The Core Problem:** Commercial fishing lacks comprehensive data collection and analysis. Fishermen make decisions based on intuition and limited information. Scientists lack fine-scale, real-time data for stock assessment. The ocean remains largely opaque.

**The Solution:** A multi-level agent system that:
1. **Captures everything** - Network packets, NMEA sentences, acoustic signatures, crew observations
2. **Analyzes incrementally** - From raw bits to physical tensors to analytical features to intelligence
3. **Learns continuously** - Patterns emerge, models improve, predictions become more accurate
4. **Shares freely** - Open tools, open data, open science

### The BMAD Methodology

**BMAD = Bottom-up, Multi-level, Agile Development**

This methodology ensures robust, iterative development while maintaining long-term architectural coherence.

#### Bottom-Up Development

**Principle:** Start with raw data capture, build upward through abstraction layers.

**Five Abstraction Levels:**

```
LEVEL 0: Raw Bits
  ├─ Network packets (UDP from Furuno sounder)
  ├─ NMEA bytes (GPS, AIS, heading, etc.)
  ├─ Raw sensor readings
  └─ Success criteria: >99.9% capture rate, <0.1% packet loss

LEVEL 1: Physical Tensors
  ├─ Sv dB (volume backscattering strength)
  ├─ Meters per bin (depth resolution)
  ├─ H3 spatial indexing (hexagonal grid)
  └─ Success criteria: <5m position error, <0.5m depth precision

LEVEL 2: Analytical Features
  ├─ Biomass density
  ├─ Species classification
  ├─ Bottom detection
  └─ Success criteria: >70% species accuracy, >80% biomass precision

LEVEL 3: Operational Intelligence
  ├─ Catch predictions
  ├─ Route optimization
  ├─ Fleet collaboration
  └─ Success criteria: >60% catch prediction at 24h, >15% CPUE improvement

LEVEL 4: Strategic Knowledge
  ├─ Stock assessment
  ├─ Ecosystem analysis
  ├─ Regulatory integration
  └─ Success criteria: within 20% of surveys, 3+ peer-reviewed publications
```

**Key Insight:** Each level must be stable before building the next. Level 0 never changes—raw data is immutable. Level 1 changes rarely—physics is constant. Levels 2-4 evolve as models improve.

#### Multi-Level Architecture

**Principle:** Maintain clear boundaries between abstraction levels with well-defined interfaces.

**Interface Contracts:** Each level has clear input/output contracts defined in the memory schema.

**Parallel Development:** Multiple teams can work at different levels simultaneously because interfaces are stable.

#### Agile Development

**Principle:** Iterate rapidly at each level with continuous validation.

**Sprint Structure:** 2-week cycles with deployable output.

**Continuous Deployment:**
- Level 0 deploys daily (data capture runs continuously)
- Level 1 deploys weekly (storage format updates)
- Levels 2-4 deploy monthly (model updates)

### System Architecture Overview

**Current Implementation:** Hybrid Python + TypeScript

```
┌─────────────────────────────────────────────────────────┐
│  Electron App (TypeScript) - Vessel-Local Deployment   │
│  ├─ React UI + WebGL Visualization                       │
│  ├─ Multi-panel interface (CAD + DAW inspired)           │
│  └─ Real-time echogram, spatial maps, timeline          │
└────────────────────────┬────────────────────────────────┘
                         │ WebSocket/SSE
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Python Backend - Phase 0 Complete                      │
│  ├─ Packet capture (pypcap, BPF filters)                  │
│  ├─ NMEA interpolation (sub-second timing)              │
│  ├─ Parquet storage (PyArrow, Hive partitioning)         │
│  ├─ H3 spatial indexing                                  │
│  └─ Data quality monitoring                              │
└─────────────────────────────────────────────────────────┘
```

**Why This Architecture:**
- **Performance is NOT the bottleneck** - 15Hz packet rate is trivial for Python
- **Time-to-market critical** - Fishing season is NOW, Python implementation exists
- **Developer efficiency** - Python for data processing, TypeScript for UI
- **Deployment simplicity** - pip + npm install, no compilation needed
- **Future-proof** - Clean module boundaries allow Rust extraction later if needed

**Technology Stack:**
- **Backend:** Python 3.10+, pypcap, PyArrow, H3, Pandas
- **Storage:** Apache Parquet, Hive partitioning, DuckDB
- **Frontend:** TypeScript, React, WebGL, D3.js, MapLibre GL
- **Communication:** WebSocket, Server-Sent Events
- **Spatial:** Uber H3 (hexagonal indexing)

### How to Navigate the Codebase

**Directory Structure:**

```
vessel-agent/
├── README.md                           # START HERE - Entry point
├── AGENT_ONBOARDING.md                 # THIS FILE - Agent orientation
├── README_IMPLEMENTATION.md           # Implementation quick start
├── vessel_agent_memory_schema.json     # Core memory schema (READ THIS FIRST)
├── vessel_agent_knowledge_base.md      # Technical knowledge base
├── vessel_agent_5year_vision.md        # 5-year roadmap (BMAD)
├── ARCHITECTURE_DECISION_RECORD.md     # Language/architecture decisions
├── LANGUAGE_ARCHITECTURE_ANALYSIS.md    # Multi-language analysis
├── phase0_implementation_plan.md      # Phase 0 detailed plan
├── phase0_quick_start.md              # Phase 0 quick start
├── capture_daemon.py                   # Main daemon entry point
├── requirements.txt                    # Python dependencies
├── requirements-dev.txt                # Development dependencies
├── tests/                              # Test suite
│   ├── test_network_capture.py
│   ├── test_nmea_interpolator.py
│   ├── test_quality_monitoring.py
│   └── test_storage.py
└── vessel_agent/                       # Main package
    ├── __init__.py
    ├── config.py                       # Configuration
    ├── capture/
    │   ├── __init__.py
    │   ├── network_capture.py          # Packet capture
    │   └── nmea_interpolator.py        # NMEA interpolation
    ├── storage/
    │   ├── __init__.py
    │   └── parquet_pipeline.py         # Parquet storage
    └── monitoring/
        ├── __init__.py
        └── data_quality.py             # Quality monitoring
```

**Code Statistics:**
- **Documentation:** 19,099 lines across 24 MD files
- **Python Code:** 2,242 lines across 7 modules
- **Test Code:** ~500 lines across 4 test files
- **Total:** ~21,841 lines

---

## Knowledge Base Navigation

### Core Documents and When to Read Them

#### Essential Reading (Every Session)

**1. README.md (5 minutes)**
- **Purpose:** Entry point and system overview
- **When to Read:** First thing every session
- **Key Sections:** Quick Start, System Status, Critical Principles

**2. vessel_agent_memory_schema.json (10 minutes)**
- **Purpose:** JSON schema for agent memory - THE SINGLE SOURCE OF TRUTH
- **When to Read:** After README, before any implementation work
- **Key Sections:**
  - `system_architecture.development_methodology` - BMAD definition
  - `system_architecture.roadmap` - 5-year plan
  - `data_schemas` - All data structures
  - `api_interfaces` - Module contracts
  - `success_metrics` - Validation criteria

**3. vessel_agent_knowledge_base.md (20 minutes)**
- **Purpose:** Comprehensive technical knowledge base
- **When to Read:** After schema, for deep technical understanding
- **Key Sections:**
  - System Architecture Overview
  - Data Schema Definitions
  - API Reference
  - Implementation Roadmap

#### Strategic Context (Read Once or Reference)

**4. vessel_agent_5year_vision.md (15 minutes)**
- **Purpose:** Strategic roadmap with BMAD methodology
- **When to Read:** For roadmap context and implementation prioritization
- **Key Sections:** BMAD Methodology, 5-Year Vision, Year-by-Year Breakdown

**5. ARCHITECTURE_DECISION_RECORD.md (10 minutes)**
- **Purpose:** Language and architecture decisions with rationale
- **When to Read:** When questioning architectural choices
- **Key Sections:** Decision Summary, Alternatives Considered

#### Implementation Guides (Read as Needed)

**6. README_IMPLEMENTATION.md (10 minutes)**
- **Purpose:** Quick start for implementation
- **When to Read:** When starting implementation work
- **Key Sections:** 30-Minute Quick Start, Architecture, Module Structure

**7. phase0_quick_start.md (15 minutes)**
- **Purpose:** Phase 0 deployment guide
- **When to Read:** When deploying Phase 0 system
- **Key Sections:** 30-Minute Quick Start, Validation, Troubleshooting

**8. phase0_implementation_plan.md (30 minutes)**
- **Purpose:** Detailed Phase 0 implementation plan
- **When to Read:** When implementing Phase 0 features
- **Key Sections:** Module Specifications, Deployment Strategy, Success Criteria

#### Specialized Documentation (Read by Task)

**9. marine_visualization_design_doc.md (70+ pages)**
- **Purpose:** Multi-panel interface design (CAD + DAW inspired)
- **When to Read:** For frontend/UI development
- **Key Sections:** Interface Design, Component Specs, Interaction Patterns

**10. nmea_implementation_guide.md (15 minutes)**
- **Purpose:** NMEA integration implementation guide
- **When to Read:** When working with NMEA data
- **Key Sections:** NMEA Protocol, Parsing Strategy, Quality Checks

**11. nmea_integration_analysis.md (60 minutes)**
- **Purpose:** Comprehensive NMEA integration analysis
- **When to Read:** For deep NMEA understanding
- **Key Sections:** Sentence Types, Timing Analysis, Error Handling

**12. edge_device_io_architecture.md (30 minutes)**
- **Purpose:** Edge device IO and DAW track architecture
- **When to Read:** For edge device integration
- **Key Sections:** IO Patterns, Track Design, Real-time Processing

**13. LANGUAGE_ARCHITECTURE_ANALYSIS.md (20 minutes)**
- **Purpose:** Multi-language analysis from specialist teams
- **When to Read:** When considering language changes
- **Key Sections:** Team Contributions, Analysis Framework, Decision Criteria

#### User Guides (Reference)

**14. USER_GUIDE_NON_TECHNICAL.md**
- **Purpose:** Non-technical user guide
- **When to Read:** When writing user-facing documentation

**15. USER_GUIDE_STUDENT.md**
- **Purpose:** Student/educational user guide
- **When to Read:** When creating educational materials

### Memory Schema Structure

**Location:** `vessel_agent_memory_schema.json`

**Schema Version:** v1.0.0 (immutable - extend only, don't modify)

**Top-Level Structure:**

```json
{
  "_meta": {
    "schema_version": "1.0.0",
    "vessel_id": "US-AK-FVEILEEN-01",
    "vessel_name": "EILEEN"
  },
  "system_architecture": {
    "development_methodology": { ... },  // BMAD definition
    "roadmap": { ... },                   // 5-year plan
    "abstraction_levels": { ... }        // Level 0-4 specs
  },
  "data_schemas": {
    "core_anchor": { ... },              // Time/Location/Source
    "acoustic_data": { ... },
    "nmea_data": { ... },
    "quality_metrics": { ... }
  },
  "api_interfaces": {
    "level_0_to_1": { ... },
    "level_1_to_2": { ... },
    "level_2_to_3": { ... },
    "level_3_to_4": { ... }
  },
  "success_metrics": {
    "level_0": { ... },
    "level_1": { ... },
    "level_2": { ... },
    "level_3": { ... },
    "level_4": { ... }
  }
}
```

**Key Principles:**
1. **Immutable Core** - `_meta`, `development_methodology`, `abstraction_levels` never change
2. **Extensible Data** - `data_schemas` can be extended with new fields
3. **Versioned APIs** - `api_interfaces` are versioned contracts
4. **Measurable Success** - `success_metrics` define validation criteria

### Decision Records and Rationale

**Location:** `ARCHITECTURE_DECISION_RECORD.md`

**Key Decisions:**

**Decision 1: Python + TypeScript Hybrid Architecture**
- **Date:** 2026-07-24
- **Status:** DECIDED - IMPLEMENTED
- **Rationale:**
  - Performance not bottleneck (15Hz trivial for Python)
  - Time-to-market critical (fishing season NOW)
  - Developer efficiency (Casey knows Python, TS excellent for UI)
  - Deployment simplicity (pip + npm, no compilation)
  - Future-proof (clean boundaries allow Rust extraction later)

**Decision 2: BMAD Methodology**
- **Date:** 2026-07-24
- **Status:** DECIDED - CORE FOUNDATION
- **Rationale:**
  - Bottom-up ensures solid foundation
  - Multi-level enables parallel development
  - Agile delivers continuous value
  - 5-year vision maintains long-term coherence

**Decision 3: Parquet + Hive Partitioning**
- **Date:** 2026-07-24
- **Status:** DECIDED - IMPLEMENTED
- **Rationale:**
  - Columnar storage perfect for analytical queries
  - Hive partitioning enables efficient time-range queries
  - Future-proof (standard format, broad tool support)
  - Zero-copy serialization (performance)

**Decision 4: H3 Spatial Indexing**
- **Date:** 2026-07-24
- **Status:** DECIDED - IMPLEMENTED
- **Rationale:**
  - Hexagonal grid superior to lat/lon for aggregation
  - Hierarchical resolution enables multi-scale analysis
  - Uber-maintained (active development)
  - Broad language support

### Technical Specifications

**Performance Requirements:** `PERFORMANCE_REQUIREMENTS.md`
- Level 0: >99.9% capture rate, <0.1% packet loss
- Level 1: <5m position error, <0.5m depth precision
- Level 2: >70% species accuracy, >80% biomass precision
- Level 3: >60% catch prediction at 24h, >15% CPUE improvement
- Level 4: within 20% of surveys, 3+ peer-reviewed publications

**Python Optimization Analysis:** `PYTHON_OPTIMIZATION_ANALYSIS.md`
- 27,000× performance headroom at 15Hz
- Zero-copy packet processing (memoryview)
- Ring buffer for lossless capture
- Async I/O for storage pipeline

**Language Architecture Analysis:** `LANGUAGE_ARCHITECTURE_ANALYSIS.md`
- Multi-team analysis (Rust, Go, Julia, TypeScript, Python, Database)
- Evaluation framework (Performance, Reliability, DX, Deployment, Integration)
- Specialist team contributions pending

---

## Development Workflow

### How to Start Work on a Task

**Step 1: Load Core Context (30 minutes)**

1. **Read README.md** (5 minutes) - System overview and current status
2. **Parse memory schema** (10 minutes) - Understand data structures and interfaces
3. **Review knowledge base** (10 minutes) - Technical architecture and patterns
4. **Check 5-year vision** (5 minutes) - Strategic alignment

**Step 2: Understand Current Status (15 minutes)**

1. **Check Phase 0 status** in `vessel_agent_memory_schema.json`
2. **Review completed tasks** in roadmap
3. **Identify pending work** for current sprint
4. **Check recent commits** for latest changes

**Step 3: Define Task (10 minutes)**

1. **Write task description** - What needs to be done
2. **Identify BMAD level** - Which abstraction level affected
3. **Check interfaces** - Which APIs/contracts involved
4. **Define success criteria** - How to validate completion

**Step 4: Create Implementation Plan (10 minutes)**

1. **List files to modify** - Which code files need changes
2. **Identify dependencies** - What other code/systems affected
3. **Plan tests** - What test coverage needed
4. **Estimate complexity** - How long will it take

**Step 5: Implement (variable)**

1. **Write code** following existing patterns
2. **Add tests** for new functionality
3. **Update documentation** as needed
4. **Run test suite** to validate

**Step 6: Validate and Deploy (15 minutes)**

1. **Run tests** - All tests must pass
2. **Check performance** - Verify no regressions
3. **Update roadmap** - Mark tasks complete
4. **Document changes** - Add to knowledge base if significant

### Which Files to Modify for What Purpose

**For Data Capture Tasks (Level 0):**

```
vessel_agent/capture/network_capture.py    # Packet capture logic
vessel_agent/capture/nmea_interpolator.py    # NMEA parsing
tests/test_network_capture.py               # Capture tests
tests/test_nmea_interpolator.py             # NMEA tests
```

**For Data Storage Tasks (Level 0-1):**

```
vessel_agent/storage/parquet_pipeline.py    # Parquet write pipeline
tests/test_storage.py                       # Storage tests
```

**For Quality Monitoring Tasks (Level 0):**

```
vessel_agent/monitoring/data_quality.py     # Quality checks
tests/test_quality_monitoring.py            # Quality tests
```

**For Configuration Changes:**

```
vessel_agent/config.py                      # System configuration
requirements.txt                            # Runtime dependencies
requirements-dev.txt                        # Development dependencies
```

**For Documentation Updates:**

```
README.md                                   # System overview
README_IMPLEMENTATION.md                    # Implementation guide
vessel_agent_knowledge_base.md             # Technical knowledge
ARCHITECTURE_DECISION_RECORD.md            # Decision records
```

**For Schema Changes (RARE - extend only):**

```
vessel_agent_memory_schema.json            # Core schema (IMMUTABLE)
```

**Principles:**
1. **Schema is immutable** - Only extend, never modify existing fields
2. **Module boundaries** - Respect module interfaces, don't cross boundaries
3. **Test coverage** - Every code change needs test coverage
4. **Documentation** - If it changes architecture, document it

### Testing Requirements

**Test Structure:**

```
tests/
├── __init__.py
├── test_network_capture.py         # Packet capture tests
├── test_nmea_interpolator.py       # NMEA parsing tests
├── test_quality_monitoring.py      # Quality monitoring tests
└── test_storage.py                 # Storage pipeline tests
```

**Running Tests:**

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_network_capture.py

# Run with coverage
pytest --cov=vessel_agent tests/

# Run specific test
pytest tests/test_network_capture.py::test_ring_buffer
```

**Test Requirements:**

1. **Unit Tests** - Every function must have unit tests
2. **Integration Tests** - Module interactions must be tested
3. **Edge Cases** - Test error conditions, boundary cases
4. **Performance Tests** - Verify no regressions

**Coverage Goals:**
- **Core modules:** >90% coverage
- **Utility functions:** >80% coverage
- **Integration points:** >95% coverage

### Documentation Standards

**When to Document:**

1. **ALWAYS** - Document all public APIs
2. **ALWAYS** - Document all data structures
3. **ALWAYS** - Document all configuration options
4. **WHEN COMPLEX** - Document complex algorithms (>20 lines)
5. **WHEN ARCHITECTURAL** - Document architectural decisions

**Documentation Format:**

**Python Docstrings:**

```python
def process_packet(packet: bytes) -> Optional[FurunoPacket]:
    """Process raw UDP packet into structured Furuno data.

    Args:
        packet: Raw UDP packet bytes from Furuno sounder

    Returns:
        FurunoPacket if parsing successful, None if invalid

    Raises:
        PacketParseError: If packet header invalid

    Example:
        >>> packet = capture_next_packet()
        >>> furuno_data = process_packet(packet)
        >>> print(furuno_data.depth_range)
    """
```

**Markdown Documentation:**

```markdown
## Feature Name

**Purpose:** Why this feature exists

**Usage:** How to use it

**Example:**
\```python
code_example()
\```

**API Reference:**
- param1: Description
- param2: Description

**Returns:** What it returns
```

**Code Comments:**

```python
# CRITICAL: This must be zero-copy to maintain 27,000× performance headroom
# Use memoryview to avoid copying packet data
packet_view = memoryview(packet)
```

---

## Session Continuity

### How to Pick Up Where Previous Agent Left Off

**Step 1: Load Minimal Context (15 minutes)**

1. **Read this file** (AGENT_ONBOARDING.md) - Agent orientation
2. **Read README.md** - System overview and current status
3. **Parse memory schema** - Core data structures (skim, reference as needed)

**Step 2: Check Implementation Status (10 minutes)**

1. **Check git status** - What files have been modified
2. **Check recent commits** - What was just completed
3. **Check test status** - Are tests passing
4. **Check roadmap** - What's the next task

**Step 3: Understand Last Session's Work (15 minutes)**

1. **Read recent commit messages** - What was done and why
2. **Check modified files** - What code was written
3. **Check documentation updates** - What decisions were made
4. **Identify next steps** - What's left to do

**Step 4: Continue Work (ongoing)**

1. **Pick up task** - Continue from last session's stopping point
2. **Follow workflow** - Use development workflow from previous section
3. **Update roadmap** - Mark progress as you complete tasks
4. **Document decisions** - Add to decision records if architectural

### What to Preserve Between Sessions

**Immutable Artifacts (Never Lose):**

1. **vessel_agent_memory_schema.json** - Core schema (extend only)
2. **vessel_agent_knowledge_base.md** - Technical knowledge base
3. **vessel_agent_5year_vision.md** - Strategic roadmap
4. **ARCHITECTURE_DECISION_RECORD.md** - Architectural decisions
5. **README.md** - System overview (update with milestones)

**Living Artifacts (Update Regularly):**

1. **README_IMPLEMENTATION.md** - Implementation guide (update with new features)
2. **phase0_implementation_plan.md** - Phase 0 plan (update status)
3. **Code** - All code in vessel_agent/ (update with implementations)
4. **Tests** - All tests in tests/ (update with new tests)

**Session-Specific (Can Be Recreated):**

1. **Agent context** - Regenerated from schemas each session
2. **Work notes** - Recreated from commit messages
3. **Task lists** - Recreated from roadmap

### How to Update Knowledge Base

**When to Update:**

1. **Architectural decisions** - Add to ARCHITECTURE_DECISION_RECORD.md
2. **New features** - Add to vessel_agent_knowledge_base.md
3. **API changes** - Update api_interfaces in memory schema
4. **Roadmap progress** - Update roadmap in memory schema
5. **Major milestones** - Update README.md

**How to Update:**

**Adding a Decision:**

```markdown
## Decision N: [Decision Name]

**Date:** YYYY-MM-DD
**Status:** DECIDED / PROPOSED / DEPRECATED
**Context:** Why this decision was needed

**Options Considered:**
1. Option A
2. Option B
3. Option C

**Decision:** Option B

**Rationale:**
- Reason 1
- Reason 2
- Reason 3

**Implications:**
- What this affects
- What needs to change
- Risks and mitigations
```

**Updating Knowledge Base:**

```markdown
## [Feature Name]

**Added:** YYYY-MM-DD
**BMAD Level:** 0-4

**Purpose:** What this feature does

**Implementation:**
- File: `path/to/code.py`
- Function: `function_name()`
- Dependencies: What it depends on

**API:**
\```python
usage_example()
\```

**Testing:**
- Test file: `tests/test_feature.py`
- Coverage: XX%
```

**Updating Roadmap:**

```json
{
  "system_architecture": {
    "roadmap": {
      "year_1": {
        "status": "in_progress",
        "deliverables": [
          {
            "item": "Continuous acoustic data capture",
            "status": "complete",
            "completed_date": "2026-07-25"
          }
        ]
      }
    }
  }
}
```

### Decision-Making Frameworks

**Framework 1: BMAD Level Check**

**Question:** Which BMAD level does this decision affect?

**Level 0 (Raw Bits):**
- Impact: HIGH - Foundation of everything
- Stability: CRITICAL - Must be bulletproof
- Process: Extensive testing, validation, monitoring
- Examples: Packet capture, NMEA parsing, storage format

**Level 1 (Physical Tensors):**
- Impact: HIGH - All analysis depends on this
- Stability: HIGH - Physics doesn't change
- Process: Careful design, scientific validation
- Examples: Normalization, calibration, spatial indexing

**Level 2 (Analytical Features):**
- Impact: MEDIUM - Models can be retrained
- Stability: MEDIUM - Models evolve
- Process: Continuous validation, iteration
- Examples: Classification, feature extraction

**Level 3 (Operational Intelligence):**
- Impact: MEDIUM - Recommendations can be adjusted
- Stability: LOW - Continuous improvement
- Process: A/B testing, user feedback
- Examples: Predictions, recommendations

**Level 4 (Strategic Knowledge):**
- Impact: LOW - Long-term analysis
- Stability: LOW - Scientific iteration
- Process: Peer review, validation
- Examples: Stock assessment, ecosystem analysis

**Framework 2: Non-Renewable Resource Check**

**Question:** Does this affect data capture?

**YES:**
- **Priority:** CRITICAL
- **Timeline:** Immediately (fishing season doesn't wait)
- **Validation:** Extensive (can't recreate lost data)
- **Monitoring:** Continuous (detect issues in real-time)

**NO:**
- **Priority:** Based on BMAD level
- **Timeline:** Based on sprint schedule
- **Validation:** Based on impact
- **Monitoring:** Based on risk

**Framework 3: Interface Contract Check**

**Question:** Does this change an existing interface?

**YES:**
- **STOP** - Interface changes are breaking changes
- **Process:**
  1. Document why change needed
  2. Propose new interface version
  3. Update all consumers
  4. Deprecate old interface
  5. Remove old interface after deprecation period

**NO:**
- **Proceed** - New functionality, new interfaces
- **Process:**
  1. Design new interface
  2. Implement with tests
  3. Document in knowledge base
  4. Update roadmap

---

## Common Tasks

### Adding a New Feature

**Step 1: Feature Definition (15 minutes)**

1. **Write feature description** - What does it do?
2. **Identify BMAD level** - Which abstraction level?
3. **Check existing interfaces** - Can it fit existing patterns?
4. **Define success criteria** - How to validate?

**Step 2: Design (20 minutes)**

1. **Define data structures** - What data in/out?
2. **Define interface** - What's the API?
3. **Identify dependencies** - What does it depend on?
4. **Plan tests** - What needs testing?

**Step 3: Implementation (variable)**

1. **Create/modify code files**
2. **Add docstrings** - Document all public APIs
3. **Add tests** - Unit and integration tests
4. **Run tests** - All tests must pass

**Step 4: Documentation (15 minutes)**

1. **Update knowledge base** - Add feature documentation
2. **Update implementation guide** - If user-facing
3. **Add examples** - Show how to use it
4. **Update roadmap** - Mark feature complete

**Step 5: Validation (10 minutes)**

1. **Run full test suite** - Verify no regressions
2. **Check performance** - Verify meets requirements
3. **Review code** - Check for issues
4. **Commit changes** - With clear commit message

**Example Commit Message:**

```
feat: Add H3 spatial indexing to acoustic data

Implements Level 1 spatial indexing using Uber H3 hexagonal grid.
Enables efficient spatial queries and aggregation.

Changes:
- Add H3Indexer class to vessel_agent/storage/
- Add h3_index_uint64 field to acoustic data schema
- Add spatial query functions
- Add unit and integration tests

Success criteria:
- H3 coverage: 100%
- Query performance: <1s for any day
- Test coverage: 95%

Refs: vessel_agent_memory_schema.json level_1 success_metrics
```

### Fixing a Bug

**Step 1: Bug Report (5 minutes)**

1. **Describe bug** - What's happening?
2. **Identify BMAD level** - Which level affected?
3. **Check impact** - How bad is it?
4. **Assign priority** - CRITICAL/HIGH/MEDIUM/LOW

**Step 2: Investigation (15 minutes)**

1. **Reproduce bug** - Create minimal reproduction
2. **Identify root cause** - Where's the issue?
3. **Check affected code** - What needs fixing?
4. **Plan fix** - What's the solution?

**Step 3: Fix (variable)**

1. **Write fix** - Minimal change to fix issue
2. **Add regression test** - Prevent future occurrences
3. **Run tests** - Verify fix and no regressions
4. **Document** - If bug-fix reveals pattern

**Step 4: Validation (10 minutes)**

1. **Run full test suite** - All tests pass
2. **Check performance** - No regressions
3. **Test in production** - If safe to do so
4. **Commit fix** - With clear commit message

**Example Commit Message:**

```
fix: Correct NMEA timestamp interpolation for sub-second precision

Bug: NMEA interpolator was truncating sub-second timestamps,
causing GPS/sounder sync errors at 10 knots.

Root cause: Floating point division was losing precision.
Fix: Use decimal module for timestamp arithmetic.

Impact: Level 0 data quality - CRITICAL
Regression test added: tests/test_nmea_interpolator.py::test_subsecond_precision
```

### Updating Documentation

**Step 1: Identify Update Needed (5 minutes)**

1. **What changed?** - Code, API, architecture?
2. **Who needs to know?** - Users, developers, future agents?
3. **Where to document?** - Which file(s)?
4. **How extensive?** - Paragraph, section, new document?

**Step 2: Choose Documentation Type**

**API Documentation:**
- Add to knowledge base under API Reference
- Include function signatures, parameters, returns, examples
- Update if API changes

**Feature Documentation:**
- Add to knowledge base under Features
- Include purpose, usage, examples, testing
- Update when features added

**Architectural Documentation:**
- Add to ARCHITECTURE_DECISION_RECORD.md
- Include decision, options, rationale, implications
- Update when architecture changes

**User Documentation:**
- Add to README_IMPLEMENTATION.md
- Include quick start, examples, troubleshooting
- Update when user-facing features added

**Step 3: Write Documentation (20 minutes)**

1. **Start with purpose** - Why this exists
2. **Add usage** - How to use it
3. **Add examples** - Show, don't just tell
4. **Add references** - Link to related docs

**Step 4: Review and Commit (10 minutes)**

1. **Check clarity** - Is it understandable?
2. **Check completeness** - Is anything missing?
3. **Check accuracy** - Is it correct?
4. **Commit** - With clear commit message

**Example Commit Message:**

```
docs: Add H3 spatial indexing documentation

Documents new H3Indexer class and spatial query functions.
Includes API reference, usage examples, and performance notes.

Updates:
- vessel_agent_knowledge_base.md - Add H3 indexing section
- README_IMPLEMENTATION.md - Add spatial query examples
- Add performance benchmark results

Related to: commit abc1234 "feat: Add H3 spatial indexing"
```

### Creating Tests

**Step 1: Identify Test Needs (5 minutes)**

1. **What to test?** - Function, module, integration?
2. **What cases?** - Happy path, edge cases, errors?
3. **What coverage?** - Target coverage %?
4. **What type?** - Unit, integration, performance?

**Step 2: Write Test (20 minutes)**

**Unit Test Example:**

```python
def test_ring_buffer_put_get():
    """Test ring buffer put and get operations."""
    buffer = RingBuffer(capacity=10)

    # Test single packet
    packet = b'test_packet_1'
    assert buffer.put(packet) is True
    assert buffer.get() == packet
    assert buffer.dropped_packets == 0

    # Test buffer overflow
    for i in range(15):
        buffer.put(f'packet_{i}'.encode())

    assert buffer.dropped_packets == 5
```

**Integration Test Example:**

```python
def test_capture_to_storage_pipeline():
    """Test end-to-end capture to storage pipeline."""
    # Setup
    capture = NetworkCapture(interface='loopback')
    storage = ParquetPipeline(path=temp_path)

    # Capture packets
    packets = capture.capture(duration=5)

    # Store packets
    storage.write(packets)

    # Verify
    stored = storage.read(time_range=(start, end))
    assert len(stored) == len(packets)
```

**Step 3: Run and Validate (10 minutes)**

1. **Run test** - Does it pass?
2. **Check coverage** - Does it cover the code?
3. **Check performance** - Is it fast enough?
4. **Check independence** - Does it run alone?

**Step 4: Commit (5 minutes)**

1. **Add test file** - In tests/ directory
2. **Run test suite** - All tests pass
3. **Commit** - With clear commit message

**Example Commit Message:**

```
test: Add ring buffer overflow test

Test validates ring buffer behavior when capacity exceeded.
Ensures packet counting and overflow detection work correctly.

Test file: tests/test_network_capture.py
Test function: test_ring_buffer_overflow
Coverage: RingBuffer class 100%

Related to: issue #123 - Packet loss detection
```

---

## Quality Standards

### Code Quality Expectations

**Python Code Style:**

1. **Follow PEP 8** - Standard Python style guide
2. **Use type hints** - All function signatures
3. **Document all public APIs** - Docstrings with examples
4. **Keep functions focused** - One responsibility per function
5. **Avoid globals** - Pass dependencies explicitly

**Example:**

```python
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class AcousticData:
    """Structured acoustic ping data.

    Attributes:
        timestamp_ns: Nanosecond timestamp
        depth_range_m: Depth range in meters
        backscatter_db: Volume backscattering strength (dB)
    """
    timestamp_ns: int
    depth_range_m: float
    backscatter_db: float

def process_acoustic_data(
    data: List[AcousticData],
    calibration: Optional[float] = None
) -> List[AcousticData]:
    """Process and calibrate acoustic data.

    Args:
        data: Raw acoustic data points
        calibration: Optional calibration factor in dB

    Returns:
        Calibrated acoustic data

    Raises:
        ValueError: If data empty or calibration invalid
    """
    if not data:
        raise ValueError("Acoustic data cannot be empty")

    if calibration is not None and calibration < 0:
        raise ValueError("Calibration must be non-negative")

    # Process data...
    return processed_data
```

**Performance Standards:**

1. **Zero-copy operations** - Use memoryview for packet processing
2. **Efficient data structures** - Use appropriate data types
3. **Lazy evaluation** - Defer computation until needed
4. **Batch operations** - Vectorize where possible

**Example:**

```python
# GOOD: Zero-copy packet processing
def process_packet(packet: bytes) -> FurunoPacket:
    packet_view = memoryview(packet)  # No copy
    header = parse_header(packet_view[:20])  # Slice, no copy
    payload = packet_view[20:]  # Slice, no copy
    return FurunoPacket(header, payload)

# BAD: Copying packet data
def process_packet_bad(packet: bytes) -> FurunoPacket:
    header = packet[:20]  # Creates copy
    payload = packet[20:]  # Creates copy
    return FurunoPacket(header, payload)
```

**Error Handling Standards:**

1. **Use exceptions for errors** - Don't return error codes
2. **Handle expected errors** - Catch and handle specific exceptions
3. **Let unexpected errors propagate** - Don't catch Exception
4. **Log errors** - Use Python logging module

**Example:**

```python
import logging

logger = logging.getLogger(__name__)

def process_data(data: bytes) -> Result:
    """Process data with proper error handling."""
    try:
        parsed = parse_packet(data)
        return process_parsed(parsed)
    except PacketParseError as e:
        logger.error(f"Packet parse error: {e}")
        raise  # Re-raise for caller to handle
    except ValueError as e:
        logger.warning(f"Invalid data value: {e}")
        return Result.error(f"Invalid value: {e}")
    # Don't catch Exception - let unexpected errors propagate
```

### Documentation Requirements

**All Public APIs Must:**

1. **Have docstrings** - With purpose, parameters, returns, examples
2. **Have type hints** - All parameters and return values
3. **Have examples** - Show common usage
4. **Have error documentation** - What exceptions can be raised

**Docstring Template:**

```python
def function_name(
    param1: type1,
    param2: type2,
    optional_param: type3 = default
) -> return_type:
    """One-line summary of function.

    Extended description of function purpose and behavior.
    Include any important implementation details.

    Args:
        param1: Description of param1
        param2: Description of param2
        optional_param: Description of optional_param

    Returns:
        Description of return value

    Raises:
        SpecificError: When error condition occurs

    Example:
        >>> result = function_name(value1, value2)
        >>> print(result)
        'expected_output'
    """
```

**All Features Must:**

1. **Have knowledge base entry** - In vessel_agent_knowledge_base.md
2. **Have implementation guide** - In README_IMPLEMENTATION.md if user-facing
3. **Have examples** - Show common usage patterns
4. **Have performance notes** - If performance-critical

**All Architectural Decisions Must:**

1. **Be recorded** - In ARCHITECTURE_DECISION_RECORD.md
2. **Have rationale** - Why this decision was made
3. **Have alternatives** - What other options were considered
4. **Have implications** - What this affects

### Testing Standards

**Test Coverage Requirements:**

- **Core modules** (capture, storage): >90% coverage
- **Utility modules** (monitoring): >80% coverage
- **Integration points**: >95% coverage

**Test Types Required:**

1. **Unit tests** - Test individual functions/classes
2. **Integration tests** - Test module interactions
3. **Edge case tests** - Test boundary conditions
4. **Error tests** - Test error handling

**Test Quality Standards:**

1. **Test independence** - Each test should run alone
2. **Test clarity** - Test names should describe what they test
3. **Test maintainability** - Tests should be easy to update
4. **Test speed** - Tests should run quickly (<5 seconds total)

**Example Test Suite:**

```python
class TestNetworkCapture:
    """Test suite for network capture module."""

    def test_ring_buffer_initialization(self):
        """Test ring buffer initializes correctly."""
        buffer = RingBuffer(capacity=100)
        assert buffer.capacity == 100
        assert buffer.dropped_packets == 0

    def test_ring_buffer_put(self):
        """Test ring buffer put operation."""
        buffer = RingBuffer(capacity=10)
        packet = b'test_packet'
        assert buffer.put(packet) is True
        assert len(buffer.buffer) == 1

    def test_ring_buffer_overflow(self):
        """Test ring buffer overflow detection."""
        buffer = RingBuffer(capacity=5)
        for i in range(10):
            buffer.put(f'packet_{i}'.encode())
        assert buffer.dropped_packets == 5

    def test_packet_parsing_valid(self):
        """Test parsing valid packet."""
        packet = create_valid_furuno_packet()
        parsed = parse_packet(packet)
        assert parsed.packet_type == 'FURUNO_DFF3'
        assert parsed.depth_range is not None

    def test_packet_parsing_invalid(self):
        """Test parsing invalid packet raises error."""
        packet = b'invalid_packet_data'
        with pytest.raises(PacketParseError):
            parse_packet(packet)

    def test_end_to_end_capture(self):
        """Test full capture pipeline."""
        capture = NetworkCapture(interface='loopback')
        packets = capture.capture(duration=1)
        assert len(packets) > 0
        assert all(p.timestamp_ns > 0 for p in packets)
```

### Review Criteria

**Before Committing Code, Check:**

**Code Quality:**
- [ ] Follows PEP 8 style guide
- [ ] Has type hints for all functions
- [ ] Has docstrings for all public APIs
- [ ] Has no debugging code (print statements, etc.)
- [ ] Has no commented-out code
- [ ] Has no unused imports or variables

**Testing:**
- [ ] All tests pass
- [ ] New code has test coverage
- [ ] Edge cases are tested
- [ ] Error handling is tested
- [ ] Performance is acceptable

**Documentation:**
- [ ] Public APIs documented
- [ ] New features documented in knowledge base
- [ ] Examples provided
- [ ] Architectural decisions recorded

**Architecture:**
- [ ] Follows BMAD principles
- [ ] Respects module boundaries
- [ ] Uses existing interfaces
- [ ] Doesn't break existing contracts
- [ ] Aligns with 5-year vision

**Performance:**
- [ ] Meets performance requirements
- [ ] No regressions in existing code
- [ ] Efficient data structures used
- [ ] Zero-copy operations where critical

**Security:**
- [ ] No hardcoded secrets
- [ ] Input validation where needed
- [ ] Error handling doesn't expose internals
- [ ] Dependencies are up to date

**Commit Message Checklist:**

```
[ ] Type: feat/fix/docs/test/refactor
[ ] Scope: What was changed
[ ] Subject: Clear description (50 chars or less)
[ ] Body: What changed and why
[ ] Body: Breaking changes (if any)
[ ] Body: Related issues
[ ] Footer: References to docs/schemas
```

**Example Commit Message:**

```
feat: Add sub-second NMEA timestamp interpolation

Implement high-precision timestamp interpolation for NMEA sentences
to enable accurate GPS/sounder synchronization at vessel speeds up
to 10 knots.

Changes:
- Add NMEAInterpolator class with sub-second precision
- Add vector clock synchronization for multi-sensor timing
- Add unit and integration tests

Performance:
- Interpolation accuracy: <100ms at 10 knots
- Processing overhead: <1ms per sentence
- Test coverage: 95%

Breaking changes: None
Related to: vessel_agent_memory_schema.json level_0 success_metrics
Refs: issue #45 - GPS/sounder sync
```

---

## Quick Reference

**Critical Paths:**

```
Start Session → README → Memory Schema → Knowledge Base → Task
```

**Key Commands:**

```bash
# Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run tests
pytest tests/

# Run capture
python capture_daemon.py run

# Check status
python capture_daemon.py status

# Validate
python capture_daemon.py doctor
```

**Key Files:**

```
README.md                           # START HERE
vessel_agent_memory_schema.json    # CORE SCHEMA
vessel_agent_knowledge_base.md     # TECH KNOWLEDGE
vessel_agent_5year_vision.md       # STRATEGIC ROADMAP
ARCHITECTURE_DECISION_RECORD.md    # DECISIONS
README_IMPLEMENTATION.md            # IMPLEMENTATION GUIDE
```

**BMAD Levels Quick Reference:**

```
Level 0: Raw Bits          → >99.9% capture, <0.1% loss
Level 1: Physical Tensors   → <5m error, <0.5m precision
Level 2: Analytical Features → >70% accuracy, >80% precision
Level 3: Operational Intel   → >60% prediction, >15% improvement
Level 4: Strategic Knowledge → within 20% surveys, 3+ publications
```

**Success Criteria:**

- [ ] Code passes all tests
- [ ] Code meets coverage requirements
- [ ] Code is documented
- [ ] Code follows style guide
- [ ] Code meets performance requirements
- [ ] Architecture decisions recorded
- [ ] Knowledge base updated
- [ ] Roadmap updated

---

**End of AGENT_ONBOARDING.md**

*Version: 1.0.0*
*Created: 2026-07-25*
*Last Updated: 2026-07-25*
*Status: Active - Use for all agent session onboarding*
*Next Review: After Phase 0 completion*
