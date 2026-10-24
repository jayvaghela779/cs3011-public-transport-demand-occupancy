# Validation-only experiments. The test weeks are not touched.
import numpy as np, pandas as pd, time
from transit import config
from transit.data.manifest import study_dates
from transit.data.service import build_slots
from transit.features import build_features, model_feature_names, CELL
from transit.metrics import regression_metrics
from transit.models import lgbm, baselines
from transit.models.run import split_of
table = pd.read_parquet(config.PROCESSED_DIR / "route_hour.parquet")
slots = build_slots(table)
out = []
for target in ["boardings", "load_trip_peak_mean"]:
    X = build_features(slots, target).assign(split=lambda d: split_of(d["service_date"]))
    # history count feature: number of earlier observed same-daytype days in the cell
    f = X[CELL + ["daytype", "service_date"]].copy(); f["_o"] = np.arange(len(f)); f["_n"] = X["target"].notna().astype(float)
    f = f.sort_values(CELL + ["daytype", "service_date"])
    f["hist_n"] = f.groupby(CELL + ["daytype"], sort=False)["_n"].cumsum() - f["_n"]
    X["y_hist_n"] = f.sort_values("_o")["hist_n"].to_numpy()
    X["resid"] = X["target"] - X["y_hist_daytype"]
    sc = X[X.target.notna()]
    tr, va = sc[sc.split == "train"], sc[sc.split == "valid"]
    feats = model_feature_names(target)
    cfg = {"objective": "regression_l1", "num_leaves": 63}
    hist_va = baselines.predict(va, "hist_average", baselines.hour_medians(tr))[0]
    out.append((target, "hist_average baseline", regression_metrics(va.target, hist_va)["wape"], None))
    def run(name, trd, fts, resid=False, cfg=cfg):
        t0 = time.time()
        a, b = trd.copy(), va.copy()
        if resid:
            a = a[a.y_hist_daytype.notna()]; a["target"] = a["resid"]
            b2 = b[b.y_hist_daytype.notna()].copy(); b2["target"] = b2["resid"]
            m = lgbm.fit_with_early_stopping(a, b2, fts, cfg)
            raw = m.predict(b[fts], num_iteration=m.best_iteration)
            p = np.clip(np.where(b.y_hist_daytype.notna(), b.y_hist_daytype.fillna(0) + raw, hist_va), 0, None)
        else:
            m = lgbm.fit_with_early_stopping(a, b, fts, cfg); p = lgbm.predict(m, b, fts)
        w = regression_metrics(b.target, p)["wape"]
        out.append((target, name, w, m.best_iteration)); print(target, name, round(w, 4), m.best_iteration, f"{time.time()-t0:.0f}s", flush=True)
    run("v1 (reference)", tr, feats)
    run("+ y_hist_n", tr, feats + ["y_hist_n"])
    run("+ y_hist_n, train rows with >=3 history days", tr[tr.y_hist_n >= 3], feats + ["y_hist_n"])
    run("residual on hist_average + y_hist_n", tr, feats + ["y_hist_n"], resid=True)
    run("residual, >=3 history days", tr[tr.y_hist_n >= 3], feats + ["y_hist_n"], resid=True)
    run("residual, >=3 days, 15 leaves", tr[tr.y_hist_n >= 3], feats + ["y_hist_n"], resid=True,
        cfg={"objective": "regression_l1", "num_leaves": 15})
pd.DataFrame(out, columns=["target", "variant", "valid_wape", "best_iteration"]).to_csv(
    "reports/archive/experiments_validation_v2.csv", index=False)
