"""Smoke tests: every dashboard page renders without an exception, and the
dashboard's numbers come from the same files the evaluation wrote."""

import json

import pandas as pd
import pytest

from transit import config
from transit.metrics import regression_metrics

METRICS = config.ROOT / "reports" / "metrics.json"
APP = str(config.ROOT / "app" / "streamlit_app.py")
PAGES = ["Forecast explorer", "Model comparison", "Crowding and capacity", "Next-day forecast",
         "Data and limitations"]

pytestmark = pytest.mark.skipif(not METRICS.exists(), reason="run python -m transit.models.run first")


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    at.sidebar.radio[0].set_value(page).run()
    assert not at.exception, at.exception
    assert any(page.split()[0].lower() in s.value.lower() for s in at.subheader)


def test_explorer_route_and_split_selection():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    at.radio[0].set_value("Validation, 8–14 Apr 2024").run()   # period selector on the explorer page
    assert not at.exception
    at.selectbox[0].set_value(at.selectbox[0].options[5]).run()
    assert not at.exception


@pytest.mark.parametrize("short", ["demand", "load"])
def test_reported_test_metrics_match_prediction_files(short):
    m = json.loads(METRICS.read_text(encoding="utf-8"))["targets"][short]["test"]
    df = pd.read_parquet(config.DATA_DIR / "predictions" / f"{short}_test.parquet")
    scored = df[df["target"].notna()]
    for k in ("ensemble", "model", "seasonal_naive", "dow4_mean", "hist_average"):
        re = regression_metrics(scored["target"], scored[k])
        assert re["n"] == m[k]["n"]
        assert re["wape"] == pytest.approx(m[k]["wape"], rel=1e-12)
        assert re["mae"] == pytest.approx(m[k]["mae"], rel=1e-12)


def test_missing_records_are_never_scored():
    df = pd.read_parquet(config.DATA_DIR / "predictions" / "demand_test.parquet")
    assert df.loc[df["status"] == "missing_record", "target"].isna().all()
    assert (df["status"] == "missing_record").sum() == 2797


def test_forecast_file_is_the_same_blend_as_evaluated():
    m = json.loads(METRICS.read_text(encoding="utf-8"))
    f = pd.read_parquet(config.DATA_DIR / "predictions" / f"forecast_{m['split']['forecast_demo']}.parquet")
    assert len(f) == m["forecast_rows"] > 0
    assert (f["demand_forecast"] >= 0).all() and (f["load_forecast"] >= 0).all()
    assert m["targets"]["demand"]["blend"]["weight_on_lightgbm"] in (0.0, 0.25, 0.5, 0.75, 1.0)


@pytest.mark.parametrize("short", ["demand", "load"])
def test_interval_coverage_matches_prediction_files(short):
    m = json.loads(METRICS.read_text(encoding="utf-8"))["targets"][short]
    if "intervals" not in m:
        pytest.skip("intervals not in this metrics.json")
    df = pd.read_parquet(config.DATA_DIR / "predictions" / f"{short}_test.parquet")
    assert (df["lo"] <= df["hi"]).all() and (df["lo"] >= 0).all()
    s = df[df["target"].notna()]
    inside = ((s["target"] >= s["lo"]) & (s["target"] <= s["hi"])).mean()
    assert inside == pytest.approx(m["intervals"]["test_calibrated"]["coverage"], rel=1e-12)
