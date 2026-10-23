"""Checks on the committed processed table. Skipped if it has not been built."""

import json

import pandas as pd
import pytest

from transit import config
from transit.data.aggregate import KEYS

TABLE = config.PROCESSED_DIR / "route_hour.parquet"
REPORT = config.PROCESSED_DIR / "quality_report.json"

pytestmark = pytest.mark.skipif(not TABLE.exists(), reason="run python -m transit.data.build first")


@pytest.fixture(scope="module")
def table():
    return pd.read_parquet(TABLE)


@pytest.fixture(scope="module")
def report():
    with open(REPORT, encoding="utf-8") as f:
        return json.load(f)


def test_report_matches_pinned_source(report):
    assert report["source"]["commit"] == config.SUNT_COMMIT
    assert report["source"]["n_days"] == 59
    assert report["all_checks_passed"]


def test_keys_unique_and_days_complete(table):
    assert not table.duplicated(subset=KEYS).any()
    assert table["service_date"].nunique() == 59
    assert table["service_date"].min() == pd.Timestamp(config.START_DATE)
    assert table["service_date"].max() == pd.Timestamp(config.END_DATE)


def test_table_agrees_with_report(table, report):
    s = report["summary"]
    assert len(table) == s["route_hour_rows"]
    assert table["boardings"].sum() == pytest.approx(s["boardings_total"], rel=1e-12)


def test_no_negative_values(table):
    cols = ["boardings", "alightings", "n_stop_events", "n_trips", "load_max", "load_trip_peak_mean"]
    assert (table[cols].fillna(0) >= 0).all().all()


def test_trip_peak_mean_never_exceeds_hour_max(table):
    t = table.dropna(subset=["load_max", "load_trip_peak_mean"])
    assert (t["load_trip_peak_mean"] <= t["load_max"] + 1e-9).all()


# Regression pins: the committed table must reproduce these figures from the
# first verified build (24 Oct 2026). If a code change moves them, the change
# must be explained in docs/DECISIONS.md and these numbers updated on purpose.
EXPECTED = {
    "route_hour_rows": 541_611,
    "routes": 410,
    "route_directions": 713,
    "boardings_total": 51_353_180.0,
    "stop_events_in": 37_600_997,
    "trips_with_repeated_stop_sequence": 222,
    "route_hours_with_malformed_trips": 116,
    "burst_events_total": 2_685,
}


@pytest.mark.parametrize("key", list(EXPECTED))
def test_summary_matches_pinned_regression_values(report, key):
    got = report["summary"][key]
    if isinstance(EXPECTED[key], float):
        assert got == pytest.approx(EXPECTED[key], abs=1.0)
    else:
        assert got == EXPECTED[key]


def test_malformed_route_hours_are_flagged_in_table(table):
    assert int((table["n_malformed_trips"] > 0).sum()) == EXPECTED["route_hours_with_malformed_trips"]
    bad = table[table["n_malformed_trips"] > 0]
    assert set(bad["service_date"].dt.strftime("%Y-%m-%d")) == {"2024-04-02", "2024-04-03"}
