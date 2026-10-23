"""Build the route x direction x hour table and its quality report.

    python -m transit.data.build

Reads the verified raw files from data/raw/sunt_od/ (run transit.data.download
first) and writes:

    data/processed/route_hour.parquet    the modelling table
    data/processed/quality_report.json   per-day statistics and check results

Exits with an error if any quality check fails.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from transit import __version__, config
from transit.data.aggregate import BURST_BOARDINGS, KEYS, WINDOW_HOURS, aggregate_day, load_day
from transit.data.manifest import od_filename, study_dates

TABLE_NAME = "route_hour.parquet"
REPORT_NAME = "quality_report.json"
CONSERVATION_TOL = 1e-9  # relative


def run_checks(table: pd.DataFrame, per_day: list[dict], expected_days: int) -> dict:
    checks = {}

    def add(name: str, passed: bool, detail: str) -> None:
        checks[name] = {"passed": bool(passed), "detail": detail}

    n_dup = int(table.duplicated(subset=KEYS).sum())
    add("unique_route_direction_hour", n_dup == 0,
        f"{n_dup} duplicate (route, direction, ts_hour) keys")

    n_days = int(table["service_date"].nunique())
    add("all_service_days_present", n_days == expected_days,
        f"{n_days} of {expected_days} service days present")

    worst = max(abs(d["boardings_raw"] - d["boardings_aggregated"]) / max(1.0, d["boardings_raw"])
                for d in per_day)
    add("boardings_conserved", worst <= CONSERVATION_TOL,
        f"largest relative difference between raw and aggregated boardings: {worst:.2e}")

    neg_raw = sum(d["negative_values"] for d in per_day)
    neg_out = int((table[["boardings", "alightings", "load_max", "load_trip_peak_mean"]] < 0).to_numpy().sum())
    add("no_negative_values", neg_raw == 0 and neg_out == 0,
        f"{neg_raw} negative raw values, {neg_out} negative aggregated values")

    lost = sum(d["boardings_outside_window"] for d in per_day)
    total = sum(d["boardings_raw"] for d in per_day) + lost
    add("few_events_outside_window", lost <= 1e-4 * total,
        f"{sum(d['rows_outside_window'] for d in per_day)} stop events outside the "
        f"{WINDOW_HOURS} h service window ({lost:.1f} boardings)")
    return checks


def build(raw_dir: Path = config.RAW_DIR, out_dir: Path = config.PROCESSED_DIR) -> tuple[pd.DataFrame, dict]:
    days = study_dates()
    tables, per_day = [], []
    for i, day in enumerate(days, 1):
        path = raw_dir / od_filename(day)
        if not path.exists():
            raise FileNotFoundError(f"{path} not found. Run: python -m transit.data.download")
        agg, stats = aggregate_day(load_day(path), day)
        tables.append(agg)
        per_day.append(stats)
        print(f"[{i}/{len(days)}] {day}  {stats['rows_in']:>7} events -> {stats['rows_out']:>5} route-hours")

    table = pd.concat(tables, ignore_index=True).sort_values(KEYS, kind="stable").reset_index(drop=True)
    checks = run_checks(table, per_day, expected_days=len(days))

    report = {
        "generated_by": "python -m transit.data.build",
        "package_version": __version__,
        "source": {"repository": config.SUNT_REPO, "commit": config.SUNT_COMMIT,
                   "first_date": days[0].isoformat(), "last_date": days[-1].isoformat(),
                   "n_days": len(days)},
        "parameters": {"burst_boardings_threshold": BURST_BOARDINGS, "window_hours": WINDOW_HOURS},
        "summary": {
            "stop_events_in": int(sum(d["rows_in"] for d in per_day)),
            "route_hour_rows": int(len(table)),
            "routes": int(table["route"].nunique()),
            "route_directions": int(table[["route", "direction"]].drop_duplicates().shape[0]),
            "boardings_total": float(table["boardings"].sum()),
            "burst_events_total": int(sum(d["burst_events"] for d in per_day)),
            "max_load": float(np.nanmax(table["load_max"].to_numpy())),
            "route_hours_with_missing_load": int(table["load_max"].isna().sum()),
        },
        "checks": checks,
        "all_checks_passed": all(c["passed"] for c in checks.values()),
        "per_day": per_day,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_parquet(out_dir / TABLE_NAME, index=False, compression="zstd")
    with open(out_dir / REPORT_NAME, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    return table, report


def main() -> None:
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    table, report = build()
    s = report["summary"]
    print(f"\n{s['route_hour_rows']} route-hour rows, {s['routes']} routes, "
          f"{s['boardings_total']:,.0f} boardings")
    for name, c in report["checks"].items():
        print(f"  {'PASS' if c['passed'] else 'FAIL'}  {name}: {c['detail']}")
    print(f"Wrote {config.PROCESSED_DIR / TABLE_NAME} and {REPORT_NAME}")
    if not report["all_checks_passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
