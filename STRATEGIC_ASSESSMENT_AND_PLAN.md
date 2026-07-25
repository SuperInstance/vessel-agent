# Vessel Agent — Strategic Assessment & Plan

**Vessel:** F/V EILEEN (51' power troller, Southeast Alaska)
**Date:** 2026-07-25
**Author:** Agent session `claude/planning-research-r4xji4`
**Method:** Direct execution and measurement against the repository at `006df73`. Every claim below was reproduced, not inferred.
**Status:** Assessment — no production code changed in this commit.

---

## 0. Bottom line

The repository's founding principle is:

> *"Data captured in 2026 cannot be recreated in 2031. Capture now, analyze later."*

**The capture system does not run.** `capture_daemon.py` raises `NameError` on import. It has never
executed on any machine. The fishing season is in progress, and every day it stays broken is
permanent, unrecoverable loss of exactly the non-renewable resource the project exists to protect.

Meanwhile the repository contains ~600 KB of documentation across 21 files — six audience-specific
user guides, a 5-year roadmap through "Level 4 Strategic Knowledge," an architecture decision record,
and a play-test report scoring the repo 9.8/10. All of it describes a system that has never produced
a single byte of archived data.

This is the whole problem, and it has a clear shape: **effort has been spent on describing the system
instead of running it.** The plan in §4 is built around inverting that.

There is a second, deeper finding. Even if every crash were fixed, the storage design would still be
wrong — and wrong in a way that *violates the project's own founding principle*. The daemon discards
the raw Furuno bytes and persists a derived interpretation built on admitted guesswork. When the
actual FCV wire format is eventually understood, the season will not be reprocessable. §3 argues that
raw-first capture is the single highest-leverage change available, and that it follows directly from
principles the project already holds.

---

## 1. What I verified

Everything in this section is reproducible from a clean checkout. Commands are given.

### 1.1 The system cannot start

```
$ python3 -c "import capture_daemon"
NameError: name 'FurinoPacket' is not defined. Did you mean: 'FurunoPacket'?
```

The dataclass is `FurunoPacket` (`network_capture.py:44`). The name `FurinoPacket` — a one-letter
substitution — is used at `network_capture.py:233, 257, 264, 314, 356` and is defined nowhere in the
repository. Because line 233 is a function *annotation*, evaluated when the class body executes, the
module fails at **import**, not at call time. Nothing downstream of it can load.

The test suite does not collect. On a fresh checkout with only `pytest` installed:

```
$ python3 -m pytest tests/ -q
ERROR tests/test_network_capture.py - NameError: name 'FurinoPacket' is not defined
ERROR tests/test_storage.py         - NameError: name 'pa' is not defined
!!!! Interrupted: 2 errors during collection !!!!
```

The second error is a separate defect worth naming. `parquet_pipeline.py:29-35` wraps the pyarrow
import in `try/except ImportError` and prints *"Warning: pyarrow not available"*, which advertises
graceful degradation. It does not degrade: `-> pa.Table` annotations at lines 342, 365 and 395 are
evaluated when the class body executes, so the module hard-fails on import. The `PYARROW_AVAILABLE`
guard at line 168 that exists to raise a friendly error is therefore unreachable in the very case it
was written for.

Installing the declared dependencies clears that one and leaves the first:

```
$ pip install pyarrow h3 && python3 -m pytest tests/ -q
ERROR tests/test_network_capture.py - NameError: name 'FurinoPacket' is not defined
!!!! Interrupted: 1 error during collection !!!!
```

Of the modules that *do* collect, `test_nmea_interpolator.py` fails 6 of its 24 tests:

```
$ python3 -m pytest tests/test_nmea_interpolator.py -q
6 failed, 18 passed
```

The root cause of the NMEA failures is at `nmea_interpolator.py:121`, and it is labelled in the
source:

```python
return datetime.combine(today, timedelta(...).seconds() / 3600)  # Bug, need to fix
```

`timedelta.seconds` is an attribute, not a method; calling it raises `TypeError`. This is the time
parser. Every NMEA sentence that reaches it fails, so `parse_rmc` and `parse_gga` return `None` for
all input. **There is no position data path.**

`DOCUMENTATION_INDEX.md:290` states: *"Test Coverage: 4 test modules, all passing."* That statement
has never been true.

### 1.2 Silent corruption of the spatial anchor

This one is worse than a crash, because it does not crash.

`requirements.txt` pins `h3>=4.0.0`. In h3 v4, `latlng_to_cell` returns a **string**:

```
$ python3 -c "import h3; print(repr(h3.latlng_to_cell(56.3,-134.5,7)))"
'871d2539effffff'
```

`parquet_pipeline.py:125-126` does:

```python
h3_int = h3.latlng_to_cell(latitude, longitude, resolution)
return hex(h3_int)          # TypeError: 'str' object cannot be interpreted as an integer
```

The `except Exception` at line 127 swallows the `TypeError` and returns the *mock fallback*:
`f"{resolution:02x}{'0'*15}"` → `"07000000000000000"`.

Demonstrated across three widely separated positions:

```
$ python3 -c "from vessel_agent.storage.parquet_pipeline import lat_lon_to_h3
for p in [(56.3,-134.5),(57.9,-135.2),(0.0,0.0)]: print(p, lat_lon_to_h3(*p, 7))"
(56.3, -134.5) -> '07000000000000000'
(57.9, -135.2) -> '07000000000000000'
(0.0, 0.0)     -> '07000000000000000'
```

Every row ever written would carry that identical constant. The archive would look healthy, files
would grow, `files_created` would climb — and the spatial anchor, one of the three foundational
anchors the entire architecture rests on (time / location / source), would be a constant. Discovered
a season later, the data is unusable for anything spatial, which is nearly everything.

This is the most dangerous class of defect in the codebase: a bare `except` converting a hard failure
into plausible-looking garbage. That pattern deserves a dedicated audit.

**The test suite passes over this bug.** `tests/test_storage.py` has two H3 tests. One
(`test_lat_lon_to_h3_fallback`) patches `H3_AVAILABLE = False` before calling — so the real code path
is never exercised. The other (`test_h3_auto_fill`) asserts only:

```python
assert pipeline.acoustic_buffer[0].h3_index != ""
```

`"07000000000000000" != ""` is true, so the test passes while the archive fills with a constant. Both
tests are green. This is worth dwelling on: it is not that the tests are absent or failing here — it
is that they are shaped to pass rather than to detect, which is strictly more dangerous than having
no tests, because it produces confidence.

### 1.3 The storage path cannot survive a fishing day

`ParquetStoragePipeline.flush_acoustic` appends by **reading the entire day's file, concatenating in
memory, and rewriting it** (`parquet_pipeline.py:259-267`). `capture_daemon.py:174` calls `flush()`
every 100 cycles — every ~6.7 s at 15 Hz.

I measured the real cost by writing the repo's exact schema with pyarrow 25.0. Reproduce with
`python3 scripts/measure_storage_cost.py`, added in this commit:

| Quantity | Measured / derived |
|---|---|
| Parquet size, repo schema | **8.6 bytes/row** compressed (snappy) |
| Rows per 10-hour day (15 Hz × 100 bins) | **54,000,000** |
| Archive growth | **~460 MB/day**, ~46 GB per 100-day season |
| In-memory Arrow size | **156 bytes/row** |
| RAM to `read_table()` a full day | **8.4 GB** — and `concat_tables` peaks at **~16.8 GB** |
| Flushes per day | 5,400 |
| Bytes rewritten per day | **1.25 TB** |
| **Write amplification** | **~2,700×** |

Two independent failure modes follow.

**Memory.** Peak flush cost is ~2× the in-memory table, so the ceiling is reached at
`RAM / (2 × 156 B)` rows. On an 8 GB vessel PC that is **~4.7 hours** of capture; on 16 GB, ~9.5
hours. Either way it lands *inside* a fishing day — the daemon dies mid-trip, and because the failure
is an OOM during flush rather than at startup, it will look like it was working right up until the
data stops.

**Endurance.** 1.25 TB/day of rewrites is roughly 40 minutes/day of pure redundant I/O on a consumer
SSD, and burns write endurance ~2,700× faster than the data warrants.

Note also that `PERFORMANCE_REQUIREMENTS.md:93` budgets *"~80-130 MB/day (compressed)"*. That figure
correctly sizes the **raw UDP payload** (204 B × 15 Hz × 10 h = 110 MB/day). It does not describe what
the code writes, because the code explodes each ping into 100 rows with repeated string columns. The
design doc and the implementation are sizing two different systems.

### 1.4 The daemon's wiring was never executed

`capture_daemon.py:67`:

```python
self.interpolator = NMEAInterpolator(
    max_age_ms=config.NMEA["interpolation_method"],   # -> the string "linear"
)
```

A string is passed where milliseconds are expected. The correctly-named key
`NMEA["max_interpolation_age_ms"] = 2000` exists two lines below it in `config.py` and is **never read
by anything**. Downstream, `_interpolate_between` evaluates `max_age > self.max_age_ms` — `float > str`
— which raises `TypeError`. A single mock run would have surfaced this.

It is not an isolated case. Checking which config keys anything actually consumes:

| Key | Consumers outside `config.py` |
|---|---|
| `packet_loss_threshold_percent` | 0 |
| `max_interpolation_age_ms` | 0 |
| `ring_buffer_size` | 0 |
| `retention_days` | 0 |
| `rotation_interval_minutes` | 0 |
| `furuno_address` | 0 |
| entire `TIMEZERO` block | 0 |

Most of the configuration file is decorative.

### 1.5 Capture is not what the documentation says it is

The module docstring claims *"BPF filters and ring buffers for zero-copy packet processing."*
The implementation (`network_capture.py:163-168`) is a plain blocking `SOCK_DGRAM` socket bound to
`0.0.0.0:8000`.

- `bpf_filter` is stored on the instance and never applied — there is no pcap involvement at all.
- `RingBuffer` is instantiated at line 139 and **never touched by the capture path**. `get_packet`
  reads straight from the socket. The "lossless ring buffer" does not exist in the data flow.
- `RingBuffer` itself is self-contradictory: it uses `deque(maxlen=capacity)` (silently evicts oldest)
  *and* a manual full-check that returns `False` first, so the `maxlen` can never engage. Its
  docstring claims it "pre-allocates memory"; a `deque` does not.
- Timestamps use `int(datetime.now().timestamp() * 1e9)` (line 205). `datetime.now()` is naive local
  time — it will jump at DST and is not monotonic — and the float64 multiply quantizes to ~380 ns near
  current epoch values. For a system whose first principle is nanosecond time anchoring, the anchor is
  built on a lossy, DST-sensitive clock. `time.time_ns()` is exact and costs nothing.

**Unassessed operational risk:** binding UDP port 8000 may *steal* packets from TimeZero Professional.
If the Furuno unicasts, the first bound socket wins and the captain's plotter goes dark. If it
broadcasts or multicasts, `SO_REUSEADDR`/`SO_REUSEPORT` can share. Nothing in the repo establishes
which. This must be settled at the dock, not underway — a capture system that blinds the plotter
mid-trip will be uninstalled immediately and permanently.

### 1.6 Documented claims not supported by any artifact

| Claim | Location | Reality |
|---|---|---|
| "Test Coverage: 4 test modules, all passing" | `DOCUMENTATION_INDEX.md:290` | 2 modules do not import; 6 tests fail |
| "Python Backend: ✅ Complete (85%)" | `DOCUMENTATION_INDEX.md:303` | Does not import |
| "27,000× headroom **with Python**" | `DOCUMENTATION_INDEX.md:331`; `ADR:46, 400` | The 27,000× in `PERFORMANCE_REQUIREMENTS.md:125` is *gigabit-Ethernet link capacity* vs. packet rate. It says nothing about Python. The ADR's own processing estimate is "5-10×" (`ADR:175`) — the two numbers are 3,000× apart and sit 225 lines apart in the same document |
| Repo scores 9.8/10, "APPROVED FOR EXTERNAL AGENT CONSUMPTION" | `PLAY_TEST_RESULTS.md` | The "play-test" only counted lines and quoted files; it never ran code |
| Canonical NMEA examples | 16 occurrences across 6 docs | Checksums are wrong (see below) |
| `DIRECTOR_ORCHESTRATION.md` listed as "Added" | `DOCUMENTATION_INDEX.md:389` | File does not exist |
| `tzpro/lifecycle_manager.py` — "deploy this file" | `phase0_quick_start.md` | File does not exist |
| `tzrawcapturesystem1.md` — indexed as doc #8 | `README.md:78` | File does not exist |

On the NMEA examples — the sentence used as *the* worked example throughout the documentation:

```
$GPRMC,210230,A,3855.4487,N,09446.0071,W,0.0,076.2,210324,,,A*47
```

Its checksum is `47`. The correct checksum is `68`. The GGA example claims `47`; correct is `49`.
Even the doctest inside `validate_nmea_checksum` asserts `True` for a sentence whose checksum is `08`.
A student following `USER_GUIDE_STUDENT.md` will find that valid-looking sentences are all rejected.

The pattern is consistent and diagnostic: **these artifacts were written, not run.**

---

## 2. Diagnosis

The individual bugs are cheap to fix. A day of focused work clears §1.1, §1.2, §1.4, §1.5. That is
not the interesting part of this assessment, and fixing them without addressing what follows would
leave the project in the same position in a month.

The failure is a **process** failure with three reinforcing parts:

**1. Documentation was treated as evidence of progress.** 21 documents, six audience variants of
substantially the same content, a five-year roadmap to "Level 4 Strategic Knowledge" — produced
against a Level 0 that has never executed. Each document made the project *feel* more complete while
making it no more capable. Six audience guides is a mature-product deliverable; this is a pre-alpha
that cannot import.

**2. Verification was simulated rather than performed.** `PLAY_TEST_RESULTS.md` is the clearest
instance. It presents itself as an external agent cloning and evaluating the repo, complete with
terminal transcripts and a 9.8/10 score. Its "tests" consist of `wc -l` and quoting file contents.
Had it run `pytest` — the one command that its own "Test Coverage: 4 test modules, all passing"
claim implies — the entire assessment would have collapsed. **A test report that cannot fail is not a
test report.**

The same shape recurs one level down, inside the tests themselves. The H3 tests in §1.2 are green
while the function they cover returns a constant for every input on Earth: one patches the real code
path out of existence, the other asserts only that the result is non-empty. The tests were written to
be satisfied, not to be informative. This matters more than the count of failing tests, because a
green suite is what future sessions will trust.

**3. The BMAD rule was stated and then not enforced.** *"Level 0 must be bulletproof before Level 1
begins"* is in `README.md`. Levels 1–4 have detailed roadmaps, schemas, and success metrics. Level 0
does not import. The methodology was documented rather than applied — which is precisely the same
error as (1), one level up.

The through-line: **artifacts about the work substituted for the work.** The correction is not more
process. It is a single hard gate — nothing is "done" until it has run on real data — plus deleting
the work that shouldn't have been started yet.

---

## 3. Strategic reframing: capture raw, derive later

This is the most consequential recommendation in this document.

The daemon currently reads a Furuno packet, converts it into 100 `AcousticDataPoint` rows, writes
those, and **discards the original bytes.** Each derived row embeds three assumptions:

| Assumption | Where | Assessment |
|---|---|---|
| Each depth bin is 1 ms after the previous | `capture_daemon.py:157` | **Wrong.** Bins are range samples within a *single* ping — microseconds apart, determined by range and sound speed. At 1 ms/bin a 100-bin ping spans 100 ms, longer than the 66 ms ping interval, so consecutive pings' bins interleave. The time anchor is not merely imprecise; it is scrambled. |
| `backscatter_db = raw / 10.0` | `capture_daemon.py:163` | Arbitrary and uncalibrated. Produces *positive* dB from the mock's values; Sv is conventionally −70 to −30 dB. The stated "Sv calibration <1 dB variance" metric has nothing to measure against. |
| The FCV packet layout | `network_capture.py:236-241` | The source comment says it plainly: *"This is a basic parser. Real Furuno parsing requires spec."* The format is not known. |

So the pipeline discards ground truth and persists a guess. If the guess is wrong — and by the
authors' own admission the third one is unverified — **the season is unrecoverable.** That is the
exact outcome the "non-renewable resource" principle exists to prevent. The implementation
contradicts the project's founding principle.

**The principle, applied honestly, prescribes the fix.** "Capture now, analyze later" means the
durable artifact is the **raw byte stream**, not an interpretation of it:

```
Furuno UDP  ──► raw packet log   (payload verbatim + capture timestamp)  ← the archive of record
NMEA serial ──► raw sentence log (line verbatim + capture timestamp)     ← the archive of record
                        │
                        └──► derived Parquet tables — rebuildable, disposable, versioned
```

Everything this buys:

- **Assumption-free.** No parse, no interpolation, no calibration between the wire and the disk. Nothing
  can be silently corrupted (§1.2) because nothing is interpreted.
- **Reprocessable forever.** When the FCV format is understood — from the spec, a vendor contact, or
  reverse-engineering against TimeZero's own display — every past trip can be re-derived correctly.
  This is the difference between a season of data and a season of guesses.
- **~110 MB/day instead of ~460 MB/day** (§1.3), and append-only, so write amplification is ~1× rather
  than ~2,700×. Both problems in §1.3 dissolve; they were artifacts of persisting the derived form.
- **Radically simpler to make correct.** The critical path becomes: receive bytes → stamp with
  `time.time_ns()` → append. That is a few hundred lines that can be made genuinely reliable and
  tested against real capture files, versus ~3,600 lines of interdependent parsing that currently
  cannot import.
- **Derived tables become cheap and safe to be wrong about.** A rebuildable view can be regenerated
  after a bug fix. That is exactly the property the current archive lacks.

The 5-year vision, the multi-panel interface, the agent ecosystem — none of it is invalidated. It is
*deferred*, and it becomes buildable later against a complete, honest archive instead of a corrupted
partial one. The Level 1–4 work in the roadmap is largely reprocessing work, and reprocessing is
precisely what raw-first enables.

**Recommended format:** append-only length-delimited records, one file per hour, with a sidecar
manifest (SHA-256, record count, first/last timestamp). Standard `pcap` is a reasonable alternative
for the UDP side and buys tcpdump/Wireshark compatibility for free; a plain custom framing is simpler
if NMEA and UDP share one writer. Either is fine — the decisive property is *verbatim payload plus a
trustworthy timestamp, appended, never rewritten*. This is a decision to make deliberately in Stage 0
(§7, D1), not to drift into.

---

## 4. The plan

Sequenced by *irreversibility of loss*, not by architectural tidiness. The season is running.

### Stage 0 — Get honest bytes on disk (target: days, not weeks)

The only stage with real time pressure. Goal: **a working raw recorder on EILEEN**, nothing more.

1. **Scope down to the critical path.** Raw UDP recorder + raw NMEA recorder + hourly rotation +
   manifest. No parsing, no interpolation, no H3, no Parquet, no quality scoring. Those are Stage 2.
2. **Fix the clock first.** `time.time_ns()`, UTC, monotonic sequence counter per stream. The
   timestamp is the one thing that cannot be recovered later by reprocessing — if it is wrong, raw
   bytes don't save you. Everything else in this plan is recoverable; this is not.
3. **Settle the TimeZero coexistence question at the dock** (§1.5). Determine empirically whether the
   Furuno unicasts, broadcasts, or multicasts, and confirm with TimeZero running that both receive.
   **This gates deployment** — it is the risk most likely to get the system permanently uninstalled.
4. **Prove it on real hardware before trusting it.** Success = a 6-hour dockside run producing
   files that a separate reader tool can re-read completely, with byte counts and packet counts that
   reconcile, and TimeZero unaffected throughout.
5. **Keep the measurement harness.** `scripts/measure_storage_cost.py` (added with this assessment)
   produces §1.3's numbers on demand. Re-run it whenever the schema changes, so storage projections
   stay measured rather than asserted — the 4× gap between the design doc and the implementation
   existed precisely because nobody ran the numbers against the real schema.

**Gate: no Stage 1 until Stage 0 has recorded a real trip and the files have been read back intact.**

### Stage 1 — Trust the recorder (weeks 2–3, overlapping the season)

Purpose: make it something that runs unattended on a boat, because an unreliable recorder produces
gaps that are just as unrecoverable as no recorder.

- Crash-only design: assume power loss at any instant; never lose more than the current record.
- Supervised restart (systemd / Windows service) with capture resuming automatically.
- Disk-space guard with a defined policy at capacity — **decide in advance** whether to stop or
  overwrite oldest, and make it explicit (§7, D2).
- One-glance liveness signal the captain can check in three seconds: is it recording, how much disk
  is left. Not a dashboard.
- Automated off-vessel copy when in port. **A single-copy archive of non-renewable data is not an
  archive.** Vessel electronics fail; a fire or a drive failure ends the project.

**Gate: one full trip captured with no gaps and verified byte-identical off-vessel.**

### Stage 2 — Derived layer, rebuildable (weeks 4–8, no season pressure)

Now, and only now, is derivation worth building — offline, against recorded files, re-runnable.

- A `derive` command: raw files in, Parquet out. Pure function, deterministic, versioned with a
  `derivation_version` column so every row can be traced to the code that produced it.
- Fix the NMEA parser properly (§1.1) and **correct the checksums in all six documents** (§1.6).
  Validate against a real recorded sentence stream, not hand-written examples.
- H3 against the v4 string API, and **remove the fallback-on-exception pattern** (§1.2). At this
  layer, a parse failure must be loud. Derivation can afford to fail; capture cannot.
- Batch writes per partition — no read-modify-write. Since derivation is now offline, the §1.3
  amplification problem simply does not arise.
- Attack the FCV format deliberately: correlate recorded packets against TimeZero's own display, and
  pursue the vendor spec. Until the format is known, derived acoustic values remain provisional and
  should be labelled as such in the schema.

### Stage 3 — Reassess (month 3)

With a real archive and a working derivation pipeline, revisit the 5-year roadmap against evidence
rather than intention. Most of Levels 1–2 will be far cheaper than estimated (it is reprocessing);
the UI and agent work in Levels 3–4 should be re-scoped against what the data actually supports.

---

## 5. What to stop

Explicitly, because continuing these is the main risk to the plan:

- **Stop writing documentation.** The repo has ~600 KB of docs and 0 bytes of captured data. No new
  document until Stage 0 ships. This assessment is the last one that should be written for a while,
  and it exists only because the gap between claims and reality had to be established with evidence.
- **Stop the audience-guide expansion.** Six guides describing a system that does not run is six
  documents that will need rewriting once it does.
- **Retract or annotate `PLAY_TEST_RESULTS.md`.** As written it certifies a broken repository as
  9.8/10 and "APPROVED FOR EXTERNAL AGENT CONSUMPTION." Anyone — human or agent — who trusts it is
  actively misled. This is the single most damaging file in the repository.
- **Correct the status claims** in `README.md` and `DOCUMENTATION_INDEX.md` (§1.6). "Level 0: 60%"
  and "Backend Complete (85%)" describe code that does not import. An agent resuming this project
  will make bad decisions from them — which is not hypothetical, it is what this session had to work
  around.
- **Stop treating the ADR as settled.** Its conclusion (Python is adequate) is probably right, but it
  rests on a misattributed headroom number (§1.6) and on a performance analysis of a system that was
  never profiled because it was never run. Right answer, unearned. Keep the decision; note the
  reasoning needs redoing once there is something to measure.
- **Do not start the TypeScript/Electron layer.** `ADR` Phase 1 schedules 4–6 weeks of UI work. There
  is nothing to visualize.

---

## 6. Risk register

| # | Risk | Severity | Likelihood now | Mitigation |
|---|---|---|---|---|
| R1 | Season data permanently lost while capture is broken | **Critical** | **Occurring** | Stage 0, days not weeks |
| R2 | Capture steals UDP from TimeZero; system uninstalled | **Critical** | Unknown — unassessed | Dockside test gates deployment (Stage 0.3) |
| R3 | Single-copy archive lost to drive failure/fire/flooding | **Critical** | Moderate over a season | Off-vessel replication (Stage 1) |
| R4 | Silent corruption produces plausible garbage | High | **Confirmed present** (§1.2) | Raw-first (§3); ban fallback-on-exception in capture |
| R5 | Derived-only archive unreprocessable once format is known | High | **Confirmed present** (§3) | Raw-first archive of record |
| R6 | OOM mid-trip from read-modify-write flush | High | **Confirmed present** (§1.3) | Eliminated by Stage 0 scope |
| R7 | Clock wrong (naive local time, DST, ~380 ns quantization) | High | **Confirmed present** (§1.5) | `time.time_ns()` UTC, Stage 0.2 |
| R8 | Future sessions trust the inaccurate status docs | Moderate | High | §5 corrections |
| R9 | Effort resumes flowing to documentation | Moderate | High | §5, enforced by the Stage gates |

R1 is the only one with a deadline set by something other than us.

---

## 7. Decisions needed from Casey

Four, and the first two block Stage 0:

- **D1 — Raw format.** `pcap` (Wireshark/tcpdump compatible, standard, slightly awkward for the
  serial NMEA side) vs. a simple length-delimited append log (one writer for both streams, trivial to
  verify). *Recommendation: length-delimited append log with a sidecar manifest — one code path for
  both streams, and the reader is twenty lines.*
- **D2 — Disk-full policy.** Stop recording, or overwrite oldest? Given "non-renewable," stopping and
  alerting loudly is probably right, but it is your call and it must be decided before deployment,
  not discovered at sea.
- **D3 — Deployment target.** Same Windows box as TimeZero, or a dedicated small Linux machine on the
  network? A separate box eliminates R2 entirely and is the more robust answer if a spare NIC/port is
  available. Worth the hardware.
- **D4 — `PLAY_TEST_RESULTS.md`.** Delete, or keep with a correction header? *Recommendation: keep it
  with a prominent header explaining what it got wrong and why* — it is a useful record of exactly the
  failure mode this plan is designed to prevent.

---

## Appendix: reproducing this assessment

Order matters — two findings are only visible before the optional dependencies are installed.

```bash
# --- fresh checkout, pytest only ---
pip install pytest
python3 -m pytest tests/ -q          # 2 collection errors: FurinoPacket, and `pa`
                                     # (the broken pyarrow degradation path)   §1.1

# --- with declared dependencies present ---
pip install pyarrow h3
python3 -c "import capture_daemon"                     # NameError: FurinoPacket   §1.1
python3 -m pytest tests/ -q                            # 1 collection error        §1.1
python3 -m pytest tests/test_nmea_interpolator.py -q   # 6 failed, 18 passed       §1.1
python3 -m pytest tests/test_storage.py -q             # 8 passed — over a broken
                                                       # H3 path                   §1.2
python3 -c "from vessel_agent.storage.parquet_pipeline import lat_lon_to_h3
print(lat_lon_to_h3(56.3,-134.5,7), lat_lon_to_h3(0,0,7))"   # identical constants §1.2
python3 -c "import vessel_agent.config" && ls -d 'C:'  # creates a literal C: dir  below
```

The last one is its own small bug: `config.py:216-219` runs `validate_config()` at import time, which
`mkdir -p`s the hardcoded Windows paths at `config.py:79,160`. On Linux or macOS, merely importing the
config creates a directory literally named `C:` in the working directory. Imports should not have
filesystem side effects.

Storage measurements (§1.3) were produced with pyarrow 25.0 by writing the exact schema from
`_acoustic_to_arrow` at 150,000 rows and extrapolating:

```bash
python3 scripts/measure_storage_cost.py               # defaults: 10 h day, 8 GB RAM
python3 scripts/measure_storage_cost.py --ram-gb 16   # sensitivity check
```

`scripts/` and this document are the only files added by this assessment. No module under
`vessel_agent/` was modified — the defects above are all still present as described.

---

*Assessment version 1.0.0 — 2026-07-25*
*Scope: assessment and plan only. No production code modified.*
*Supersedes the status claims in `README.md`, `DOCUMENTATION_INDEX.md`, and `PLAY_TEST_RESULTS.md`
where they conflict.*
