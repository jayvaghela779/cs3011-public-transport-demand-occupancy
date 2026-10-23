"""No-leakage, lag correctness, baseline fallbacks, metrics and crowding levels.

The tables here are small synthetic test fixtures, not observations.
"""

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from transit.crowding import CAPACITY_SCENARIOS, crowding_level
from transit.data.service import build_slots
from transit.features import build_features, model_feature_names
from transit.metrics import classification_metrics, regression_metrics
from transit.models import baselines

DAYS = [date(2024, 3, 1) + timedelta(days=i) for i in range(42)]
TRAIN_END = DAYS[27]


def fixture_table(scale_from: date | None = None, factor: float = 1.0) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    rows = []
    for d in DAYS:
        for route in ("A", "B"):
            for h in (7, 8, 17):
                b = float(rng.integers(5, 60)) * (2 if h in (7, 17) else 1)
                if scale_from and d >= scale_from:
                    b *= factor
                rows.append({"service_date": pd.Timestamp(d), "route": route, "direction": "I",
                             "ts_hour": pd.Timestamp(d) + pd.Timedelta(hours=h), "boardings": b,
                             "n_trips": 3, "load_trip_peak_mean": b / 3, "n_malformed_trips": 0,
                             "n_burst_events": 0})
    return pd.DataFrame(rows)


def features(table, target="boardings"):
    X = build_features(build_slots(table, TRAIN_END, DAYS), target)
    return X.set_index(["route", "direction", "service_date", "service_hour"]).sort_index()


@pytest.mark.parametrize("target", ["boardings", "load_trip_peak_mean"])
def test_features_for_day_d_ignore_day_d_and_later(target):
    d = DAYS[35]
    a = features(fixture_table(), target)
    b = features(fixture_table(scale_from=d, factor=50.0), target)
    cols = [c for c in model_feature_names(target) if c not in ("route", "direction", "service_hour")]
    day = pd.Timestamp(d)
    left = a.xs(day, level="service_date")[cols]
    right = b.xs(day, level="service_date")[cols]
    pd.testing.assert_frame_equal(left, right)
    # ...while the target itself did change, so the perturbation was real
    assert not np.allclose(a.xs(day, level="service_date")["target"],
                           b.xs(day, level="service_date")["target"])


def test_lag7_and_lag1_are_exact_earlier_values():
    t = fixture_table()
    X = features(t)
    d, h = pd.Timestamp(DAYS[20]), 8
    val = lambda day: t[(t.route == "A") & (t.service_date == day)  # noqa: E731
                        & (t.ts_hour == day + pd.Timedelta(hours=h))]["boardings"].item()
    row = X.loc[("A", "I", d, h)]
    assert row["y_lag7"] == val(d - pd.Timedelta(days=7))
    assert row["y_lag1"] == val(d - pd.Timedelta(days=1))


def test_hist_daytype_mean_uses_only_earlier_same_type_days():
    t = fixture_table()
    X = features(t)
    d = pd.Timestamp(DAYS[10])  # 11 Mar 2024, Monday
    earlier = [x for x in DAYS[:10] if x.weekday() < 5]
    vals = [t[(t.route == "B") & (t.ts_hour == pd.Timestamp(x) + pd.Timedelta(hours=17))]["boardings"].item()
            for x in earlier]
    assert X.loc[("B", "I", d, 17), "y_hist_daytype"] == pytest.approx(np.mean(vals))


def test_missing_records_are_nan_in_lags_not_zero():
    t = fixture_table()
    gone = pd.Timestamp(DAYS[30])
    t = t[~((t.route == "A") & (t.service_date == gone) & (t.ts_hour == gone + pd.Timedelta(hours=8)))]
    X = features(t)
    assert np.isnan(X.loc[("A", "I", gone, 8), "target"])
    assert np.isnan(X.loc[("A", "I", gone + pd.Timedelta(days=7), 8), "y_lag7"])


def test_baseline_fallback_chain_covers_every_row():
    X = pd.DataFrame({"y_lag7": [10.0, np.nan, np.nan, np.nan],
                      "y_mean_dow4": [9.0, 8.0, np.nan, np.nan],
                      "y_hist_daytype": [7.0, 6.0, 5.0, np.nan],
                      "y_roll7": [4.0, 3.0, 2.0, np.nan],
                      "service_hour": [8, 8, 8, 8]})
    med = pd.Series({8: 42.0})
    p, src = baselines.predict(X, "seasonal_naive", med)
    assert p.tolist() == [10.0, 6.0, 5.0, 42.0]
    assert src.tolist() == ["y_lag7", "y_hist_daytype", "y_hist_daytype", "hour_median"]
    p, _ = baselines.predict(X, "dow4_mean", med)
    assert p.tolist() == [9.0, 8.0, 5.0, 42.0]


def test_regression_metrics_known_values():
    m = regression_metrics([10, 0, 30], [12, 1, 27])
    assert m["mae"] == pytest.approx(2.0)
    assert m["rmse"] == pytest.approx(np.sqrt((4 + 1 + 9) / 3))
    assert m["wape"] == pytest.approx(6 / 40)
    assert m["bias"] == pytest.approx(0.0)
    with pytest.raises(ValueError):
        regression_metrics([1, np.nan], [1, 2])


def test_crowding_levels_and_scenarios():
    assert crowding_level([34.9, 35, 55.9, 56, 200], 70).tolist() == ["low", "medium", "medium", "high", "high"]
    assert crowding_level([np.nan], 70)[0] is None
    assert CAPACITY_SCENARIOS["basico"] == 70
    m = classification_metrics(["low", "high", "high"], ["low", "high", "low"], ["low", "medium", "high"])
    assert m["per_class"]["high"]["recall"] == pytest.approx(0.5)
    assert m["confusion"]["matrix"][2] == [1, 0, 1]
