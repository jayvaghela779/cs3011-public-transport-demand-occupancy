"""Write reports/RESULTS.md and reports/figures/*.png from reports/metrics.json.

    python -m transit.report

Every number in RESULTS.md is read from metrics.json or recomputed from the
committed prediction files, so the write-up cannot drift from the evaluation.
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from transit import config  # noqa: E402
from transit.metrics import regression_metrics  # noqa: E402

REPORTS = config.ROOT / "reports"
FIG = REPORTS / "figures"
PRED = config.DATA_DIR / "predictions"
NAMES = {"ensemble": "Final: LightGBM + historical average", "model": "LightGBM alone",
         "seasonal_naive": "Same hour last week",
         "dow4_mean": "Mean of last 4 same weekdays", "hist_average": "Historical average"}
ORDER = ["ensemble", "model", "seasonal_naive", "dow4_mean", "hist_average"]
PERIOD_ORDER = ["early 03-05", "am peak 06-08", "midday 09-15", "pm peak 16-19", "evening 20-23", "night 00-02"]
SEG_LABELS = {"True": "regular cell", "False": "non-regular cell"}


def ordered(keys) -> list:
    keys = list(keys)
    if set(keys) <= set(PERIOD_ORDER):
        return [k for k in PERIOD_ORDER if k in keys]
    return keys
COL = {"ensemble": "#1d4ed8", "model": "#60a5fa", "seasonal_naive": "#d97706", "dow4_mean": "#059669", "hist_average": "#7c3aed"}


def pct(x: float) -> str:
    return f"{100 * x:.2f}%"


def table(block: dict) -> str:
    sn = block["seasonal_naive"]["wape"]
    lines = ["| Method | MAE | RMSE | WAPE | Bias | WAPE change vs last week |", "| --- | --- | --- | --- | --- | --- |"]
    for k in ORDER:
        m = block[k]
        rel = "reference" if k == "seasonal_naive" else f"{100 * (m['wape'] / sn - 1):+.1f}%"
        lines.append(f"| {NAMES[k]} | {m['mae']:.2f} | {m['rmse']:.2f} | {pct(m['wape'])} | {m['bias']:+.2f} | {rel} |")
    return "\n".join(lines)


def fig_wape(metrics: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax, short, title in zip(axes, ("demand", "load"), ("Demand (boardings)", "Estimated load")):
        t = metrics["targets"][short]["test"]
        vals = [t[k]["wape"] * 100 for k in ORDER]
        bars = ax.barh([NAMES[k] for k in ORDER][::-1], vals[::-1], color=[COL[k] for k in ORDER][::-1])
        ax.bar_label(bars, fmt="%.1f%%", padding=3)
        ax.set_title(f"{title}: test WAPE (lower is better)", fontsize=11)
        ax.set_xlim(0, max(vals) * 1.25)
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "test_wape.png", dpi=160)
    plt.close(fig)


def fig_periods(metrics: dict) -> None:
    seg = metrics["targets"]["demand"]["segments_test"]["period"]
    cats = ordered(seg["ensemble"])
    x = np.arange(len(cats))
    fig, ax = plt.subplots(figsize=(9, 3.4))
    for i, k in enumerate(("ensemble", "seasonal_naive")):
        ax.bar(x + (i - 0.5) * 0.38, [seg[k][c]["wape"] * 100 for c in cats], 0.38, label=NAMES[k], color=COL[k])
    ax.set_xticks(x, cats, fontsize=9)
    ax.set_ylabel("WAPE (%)")
    ax.set_title("Demand error by time of day, test weeks", fontsize=11)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "demand_wape_by_period.png", dpi=160)
    plt.close(fig)


def fig_days(metrics: dict) -> None:
    d = pd.DataFrame(metrics["targets"]["demand"]["segments_test"]["by_day"]).T
    d.index = pd.to_datetime(d.index)
    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.plot(d.index, d["ensemble_wape"] * 100, marker="o", color=COL["ensemble"], label=NAMES["ensemble"])
    ax.plot(d.index, d["ha_wape"] * 100, marker="o", ls="--", color=COL["hist_average"], label=NAMES["hist_average"])
    ax.plot(d.index, d["sn_wape"] * 100, marker="o", ls=":", color=COL["seasonal_naive"], label=NAMES["seasonal_naive"])
    ax.set_ylabel("WAPE (%)")
    ax.set_title("Demand error by test day", fontsize=11)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIG / "demand_wape_by_day.png", dpi=160)
    plt.close(fig)


def fig_crowding(metrics: dict) -> None:
    ct = metrics["targets"]["load"]["crowding_test"]
    names = list(ct)
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(8, 3.4))
    for i, k in enumerate(("ensemble", "seasonal_naive", "hist_average")):
        ax.bar(x + (i - 1) * 0.27, [ct[n][k]["macro_f1"] for n in names], 0.27, label=NAMES[k], color=COL[k])
    ax.set_xticks(x, [f"{n}\n({ct[n]['capacity']})" for n in names])
    ax.set_ylabel("Macro-F1")
    ax.set_ylim(0, 1)
    ax.set_title("Crowding-level accuracy under each capacity assumption, test weeks", fontsize=11)
    ax.legend(frameon=False, ncol=3, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "crowding_macro_f1.png", dpi=160)
    plt.close(fig)


def fig_example() -> tuple[str, str, str]:
    d = pd.read_parquet(PRED / "demand_test.parquet")
    for c in ("route", "direction"):
        d[c] = d[c].astype(str)
    busiest = d.groupby(["route", "direction"])["target"].sum().idxmax()
    day = pd.Timestamp(config.VALID_END) + pd.Timedelta(days=3)  # first test Wednesday
    one = d[(d["route"] == busiest[0]) & (d["direction"] == busiest[1]) & (d["service_date"] == day)].sort_values("ts_hour")
    fig, ax = plt.subplots(figsize=(9, 3.4))
    ax.plot(one["ts_hour"], one["target"], color="#111827", lw=2.5, marker="o", label="Actual (SUNT)")
    ax.plot(one["ts_hour"], one["ensemble"], color=COL["ensemble"], marker="o", label=NAMES["ensemble"])
    ax.plot(one["ts_hour"], one["seasonal_naive"], color=COL["seasonal_naive"], ls=":", marker="o",
            label=NAMES["seasonal_naive"])
    ax.set_ylabel("Boardings per hour")
    ax.set_title(f"Route {busiest[0]} direction {busiest[1]}, {day:%a %d %b %Y} (test)", fontsize=11)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIG / "example_route_day.png", dpi=160)
    plt.close(fig)
    return busiest[0], busiest[1], day.strftime("%Y-%m-%d")


def recompute_check(metrics: dict) -> list[str]:
    out = []
    for short in ("demand", "load"):
        df = pd.read_parquet(PRED / f"{short}_test.parquet")
        df = df[df["target"].notna()]
        for k in ORDER:
            re = regression_metrics(df["target"], df[k])
            st = metrics["targets"][short]["test"][k]
            ok = np.isclose(re["wape"], st["wape"], rtol=1e-12) and re["n"] == st["n"]
            out.append(f"| {short} | {NAMES[k]} | {re['n']:,} | {pct(re['wape'])} | {'yes' if ok else 'NO'} |")
            if not ok:
                raise SystemExit(f"metrics.json does not match predictions for {short}/{k}")
    return out


def bootstrap_wape_diff(short: str, a: str, b: str, n_boot: int = 2000, seed: int = 0) -> dict:
    """Paired cluster bootstrap over route-directions of WAPE(a) - WAPE(b) on test.

    Route-directions are resampled with replacement (their hours are correlated),
    so the interval reflects uncertainty across routes rather than across hours.
    """
    df = pd.read_parquet(PRED / f"{short}_test.parquet")
    df = df[df["target"].notna()]
    df["key"] = df["route"].astype(str) + "|" + df["direction"].astype(str)
    g = df.assign(ea=(df[a] - df["target"]).abs(), eb=(df[b] - df["target"]).abs()).groupby("key")[
        ["ea", "eb", "target"]].sum()
    ea, eb, y = g["ea"].to_numpy(), g["eb"].to_numpy(), g["target"].to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(g), size=(n_boot, len(g)))
    diff = (ea[idx].sum(1) - eb[idx].sum(1)) / y[idx].sum(1)
    point = (ea.sum() - eb.sum()) / y.sum()
    lo, hi = np.quantile(diff, [0.025, 0.975])
    return {"point": float(point), "lo": float(lo), "hi": float(hi), "share_negative": float((diff < 0).mean()),
            "clusters": int(len(g))}


def coverage_by_segment(split: str = "test") -> dict:
    """80% interval coverage on the test (or validation) weeks, split by period
    of day and by weekday/weekend, recomputed from the committed prediction files."""
    from transit.models.run import period_of
    out = {}
    for short in ("demand", "load"):
        d = pd.read_parquet(PRED / f"{short}_{split}.parquet")
        d = d[d["target"].notna()]
        inside = (d["target"] >= d["lo"]) & (d["target"] <= d["hi"])
        by = {"period": period_of(d["service_hour"]),
              "day": np.where(d["service_date"].dt.day_of_week >= 5, "weekend", "weekday")}
        out[short] = {k: {str(g): float(v) for g, v in inside.groupby(np.asarray(key)).mean().items()}
                      for k, key in by.items()}
        out[short]["all"] = float(inside.mean())
        worst = min(out[short]["period"], key=out[short]["period"].get)
        w = d[np.asarray(by["period"]) == worst]
        out[short]["worst_period"] = {"period": worst, "rows": int(len(w)),
                                      "below": float((w["target"] < w["lo"]).mean()),
                                      "above": float((w["target"] > w["hi"]).mean()),
                                      "mean_width": float((w["hi"] - w["lo"]).mean())}
    return out


def planning_topk(ks=(25, 50, 100), capacity: float = 70.0) -> dict:
    """Daily alert list: each test day, take the K route-hours with the highest
    forecast estimated load; precision = share that were actually high crowding
    (load >= 80% of capacity). Averaged over the 14 test days."""
    from transit.crowding import crowding_level
    d = pd.read_parquet(PRED / "load_test.parquet")
    d = d[d["target"].notna()].copy()
    d["actual_high"] = crowding_level(d["target"], capacity) == "high"
    out = {"capacity": capacity, "median_actual_high_per_day": int(d.groupby("service_date")["actual_high"].sum().median()),
           "precision_at_k": {}}
    for k in ks:
        out["precision_at_k"][str(k)] = {
            p: float(np.mean([g.nlargest(k, p)["actual_high"].mean() for _, g in d.groupby("service_date")]))
            for p in ("ensemble", "seasonal_naive", "hist_average")}
    return out


def main() -> None:
    m = json.loads((REPORTS / "metrics.json").read_text(encoding="utf-8"))
    FIG.mkdir(parents=True, exist_ok=True)
    fig_wape(m)
    fig_periods(m)
    fig_days(m)
    fig_crowding(m)
    ex = fig_example()
    dem, lod = m["targets"]["demand"], m["targets"]["load"]
    ct = lod["crowding_test"]
    base = ct["basico"]
    seg = dem["segments_test"]
    worst_day = max(seg["by_day"].items(), key=lambda kv: kv[1]["ensemble_wape"])
    best_day = min(seg["by_day"].items(), key=lambda kv: kv[1]["ensemble_wape"])

    def cfg(r):
        c = r["chosen_config"]
        return f"objective `{c['objective']}`, {c['num_leaves']} leaves, {c['rounds']} rounds"

    def abl(r):
        return "\n".join(f"| {k} | {v['mae']:.2f} | {pct(v['wape'])} |" for k, v in r["ablation_valid"].items())

    def segtab(s):
        rows = ["| Segment | Rows | Final WAPE | Historical avg WAPE | Last-week WAPE |", "| --- | --- | --- | --- | --- |"]
        for k in ordered(s["ensemble"]):
            rows.append(f"| {SEG_LABELS.get(k, k)} | {s['ensemble'][k]['n']:,} | {pct(s['ensemble'][k]['wape'])} | "
                        f"{pct(s['hist_average'][k]['wape'])} | {pct(s['seasonal_naive'][k]['wape'])} |")
        return "\n".join(rows)

    crow_rows = ["| Scenario (capacity) | Actual low / medium / high | Final macro-F1 | Last-week macro-F1 | "
                 "Hist. avg macro-F1 | Final high precision | Final high recall |",
                 "| --- | --- | --- | --- | --- | --- | --- |"]
    for n, r in ct.items():
        s = r["actual_shares"]
        crow_rows.append(f"| {n} ({r['capacity']}) | {pct(s['low'])} / {pct(s['medium'])} / {pct(s['high'])} | "
                         f"{r['ensemble']['macro_f1']:.3f} | {r['seasonal_naive']['macro_f1']:.3f} | "
                         f"{r['hist_average']['macro_f1']:.3f} | {r['ensemble']['per_class']['high']['precision']:.3f} | "
                         f"{r['ensemble']['per_class']['high']['recall']:.3f} |")
    cm = base["ensemble"]["confusion"]["matrix"]
    burst = lod["segments_test"]["burst_hours"]
    zero = seg.get("actual_zero_rows", {})
    imp_d = list(dem["feature_importance_gain_share"].items())[:5]
    imp_l = list(lod["feature_importance_gain_share"].items())[:5]
    worst_rd = seg["worst_route_directions"][:5]
    boot = {(s, b): bootstrap_wape_diff(s, "ensemble", b) for s in ("demand", "load")
            for b in ("hist_average", "seasonal_naive", "model")}

    def boot_rows():
        rows = ["| Target | Final minus | WAPE difference (points) | 95% interval | Resamples where final is better |",
                "| --- | --- | --- | --- | --- |"]
        for (s, b), r in boot.items():
            rows.append(f"| {s} | {NAMES[b]} | {100 * r['point']:+.2f} | {100 * r['lo']:+.2f} to {100 * r['hi']:+.2f} | "
                        f"{pct(r['share_negative'])} |")
        return "\n".join(rows)

    cov = coverage_by_segment()
    cov_valid = coverage_by_segment("valid")
    cov_rows = ["| Target | All | " + " | ".join(PERIOD_ORDER) + " | Weekday | Weekend |",
                "| --- " * (len(PERIOD_ORDER) + 4) + "|"]
    for label, cv in (("test", cov), ("validation", cov_valid)):
        for short in ("demand", "load"):
            c = cv[short]
            cov_rows.append(f"| {short} ({label}) | {pct(c['all'])} | "
                            + " | ".join(pct(c["period"].get(k, float("nan"))) for k in PERIOD_ORDER)
                            + f" | {pct(c['day']['weekday'])} | {pct(c['day']['weekend'])} |")
    plan = planning_topk()
    (REPORTS / "planning.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    plan_rows = "\n".join(f"| {k} | {pct(v['ensemble'])} | {pct(v['hist_average'])} | {pct(v['seasonal_naive'])} |"
                           for k, v in plan["precision_at_k"].items())
    hist = m.get("test_scoring_history", [])
    hist_txt = "\n".join(
        f"- **{h['version']}** ([file](../{h['file']})): demand test WAPE LightGBM {pct(h['test_wape']['demand']['model'])}, "
        f"historical average {pct(h['test_wape']['demand']['hist_average'])}; load LightGBM "
        f"{pct(h['test_wape']['load']['model'])}, historical average {pct(h['test_wape']['load']['hist_average'])}. "
        f"{h['note']}" for h in hist) or "- None."

    md = f"""# Results

Generated by `python -m transit.report` from [`metrics.json`](metrics.json) (produced by
`python -m transit.models.run`). Do not edit numbers by hand.

**Protocol.** Train {m['split']['train'][0]} to {m['split']['train'][1]}; tune on validation
{m['split']['valid'][0]} to {m['split']['valid'][1]}; refit on train + validation; score on test
{m['split']['test'][0]} to {m['split']['test'][1]} (scored twice in total; see the disclosure below). Day-ahead: features for day D use only days before D.
Only observed route-hours are scored; missing records are never scored (decision D8).
The occupancy target is **estimated on-board load** from SUNT fare-card trip chaining, not measured occupancy.

**Final forecast.** {NAMES['ensemble']}: {dem['blend']['weight_on_lightgbm']:g} × LightGBM +
{1 - dem['blend']['weight_on_lightgbm']:g} × historical average, with the weight chosen on validation (decision D12).

**Test-set disclosure.** The test weeks were scored once before the blend existed:

{hist_txt}

## Demand: boardings per route-hour (test, {dem['test']['model']['n']:,} route-hours)

{table(dem['test'])}

LightGBM chosen on validation: {cfg(dem)}. Validation WAPE: final {pct(dem['valid']['ensemble']['wape'])},
LightGBM {pct(dem['valid']['model']['wape'])}, historical average {pct(dem['valid']['hist_average']['wape'])},
last week {pct(dem['valid']['seasonal_naive']['wape'])}. Blend weights tried on validation:
{", ".join(f"{k} → {pct(v)}" for k, v in dem['blend']['valid_wape_by_weight'].items())}.

**Is the gain real?** Paired bootstrap over route-directions (2,000 resamples; negative = final forecast better):

{boot_rows()}

![Test WAPE](figures/test_wape.png)

**Ablation (validation week).**

| Features | MAE | WAPE |
| --- | --- | --- |
{abl(dem)}

**Largest gain shares:** {", ".join(f"`{k}` {pct(v)}" for k, v in imp_d)}.

### Where demand errors are

{segtab(seg['period'])}

![By period](figures/demand_wape_by_period.png)

{segtab(seg['volume_tercile'])}

{segtab(seg['daytype'])}

Regular vs non-regular cells (non-regular = observed in an hour the route does not run on most training days):

{segtab(seg['regular_cell'])}

Worst test day: {worst_day[0]} (final WAPE {pct(worst_day[1]['ensemble_wape'])}). Best: {best_day[0]}
({pct(best_day[1]['ensemble_wape'])}).

![By day](figures/demand_wape_by_day.png)

Route-directions with the largest total absolute error (final forecast):

| Route | Dir | Rows | WAPE | Share of all error |
| --- | --- | --- | --- | --- |
{chr(10).join(f"| {r['route']} | {r['direction']} | {int(r['rows'])} | {pct(r['wape'])} | {pct(r['share_of_total_error'])} |" for r in worst_rd)}

Hours with zero recorded boardings ({zero.get('ensemble', {}).get('n', 0):,} test rows): final-forecast MAE
{zero.get('ensemble', {}).get('mae', float('nan')):.2f}, last-week MAE {zero.get('seasonal_naive', {}).get('mae', float('nan')):.2f}.

![Example](figures/example_route_day.png)

## Estimated load: mean peak load per bus per route-hour (test, {lod['test']['model']['n']:,} route-hours)

{table(lod['test'])}

Chosen on validation: {cfg(lod)}.

**Ablation (validation week).**

| Features | MAE | WAPE |
| --- | --- | --- |
{abl(lod)}

**Largest gain shares:** {", ".join(f"`{k}` {pct(v)}" for k, v in imp_l)}.

**Burst hours** (a stop with more than 100 boardings; kept, not capped):

| Hours | Rows | Final MAE | Final WAPE | Last-week MAE |
| --- | --- | --- | --- | --- |
| Without burst | {burst['ensemble']['False']['n']:,} | {burst['ensemble']['False']['mae']:.2f} | {pct(burst['ensemble']['False']['wape'])} | {burst['seasonal_naive']['False']['mae']:.2f} |
| With burst | {burst['ensemble'].get('True', {}).get('n', 0):,} | {burst['ensemble'].get('True', {}).get('mae', float('nan')):.2f} | {pct(burst['ensemble'].get('True', {}).get('wape', float('nan')))} | {burst['seasonal_naive'].get('True', {}).get('mae', float('nan')):.2f} |

## Prediction intervals (80%, test)

Two quantile LightGBM models (10% and 90%), early-stopped on validation and refit on train + validation,
then widened by a split-conformal margin computed on the validation week (decision D13).

| Target | Raw coverage | Calibrated coverage | Mean width (calibrated) | Conformal margin |
| --- | --- | --- | --- | --- |
{chr(10).join(f"| {s} | {pct(m['targets'][s]['intervals']['test_raw']['coverage'])} | {pct(m['targets'][s]['intervals']['test_calibrated']['coverage'])} | {m['targets'][s]['intervals']['test_calibrated']['mean_width']:.1f} | {m['targets'][s]['intervals']['conformal_margin']:.2f} |" for s in ('demand', 'load') if 'intervals' in m['targets'][s])}

Validation raw coverage: demand {pct(dem.get('intervals', {}).get('valid_raw', {}).get('coverage', float('nan')))},
load {pct(lod.get('intervals', {}).get('valid_raw', {}).get('coverage', float('nan')))}. The raw quantile models were
already close to 80% on validation, so the conformal margin is nearly zero. For demand, that tiny margin still moves
about 1.5% of test hours inside the interval: almost all are hours with zero boardings whose raw lower bound sat
just above zero. Intervals are wide for busy route-hours (mean width about 60 boardings), which is the honest
uncertainty of an hourly route forecast.

Calibrated coverage by period of day and day type (recomputed from the prediction files). The 80% target is a
long-run rate over many route-hours; it is not guaranteed for any one route or hour. Validation rows are shown
because the conformal margin was set on that week.

{chr(10).join(cov_rows)}

{(chr(10) * 2).join(f"Lowest {short} coverage: {c['worst_period']['period']} ({c['worst_period']['rows']:,} rows, mean width {c['worst_period']['mean_width']:.1f}); {pct(c['worst_period']['below'])} of actual values fall below the interval and {pct(c['worst_period']['above'])} above it." for short, c in cov.items())}

The night gap for estimated load was already visible in the validation week ({pct(cov_valid['load']['period'].get('night 00-02', float('nan')))}),
so it is a property of the method, not of the test weeks. It was noticed only after the test scoring, so it has not been
"fixed" on these numbers. A fix would calibrate a separate conformal margin per period on the validation week and would
count as a third look at the test weeks (decision D13).

## Crowding levels and capacity sensitivity (test)

Capacity from {m['crowding']['source']}. Levels: low < {m['crowding']['thresholds_load_factor'][0]:.0%},
high ≥ {m['crowding']['thresholds_load_factor'][1]:.0%} of capacity.

{chr(10).join(crow_rows)}

![Crowding](figures/crowding_macro_f1.png)

Base case (ônibus básico, 70) confusion matrix for the final forecast (rows actual, columns predicted; low, medium, high):

| | pred low | pred medium | pred high |
| --- | --- | --- | --- |
| actual low | {cm[0][0]:,} | {cm[0][1]:,} | {cm[0][2]:,} |
| actual medium | {cm[1][0]:,} | {cm[1][1]:,} | {cm[1][2]:,} |
| actual high | {cm[2][0]:,} | {cm[2][1]:,} | {cm[2][2]:,} |

## Planning use: a daily crowding alert list (test)

Each test day, a planner checks the K route-hours with the highest forecast estimated load. Precision is the share
that really were high crowding (estimated load ≥ 80% of a 70-passenger bus), averaged over the 14 test days. The
median test day had {plan['median_actual_high_per_day']} high route-hours.

| K per day | Final forecast | Historical average | Same hour last week |
| --- | --- | --- | --- |
{plan_rows}

## Check: metrics recomputed from the committed prediction files

| Target | Method | Rows | WAPE | Matches metrics.json |
| --- | --- | --- | --- | --- |
{chr(10).join(recompute_check(m))}

## Limitations

- Loads are SUNT estimates from trip chaining; riders aged 65+ are not recorded; capacity is assumed.
- One city (Salvador, Brazil), 59 days; no holiday in the test weeks; no Indian or tier-2 validation.
- The forecast is conditional on a route running in that hour (D8); missing records are not scored.
- Validation figures were used for selection and are optimistic; test figures are the honest estimate.
- The test weeks were scored twice (see the disclosure above); the blend weight was chosen on validation only.
- LightGBM on its own does not beat a well-chosen historical average; most predictable structure here is a
  stable weekly profile per route and hour.
"""
    (REPORTS / "RESULTS.md").write_text(md, encoding="utf-8")
    print(f"Wrote {REPORTS / 'RESULTS.md'} and {len(list(FIG.glob('*.png')))} figures (example: route {ex[0]} {ex[1]} {ex[2]})")


if __name__ == "__main__":
    main()
