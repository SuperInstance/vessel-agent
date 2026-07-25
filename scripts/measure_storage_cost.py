#!/usr/bin/env python3
"""Measure the real storage cost of the current acoustic schema.

Produces the numbers cited in STRATEGIC_ASSESSMENT_AND_PLAN.md section 1.3.
Storage projections in this project should be measured, not asserted --- the
existing design docs and the implementation disagree by roughly 4x because one
sized the raw packet stream and the other writes one row per depth bin.

    python3 scripts/measure_storage_cost.py

Requires pyarrow. Writes a temporary file and removes it.
"""

import argparse
import os
import tempfile

import pyarrow as pa
import pyarrow.parquet as pq

# Operating assumptions for F/V EILEEN. Override on the command line.
PING_RATE_HZ = 15.0
BINS_PER_PING = 100
FISHING_HOURS = 10.0
FLUSH_EVERY_N_CYCLES = 100  # capture_daemon.py:174
RAW_PACKET_BYTES = 204      # Furuno UDP payload, per PERFORMANCE_REQUIREMENTS.md


def build_sample(n_rows):
    """Rebuild the exact column set from ParquetStoragePipeline._acoustic_to_arrow.

    Kept in sync by hand: if that schema changes, change this too, or the
    projection stops describing the real archive.
    """
    base_ns = 1_753_000_000_000_000_000
    return pa.table({
        "timestamp_ns": [base_ns + i * 1_000_000 for i in range(n_rows)],
        "latitude": [56.3 + (i % 1000) * 1e-6 for i in range(n_rows)],
        "longitude": [-134.5 + (i % 1000) * 1e-6 for i in range(n_rows)],
        "h3_index": ["871d2539effffff"] * n_rows,
        "altitude": [None] * n_rows,
        "vessel_id": ["US-AK-FVCATCHER-01"] * n_rows,
        "device_id": ["FURUNO-FCV585"] * n_rows,
        "source_port": [8000] * n_rows,
        "depth_range": [100.0] * n_rows,
        "depth_bin": [i % BINS_PER_PING for i in range(n_rows)],
        "backscatter_db": [10.0 + (i % 500) * 0.01 for i in range(n_rows)],
        "frequency": [50000] * n_rows,
        "speed_knots": [8.0] * n_rows,
        "heading": [90.0] * n_rows,
        "data_quality": [0.75] * n_rows,
        "interpolation_method": ["linear"] * n_rows,
    })


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample-rows", type=int, default=150_000,
                    help="rows written to derive per-row cost (default: 150000)")
    ap.add_argument("--hours", type=float, default=FISHING_HOURS,
                    help=f"fishing hours per day (default: {FISHING_HOURS})")
    ap.add_argument("--ram-gb", type=float, default=8.0,
                    help="vessel PC RAM, for the OOM estimate (default: 8)")
    ap.add_argument("--compression", default="snappy")
    args = ap.parse_args()

    table = build_sample(args.sample_rows)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as fh:
        path = fh.name
    try:
        pq.write_table(table, path, compression=args.compression)
        disk_bytes_per_row = os.path.getsize(path) / args.sample_rows
    finally:
        os.unlink(path)

    mem_bytes_per_row = table.nbytes / args.sample_rows

    rows_per_second = PING_RATE_HZ * BINS_PER_PING
    rows_per_day = rows_per_second * 3600 * args.hours
    day_bytes = rows_per_day * disk_bytes_per_row

    # Every flush reads the whole day file back and rewrites it
    # (parquet_pipeline.py:259-267), so total bytes written grows quadratically.
    flushes = PING_RATE_HZ * 3600 * args.hours / FLUSH_EVERY_N_CYCLES
    rewritten = day_bytes * (flushes + 1) / 2

    # concat_tables holds the old table and the combined one at once.
    peak_bytes_per_row = 2 * mem_bytes_per_row
    oom_rows = args.ram_gb * 1e9 / peak_bytes_per_row
    oom_hours = oom_rows / rows_per_second / 3600

    raw_day = RAW_PACKET_BYTES * PING_RATE_HZ * 3600 * args.hours

    print(f"measured on {args.sample_rows:,} rows, pyarrow {pa.__version__}, "
          f"{args.compression}\n")
    print(f"  parquet on disk      {disk_bytes_per_row:6.1f} B/row")
    print(f"  arrow in memory      {mem_bytes_per_row:6.0f} B/row\n")

    print(f"projected for a {args.hours:g}-hour day at "
          f"{PING_RATE_HZ:g} Hz x {BINS_PER_PING} bins:\n")
    print(f"  rows/day             {rows_per_day:>14,.0f}")
    print(f"  archive growth       {day_bytes / 1e9:>14.2f} GB/day")
    print(f"  RAM to read a day    {rows_per_day * mem_bytes_per_row / 1e9:>14.1f} GB")
    print(f"    peak during concat {rows_per_day * peak_bytes_per_row / 1e9:>14.1f} GB")
    print(f"  flushes/day          {flushes:>14,.0f}")
    print(f"  bytes rewritten      {rewritten / 1e12:>14.2f} TB/day")
    print(f"  write amplification  {rewritten / day_bytes:>14,.0f}x\n")

    print(f"  OOM on a {args.ram_gb:g} GB machine after ~{oom_hours:.1f} h of capture")
    print(f"  raw UDP payload for comparison: {raw_day / 1e6:.0f} MB/day "
          f"({day_bytes / raw_day:.1f}x smaller than the derived archive)")


if __name__ == "__main__":
    main()
