# Decision log

Newest first. Each entry records what was decided, why, and what it rules out.

## D9. Malformed trips (24 Oct 2026)

- **Finding:** 222 SUNT trips repeat stop sequence numbers with different stop IDs and timestamps. All are on 2 and 3 April 2024, on three route-directions (1235 I, 1246 V, 1383 V). Every trip of those route-directions on those days is malformed, and they appear on no other day. They cover 116 route-hours (0.021%) and 5,555 boardings (0.011%). One of them holds the only negative inferred alighting in the data.
- **Decision:** keep them in the route-hour table, flagged by `n_malformed_trips`. Their estimated loads are unreliable, so `load_reliable` is False in those route-hours and they are never load targets. In practice they are also out of scope, because those route-directions have only 2 days of history (below the 10-day minimum).
- **Effect on targets:** boardings negligible (at most 330 boardings could be double-counted); estimated load in those 116 route-hours unusable; no validation or test rows are affected.

## D8. Absent route-hours are missing, not zero (24 Oct 2026)

- **Problem:** the route-hour table only has a row when SUNT recorded a stop event. An absent hour can mean "no bus scheduled" or "a bus ran but SUNT has no record". SUNT's timetable (GTFS) covers 21 May to 21 Jun 2024, not our study period, so it cannot separate the two.
- **Decision:**
    1. Observed rows are targets, including the 22,674 rows (4.2%) with zero boardings: a bus was recorded and no card was tapped.
    2. Each route, direction, day type and service hour gets a profile from **training days only**. A cell is *regular* if observed on at least 80% of training days of that day type.
    3. An absent hour in a regular cell is a **missing record**: excluded from targets and metrics, and NaN in features. It is never filled with zero.
    4. Absent hours in non-regular cells are treated as no regular service and are not predicted.
    5. Route-directions observed on fewer than 10 training days are out of scope (38 of 713, 1,160 rows).
- **Why:** zero-filling would turn likely data gaps into fake zero demand and pad the test set with easy zeros. The forecast is therefore "boardings in this hour, given that the route runs", which matches how an operator with a timetable would use it.
- **Implementation:** `src/transit/data/service.py`, tested in `tests/test_service.py`.

## D7. Aggregation unit and hour definition (24 Oct 2026)

- **Decision:** the modelling table has one row per route (`route_short_name`), direction (`I` or `V`) and clock hour of `stop_time`. A service day's file runs from about 03:45 to about 02:15 the next morning, so the clock hour, not the service date, is the time key.
- **Why:** route-hour is the level at which planners set frequencies, and it keeps the table small enough for free cloud hosting.
- **Consequence:** hours with no bus on a route produce no row. Whether a missing hour means zero demand is decided in the modelling code, not in the pipeline.

## D6. Code reuse (24 Oct 2026)

- **Decision:** no code is copied from repositories without a licence (SUNT examples, the Aarhus thesis repository, the Nashville and Trondheim research repositories). Their ideas are cited. Code from MIT-licensed repositories may be adapted with attribution.

## D5. "Extra trips needed" (24 Oct 2026)

- **Decision:** optional. If shown, it is labelled as an illustrative estimate under the stated capacity assumption. It is dropped if it cannot be justified.

## D4. Capacity assumption for crowding levels (24 Oct 2026)

- **Decision:** SUNT has no vehicle capacity. Crowding levels will use a capacity value documented with its source, and results will be reported under at least three alternative values.
- **Status:** the value and its source are not chosen yet (occupancy module).

## D3. Chronological split and holidays (24 Oct 2026)

- **Decision:** train 1 Mar to 7 Apr 2024, validate 8 to 14 Apr, test 15 to 28 Apr. 29 and 30 Apr are excluded.
- **Correction recorded:** Good Friday (29 Mar 2024) is inside the training period, so it is not a held-out holiday-generalisation test. The test window has no weekday national holiday.

## D2. Title and occupancy wording (24 Oct 2026)

- **Decision:** use the registered title exactly: "AI Based Public Transport Demand and Occupancy Prediction". The occupancy target is called "estimated on-board load derived from fare-card trip chaining", never measured occupancy. No validation for Indian or tier-2 cities is claimed.

## D1. Primary dataset (24 Oct 2026)

- **Decision:** SUNT origin-destination tables, 1 March to 28 April 2024.
- **Why:** the only candidate found with real demand and on-board load labels in files we could download and open, under CC BY 4.0. Alternatives compared: Victoria train counts (strongest alternative), UrbanBus, TfNSW bus occupancy, TfL BUSTO, MTA hourly ridership, Trafiklab KoDa, BMRCL Bengaluru, and the repositories suggested earlier. The comparison is in the team's decision report.
- **Rules out:** simulated data (for example the Pune bus optimisation repository's ridership) as evidence of real-world accuracy.
