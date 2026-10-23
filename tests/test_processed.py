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
