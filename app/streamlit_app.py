"""Streamlit dashboard: AI Based Public Transport Demand and Occupancy Prediction.

    streamlit run app/streamlit_app.py

Reads only committed files (reports/metrics.json, data/predictions/*.parquet),
so it starts without downloading SUNT and works offline.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from transit.crowding import CAPACITY_SCENARIOS, LEVELS, THRESHOLDS, crowding_level  # noqa: E402
from transit.metrics import regression_metrics  # noqa: E402

TITLE = "AI Based Public Transport Demand and Occupancy Prediction"
PRED = ROOT / "data" / "predictions"
METRICS = ROOT / "reports" / "metrics.json"
NAMES = {"ensemble": "Final forecast (LightGBM + historical average)", "model": "LightGBM alone",
         "seasonal_naive": "Same hour last week",
         "dow4_mean": "Mean of last 4 same weekdays", "hist_average": "Historical average (same day type)"}
COLOURS = {"target": "#1f2937", "ensemble": "#1d4ed8", "model": "#60a5fa", "seasonal_naive": "#d97706",
           "dow4_mean": "#059669", "hist_average": "#7c3aed"}
LEVEL_COLOURS = {"low": "#16a34a", "medium": "#eab308", "high": "#dc2626"}
ESTIMATE_NOTE = ("**Occupancy here means estimated on-board load.** SUNT infers alightings from "
                 "fare-card trip chaining, so loads are estimates, not passenger counts. Riders aged 65+ "
                 "travel without cards and are missing. Data: Salvador, Brazil, 2024. No validation for "
                 "Indian or tier-2 cities is claimed.")


@st.cache_data
def load_metrics() -> dict:
    return json.loads(METRICS.read_text(encoding="utf-8"))


@st.cache_data
def load_predictions(name: str) -> pd.DataFrame:
    df = pd.read_parquet(PRED / f"{name}.parquet")
    df["route"] = df["route"].astype(str)
    df["direction"] = df["direction"].astype(str)
    df["service_date"] = pd.to_datetime(df["service_date"])
    df["ts_hour"] = pd.to_datetime(df["ts_hour"])
    return df


@st.cache_data
def route_options(split: str) -> list[str]:
    d = load_predictions(f"demand_{split}")
    vol = d.groupby(["route", "direction"])["target"].sum().sort_values(ascending=False)
    return [f"{r} · {dr}" for r, dr in vol.index]


def fmt_pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def metrics_table(block: dict, keys=("ensemble", "model", "seasonal_naive", "dow4_mean", "hist_average")) -> pd.DataFrame:
    rows = []
    sn = block["seasonal_naive"]["wape"]
    for k in keys:
        m = block[k]
        rows.append({"Method": NAMES[k], "MAE": round(m["mae"], 2), "RMSE": round(m["rmse"], 2),
                     "WAPE": fmt_pct(m["wape"]), "Bias": round(m["bias"], 2),
                     "WAPE vs last week": "" if k == "seasonal_naive" else f"{100 * (m['wape'] / sn - 1):+.1f}%",
                     "Rows": m["n"]})
    return pd.DataFrame(rows)


def day_chart(df: pd.DataFrame, value_name: str, capacity: float | None = None) -> go.Figure:
    fig = go.Figure()
    obs = df[df["status"] == "observed"]
    miss = df[df["status"] != "observed"]
    fig.add_trace(go.Scatter(x=obs["ts_hour"], y=obs["target"], mode="lines+markers", name="Actual (SUNT)",
                             line=dict(color=COLOURS["target"], width=3)))
    for k in ("ensemble", "seasonal_naive"):
        fig.add_trace(go.Scatter(x=df["ts_hour"], y=df[k], mode="lines+markers", name=NAMES[k],
                                 line=dict(color=COLOURS[k], dash="solid" if k == "ensemble" else "dot")))
    if len(miss):
        fig.add_trace(go.Scatter(x=miss["ts_hour"], y=miss["ensemble"], mode="markers", name="No SUNT record (not scored)",
                                 marker=dict(symbol="circle-open", size=12, color="#6b7280")))
    if capacity:
        for frac, lab in zip(THRESHOLDS, ("medium from", "high from")):
            fig.add_hline(y=frac * capacity, line_dash="dash", line_color="#9ca3af",
                          annotation_text=f"{lab} {frac * capacity:.0f}", annotation_position="top left")
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), yaxis_title=value_name,
                      xaxis_title="Hour", legend=dict(orientation="h", y=-0.25))
    return fig


def page_explorer(metrics: dict) -> None:
    st.subheader("Forecast explorer")
    st.caption("Day-ahead forecasts made before each service day starts, using only earlier days.")
    c1, c2, c3 = st.columns([1, 1.2, 1])
    periods = {"Test, 15–28 Apr 2024": "test", "Validation, 8–14 Apr 2024": "valid"}
    split = periods[c1.radio("Period", list(periods))]
    options = route_options(split)
    choice = c2.selectbox("Route · direction (busiest first)", options, index=0)
    route, direction = [x.strip() for x in choice.split("·")]
    dem = load_predictions(f"demand_{split}")
    lod = load_predictions(f"load_{split}")
    days = sorted(dem["service_date"].dt.date.unique())
    day = c3.selectbox("Service day", days, index=0, format_func=lambda d: d.strftime("%a %d %b %Y"))
    sel = lambda df: df[(df["route"] == route) & (df["direction"] == direction)  # noqa: E731
                        & (df["service_date"] == pd.Timestamp(day))].sort_values("ts_hour")
    d1, l1 = sel(dem), sel(lod)
    if d1.empty:
        st.info("This route-direction has no regular service or records on that day.")
        return
    cap_name = st.select_slider("Capacity assumption for crowding lines", list(CAPACITY_SCENARIOS),
                                value="basico", format_func=lambda k: f"{k} ({CAPACITY_SCENARIOS[k]})")
    cap = CAPACITY_SCENARIOS[cap_name]

    obs = d1[d1["status"] == "observed"]
    a, b, c = st.columns(3)
    a.metric("Boardings that day (observed hours)", f"{obs['target'].sum():,.0f}")
    if len(obs):
        a2 = regression_metrics(obs["target"], obs["ensemble"])
        b2 = regression_metrics(obs["target"], obs["seasonal_naive"])
        b.metric("Final forecast WAPE this day", fmt_pct(a2["wape"]))
        c.metric("Last-week WAPE this day", fmt_pct(b2["wape"]))
    st.markdown("**Hourly boardings**")
    st.plotly_chart(day_chart(d1, "Boardings per hour"), width="stretch")
    st.markdown("**Estimated peak load per bus** (mean over the hour's trips of each trip's highest estimated load)")
    st.plotly_chart(day_chart(l1, "Estimated passengers on board", capacity=cap), width="stretch")

    if len(l1):
        strip = l1.assign(Actual=crowding_level(l1["target"], cap), Forecast=crowding_level(l1["ensemble"], cap))
        strip["Hour"] = strip["ts_hour"].dt.strftime("%H:00")
        st.markdown(f"**Crowding level by hour** (capacity {cap}; low < {THRESHOLDS[0]:.0%}, "
                    f"high ≥ {THRESHOLDS[1]:.0%} of capacity)")
        show = strip[["Hour", "Actual", "Forecast"]].set_index("Hour").T

        def colour(v):
            return f"background-color: {LEVEL_COLOURS.get(v, '#e5e7eb')}; color: white" if v else ""
        st.dataframe(show.style.map(colour), width="stretch")
    if (d1["status"] != "observed").any():
        st.caption("Open circles: hours this route normally runs but SUNT has no record that day. "
                   "They are treated as missing data, not zero demand, and are not scored (decision D8).")


def page_comparison(metrics: dict) -> None:
    st.subheader("Model comparison on the test weeks (15–28 Apr 2024)")
    st.caption("The model was tuned on the validation week only and scored once on the test weeks. "
               "All methods are scored on exactly the same observed route-hours.")
    for short, label in (("demand", "Demand: boardings per route-hour"),
                         ("load", "Estimated load: mean peak load per bus per route-hour")):
        r = metrics["targets"][short]
        st.markdown(f"**{label}**")
        st.dataframe(metrics_table(r["test"]), hide_index=True, width="stretch")
    with st.expander("Check: recompute the test metrics from the committed prediction files"):
        rows = []
        for short in ("demand", "load"):
            df = load_predictions(f"{short}_test")
            df = df[df["target"].notna()]
            for k in ("ensemble", "model", "seasonal_naive", "dow4_mean", "hist_average"):
                re = regression_metrics(df["target"], df[k])
                stored = metrics["targets"][short]["test"][k]
                rows.append({"Target": short, "Method": NAMES[k], "Recomputed WAPE": round(re["wape"], 6),
                             "Reported WAPE": round(stored["wape"], 6),
                             "Match": bool(np.isclose(re["wape"], stored["wape"]) and re["n"] == stored["n"])})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    short = st.radio("Error breakdown for", ["demand", "load"], horizontal=True)
    seg = metrics["targets"][short]["segments_test"]
    c1, c2 = st.columns(2)
    for col, key, title in ((c1, "period", "WAPE by time of day"), (c2, "volume_tercile", "WAPE by route volume")):
        s = seg[key]
        cats = list(s["ensemble"])
        fig = go.Figure([go.Bar(name=NAMES[p], x=cats, y=[s[p][c]["wape"] for c in cats],
                                marker_color=COLOURS[p]) for p in ("ensemble", "hist_average", "seasonal_naive")])
        fig.update_layout(barmode="group", height=320, title=title, yaxis_tickformat=".0%",
                          margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.3))
        col.plotly_chart(fig, width="stretch")
    byday = pd.DataFrame(seg["by_day"]).T
    byday.index = pd.to_datetime(byday.index)
    fig = go.Figure([go.Scatter(x=byday.index, y=byday["ensemble_wape"], name=NAMES["ensemble"], mode="lines+markers",
                                line=dict(color=COLOURS["ensemble"])),
                     go.Scatter(x=byday.index, y=byday["ha_wape"], name=NAMES["hist_average"], mode="lines+markers",
                                line=dict(color=COLOURS["hist_average"], dash="dash")),
                     go.Scatter(x=byday.index, y=byday["sn_wape"], name=NAMES["seasonal_naive"], mode="lines+markers",
                                line=dict(color=COLOURS["seasonal_naive"], dash="dot"))])
    fig.update_layout(height=300, title="WAPE by test day", yaxis_tickformat=".0%",
                      margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fig, width="stretch")
    worst = pd.DataFrame(seg["worst_route_directions"])[["route", "direction", "wape", "share_of_total_error", "rows"]]
    worst["wape"] = worst["wape"].map(fmt_pct)
    worst["share_of_total_error"] = worst["share_of_total_error"].map(fmt_pct)
    st.markdown("**Route-directions with the largest total error (final forecast)**")
    st.dataframe(worst, hide_index=True, width="stretch")

    r = metrics["targets"][short]
    st.markdown(f"**How LightGBM was chosen (validation week).** The final forecast blends it 50/50 with the historical average; the weight {r['blend']['weight_on_lightgbm']} was chosen on validation.")
    tun = pd.DataFrame(r["tuning"])[["objective", "num_leaves", "best_iteration", "mae", "wape"]]
    tun["wape"] = tun["wape"].map(fmt_pct)
    st.dataframe(tun, hide_index=True, width="stretch")
    abl = pd.DataFrame(r["ablation_valid"]).T[["mae", "wape"]]
    abl["wape"] = abl["wape"].map(fmt_pct)
    st.markdown("**Feature-group ablation (validation week)**")
    st.dataframe(abl, width="stretch")
    imp = pd.Series(r["feature_importance_gain_share"]).head(12)[::-1]
    fig = go.Figure(go.Bar(x=imp.values, y=imp.index, orientation="h", marker_color=COLOURS["model"]))
    fig.update_layout(height=360, title="Feature importance (share of total gain)", xaxis_tickformat=".0%",
                      margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")


def page_crowding(metrics: dict) -> None:
    st.subheader("Crowding levels and the capacity assumption")
    cr = metrics["crowding"]
    st.markdown(
        f"SUNT has no vehicle capacity. Capacities are the minimum seated-plus-standing figures in "
        f"**{cr['source']}**: midiônibus 40, ônibus básico **70 (base case)**, padron 80, articulado 100. "
        f"Levels use load factor = estimated load / capacity: low < {THRESHOLDS[0]:.0%}, "
        f"medium {THRESHOLDS[0]:.0%}–{THRESHOLDS[1]:.0%}, high ≥ {THRESHOLDS[1]:.0%}.")
    ct = metrics["targets"]["load"]["crowding_test"]
    rows = []
    for name, res in ct.items():
        rows.append({"Scenario": f"{name} ({res['capacity']})",
                     **{f"Actual {k}": fmt_pct(v) for k, v in res["actual_shares"].items()},
                     **{f"Macro-F1: {NAMES[p].split(' (')[0]}": round(res[p]["macro_f1"], 3)
                        for p in ("ensemble", "seasonal_naive", "hist_average")},
                     "High: precision (final)": round(res["ensemble"]["per_class"]["high"]["precision"], 3),
                     "High: recall (final)": round(res["ensemble"]["per_class"]["high"]["recall"], 3)})
    st.markdown("**Test weeks, every capacity scenario**")
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    name = st.selectbox("Confusion matrix for scenario", list(ct), index=list(ct).index("basico"))
    cm = np.array(ct[name]["ensemble"]["confusion"]["matrix"])
    fig = go.Figure(go.Heatmap(z=cm, x=[f"pred {l}" for l in LEVELS], y=[f"actual {l}" for l in LEVELS],
                               text=cm, texttemplate="%{text}", colorscale="Blues", showscale=False))
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), yaxis_autorange="reversed")
    st.plotly_chart(fig, width="stretch")
    burst = metrics["targets"]["load"]["segments_test"]["burst_hours"]["ensemble"]
    st.markdown("**Hours with burst validations** (a single stop with more than 100 boardings; almost all at "
                "terminal stations at peak times). They are kept, not capped, and reported separately:")
    st.dataframe(pd.DataFrame({("With burst" if k == "True" else "Without burst"):
                               {"MAE": round(v["mae"], 2), "WAPE": fmt_pct(v["wape"]), "Rows": v["n"]}
                               for k, v in burst.items()}).T, width="stretch")


def page_forecast(metrics: dict) -> None:
    st.subheader(f"Next-day forecast: {metrics['split']['forecast_demo']}")
    st.warning("This is a genuine next-day forecast from data up to 28 Apr 2024. There are no actuals for this "
               "day in our study data, so it is a demonstration, not an evaluated result.")
    f = load_predictions(f"forecast_{metrics['split']['forecast_demo']}")
    cap_name = st.select_slider("Capacity assumption", list(CAPACITY_SCENARIOS), value="basico",
                                format_func=lambda k: f"{k} ({CAPACITY_SCENARIOS[k]})", key="fc_cap")
    cap = CAPACITY_SCENARIOS[cap_name]
    f["level"] = crowding_level(f["load_forecast"], cap)
    st.markdown(f"**Planning view: route-hours forecast as high crowding (≥ {THRESHOLDS[1]:.0%} of {cap})**")
    top = f[f["level"] == "high"].sort_values("load_forecast", ascending=False)
    a, b = st.columns(2)
    a.metric("Route-hours forecast", f"{len(f):,}")
    b.metric("Forecast high crowding", f"{len(top):,}")
    show = top.assign(Hour=top["ts_hour"].dt.strftime("%H:00"))[
        ["route", "direction", "Hour", "demand_forecast", "load_forecast"]].head(25)
    show.columns = ["Route", "Dir", "Hour", "Boardings forecast", "Est. peak load forecast"]
    st.dataframe(show.round(1), hide_index=True, width="stretch")
    st.caption("Use: these are the hours to check first for extra trips or larger vehicles. Validated "
               "precision and recall of the high level are on the Crowding page.")
    options = (f.groupby(["route", "direction"])["demand_forecast"].sum().sort_values(ascending=False))
    choice = st.selectbox("Route · direction", [f"{r} · {d}" for r, d in options.index])
    r, d = [x.strip() for x in choice.split("·")]
    one = f[(f["route"] == r) & (f["direction"] == d)].sort_values("ts_hour")
    fig = go.Figure([go.Bar(x=one["ts_hour"], y=one["demand_forecast"], name="Boardings forecast",
                            marker_color=COLOURS["model"]),
                     go.Scatter(x=one["ts_hour"], y=one["load_forecast"], name="Est. peak load forecast",
                                yaxis="y2", mode="lines+markers", line=dict(color="#dc2626"))])
    fig.update_layout(height=360, yaxis=dict(title="Boardings"),
                      yaxis2=dict(title="Estimated load", overlaying="y", side="right"),
                      margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig, width="stretch")


def page_data(metrics: dict) -> None:
    st.subheader("Data and limitations")
    st.markdown(f"""
**Source.** Salvador Urban Network Transportation (SUNT), Ferreira et al., *Scientific Data* 12, 1320 (2025),
doi:10.1038/s41597-025-05674-6; dataset doi:10.17632/85fdtx3kr5.1, licensed CC BY 4.0. We use the
origin-destination tables for 1 Mar to 28 Apr 2024 (59 days, 37.6 million stop events), aggregated to
route × direction × hour.

**Split.** Train {metrics['split']['train'][0]} to {metrics['split']['train'][1]}; validation
{metrics['split']['valid'][0]} to {metrics['split']['valid'][1]}; test {metrics['split']['test'][0]} to
{metrics['split']['test'][1]}. Good Friday (29 Mar) is in training, so holiday behaviour is not tested.

**What counts as occupancy.** {ESTIMATE_NOTE}

**Missing hours (D8).** Hours a route regularly runs but SUNT did not record are *missing data*, never zero
demand. They are not scored. SUNT's timetable file covers May–June 2024, so it cannot confirm which hours
were scheduled in March–April.

**Malformed trips (D9).** 222 trips on 2–3 April repeat stop numbers; their loads are unusable and those
route-directions are out of scope.

**Burst validations.** 2,685 stop events with more than 100 boardings, 99.8% at 10 terminal stations at the
first stop of a trip. Kept, not capped; load results are shown with and without them.

**Capacity.** Not in the data. Crowding uses ABNT NBR 15570 minimum capacities and is reported for four
vehicle classes because the fleet mix per route is unknown.
""")


def main() -> None:
    st.set_page_config(page_title="Transit demand and occupancy", layout="wide")
    st.title(TITLE)
    st.caption("CS3011 Artificial Intelligence · Group 52 · PDPM IIITDM Jabalpur")
    st.info(ESTIMATE_NOTE)
    metrics = load_metrics()
    pages = {"Forecast explorer": page_explorer, "Model comparison": page_comparison,
             "Crowding and capacity": page_crowding, "Next-day forecast": page_forecast,
             "Data and limitations": page_data}
    choice = st.sidebar.radio("Page", list(pages))
    pages[choice](metrics)


main()
