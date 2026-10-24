"""End-to-end run of the training and evaluation code on a small synthetic table.

The table is a synthetic test fixture (a weekly profile plus noise), not data.
It checks that run_target trains, tunes on validation only, blends, scores and
forecasts without error, and that the blend is exactly the documented formula.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
import pytest

from transit import config
from transit.data.manifest import study_dates
from transit.data.service import build_slots
from transit.features import build_features
from transit.models import lgbm, run


@pytest.fixture(scope="module")
def synthetic_table():
    rng = np.random.default_rng(1)
    rows = []
    for d in study_dates():
        for route, scale in (("A", 1.0), ("B", 2.5), ("C", 0.6)):
            for h in (6, 7, 8, 12, 17, 18):
                base = scale * (40 if h in (7, 8, 17, 18) else 15) * (0.5 if d.weekday() >= 5 else 1.0)
                b = float(max(0.0, base + rng.normal(0, 4)))
                rows.append({"service_date": pd.Timestamp(d), "route": route, "direction": "I",
                             "ts_hour": pd.Timestamp(d) + pd.Timedelta(hours=h), "boardings": b, "n_trips": 4,
                             "load_trip_peak_mean": b / 4, "n_malformed_trips": 0, "n_burst_events": 0})
    return pd.DataFrame(rows)


@pytest.fixture(scope="module")
def results(synthetic_table):
    mp = pytest.MonkeyPatch()
    mp.setattr(lgbm, "GRID", {k: v[:2] for k, v in lgbm.GRID.items()})
    mp.setattr(lgbm, "MAX_ROUNDS", 200)
    mp.setattr(lgbm, "BASE_PARAMS", {**lgbm.BASE_PARAMS, "min_data_in_leaf": 5})
    mp.setattr(run, "MODEL_DIR", config.ROOT / "models" / "_test")
    slots = build_slots(synthetic_table, dates=study_dates() + [config.END_DATE + timedelta(days=1)])
    out = {t: run.run_target(build_features(slots, t), t, lambda s: None) for t in run.TARGETS}
    mp.undo()
    return out


@pytest.mark.parametrize("target", list(run.TARGETS))
def test_run_target_produces_complete_results(results, target):
    res, va, te, fc = results[target]
    assert set(res["test"]) == {"ensemble", "model", "seasonal_naive", "dow4_mean", "hist_average"}
    assert all(np.isfinite(m["wape"]) for m in res["test"].values())
    assert res["rows"]["test"] == int(te["target"].notna().sum()) > 0
    assert res["blend"]["weight_on_lightgbm"] in run.BLEND_WEIGHTS
    assert len(fc) > 0 and fc["model"].notna().all()
    if target != "boardings":
        assert set(res["crowding_test"]) == {"midionibus", "basico", "padron", "articulado"}


@pytest.mark.parametrize("target", list(run.TARGETS))
def test_ensemble_is_the_documented_blend(results, target):
    res, va, te, _ = results[target]
    w = res["blend"]["weight_on_lightgbm"]
    np.testing.assert_allclose(te["ensemble"], w * te["model"] + (1 - w) * te["hist_average"])


def test_blend_weight_is_chosen_on_validation_not_test(results):
    res, va, _, _ = results["boardings"]
    by_w = {float(k): v for k, v in res["blend"]["valid_wape_by_weight"].items()}
    assert res["blend"]["weight_on_lightgbm"] == min(by_w, key=by_w.get)
    s = va[va["target"].notna()]
    w = res["blend"]["weight_on_lightgbm"]
    from transit.metrics import regression_metrics
    assert regression_metrics(s["target"], w * s["model"] + (1 - w) * s["hist_average"])["wape"] == \
        pytest.approx(by_w[w])


def test_learned_model_beats_last_week_on_a_learnable_pattern(results):
    res = results["boardings"][0]
    assert res["test"]["ensemble"]["wape"] < res["test"]["seasonal_naive"]["wape"]
