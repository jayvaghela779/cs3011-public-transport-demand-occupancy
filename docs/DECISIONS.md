# Decision log

Newest first. Each entry records what was decided, why, and what it rules out.

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
