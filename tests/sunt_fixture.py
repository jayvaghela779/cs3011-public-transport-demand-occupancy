"""Helpers that write tiny SUNT-shaped parquet files for tests.

Column names and types match the real SUNT OD files (category direction_id and
trip_id, int16 pt_sequence, float32 measures, string timestamps). The values
are hand-written test fixtures, not observations.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def sunt_frame(rows: list[tuple]) -> pd.DataFrame:
    """rows: (route, direction, trip_id, pt_sequence, stop_time, boardings, alighting, loading)."""
    cols = ["route_short_name", "direction_id", "trip_id", "pt_sequence", "stop_time",
            "n-boardings", "n-alighting", "loading"]
    df = pd.DataFrame(rows, columns=cols)
    df["route_short_name"] = df["route_short_name"].astype(str)
    df["direction_id"] = df["direction_id"].astype("category")
    df["trip_id"] = df["trip_id"].astype("category")
    df["pt_sequence"] = df["pt_sequence"].astype("int16")
    df["stop_time"] = df["stop_time"].astype(str)
    for c in ["n-boardings", "n-alighting", "loading"]:
        df[c] = df[c].astype("float32")
    # Columns present in real files but unused by the pipeline
    df["vehicle"] = "v1"
    df["stop_id"] = pd.Series(range(len(df)), dtype="int32")
    return df


def write_day(raw_dir: Path, day: str, rows: list[tuple]) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"od-{day}.parquet"
    sunt_frame(rows).to_parquet(path, index=False)
    return path
