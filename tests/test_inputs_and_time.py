"""Real SUNT column types, missing values and time handling."""

from datetime import date

import numpy as np
import pandas as pd
import pytest
from sunt_fixture import write_day

from transit.data.aggregate import aggregate_day, load_day

DAY = date(2024, 3, 5)


def test_categorical_sunt_types_give_same_result_as_strings(tmp_path):
    rows = [
        ("100", "I", "A", 1, "2024-03-05 07:01:00", 4, 0, 4),
        ("100", "I", "A", 2, "2024-03-05 07:30:00", 2, 1, 5),
        ("100", "V", "B", 1, "2024-03-05 07:10:00", 3, 0, 3),
    ]
    df = load_day(write_day(tmp_path, "2024-03-05", rows))
    assert df["direction"].dtype == object or pd.api.types.is_string_dtype(df["direction"])
    agg, _ = aggregate_day(df, DAY)
    # Categorical groupers must not create empty route x direction combinations
    assert len(agg) == 2
    assert agg.set_index("direction").loc["I", "boardings"] == pytest.approx(6)
    assert agg["n_malformed_trips"].tolist() == [0, 0]


def test_all_missing_loads_give_nan_not_zero(tmp_path):
    rows = [
        ("100", "I", "A", 1, "2024-03-05 07:01:00", 4, 0, np.nan),
        ("100", "I", "A", 2, "2024-03-05 07:20:00", 1, 0, np.nan),
    ]
    agg, stats = aggregate_day(load_day(write_day(tmp_path, "2024-03-05", rows)), DAY)
    assert agg.loc[0, "boardings"] == pytest.approx(5)
    assert np.isnan(agg.loc[0, "load_max"])
    assert np.isnan(agg.loc[0, "load_trip_peak_mean"])
    assert np.isnan(stats["max_load"])
    assert stats["null_loading"] == 2


def test_unparseable_stop_time_is_counted_and_dropped(tmp_path):
    rows = [
        ("100", "I", "A", 1, "2024-03-05 07:01:00", 4, 0, 4),
        ("100", "I", "A", 2, "not a time", 9, 0, 13),
    ]
    agg, stats = aggregate_day(load_day(write_day(tmp_path, "2024-03-05", rows)), DAY)
    assert stats["null_stop_time"] == 1
    assert stats["rows_outside_window"] == 1
    assert stats["boardings_outside_window"] == pytest.approx(9)
    assert agg["boardings"].sum() == pytest.approx(4)


@pytest.mark.parametrize("stamp, hour", [
    ("2024-03-05 07:59:59", "2024-03-05 07:00"),
    ("2024-03-05 08:00:00", "2024-03-05 08:00"),
    ("2024-03-06 00:00:00", "2024-03-06 00:00"),
    ("2024-03-06 05:59:59", "2024-03-06 05:00"),  # last second inside the 30 h window
])
def test_hour_boundaries(tmp_path, stamp, hour):
    rows = [("100", "I", "A", 1, stamp, 1, 0, 1)]
    agg, stats = aggregate_day(load_day(write_day(tmp_path, "2024-03-05", rows)), DAY)
    assert stats["rows_outside_window"] == 0
    assert agg.loc[0, "ts_hour"] == pd.Timestamp(hour)


def test_window_end_is_exclusive(tmp_path):
    rows = [("100", "I", "A", 1, "2024-03-06 06:00:00", 1, 0, 1)]
    _, stats = aggregate_day(load_day(write_day(tmp_path, "2024-03-05", rows)), DAY)
    assert stats["rows_outside_window"] == 1


def test_malformed_trip_is_flagged_on_its_route_hours_only(tmp_path):
    rows = [
        ("100", "I", "A", 1, "2024-03-05 07:01:00", 4, 0, 4),
        ("100", "I", "A", 1, "2024-03-05 07:05:00", 2, 0, 6),   # repeats sequence 1
        ("100", "I", "A", 2, "2024-03-05 08:10:00", 0, 1, 5),
        ("100", "I", "B", 1, "2024-03-05 07:30:00", 3, 0, 3),   # well-formed
        ("200", "V", "C", 1, "2024-03-05 07:30:00", 3, 0, 3),
    ]
    agg, stats = aggregate_day(load_day(write_day(tmp_path, "2024-03-05", rows)), DAY)
    flags = agg.set_index(["route", "ts_hour"])["n_malformed_trips"]
    assert flags[("100", pd.Timestamp("2024-03-05 07:00"))] == 1
    assert flags[("100", pd.Timestamp("2024-03-05 08:00"))] == 1
    assert flags[("200", pd.Timestamp("2024-03-05 07:00"))] == 0
    assert stats["trips_with_repeated_stop_sequence"] == 1
    assert stats["route_hours_with_malformed_trips"] == 2
