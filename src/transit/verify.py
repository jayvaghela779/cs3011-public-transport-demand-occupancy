"""Check that a rerun reproduced the committed results.

    python -m transit.verify                      # compare with the committed files
    python -m transit.verify OLD.json NEW.json    # compare any two metrics files

With no arguments, the route-hour table (data/processed/route_hour.parquet) is
compared cell by cell with the committed one, and every number in
reports/metrics.json is compared with the committed file, except the run time.
LightGBM runs with a fixed seed and deterministic mode, so a rerun on the same
package versions should match to rounding; differences above the tolerance
are listed and the command exits with status 1.
"""

from __future__ import annotations

import io
import json
import math
import subprocess
import sys
from pathlib import Path

import pandas as pd

from transit.config import ROOT

VOLATILE = {"runtime_seconds"}
TOLERANCE = 1e-6   # relative, on every number


def flatten(obj, prefix: str = "") -> dict:
    """{'a.b.0': value} for every leaf of nested dicts and lists."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in VOLATILE:
                continue
            out.update(flatten(v, f"{prefix}{k}."))
        return out
    if isinstance(obj, list):
        out = {}
        for i, v in enumerate(obj):
            out.update(flatten(v, f"{prefix}{i}."))
        return out
    return {prefix.rstrip("."): obj}


def differences(old: dict, new: dict, tol: float = TOLERANCE) -> list[str]:
    a, b = flatten(old), flatten(new)
    diffs = [f"only in old: {k}" for k in sorted(a.keys() - b.keys())]
    diffs += [f"only in new: {k}" for k in sorted(b.keys() - a.keys())]
    for k in sorted(a.keys() & b.keys()):
        x, y = a[k], b[k]
        if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
            if math.isnan(x) and math.isnan(y):
                continue          # e.g. WAPE of rows whose actual total is 0
            if not math.isclose(x, y, rel_tol=tol, abs_tol=tol):
                diffs.append(f"{k}: {x} -> {y}")
        elif x != y:
            diffs.append(f"{k}: {x!r} -> {y!r}")
    return diffs


def committed(path: str) -> bytes:
    """Contents of `path` as committed in git HEAD."""
    return subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT,
                          capture_output=True, check=True).stdout


def table_differences(old: pd.DataFrame, new: pd.DataFrame) -> str | None:
    """None if the two tables hold the same rows, columns and values."""
    try:
        pd.testing.assert_frame_equal(old.reset_index(drop=True), new.reset_index(drop=True),
                                      check_dtype=False, rtol=TOLERANCE)
    except AssertionError as e:
        return str(e).splitlines()[0]
    return None


def main(argv: list[str]) -> int:
    if len(argv) == 2:
        old, new = (json.loads(Path(p).read_text()) for p in argv)
    else:
        table = "data/processed/route_hour.parquet"
        t_old = pd.read_parquet(io.BytesIO(committed(table)))
        t_new = pd.read_parquet(ROOT / table)
        problem = table_differences(t_old, t_new)
        if problem:
            print(f"{table} differs from the committed table: {problem}")
            return 1
        print(f"{table}: all {t_new.shape[0]:,} rows x {t_new.shape[1]} columns match.")
        old = json.loads(committed("reports/metrics.json"))
        new = json.loads((ROOT / "reports" / "metrics.json").read_text())
    diffs = differences(old, new)
    n = len(flatten(old))
    if diffs:
        print(f"{len(diffs)} of {n} values differ:")
        print("\n".join(f"  {d}" for d in diffs[:50]))
        return 1
    print(f"Reproduced: all {n} values match (relative tolerance {TOLERANCE:g}; run time ignored).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
