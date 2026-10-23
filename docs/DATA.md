# Data card

## Source

| Item | Value |
| --- | --- |
| Dataset | Salvador Urban Network Transportation (SUNT) |
| Authors | Ferreira, Souza, Rios, Fernandes, Nery, Gama, Bifet, Rios (LabIA, Federal University of Bahia) |
| Paper | Scientific Data 12, 1320 (2025), https://doi.org/10.1038/s41597-025-05674-6 |
| Dataset DOI | https://doi.org/10.17632/85fdtx3kr5.1 (Mendeley Data, version 1) |
| Files we use | `data/od/od-YYYY-MM-DD.parquet` from https://github.com/LabIA-UFBA/SUNT |
| Pinned version | SUNT commit `f8d90fb38f3b1a6f74a18f0298d72fe0c6eaa54c` (15 Sep 2026) |
| Dates used | 1 March to 28 April 2024 (59 daily files) |
| Checksums | [`data/manifest/sunt_od_manifest.csv`](../data/manifest/sunt_od_manifest.csv) (SHA-256 per file) |

## Licence

SUNT data is licensed **CC BY 4.0**. Checked on 24 Oct 2026 on all three hosts:

- GitHub README of LabIA-UFBA/SUNT: "licensed under the CC BY 4.0 License".
- Mendeley Data record 10.17632/85fdtx3kr5.1: CC BY 4.0.
- Hugging Face dataset card `labiaufba/PublicTransportationSunt`: `cc-by-4.0`.

The Scientific Data **article** carries its own licence (CC BY-NC-ND 4.0 per its rights section). That applies to the paper's text, which we cite but do not reproduce.

CC BY 4.0 lets us share adapted data if we credit the authors, link the licence and say what we changed. Our changes are listed below. Raw SUNT files are not committed to this repository; the pipeline downloads them.

## What the OD table contains

One row per vehicle stop event on a trip (route, direction, stop, vehicle, trip, timestamp), with:

| SUNT column | Meaning (from SUNT's data dictionary) |
| --- | --- |
| `n-boardings` | Passengers boarding at this stop (can be fractional) |
| `n-alighting` | Passengers alighting at this stop (**inferred**) |
| `lag_loading` | Load before the vehicle arrives |
| `balance` | Load after alightings |
| `loading` | Load after boardings |

The SUNT documentation spells the first two with underscores, but the files use hyphens. Our code renames them to `n_boardings` and `n_alighting`.

## How SUNT derives these numbers, and what that means for us

- **Boardings** come from contactless fare-card validations matched to vehicle GPS. Unmatched validations are discarded or spread across buses, which is a likely reason for fractional counts.
- **Alightings are inferred**, not measured: Salvador has no exit validators. SUNT uses trip chaining (a passenger's next boarding, within 1.1 km walking distance).
- **Load is therefore an estimate.** We call our occupancy target **estimated on-board load derived from fare-card trip chaining**. It is not directly measured occupancy.
- **Riders aged 65+** ride free without a card and are not in the AFC data, so demand and load are under-counted.
- **Burst validations:** mobile turnstiles occasionally register many passengers at once (the paper cites a 264-boarding case). Our quality report counts stop events with more than 100 boardings.
- **No vehicle capacity** is provided, so crowding levels need an external assumption (decision D4).

## Derived table: `data/processed/route_hour.parquet`

Built by `python -m transit.data.build` from the 59 verified raw files. One row per route, direction and clock hour of `stop_time` (decision D7). About 12.5 MB.

| Column | Meaning |
| --- | --- |
| `service_date` | SUNT service day the stop event came from (file date) |
| `route`, `direction` | SUNT `route_short_name` and `direction_id` (`I` or `V`) |
| `ts_hour` | Clock hour of the stop events (local Salvador time, no time zone stored) |
| `boardings` | Sum of boardings in the hour |
| `alightings` | Sum of inferred alightings in the hour |
| `n_stop_events`, `n_trips` | Stop events and distinct trips in the hour |
| `load_max` | Highest estimated on-board load at any stop event in the hour |
| `load_trip_peak_mean` | Mean, over trips, of each trip's highest estimated load in the hour |
| `n_burst_events` | Stop events with more than 100 boardings (possible burst validations) |

Hours in which a route ran no bus have no row. How to treat them is decided in the modelling code.

### First full build (24 Oct 2026)

Figures from [`data/processed/quality_report.json`](../data/processed/quality_report.json):

| Measure | Value |
| --- | --- |
| Stop events read | 37,600,997 |
| Route-hour rows | 541,611 |
| Routes; route-directions | 410; 713 |
| Total boardings | 51,353,180 |
| Burst stop events (> 100 boardings) | 2,685 |
| Trips repeating a stop sequence number | 222 of 1,168,044 (0.019%) |
| Raw stop events with a negative value | 1 |
| Route-hours with no load value | 340 |
| Highest estimated load at one stop event | 469.6 |

All six checks passed: unique keys, 59 of 59 days, boardings conserved exactly, no negative aggregated values, malformed trips under 0.1%, and no stop events outside the 30-hour service window. A rerun produced byte-identical files, and a rebuild under pandas 2.2 gave the same table as pandas 3.0.

The highest load (469.6) is far above any plausible bus capacity. Loads like this come from burst validations and are why crowding levels need care in the occupancy module.

### What we changed from SUNT (CC BY 4.0 attribution)

- Selected 59 daily OD files (1 Mar to 28 Apr 2024) at SUNT commit `f8d90fb`.
- Renamed columns, dropped stop-level identifiers (stop, vehicle, register code) from the output.
- Aggregated stop events to route, direction and hour as described above. No values were edited, capped or removed.
