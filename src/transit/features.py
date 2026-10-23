"""Day-ahead features for route-hour forecasting, with no future information.

Forecast setting: before service day D starts (about 03:00), predict every
route-hour slot of day D. Every feature for day D is computed only from
service days strictly before D. A service day ends around 02:15 the next
morning, before day D's first trips, so all of day D-1 is known in time.

Values from missing records and from hours without service are NaN, never 0
(decision D8). LightGBM handles NaN natively; baselines fall back explicitly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from transit.data.service import SLOT_KEYS

CELL = ["route", "direction", "service_hour"]
LAGS = [1, 7, 14, 21, 28]

CALENDAR_FEATURES = ["service_hour", "dow", "is_weekend", "is_holiday", "lag7_was_holiday"]
ID_FEATURES = ["route", "direction"]


def target_series(slots: pd.DataFrame, target: str) -> pd.Series:
    """Observed value of `target`, NaN where it must not be used."""
    y = slots[target].where(slots["status"].eq("observed"))
    if target.startswith("load"):
        y = y.where(slots["load_reliable"])
    return y.astype("float64")


def _lag_frame(slots: pd.DataFrame, value: pd.Series, name: str, lags=LAGS) -> pd.DataFrame:
    """value at the same route, direction and service hour k service days earlier."""
    base = slots[CELL + ["service_date"]].copy()
    base["_v"] = value.to_numpy()
    out = pd.DataFrame(index=slots.index)
    for k in lags:
        shifted = base.copy()
        shifted["service_date"] = shifted["service_date"] + pd.Timedelta(days=k)
        m = slots[CELL + ["service_date"]].merge(shifted, on=CELL + ["service_date"], how="left")
        out[f"{name}_lag{k}"] = m["_v"].to_numpy()
    return out


def _expanding_daytype_mean(slots: pd.DataFrame, value: pd.Series) -> np.ndarray:
    """Mean of all earlier observed values in the same cell and day type."""
    f = slots[CELL + ["daytype", "service_date"]].copy()
    f["_v"] = value.to_numpy()
    f["_order"] = np.arange(len(f))
    f = f.sort_values(CELL + ["daytype", "service_date"])
    f["_v0"] = f["_v"].fillna(0.0)
    f["_n0"] = f["_v"].notna().astype("float64")
    g = f.groupby(CELL + ["daytype"], sort=False)
    prev_sum = g["_v0"].cumsum() - f["_v0"]          # sum of strictly earlier days
    prev_n = g["_n0"].cumsum() - f["_n0"]
    f["_mean"] = prev_sum / prev_n.replace(0, np.nan)
    return f.sort_values("_order")["_mean"].to_numpy()


def _route_day_total(slots: pd.DataFrame, value: pd.Series, lags=(1, 7)) -> pd.DataFrame:
    """Route-direction total of `value` on earlier service days."""
    f = slots[["route", "direction", "service_date"]].copy()
    f["_v"] = value.to_numpy()
    day = (f.groupby(["route", "direction", "service_date"])["_v"]
           .agg(lambda v: v.sum() if v.notna().any() else np.nan).rename("_t").reset_index())
    out = pd.DataFrame(index=slots.index)
    for k in lags:
        d = day.copy()
        d["service_date"] = d["service_date"] + pd.Timedelta(days=k)
        m = slots[["route", "direction", "service_date"]].merge(d, on=["route", "direction", "service_date"],
                                                                 how="left")
        out[f"rd_total_lag{k}"] = m["_t"].to_numpy()
    return out


def build_features(slots: pd.DataFrame, target: str) -> pd.DataFrame:
    """Feature frame (one row per slot) for `target` ('boardings' or 'load_trip_peak_mean')."""
    slots = slots.reset_index(drop=True)
    y = target_series(slots, target)
    X = slots[SLOT_KEYS + ["ts_hour", "daytype", "dow", "is_holiday", "status", "regular"]].copy()
    X["is_weekend"] = X["dow"] >= 5
    X["lag7_was_holiday"] = (X["service_date"] - pd.Timedelta(days=7)).dt.date.isin(
        set(slots.loc[slots["is_holiday"], "service_date"].dt.date))

    short = "y"
    lags = _lag_frame(slots, y, short)
    X = pd.concat([X, lags], axis=1)
    X["y_mean_dow4"] = lags[[f"y_lag{k}" for k in (7, 14, 21, 28)]].mean(axis=1, skipna=True)
    X["y_roll7"] = _lag_frame(slots, y, "_r", lags=range(1, 8)).mean(axis=1, skipna=True)
    X["y_hist_daytype"] = _expanding_daytype_mean(slots, y)

    # Service intensity known from earlier weeks (proxy for the timetable).
    trips = slots["n_trips"].where(slots["status"].eq("observed")).astype("float64")
    tl = _lag_frame(slots, trips, "trips", lags=[7, 14, 21, 28])
    X["trips_lag7"] = tl["trips_lag7"]
    X["trips_mean_dow4"] = tl.mean(axis=1, skipna=True)

    demand = target_series(slots, "boardings")
    X = pd.concat([X, _route_day_total(slots, demand)], axis=1)
    if target != "boardings":
        dl = _lag_frame(slots, demand, "boardings", lags=[7, 14, 21, 28])
        X["boardings_lag7"] = dl["boardings_lag7"]
        X["boardings_mean_dow4"] = dl.mean(axis=1, skipna=True)

    X["target"] = y.to_numpy()
    X["n_burst_events"] = slots["n_burst_events"].to_numpy()
    for c in ID_FEATURES:
        X[c] = X[c].astype("category")
    return X


def model_feature_names(target: str) -> list[str]:
    cols = (ID_FEATURES + CALENDAR_FEATURES
            + [f"y_lag{k}" for k in LAGS] + ["y_mean_dow4", "y_roll7", "y_hist_daytype",
                                             "trips_lag7", "trips_mean_dow4",
                                             "rd_total_lag1", "rd_total_lag7"])
    if target != "boardings":
        cols += ["boardings_lag7", "boardings_mean_dow4"]
    return cols
