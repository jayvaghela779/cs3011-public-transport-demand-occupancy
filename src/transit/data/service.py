"""Service calendar, service profile and modelling slots (decisions D8 and D9).

The route-hour table only has a row when SUNT recorded at least one stop event.
An absent route-hour can mean "no bus was scheduled" or "a bus ran but SUNT has
no record of it" (AVL and fare data not matched, outage, cancelled trip).
SUNT's timetable (GTFS) covers 21 May to 21 Jun 2024, not our study period, so
it cannot tell the two apart. We therefore never fill absent hours with zero.

Instead, each route, direction, day type and hour of the service day gets a
*service profile* computed from the TRAINING period only:

    regular   observed on at least REGULAR_SHARE of training days of that day type

A modelling *slot* is either
    observed        a row exists (boardings may be 0: a bus ran, nobody tapped)
    missing_record  a regular cell with no row on that day (unknown demand)

Hours that are neither observed nor regular are treated as "no regular service"
and are not predicted. Missing records are excluded from targets and metrics;
features computed from them are left as NaN.

Estimated loads are unreliable in route-hours containing malformed trips
(decision D9), so `load_reliable` is False there.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from transit import config
from transit.data.manifest import study_dates

# National holiday inside the study period. Tiradentes (21 Apr 2024) fell on a
# Sunday, so it is already a Sunday service day.
HOLIDAYS = {date(2024, 3, 29): "Good Friday (Sexta-feira da Paixao), national holiday"}

REGULAR_SHARE = 0.8      # share of training days of the same day type
MIN_TRAIN_DAYS = 10      # route-directions observed on fewer training days are out of scope

SLOT_KEYS = ["route", "direction", "service_date", "service_hour"]
DAYTYPES = ["weekday", "saturday", "sunday", "holiday"]


def daytype(d: pd.Series) -> pd.Series:
    """Day type of each service date: weekday, saturday, sunday or holiday."""
    d = pd.to_datetime(d)
    hol = d.dt.date.isin(HOLIDAYS.keys())
    dow = d.dt.day_of_week
    out = pd.Series("weekday", index=d.index, dtype="object")
    out[dow == 5] = "saturday"
    out[dow == 6] = "sunday"
    out[hol] = "holiday"
    return out


def add_calendar(table: pd.DataFrame) -> pd.DataFrame:
    """Add service_hour (hours since the service date's midnight, e.g. 25 = 01:00
    the next morning), day of week, day type and holiday flag."""
    t = table.copy()
    t["service_date"] = pd.to_datetime(t["service_date"]).dt.normalize()
    t["ts_hour"] = pd.to_datetime(t["ts_hour"])
    t["service_hour"] = ((t["ts_hour"] - t["service_date"]) // pd.Timedelta(hours=1)).astype("int64")
    t["dow"] = t["service_date"].dt.day_of_week.astype("int64")
    t["daytype"] = daytype(t["service_date"])
    t["is_holiday"] = t["daytype"].eq("holiday")
    return t


def _days_per_daytype(dates: list[date]) -> pd.Series:
    s = pd.Series(pd.to_datetime(dates))
    return daytype(s).value_counts()


def service_profile(table: pd.DataFrame, train_end: date = config.TRAIN_END,
                    dates: list[date] | None = None) -> pd.DataFrame:
    """Per (route, direction, daytype, service_hour): how often it was observed in
    training, and whether that makes it a regular service cell."""
    dates = study_dates() if dates is None else dates
    train_dates = [d for d in dates if d <= train_end]
    t = add_calendar(table)
    tr = t[t["service_date"] <= pd.Timestamp(train_end)]
    n_days = _days_per_daytype(train_dates)
    prof = (tr.groupby(["route", "direction", "daytype", "service_hour"])["service_date"]
            .nunique().rename("train_days_observed").reset_index())
    prof["train_days_of_type"] = prof["daytype"].map(n_days).astype("int64")
    prof["share"] = prof["train_days_observed"] / prof["train_days_of_type"]
    prof["regular"] = prof["share"] >= REGULAR_SHARE
    return prof


def in_scope_route_directions(table: pd.DataFrame, train_end: date = config.TRAIN_END,
                              min_days: int = MIN_TRAIN_DAYS) -> pd.DataFrame:
    """Route-directions observed on at least `min_days` training days."""
    t = table[pd.to_datetime(table["service_date"]) <= pd.Timestamp(train_end)]
    n = t.groupby(["route", "direction"])["service_date"].nunique().rename("train_days").reset_index()
    return n[n["train_days"] >= min_days].reset_index(drop=True)


def build_slots(table: pd.DataFrame, train_end: date = config.TRAIN_END,
                dates: list[date] | None = None) -> pd.DataFrame:
    """All modelling slots for in-scope route-directions: observed rows plus
    missing records in regular cells. Measures are NaN for missing records."""
    dates = study_dates() if dates is None else dates
    prof = service_profile(table, train_end, dates)
    scope = in_scope_route_directions(table, train_end)
    t = add_calendar(table).merge(scope[["route", "direction"]], on=["route", "direction"])

    cal = pd.DataFrame({"service_date": pd.to_datetime(dates)})
    cal["daytype"] = daytype(cal["service_date"])
    regular = prof[prof["regular"]].merge(scope[["route", "direction"]], on=["route", "direction"])
    expected = regular[["route", "direction", "daytype", "service_hour"]].merge(cal, on="daytype")

    slots = expected.merge(t, on=SLOT_KEYS + ["daytype"], how="outer", indicator=True)
    slots["status"] = slots["_merge"].map({"both": "observed", "right_only": "observed",
                                           "left_only": "missing_record"}).astype("object")
    slots = slots.drop(columns="_merge")
    slots = slots.merge(prof[["route", "direction", "daytype", "service_hour", "share", "regular"]],
                        on=["route", "direction", "daytype", "service_hour"], how="left")
    slots["regular"] = slots["regular"].fillna(False).astype(bool)
    slots["share"] = slots["share"].fillna(0.0)

    # Fill calendar fields for missing records (measures stay NaN, never zero).
    slots["ts_hour"] = slots["service_date"] + pd.to_timedelta(slots["service_hour"], unit="h")
    slots["dow"] = slots["service_date"].dt.day_of_week.astype("int64")
    slots["is_holiday"] = slots["daytype"].eq("holiday")
    obs = slots["status"].eq("observed")
    slots["load_reliable"] = (obs & slots["load_trip_peak_mean"].notna()
                              & slots["n_malformed_trips"].fillna(0).eq(0))
    return slots.sort_values(SLOT_KEYS, kind="stable").reset_index(drop=True)
