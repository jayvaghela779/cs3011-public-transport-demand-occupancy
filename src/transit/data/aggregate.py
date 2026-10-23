"""Turn one day of SUNT OD stop events into a route x direction x hour table.

Input (one row per vehicle stop event): route, direction, trip, stop_time,
boardings, inferred alightings and estimated load after boardings.

Output (one row per route, direction and clock hour of stop_time):

    boardings            sum of boardings at all stop events in the hour
    alightings           sum of inferred alightings in the hour
    n_stop_events        number of stop events in the hour
    n_trips              number of distinct trips with a stop event in the hour
    load_max             highest estimated on-board load at any stop event
    load_trip_peak_mean  mean over trips of each trip's highest estimated load
                         within the hour ("a typical bus's peak load")
    n_burst_events       stop events with more than BURST_BOARDINGS boardings

Loads are SUNT's estimates from fare-card trip chaining, not measured occupancy.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

KEYS = ["route", "direction", "ts_hour"]

RAW_COLUMNS = ["route_short_name", "direction_id", "trip_id", "pt_sequence", "stop_time",
               "n-boardings", "n-alighting", "loading"]

# Stop events with more boardings than this are counted as possible burst
# validations (SUNT paper: mobile turnstiles occasionally register many at once).
# They are counted, not removed, so total demand is preserved.
BURST_BOARDINGS = 100.0

# A service day's file runs from about 03:45 to about 02:15 the next morning.
# Stop events outside [service_date 00:00, service_date + 30 h) are treated as
# timestamp errors and dropped (and counted in the quality report).
WINDOW_HOURS = 30


def load_day(path: Path) -> pd.DataFrame:
    """Read one SUNT OD parquet file and normalise names and types."""
    df = pd.read_parquet(path, columns=RAW_COLUMNS)
    df = df.rename(columns={
        "route_short_name": "route",
        "direction_id": "direction",
        "n-boardings": "n_boardings",
        "n-alighting": "n_alighting",
    })
    for c in ["route", "direction", "trip_id"]:
        df[c] = df[c].astype(str)
    df["stop_time"] = pd.to_datetime(df["stop_time"], errors="coerce")
    for c in ["n_boardings", "n_alighting", "loading"]:
        df[c] = df[c].astype("float64")
    return df


def aggregate_day(df: pd.DataFrame, service_date: date) -> tuple[pd.DataFrame, dict]:
    """Aggregate one service day. Returns the table and per-day quality stats."""
    start = pd.Timestamp(service_date)
    in_window = df["stop_time"].ge(start) & df["stop_time"].lt(start + pd.Timedelta(hours=WINDOW_HOURS))
    dropped = df[~in_window]
    d = df[in_window].copy()
    d["ts_hour"] = d["stop_time"].dt.floor("h")
    d["is_burst"] = (d["n_boardings"] > BURST_BOARDINGS).astype("int64")

    g = d.groupby(KEYS, sort=True)
    agg = pd.DataFrame({
        "boardings": g["n_boardings"].sum(),
        "alightings": g["n_alighting"].sum(),
        "n_stop_events": g.size(),
        "n_trips": g["trip_id"].nunique(),
        "load_max": g["loading"].max(),
        "n_burst_events": g["is_burst"].sum(),
    })
    trip_peak = d.groupby(KEYS + ["trip_id"], sort=True)["loading"].max()
    agg["load_trip_peak_mean"] = trip_peak.groupby(level=KEYS).mean()
    agg = agg.reset_index()
    agg.insert(0, "service_date", start)

    raw_in_window = float(d["n_boardings"].sum())
    # A well-formed trip visits each stop sequence number once. A few SUNT trips
    # repeat sequence numbers with different timestamps, which breaks the load
    # chain (one case even has a negative alighting). They are counted here.
    seq_counts = df.groupby(["trip_id", "pt_sequence"], sort=False).size()
    repeated_trips = seq_counts[seq_counts > 1].index.get_level_values("trip_id").unique()
    stats = {
        "date": service_date.isoformat(),
        "rows_in": int(len(df)),
        "rows_outside_window": int(len(dropped)),
        "boardings_outside_window": float(dropped["n_boardings"].sum()),
        "null_stop_time": int(df["stop_time"].isna().sum()),
        "null_boardings": int(df["n_boardings"].isna().sum()),
        "null_alighting": int(df["n_alighting"].isna().sum()),
        "null_loading": int(df["loading"].isna().sum()),
        "negative_values": int((d[["n_boardings", "n_alighting", "loading"]] < 0).to_numpy().sum()),
        "routes": int(d["route"].nunique()),
        "trips": int(d["trip_id"].nunique()),
        "trips_with_repeated_stop_sequence": int(len(repeated_trips)),
        "rows_out": int(len(agg)),
        "boardings_raw": raw_in_window,
        "boardings_aggregated": float(agg["boardings"].sum()),
        "burst_events": int((d["n_boardings"] > BURST_BOARDINGS).sum()),
        "max_load": float(np.nanmax(d["loading"].to_numpy())) if len(d) else float("nan"),
        "first_stop_time": str(d["stop_time"].min()),
        "last_stop_time": str(d["stop_time"].max()),
    }
    return agg, stats
