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

## Derived table

`data/processed/route_hour.parquet` is described in the pipeline section below once it is built.
