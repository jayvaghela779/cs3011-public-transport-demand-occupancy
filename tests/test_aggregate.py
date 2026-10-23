"""Unit tests for the aggregation step, on small hand-written stop events.

These frames are test fixtures written to exercise the code paths; they are
not observations and are never used for modelling.
"""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from transit.data.aggregate import BURST_BOARDINGS, aggregate_day, load_day
from transit.data.build import run_checks

DAY = date(2024, 3, 5)


def events(rows):
    cols = ["route", "direction", "trip_id", "stop_time", "n_boardings", "n_alighting", "loading"]
    df = pd.DataFrame(rows, columns=cols)
    df["stop_time"] = pd.to_datetime(df["stop_time"])
    df["pt_sequence"] = df.groupby("trip_id").cumcount() + 1
    for c in ["n_boardings", "n_alighting", "loading"]:
        df[c] = df[c].astype("float64")
    return df


@pytest.fixture
def two_trips():
    # Route 100, direction I: trip A has 3 stops at 07:xx, trip B has 2 stops
    # at 07:xx and 1 stop at 08:05. Route 200 has one stop at 07:30.
    return events([
        ("100", "I", "A", "2024-03-05 07:01", 4, 0, 4),
        ("100", "I", "A", "2024-03-05 07:10", 3, 1, 6),
        ("100", "I", "A", "2024-03-05 07:20", 0, 2, 4),
        ("100", "I", "B", "2024-03-05 07:40", 2, 0, 2),
        ("100", "I", "B", "2024-03-05 07:50", 5, 0, 7),
        ("100", "I", "B", "2024-03-05 08:05", 1, 3, 5),
        ("200", "V", "C", "2024-03-05 07:30", 1.5, 0, 1.5),
    ])


def row(agg, route, hour):
    sel = agg[(agg.route == route) & (agg.ts_hour == pd.Timestamp(f"2024-03-05 {hour}:00"))]
    assert len(sel) == 1
    return sel.iloc[0]


def test_sums_counts_and_loads(two_trips):
    agg, _ = aggregate_day(two_trips, DAY)
    r = row(agg, "100", "07")
    assert r.boardings == 14
    assert r.alightings == 3
    assert r.n_stop_events == 5
    assert r.n_trips == 2
    assert r.load_max == 7
    # trip A peaks at 6, trip B peaks at 7 within 07:00-08:00 -> mean 6.5
    assert r.load_trip_peak_mean == pytest.approx(6.5)
    assert row(agg, "100", "08").boardings == 1
    assert row(agg, "200", "07").boardings == pytest.approx(1.5)
    assert len(agg) == 3


def test_boardings_conserved_with_missing_load(two_trips):
    two_trips.loc[1, "loading"] = np.nan
    agg, stats = aggregate_day(two_trips, DAY)
    assert stats["boardings_raw"] == stats["boardings_aggregated"] == pytest.approx(16.5)
    assert stats["null_loading"] == 1
    assert row(agg, "100", "07").load_max == 7  # NaN ignored


def test_events_outside_service_window_are_dropped_and_counted(two_trips):
    extra = events([("100", "I", "Z", "2024-03-07 09:00", 9, 0, 9)])  # 2 days later
    agg, stats = aggregate_day(pd.concat([two_trips, extra], ignore_index=True), DAY)
    assert stats["rows_outside_window"] == 1
    assert stats["boardings_outside_window"] == 9
    assert agg.boardings.sum() == pytest.approx(16.5)


def test_after_midnight_events_keep_their_clock_hour(two_trips):
    late = events([("100", "I", "D", "2024-03-06 01:15", 2, 0, 2)])
    agg, stats = aggregate_day(pd.concat([two_trips, late], ignore_index=True), DAY)
    assert stats["rows_outside_window"] == 0
    assert (agg.ts_hour == pd.Timestamp("2024-03-06 01:00")).sum() == 1
    assert (agg.service_date == pd.Timestamp("2024-03-05")).all()


def test_burst_events_are_counted_not_removed(two_trips):
    big = events([("300", "I", "E", "2024-03-05 09:00", BURST_BOARDINGS + 50, 0, BURST_BOARDINGS + 50)])
    agg, stats = aggregate_day(pd.concat([two_trips, big], ignore_index=True), DAY)
    assert stats["burst_events"] == 1
    assert row(agg, "300", "09").n_burst_events == 1
    assert row(agg, "300", "09").boardings == BURST_BOARDINGS + 50


def test_trips_with_repeated_stop_sequence_are_counted(two_trips):
    two_trips.loc[1, "pt_sequence"] = 1  # trip A now visits sequence 1 twice
    _, stats = aggregate_day(two_trips, DAY)
    assert stats["trips_with_repeated_stop_sequence"] == 1


def test_negative_raw_value_is_reported_but_does_not_fail_if_aggregate_ok(two_trips):
    two_trips.loc[2, "n_alighting"] = -1  # trip A hour 07 alightings: 1 - 1 = 0
    agg, stats = aggregate_day(two_trips, DAY)
    checks = run_checks(agg, [stats], expected_days=1)
    assert stats["negative_values"] == 1
    assert checks["no_negative_aggregated_values"]["passed"]
    assert "1 negative raw" in checks["no_negative_aggregated_values"]["detail"]


def test_load_day_renames_hyphenated_sunt_columns(tmp_path):
    raw = pd.DataFrame({
        "route_short_name": ["100"], "direction_id": ["I"], "trip_id": ["A"], "pt_sequence": [1],
        "stop_time": ["2024-03-05 07:01:00"], "n-boardings": [1.0], "n-alighting": [0.0],
        "loading": [1.0], "vehicle": ["v1"],
    })
    path = tmp_path / "od-2024-03-05.parquet"
    raw.to_parquet(path)
    df = load_day(path)
    assert {"route", "direction", "n_boardings", "n_alighting"} <= set(df.columns)
    assert "vehicle" not in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["stop_time"])


def test_checks_detect_duplicate_keys_and_missing_days(two_trips):
    agg, stats = aggregate_day(two_trips, DAY)
    doubled = pd.concat([agg, agg], ignore_index=True)
    checks = run_checks(doubled, [stats], expected_days=2)
    assert not checks["unique_route_direction_hour"]["passed"]
    assert not checks["all_service_days_present"]["passed"]
    assert checks["boardings_conserved"]["passed"]


def test_checks_detect_lost_boardings(two_trips):
    agg, stats = aggregate_day(two_trips, DAY)
    stats = dict(stats, boardings_aggregated=stats["boardings_raw"] - 1)
    assert not run_checks(agg, [stats], expected_days=1)["boardings_conserved"]["passed"]
