"""Train, tune and evaluate the demand and estimated-load models.

    python -m transit.models.run

Protocol (decision D3):
  1. Fit each LightGBM configuration on TRAIN (1 Mar - 7 Apr 2024) with early
     stopping on VALIDATION (8 - 14 Apr). Choose the configuration with the
     lowest validation WAPE. Run a feature-group ablation on validation.
  2. Refit the chosen configuration on TRAIN + VALIDATION for the same number
     of rounds.
  3. Score that model and the baselines once on TEST (15 - 28 Apr).
  4. Forecast 29 Apr 2024 (no actuals; a demonstration of a real next-day run).

Only observed slots are scored; missing records are never scored (D8).
Writes reports/metrics.json, reports/tuning_*.csv, data/predictions/*.parquet.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import timedelta

import numpy as np
import pandas as pd

from transit import __version__, config
from transit.crowding import (BASE_CAPACITY, CAPACITY_SCENARIOS, LEVELS, SOURCE, THRESHOLDS,
                              crowding_level, level_shares)
from transit.data.manifest import study_dates
from transit.data.service import MIN_TRAIN_DAYS, REGULAR_SHARE, build_slots
from transit.features import CALENDAR_FEATURES, ID_FEATURES, build_features, model_feature_names
from transit.metrics import classification_metrics, regression_metrics
from transit.models import baselines, lgbm

TARGETS = {"boardings": "demand", "load_trip_peak_mean": "load"}
BASELINES = ["seasonal_naive", "dow4_mean", "hist_average"]
FORECAST_DATE = config.END_DATE + timedelta(days=1)
REPORTS = config.ROOT / "reports"
PRED_DIR = config.DATA_DIR / "predictions"
MODEL_DIR = config.ROOT / "models"

PERIODS = [("early 03-05", 3, 5), ("am peak 06-08", 6, 8), ("midday 09-15", 9, 15),
           ("pm peak 16-19", 16, 19), ("evening 20-23", 20, 23), ("night 00-02", 24, 26)]


def split_of(d: pd.Series) -> pd.Series:
    out = pd.Series("test", index=d.index, dtype="object")
    out[d <= pd.Timestamp(config.VALID_END)] = "valid"
    out[d <= pd.Timestamp(config.TRAIN_END)] = "train"
    out[d > pd.Timestamp(config.END_DATE)] = "forecast"
    return out


def period_of(h: pd.Series) -> pd.Series:
    out = pd.Series("", index=h.index, dtype="object")
    for name, lo, hi in PERIODS:
        out[(h >= lo) & (h <= hi)] = name
    return out


def segment_metrics(df: pd.DataFrame, by: str, pred: str) -> dict:
    return {str(k): regression_metrics(g["target"], g[pred]) for k, g in df.groupby(by, observed=True)}


def crowding_results(df: pd.DataFrame, preds: list[str]) -> dict:
    out = {}
    for name, cap in CAPACITY_SCENARIOS.items():
        truth = crowding_level(df["target"], cap)
        res = {"capacity": cap, "actual_shares": level_shares(df["target"], cap)}
        for p in preds:
            res[p] = classification_metrics(truth, crowding_level(df[p], cap), LEVELS)
        out[name] = res
    return out


def run_target(X: pd.DataFrame, target: str, log) -> tuple[dict, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    feats = model_feature_names(target)
    X = X.assign(split=split_of(X["service_date"]))
    scored = X[X["target"].notna() & X["split"].isin(["train", "valid", "test"])]
    tr, va, te = (scored[scored["split"] == s] for s in ("train", "valid", "test"))
    log(f"[{target}] scored rows: train {len(tr)}, valid {len(va)}, test {len(te)}")

    # 1. tuning on validation
    tuning, best = [], None
    for cfg in lgbm.GRID[target]:
        t0 = time.time()
        m = lgbm.fit_with_early_stopping(tr, va, feats, cfg)
        met = regression_metrics(va["target"], lgbm.predict(m, va, feats))
        row = {**cfg, "best_iteration": int(m.best_iteration), "seconds": round(time.time() - t0, 1), **met}
        tuning.append(row)
        log(f"  {cfg} -> valid WAPE {met['wape']:.4f} MAE {met['mae']:.3f} ({row['best_iteration']} rounds)")
        if best is None or met["wape"] < best[1]["wape"]:
            best = (cfg, met, m)
    cfg, _, tuned = best
    rounds = int(tuned.best_iteration)

    # ablation on validation with the chosen configuration
    groups = {
        "calendar + route only": ID_FEATURES + CALENDAR_FEATURES,
        "+ same-hour history (lags, means)": ID_FEATURES + CALENDAR_FEATURES + [
            f for f in feats if f.startswith("y_")],
        "all features": feats,
    }
    ablation = {}
    for gname, gf in groups.items():
        m = lgbm.fit_with_early_stopping(tr, va, gf, cfg)
        ablation[gname] = regression_metrics(va["target"], lgbm.predict(m, va, gf))
        log(f"  ablation {gname}: valid WAPE {ablation[gname]['wape']:.4f}")

    # 2. refit on train + valid, 3. score once on test
    trva = pd.concat([tr, va])
    final = lgbm.fit_fixed_rounds(trva, feats, cfg, rounds)
    MODEL_DIR.mkdir(exist_ok=True)
    final.save_model(str(MODEL_DIR / f"{TARGETS[target]}_lgbm.txt"))

    # Predict every slot of the validation and test weeks (including missing
    # records, so the dashboard can show them), but score only observed ones.
    full = {}
    sources = {}
    for key, model, med_src in (("valid", tuned, tr), ("test", final, trva)):
        f = X[X["split"] == key].copy()
        f["model"] = lgbm.predict(model, f, feats)
        med = baselines.hour_medians(med_src)
        for b in BASELINES:
            p, src = baselines.predict(f, b, med)
            f[b] = p
            sources[key] = {**sources.get(key, {}), b: src[f["target"].notna()].value_counts().to_dict()}
        full[key] = f
    va = full["valid"][full["valid"]["target"].notna()].copy()
    te = full["test"][full["test"]["target"].notna()].copy()
    preds = ["model"] + BASELINES

    res = {
        "target": target,
        "features": feats,
        "chosen_config": {**cfg, "rounds": rounds},
        "tuning": tuning,
        "ablation_valid": ablation,
        "rows": {"train": len(tr), "valid": len(va), "test": len(te)},
        "baseline_fallbacks": sources,
        "valid": {p: regression_metrics(va["target"], va[p]) for p in preds},
        "test": {p: regression_metrics(te["target"], te[p]) for p in preds},
    }
    imp = pd.Series(final.feature_importance("gain"), index=feats)
    res["feature_importance_gain_share"] = (imp / imp.sum()).sort_values(ascending=False).round(5).to_dict()

    # error analysis on test
    te = te.assign(period=period_of(te["service_hour"]))
    vol = tr.groupby(["route", "direction"], observed=True)["target"].mean()
    terc = pd.qcut(vol, 3, labels=["low", "middle", "high"])
    te = te.merge(terc.rename("volume_tercile").reset_index(), on=["route", "direction"], how="left")
    seg = {
        "period": {p: segment_metrics(te, "period", p) for p in ("model", "seasonal_naive")},
        "daytype": {p: segment_metrics(te, "daytype", p) for p in ("model", "seasonal_naive")},
        "volume_tercile": {p: segment_metrics(te, "volume_tercile", p) for p in ("model", "seasonal_naive")},
        "regular_cell": {p: segment_metrics(te, "regular", p) for p in ("model", "seasonal_naive")},
    }
    day = te.groupby("service_date").apply(
        lambda g: pd.Series({"model_wape": regression_metrics(g["target"], g["model"])["wape"],
                             "sn_wape": regression_metrics(g["target"], g["seasonal_naive"])["wape"],
                             "rows": len(g)}), include_groups=False)
    seg["by_day"] = {d.strftime("%Y-%m-%d"): r.to_dict() for d, r in day.iterrows()}
    rd_err = (te.assign(abs_err=(te["model"] - te["target"]).abs())
              .groupby(["route", "direction"], observed=True)
              .agg(abs_err=("abs_err", "sum"), actual=("target", "sum"), rows=("target", "size")))
    rd_err["wape"] = rd_err["abs_err"] / rd_err["actual"].replace(0, np.nan)
    rd_err["share_of_total_error"] = rd_err["abs_err"] / rd_err["abs_err"].sum()
    seg["worst_route_directions"] = [
        {"route": r, "direction": d, **{k: float(v) for k, v in row.items()}}
        for (r, d), row in rd_err.sort_values("abs_err", ascending=False).head(10).iterrows()]
    zero = te[te["target"] == 0]
    if len(zero):
        seg["actual_zero_rows"] = {p: regression_metrics(zero["target"], zero[p]) for p in preds}
    if target != "boardings":
        te["has_burst"] = te["n_burst_events"] > 0
        seg["burst_hours"] = {p: segment_metrics(te, "has_burst", p) for p in preds}
        res["crowding_test"] = crowding_results(te, preds)
        res["crowding_valid"] = crowding_results(va, preds)
    res["segments_test"] = seg

    # 4. next-day forecast (no actuals)
    fc = X[X["split"] == "forecast"]
    fc = fc.assign(model=lgbm.predict(final, fc, feats))
    return res, full["valid"], full["test"], fc


def main() -> None:
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    t_start = time.time()
    log = lambda s: print(s, flush=True)  # noqa: E731
    table = pd.read_parquet(config.PROCESSED_DIR / "route_hour.parquet")
    dates = study_dates() + [FORECAST_DATE]
    slots = build_slots(table, dates=dates)
    log(f"slots: {len(slots)} ({slots['status'].value_counts().to_dict()})")

    REPORTS.mkdir(exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    keep = ["route", "direction", "service_date", "service_hour", "ts_hour", "daytype", "status", "regular",
            "n_burst_events", "target", "model"] + BASELINES
    results = {
        "generated_by": "python -m transit.models.run",
        "package_version": __version__,
        "split": {"train": [str(config.START_DATE), str(config.TRAIN_END)],
                  "valid": [str(config.TRAIN_END + timedelta(days=1)), str(config.VALID_END)],
                  "test": [str(config.VALID_END + timedelta(days=1)), str(config.END_DATE)],
                  "forecast_demo": str(FORECAST_DATE)},
        "service_policy": {"regular_share": REGULAR_SHARE, "min_train_days": MIN_TRAIN_DAYS},
        "crowding": {"base_capacity": BASE_CAPACITY, "scenarios": CAPACITY_SCENARIOS,
                     "thresholds_load_factor": THRESHOLDS, "levels": LEVELS, "source": SOURCE},
        "targets": {},
    }
    forecasts = []
    for target, short in TARGETS.items():
        X = build_features(slots, target)
        res, va, te, fc = run_target(X, target, log)
        results["targets"][short] = res
        va[keep].to_parquet(PRED_DIR / f"{short}_valid.parquet", index=False, compression="zstd")
        te[keep].to_parquet(PRED_DIR / f"{short}_test.parquet", index=False, compression="zstd")
        forecasts.append(fc[["route", "direction", "service_date", "service_hour", "ts_hour", "model"]]
                         .rename(columns={"model": f"{short}_forecast"}))
        pd.DataFrame(res["tuning"]).to_csv(REPORTS / f"tuning_{short}.csv", index=False)
    f = forecasts[0].merge(forecasts[1], on=["route", "direction", "service_date", "service_hour", "ts_hour"])
    f.to_parquet(PRED_DIR / f"forecast_{FORECAST_DATE}.parquet", index=False, compression="zstd")
    results["forecast_rows"] = int(len(f))
    results["runtime_seconds"] = round(time.time() - t_start, 1)
    with open(REPORTS / "metrics.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, default=float)
        fh.write("\n")
    for short, r in results["targets"].items():
        log(f"\n{short} TEST: " + ", ".join(f"{p} WAPE {m['wape']:.4f} MAE {m['mae']:.3f}"
                                            for p, m in r["test"].items()))
    log(f"done in {results['runtime_seconds']} s")


if __name__ == "__main__":
    main()
