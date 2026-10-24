"""Streamlit dashboard: AI Based Public Transport Demand and Occupancy Prediction.

    streamlit run app/streamlit_app.py

Reads only committed files (reports/metrics.json, data/predictions/*.parquet),
so it starts without downloading SUNT and works offline. The look (fonts, colours,
chart template, table and figure markup) lives in app/design.py.
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
sys.path.insert(0, str(Path(__file__).resolve().parent))

import design as ds  # noqa: E402
from transit.crowding import CAPACITY_SCENARIOS, LEVELS, THRESHOLDS, crowding_level  # noqa: E402
from transit.metrics import regression_metrics  # noqa: E402

TITLE = "AI Based Public Transport Demand and Occupancy Prediction"
REPO = "https://github.com/jayvaghela779/cs3011-public-transport-demand-occupancy"
PRED = ROOT / "data" / "predictions"
METRICS = ROOT / "reports" / "metrics.json"
NAMES = {"ensemble": "Final forecast (LightGBM + historical average)", "model": "LightGBM alone",
         "seasonal_naive": "Same hour last week",
         "dow4_mean": "Mean of last 4 same weekdays", "hist_average": "Historical average (same day type)"}
METHODS = ("ensemble", "model", "seasonal_naive", "dow4_mean", "hist_average")
COLOURS = ds.SERIES
VEHICLES = {"midionibus": "Midiônibus", "basico": "Ônibus básico", "padron": "Padron",
            "articulado": "Articulado"}
PERIODS = {"early 03-05": "Early<br>03–05", "am peak 06-08": "AM peak<br>06–08", "midday 09-15": "Midday<br>09–15",
           "pm peak 16-19": "PM peak<br>16–19", "evening 20-23": "Evening<br>20–23", "night 00-02": "Night<br>00–02"}
ESTIMATE_LEAD = "Occupancy here means estimated on-board load."
ESTIMATE_REST = ("SUNT infers alightings from fare-card trip chaining, so loads are estimates, not "
                 "passenger counts. Riders aged 65+ travel without cards and are missing. Data: Salvador, Brazil, "
                 "2024. No validation for Indian or tier-2 cities is claimed.")
ESTIMATE_NOTE = f"**{ESTIMATE_LEAD}** {ESTIMATE_REST}"


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


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def page_header(title: str, deck: str | None = None, occupancy_note: bool = True) -> None:
    """Page title (kept as st.subheader so the smoke tests can find it), standfirst and the
    occupancy note (the data page states it in full instead)."""
    html(f'<div class="mast-m">{TITLE}</div>')
    st.subheader(title, anchor=False)
    if deck:
        html(ds.deck(deck))
    if occupancy_note:
        html(ds.note(ESTIMATE_LEAD, ESTIMATE_REST))


def plot(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", theme=None, config=ds.CHART_CONFIG)


def best_cells(values: list[list[float | None]], cols: list[int], key=abs) -> set[tuple[int, int]]:
    """(row, col) of the best (smallest by key) value in each listed column."""
    out = set()
    for c in cols:
        col = [(key(r[c]), i) for i, r in enumerate(values) if r[c] is not None]
        if col:
            low = min(v for v, _ in col)
            out |= {(i, c) for v, i in col if np.isclose(v, low)}
    return out


def metrics_table(block: dict, keys=METHODS) -> str:
    sn = block["seasonal_naive"]["wape"]
    raw, rows = [], []
    for k in keys:
        m = block[k]
        raw.append([None, m["mae"], m["rmse"], m["wape"], m["bias"], None, None])
        rows.append([ds.swatch(COLOURS[k]) + ds.esc(NAMES[k]), f"{m['mae']:.2f}", f"{m['rmse']:.2f}",
                     fmt_pct(m["wape"]), f"{m['bias']:+.2f}",
                     "" if k == "seasonal_naive" else f"{100 * (m['wape'] / sn - 1):+.1f}%", ds.fmt_int(m["n"])])
    cols = [("Method", "l"), ("MAE", "r"), ("RMSE", "r"), ("WAPE", "r"), ("Bias", "r"),
            ("WAPE vs last week", "r"), ("Rows", "r")]
    rounded = [[None, round(r[1], 2), round(r[2], 2), round(r[3], 3), round(r[4], 2)] + r[5:] for r in raw]
    return ds.table(cols, rows, bold=best_cells(rounded, [1, 2, 3, 4]))


def day_chart(df: pd.DataFrame, value_name: str, capacity: float | None = None) -> go.Figure:
    fig = ds.figure(height=380)
    obs = df[df["status"] == "observed"]
    miss = df[df["status"] != "observed"]
    if {"lo", "hi"} <= set(df.columns):
        fig.add_trace(go.Scatter(x=df["ts_hour"], y=df["hi"], mode="lines", line=dict(width=0),
                                 showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=df["ts_hour"], y=df["lo"], mode="lines", line=dict(width=0), fill="tonexty",
                                 fillcolor="rgba(11,110,105,0.13)", name="80% interval (calibrated)",
                                 hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=obs["ts_hour"], y=obs["target"], mode="lines+markers", name="Actual (SUNT)",
                             line=dict(color=COLOURS["target"], width=2.6), marker=dict(size=5),
                             hovertemplate="%{y:,.1f}"))
    for k in ("ensemble", "seasonal_naive"):
        main = k == "ensemble"
        fig.add_trace(go.Scatter(x=df["ts_hour"], y=df[k], mode="lines+markers", name=NAMES[k],
                                 line=dict(color=COLOURS[k], width=2.6 if main else 1.6,
                                           dash="solid" if main else "dot"),
                                 marker=dict(size=5 if main else 4), hovertemplate="%{y:,.1f}"))
    if len(miss):
        fig.add_trace(go.Scatter(x=miss["ts_hour"], y=miss["ensemble"], mode="markers",
                                 name="No SUNT record (not scored)", hovertemplate="%{y:,.1f}",
                                 marker=dict(symbol="circle-open", size=12, color=ds.INK_3, line=dict(width=1.5))))
    if capacity:
        for frac, lab in zip(THRESHOLDS, ("Medium from", "High from")):
            fig.add_hline(y=frac * capacity, line_dash="dash", line_width=1, line_color="#9AA6B2",
                          annotation_text=f"{lab} {frac * capacity:.0f}", annotation_position="top right",
                          annotation_font=dict(size=11, color=ds.INK_2))
    fig.update_layout(yaxis_title=value_name, hovermode="x unified", xaxis=dict(tickformat="%H:%M"),
                      yaxis=dict(rangemode="tozero"))
    return fig


def page_explorer(metrics: dict) -> None:
    page_header("Forecast explorer", "Day-ahead forecasts made before each service day starts, using only earlier "
                                     "days. Pick a route and a day to compare the forecast with what SUNT recorded.")
    c1, c2, c3 = st.columns([1.25, 1, 1])
    periods = {"Test, 15–28 Apr 2024": "test", "Validation, 8–14 Apr 2024": "valid"}
    split = periods[c1.radio("Period", list(periods), horizontal=True)]
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
    html(f'<div class="route"><span class="badge">{ds.esc(route)}</span><span class="what">Route {ds.esc(route)}, '
         f'direction {ds.esc(direction)}<span class="when">{day.strftime("%A %d %B %Y")}</span></span></div>')
    if d1.empty:
        st.info("This route-direction has no regular service or records on that day. Choose another day or route.")
        return

    obs = d1[d1["status"] == "observed"]
    figs = [("Boardings that day", ds.fmt_int(obs["target"].sum()), "Observed hours only")]
    if len(obs):
        a2 = regression_metrics(obs["target"], obs["ensemble"])
        b2 = regression_metrics(obs["target"], obs["seasonal_naive"])
        figs += [("Final forecast WAPE this day", fmt_pct(a2["wape"]), "LightGBM + historical average"),
                 ("Last-week WAPE this day", fmt_pct(b2["wape"]), "Same hour last week")]
    html(ds.figures(figs, accent=1))

    html(ds.section("Hourly boardings", "Passengers boarding this route-direction in each hour."))
    plot(day_chart(d1, "Boardings per hour"))

    html(ds.section("Estimated peak load per bus",
                    "Mean over the hour's trips of each trip's highest estimated load. Dashed lines mark where "
                    "crowding becomes medium and high for the chosen vehicle."))
    cap_name = st.select_slider("Capacity assumption for crowding lines", list(CAPACITY_SCENARIOS),
                                value="basico",
                                format_func=lambda k: f"{VEHICLES[k]} ({CAPACITY_SCENARIOS[k]})")
    cap = CAPACITY_SCENARIOS[cap_name]
    plot(day_chart(l1, "Estimated passengers on board", capacity=cap))

    if len(l1):
        strip = l1.assign(Actual=crowding_level(l1["target"], cap), Forecast=crowding_level(l1["ensemble"], cap))
        hours = strip["ts_hour"].dt.strftime("%H:00").tolist()
        html(ds.section("Crowding level by hour",
                        f"Capacity {cap}: low below {THRESHOLDS[0]:.0%}, high from {THRESHOLDS[1]:.0%} of capacity."))
        html(ds.crowding_strip(hours, [("Actual", list(strip["Actual"])), ("Forecast", list(strip["Forecast"]))]))
    notes = []
    iv = metrics["targets"]["demand"].get("intervals")
    if iv:
        notes.append(f"Shaded band: 80% prediction interval from quantile models, widened on the validation week. "
                     f"Test coverage: {fmt_pct(iv['test_calibrated']['coverage'])} of actual demand values fall "
                     f"inside (target 80%).")
    if (d1["status"] != "observed").any():
        notes.append("Open circles: hours this route normally runs but SUNT has no record that day. "
                     "They are treated as missing data, not zero demand, and are not scored (decision D8).")
    if notes:
        html('<hr class="rule">' + "".join(f'<p class="small">{ds.esc(n)}</p>' for n in notes))


def page_comparison(metrics: dict) -> None:
    page_header("Model comparison on the test weeks (15–28 Apr 2024)",
                "Settings and the blend weight were chosen on the validation week only. The test weeks have been "
                "scored twice: LightGBM alone (first run), then this blend; both results are reported in "
                "RESULTS.md (decision D12). All methods are scored on exactly the same observed route-hours.")
    for short, label in (("demand", "Demand: boardings per route-hour"),
                         ("load", "Estimated load: mean peak load per bus per route-hour")):
        html(ds.section(label))
        html(metrics_table(metrics["targets"][short]["test"]))
    html('<p class="small">Bold marks the lowest MAE, RMSE and WAPE and the bias closest to zero in each table. '
         'WAPE vs last week is the relative change against the same-hour-last-week rule.</p>')
    with st.expander("Check: recompute the test metrics from the committed prediction files"):
        rows = []
        for short in ("demand", "load"):
            df = load_predictions(f"{short}_test")
            df = df[df["target"].notna()]
            for k in METHODS:
                re = regression_metrics(df["target"], df[k])
                stored = metrics["targets"][short]["test"][k]
                ok = bool(np.isclose(re["wape"], stored["wape"]) and re["n"] == stored["n"])
                rows.append([short.capitalize(), ds.esc(NAMES[k]), f"{re['wape']:.6f}", f"{stored['wape']:.6f}",
                             '<span class="ok">✓ Match</span>' if ok else '<span class="no">✗ Differs</span>'])
        html(ds.table([("Target", "l"), ("Method", "l"), ("Recomputed WAPE", "r"), ("Reported WAPE", "r"),
                       ("Match", "l")], rows))

    html(ds.section("Where the errors are", "WAPE of the final forecast against the two strongest baselines."))
    short = st.radio("Error breakdown for", ["demand", "load"], horizontal=True,
                     format_func=lambda s: "Demand" if s == "demand" else "Estimated load")
    seg = metrics["targets"][short]["segments_test"]
    html('<div class="legend">' + "".join(f"<span>{ds.swatch(COLOURS[p])}{ds.esc(NAMES[p])}</span>"
                                          for p in ("ensemble", "hist_average", "seasonal_naive")) + "</div>")
    c1, c2 = st.columns(2, gap="large")
    for col, key, title in ((c1, "period", "By time of day"), (c2, "volume_tercile", "By route volume")):
        s = seg[key]
        cats = [c for c in PERIODS if c in s["ensemble"]] if key == "period" else list(s["ensemble"])
        labels = [PERIODS.get(c, c.capitalize()) for c in cats]
        fig = ds.figure(height=330, barmode="group", yaxis_tickformat=".0%",
                        title=dict(text=title, font=dict(family=ds.SERIF, size=17, color=ds.INK), x=0, y=0.98))
        for p in ("ensemble", "hist_average", "seasonal_naive"):
            fig.add_trace(go.Bar(name=NAMES[p], x=labels, y=[s[p][c]["wape"] for c in cats],
                                 marker_color=COLOURS[p], hovertemplate="%{y:.1%}"))
        fig.update_layout(showlegend=False, margin=dict(t=40), hovermode="x unified")
        with col:
            plot(fig)
    byday = pd.DataFrame(seg["by_day"]).T
    byday.index = pd.to_datetime(byday.index)
    fig = ds.figure(height=320, yaxis_tickformat=".0%", hovermode="x unified",
                    title=dict(text="By test day", font=dict(family=ds.SERIF, size=17, color=ds.INK), x=0, y=0.98),
                    xaxis=dict(tickformat="%a %d %b", dtick=86400000 * 2))
    for col_, k, dash, w in (("ensemble_wape", "ensemble", "solid", 2.6), ("ha_wape", "hist_average", "dash", 1.8),
                             ("sn_wape", "seasonal_naive", "dot", 1.6)):
        fig.add_trace(go.Scatter(x=byday.index, y=byday[col_], name=NAMES[k], mode="lines+markers",
                                 line=dict(color=COLOURS[k], dash=dash, width=w), marker=dict(size=5),
                                 hovertemplate="%{y:.1%}"))
    fig.update_layout(legend=dict(y=-0.2, yanchor="top"))
    plot(fig)
    worst = seg["worst_route_directions"]
    html(ds.section("Route-directions with the largest total error (final forecast)"))
    html(ds.table([("Route", "l"), ("Direction", "l"), ("WAPE", "r"), ("Share of total error", "r"), ("Rows", "r")],
                  [[ds.esc(str(w["route"])), ds.esc(str(w["direction"])), fmt_pct(w["wape"]),
                    fmt_pct(w["share_of_total_error"]), ds.fmt_int(w["rows"])] for w in worst]))

    r = metrics["targets"][short]
    html(ds.section("How LightGBM was chosen (validation week)",
                    f"The final forecast blends it 50/50 with the historical average; the weight "
                    f"{r['blend']['weight_on_lightgbm']} was chosen on validation."))
    c1, c2 = st.columns([1.15, 1], gap="large")
    tun = r["tuning"]
    tun_vals = [[None, None, None, round(t["mae"], 4), round(t["wape"], 3)] for t in tun]
    c1.markdown('<p class="sub">Learning objective and tree size</p>' +
                ds.table([("Objective", "l"), ("Leaves", "r"), ("Best iteration", "r"), ("MAE", "r"), ("WAPE", "r")],
                         [[ds.esc(t["objective"]), str(t["num_leaves"]), str(t["best_iteration"]),
                           f"{t['mae']:.4f}", fmt_pct(t["wape"])] for t in tun],
                         bold=best_cells(tun_vals, [3, 4])), unsafe_allow_html=True)
    abl = r["ablation_valid"]
    abl_vals = [[None, round(v["mae"], 4), round(v["wape"], 3)] for v in abl.values()]
    c2.markdown('<p class="sub">Feature-group ablation</p>' +
                ds.table([("Features", "l"), ("MAE", "r"), ("WAPE", "r")],
                         [[ds.esc(k[0].upper() + k[1:]), f"{v['mae']:.4f}", fmt_pct(v["wape"])]
                          for k, v in abl.items()], bold=best_cells(abl_vals, [1, 2])),
                unsafe_allow_html=True)
    imp = pd.Series(r["feature_importance_gain_share"]).head(12)[::-1]
    fig = ds.figure(height=380, xaxis_tickformat=".0%",
                    title=dict(text="Feature importance (share of total gain)",
                               font=dict(family=ds.SERIF, size=17, color=ds.INK), x=0, y=0.98),
                    yaxis=dict(showgrid=False, tickfont=dict(size=12, color=ds.INK)),
                    xaxis=dict(showgrid=True, gridcolor="#EBEEF1", showline=False))
    fig.add_trace(go.Bar(x=imp.values, y=imp.index, orientation="h", marker_color=ds.LINE,
                         hovertemplate="%{y}: %{x:.1%}<extra></extra>"))
    plot(fig)


def page_crowding(metrics: dict) -> None:
    cr = metrics["crowding"]
    page_header("Crowding levels and the capacity assumption",
                f"SUNT has no vehicle capacity. Capacities are the minimum seated-plus-standing figures in "
                f"{ds.esc(cr['source'])}: midiônibus 40, ônibus básico <strong>70 (base case)</strong>, "
                f"padron 80, articulado 100. Levels use load factor = estimated load / capacity: low &lt; "
                f"{THRESHOLDS[0]:.0%}, medium {THRESHOLDS[0]:.0%}–{THRESHOLDS[1]:.0%}, high ≥ {THRESHOLDS[1]:.0%}.")
    ct = metrics["targets"]["load"]["crowding_test"]
    rows, vals = [], []
    for name, res in ct.items():
        f1 = [res[p]["macro_f1"] for p in ("ensemble", "seasonal_naive", "hist_average")]
        vals.append([None] * 4 + [-round(x, 3) for x in f1] + [None, None])
        rows.append([f"{VEHICLES[name]} ({res['capacity']})",
                     *[fmt_pct(res["actual_shares"][k]) for k in LEVELS],
                     *[f"{x:.3f}" for x in f1],
                     f"{res['ensemble']['per_class']['high']['precision']:.3f}",
                     f"{res['ensemble']['per_class']['high']['recall']:.3f}"])
    bold = set()
    for i, v in enumerate(vals):   # best macro-F1 within each scenario (row)
        best = min(v[4:7])
        bold |= {(i, j) for j in range(4, 7) if v[j] == best}
    html(ds.section("Test weeks, every capacity scenario",
                    "Macro-F1 of the crowding level each method implies. Bold marks the best method per scenario."))
    html(ds.table([("Scenario", "l"), ("Low", "r"), ("Medium", "r"), ("High", "r"), ("Final forecast", "r"),
                   ("Same hour last week", "r"), ("Historical average", "r"), ("Precision", "r"), ("Recall", "r")],
                  rows, bold=bold,
                  groups=[("", 1), ("Share of actual hours", 3), ("Macro-F1", 3), ("High level, final forecast", 2)]))

    html(ds.section("Confusion matrix, final forecast",
                    "Rows are the actual level, columns the forecast level; counts are route-hours."))
    c1, c2 = st.columns([1, 2.4], gap="large")
    name = c1.selectbox("Confusion matrix for scenario", list(ct), index=list(ct).index("basico"),
                        format_func=lambda k: f"{VEHICLES[k]} ({CAPACITY_SCENARIOS[k]})")
    cm = np.array(ct[name]["ensemble"]["confusion"]["matrix"])
    share = cm / cm.sum(axis=1, keepdims=True)
    c1.markdown(f'<p class="small">Of the hours that really were high, the forecast also called '
                f'{share[2, 2]:.0%} high. Of those really low, it called {share[0, 0]:.0%} low.</p>',
                unsafe_allow_html=True)
    labels = [l.capitalize() for l in LEVELS]
    fig = ds.figure(height=340, margin=dict(l=8, r=8, t=10, b=8),
                    xaxis=dict(title="Forecast level", side="top", showline=False, ticks=""),
                    yaxis=dict(title="Actual level", autorange="reversed", showgrid=False))
    for i in range(3):     # shading stays light enough for dark text in every cell
        for j in range(3):
            fig.add_annotation(x=labels[j], y=labels[i], showarrow=False, font=dict(color=ds.INK, size=14),
                               text=f"<b>{cm[i, j]:,}</b><br><span style='font-size:11px'>{share[i, j]:.0%} of row</span>")
    fig.add_trace(go.Heatmap(z=share, x=labels, y=labels,
                             colorscale=[[0, "#FFFFFF"], [0.15, "#E4F0EE"], [1, "#7DB7B1"]], zmin=0, zmax=1,
                             showscale=False, xgap=3, ygap=3, customdata=cm,
                             hovertemplate="Actual %{y}, forecast %{x}: %{customdata:,} route-hours<extra></extra>"))
    with c2:
        plot(fig)
    burst = metrics["targets"]["load"]["segments_test"]["burst_hours"]["ensemble"]
    html(ds.section("Hours with burst validations",
                    "A single stop with more than 100 boardings; almost all at terminal stations at peak times. "
                    "They are kept, not capped, and reported separately."))
    order = sorted(burst.items(), key=lambda kv: kv[0] == "True")
    html(ds.table([("Hours", "l"), ("MAE", "r"), ("WAPE", "r"), ("Rows", "r")],
                  [["With burst" if k == "True" else "Without burst", f"{v['mae']:.2f}", fmt_pct(v["wape"]),
                    ds.fmt_int(v["n"])] for k, v in order]))


def page_forecast(metrics: dict) -> None:
    day = pd.Timestamp(metrics["split"]["forecast_demo"])
    page_header(f"Next-day forecast for {day.strftime('%A %d %B %Y')}")
    html('<div class="note" style="border-color:#B23A32"><p><strong>Demonstration, not an evaluated result.</strong> '
         'This is a genuine next-day forecast from data up to 28 Apr 2024. There are no actuals for this day in our '
         'study data, so it is a demonstration, not an evaluated result.</p></div>')
    f = load_predictions(f"forecast_{metrics['split']['forecast_demo']}")
    cap_name = st.select_slider("Capacity assumption", list(CAPACITY_SCENARIOS), value="basico",
                                format_func=lambda k: f"{VEHICLES[k]} ({CAPACITY_SCENARIOS[k]})", key="fc_cap")
    cap = CAPACITY_SCENARIOS[cap_name]
    f["level"] = crowding_level(f["load_forecast"], cap)
    top = f[f["level"] == "high"].sort_values("load_forecast", ascending=False)
    figs = [("Route-hours forecast", ds.fmt_int(len(f)), "Every route-direction and hour"),
            ("Forecast high crowding", ds.fmt_int(len(top)), f"At or above {THRESHOLDS[1]:.0%} of {cap}")]
    plan_file = ROOT / "reports" / "planning.json"
    plan = json.loads(plan_file.read_text(encoding="utf-8"))["precision_at_k"]["50"] if plan_file.exists() else None
    if plan:
        figs.append(("Top-50 alerts truly high, test weeks", fmt_pct(plan["ensemble"]),
                     f"Historical average {fmt_pct(plan['hist_average'])}, last week "
                     f"{fmt_pct(plan['seasonal_naive'])} (capacity 70)"))
    html(ds.figures(figs, accent=1))

    html(ds.section(f"Planning view: route-hours forecast as high crowding (≥ {THRESHOLDS[1]:.0%} of {cap})",
                    "These are the hours to check first for extra trips or larger vehicles. Highest estimated load "
                    "first; the 25 shown are sortable."))
    show = top.assign(Hour=top["ts_hour"].dt.strftime("%H:00"))[
        ["route", "direction", "Hour", "demand_forecast", "load_forecast"]].head(25)
    show.columns = ["Route", "Dir", "Hour", "Boardings forecast", "Est. peak load forecast"]
    st.dataframe(show.round(1), hide_index=True, width="stretch",
                 column_config={"Boardings forecast": st.column_config.NumberColumn(format="%.1f"),
                                "Est. peak load forecast": st.column_config.ProgressColumn(
                                    format="%.1f", min_value=0, max_value=float(max(120, show.iloc[:, 4].max())))})

    html(ds.section("One route through the day", "Bars: boardings forecast. Line: estimated peak load per bus, "
                                                 "with the high-crowding threshold dashed."))
    options = (f.groupby(["route", "direction"])["demand_forecast"].sum().sort_values(ascending=False))
    choice = st.selectbox("Route · direction", [f"{r} · {d}" for r, d in options.index])
    r, d = [x.strip() for x in choice.split("·")]
    one = f[(f["route"] == r) & (f["direction"] == d)].sort_values("ts_hour")
    fig = ds.figure(height=380, hovermode="x unified", xaxis=dict(tickformat="%H:%M"),
                    yaxis=dict(title="Boardings", rangemode="tozero"),
                    yaxis2=dict(title="Estimated load", overlaying="y", side="right", rangemode="tozero",
                                showgrid=False, tickfont=dict(size=11.5, color=ds.INK_2),
                                title_font=dict(size=12, color=ds.INK_2)))
    fig.add_trace(go.Bar(x=one["ts_hour"], y=one["demand_forecast"], name="Boardings forecast",
                         marker_color="#B9D9D5", hovertemplate="%{y:,.1f}"))
    fig.add_trace(go.Scatter(x=one["ts_hour"], y=one["load_forecast"], name="Est. peak load forecast", yaxis="y2",
                             mode="lines+markers", line=dict(color=ds.INK, width=2.4), marker=dict(size=5),
                             hovertemplate="%{y:,.1f}"))
    fig.add_trace(go.Scatter(x=[one["ts_hour"].min(), one["ts_hour"].max()], y=[THRESHOLDS[1] * cap] * 2,
                             yaxis="y2", mode="lines", name=f"High from {THRESHOLDS[1] * cap:.0f}",
                             line=dict(color="#B23A32", dash="dash", width=1.2), hoverinfo="skip"))
    plot(fig)


def page_data(metrics: dict) -> None:
    page_header("Data and limitations", "What the numbers rest on, and where they stop.", occupancy_note=False)
    sp = metrics["split"]
    items = [
        ("Source", "Salvador Urban Network Transportation (SUNT), Ferreira et al., <em>Scientific Data</em> 12, 1320 "
                   "(2025), doi:10.1038/s41597-025-05674-6; dataset doi:10.17632/85fdtx3kr5.1, licensed CC BY 4.0. "
                   "We use the origin-destination tables for 1 Mar to 28 Apr 2024 (59 days, 37.6 million stop "
                   "events), aggregated to route × direction × hour."),
        ("Split", f"Train {sp['train'][0]} to {sp['train'][1]}; validation {sp['valid'][0]} to {sp['valid'][1]}; "
                  f"test {sp['test'][0]} to {sp['test'][1]}. Good Friday (29 Mar) is in training, so holiday "
                  f"behaviour is not tested."),
        ("What counts as occupancy", f"<strong>{ESTIMATE_LEAD}</strong> {ds.esc(ESTIMATE_REST)}"),
        ("Missing hours (D8)", "Hours a route regularly runs but SUNT did not record are <em>missing data</em>, never "
                               "zero demand. They are not scored. SUNT's timetable file covers May–June 2024, so it "
                               "cannot confirm which hours were scheduled in March–April."),
        ("Malformed trips (D9)", "222 trips on 2–3 April repeat stop numbers; their loads are unusable and those "
                                 "route-directions are out of scope."),
        ("Burst validations", "2,685 stop events with more than 100 boardings, 99.8% at 10 terminal stations at the "
                              "first stop of a trip. Kept, not capped; load results are shown with and without them."),
        ("Capacity", "Not in the data. Crowding uses ABNT NBR 15570 minimum capacities and is reported for four "
                     "vehicle classes because the fleet mix per route is unknown."),
        ("Intervals", "The 80% bands hit their target overall, but not everywhere: estimated-load bands cover only "
                      "about half of night hours (00:00–02:00). Coverage by period is in RESULTS.md."),
    ]
    html('<dl class="essay">' + "".join(f"<dt>{ds.esc(k)}</dt><dd>{v}</dd>" for k, v in items) + "</dl>")


def day_month(date: str) -> str:
    """'2024-03-01' -> '1 Mar' (no leading zero; %-d is not portable to Windows)."""
    t = pd.Timestamp(date)
    return f"{t.day} {t:%b}"


def sidebar(metrics: dict) -> str:
    sp = metrics["split"]
    with st.sidebar:
        html(f'<div class="mast"><div class="bullet" aria-hidden="true">52</div><div><h1>{TITLE}</h1>'
             f'<p>CS3011 Artificial Intelligence<br>Group 52, PDPM IIITDM Jabalpur</p></div></div>')
        pages = list(PAGES)
        choice = st.radio("Page", pages, label_visibility="collapsed")
        html(f'<div class="side-note"><p><strong>Data</strong> SUNT bus network, Salvador, Brazil. '
             f'{day_month(sp["train"][0])} to {day_month(sp["test"][1])} {sp["test"][1][:4]}.</p>'
             f'<p><strong>Test weeks</strong> {pd.Timestamp(sp["test"][0]).day} to {day_month(sp["test"][1])} {sp["test"][1][:4]}, '
             f'scored on observed route-hours only.</p>'
             f'<p><a href="{REPO}" target="_blank" rel="noopener">Code, results and report on GitHub</a></p></div>')
    return choice


PAGES = {"Forecast explorer": page_explorer, "Model comparison": page_comparison,
         "Crowding and capacity": page_crowding, "Next-day forecast": page_forecast,
         "Data and limitations": page_data}


def main() -> None:
    st.set_page_config(page_title="Transit demand and occupancy", layout="wide")
    st.html(ds.stylesheet())
    metrics = load_metrics()
    choice = sidebar(metrics)
    PAGES[choice](metrics)


main()
