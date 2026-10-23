"""Service profile and modelling slots (decision D8): absent hours are never zero."""

from datetime import date, timedelta

import pandas as pd
import pytest

from transit.data.service import (MIN_TRAIN_DAYS, add_calendar, build_slots, daytype,
                                  in_scope_route_directions, service_profile)

# Ten Mondays to Fridays (4-15 Mar 2024) of training, then two test weekdays.
TRAIN_DAYS = [d for d in (date(2024, 3, 4) + timedelta(days=i) for i in range(12)) if d.weekday() < 5]
TEST_DAYS = [date(2024, 3, 18), date(2024, 3, 19)]
TRAIN_END = TRAIN_DAYS[-1]
ALL_DAYS = TRAIN_DAYS + TEST_DAYS


def rows(route, hour, days, boardings=5.0):
    return [{"service_date": pd.Timestamp(d), "route": route, "direction": "I",
             "ts_hour": pd.Timestamp(d) + pd.Timedelta(hours=hour), "boardings": boardings,
             "load_trip_peak_mean": 10.0, "n_malformed_trips": 0} for d in days]


def table(*parts):
    return pd.DataFrame([r for p in parts for r in p])


def test_daytype_and_service_hour():
    t = add_calendar(pd.DataFrame({
        "service_date": pd.to_datetime(["2024-03-29", "2024-03-30", "2024-03-31", "2024-04-01"]),
        "ts_hour": pd.to_datetime(["2024-03-29 08:00", "2024-03-30 23:00", "2024-04-01 01:00",
                                   "2024-04-01 04:00"]),
    }))
    assert t["daytype"].tolist() == ["holiday", "saturday", "sunday", "weekday"]
    assert t["service_hour"].tolist() == [8, 23, 25, 4]   # 01:00 next morning = hour 25


def test_regular_threshold_is_80_percent_of_training_days():
    t = table(rows("A", 8, TRAIN_DAYS[:8]),      # 8 of 10 = regular
              rows("B", 8, TRAIN_DAYS[:7]))      # 7 of 10 = not regular
    p = service_profile(t, TRAIN_END, ALL_DAYS).set_index("route")
    assert p.loc["A", "regular"] and not p.loc["B", "regular"]
    assert p.loc["A", "share"] == pytest.approx(0.8)


def test_profile_uses_training_days_only():
    base = table(rows("A", 8, TRAIN_DAYS[:7]))
    with_test = table(rows("A", 8, TRAIN_DAYS[:7]), rows("A", 8, TEST_DAYS))
    pd.testing.assert_frame_equal(service_profile(base, TRAIN_END, ALL_DAYS),
                                  service_profile(with_test, TRAIN_END, ALL_DAYS))


def test_absent_regular_hour_becomes_missing_record_not_zero():
    t = table(rows("A", 8, TRAIN_DAYS), rows("A", 8, TEST_DAYS[:1]))   # absent on 19 Mar
    s = build_slots(t, TRAIN_END, ALL_DAYS)
    miss = s[s["status"] == "missing_record"]
    assert len(miss) == 1
    assert miss.iloc[0]["service_date"] == pd.Timestamp("2024-03-19")
    assert pd.isna(miss.iloc[0]["boardings"])          # NaN, never 0
    assert not miss.iloc[0]["load_reliable"]


def test_irregular_hours_get_no_slots_but_observed_rows_stay():
    t = table(rows("A", 8, TRAIN_DAYS), rows("A", 22, TRAIN_DAYS[:3]))   # 22:00 only 3 of 10
    s = build_slots(t, TRAIN_END, ALL_DAYS)
    late = s[s["service_hour"] == 22]
    assert (late["status"] == "observed").all() and len(late) == 3
    assert not late["regular"].any()


def test_observed_zero_boardings_are_kept_as_zero():
    t = table(rows("A", 8, TRAIN_DAYS), rows("A", 8, TEST_DAYS, boardings=0.0))
    s = build_slots(t, TRAIN_END, ALL_DAYS)
    test_rows = s[s["service_date"].isin(pd.to_datetime(TEST_DAYS))]
    assert (test_rows["status"] == "observed").all()
    assert (test_rows["boardings"] == 0).all()


def test_route_directions_with_little_training_history_are_out_of_scope():
    t = table(rows("A", 8, TRAIN_DAYS), rows("C", 8, TRAIN_DAYS[:MIN_TRAIN_DAYS - 1]))
    scope = in_scope_route_directions(t, TRAIN_END)
    assert scope["route"].tolist() == ["A"]
    assert set(build_slots(t, TRAIN_END, ALL_DAYS)["route"]) == {"A"}


def test_malformed_route_hours_are_not_load_reliable():
    r = rows("A", 8, TRAIN_DAYS)
    r[0]["n_malformed_trips"] = 2
    s = build_slots(table(r), TRAIN_END, ALL_DAYS)
    assert s["load_reliable"].sum() == len(TRAIN_DAYS) - 1
