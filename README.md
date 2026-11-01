# AI Based Public Transport Demand and Occupancy Prediction

CS3011 Artificial Intelligence course project, PDPM IIITDM Jabalpur. Group 52.

The system forecasts, before each service day, how many passengers will board each bus route in each direction and hour (**demand**), and the **estimated on-board load** of a typical bus on that route-hour. It compares LightGBM with simple baselines on held-out weeks, turns load into crowding levels under stated capacity assumptions, and shows the results in a Streamlit dashboard.

> **What this repository is.** The previous implementation of the project, kept as a **technical reference, a source of historical results and a working fallback**. It was written in AI-assisted sessions (see [Provenance and AI assistance](#provenance-and-ai-assistance)).
>
> The team's human-led redevelopment, under the planning assumption "Scenario 3: AI may assist; students do the substantive work", takes place in a separate repository, [jayvaghela779/transit-demand-occupancy](https://github.com/jayvaghela779/transit-demand-occupancy). Nothing in this repository describes or claims that work.
>
> - **Start here:** [docs/REFERENCE_GUIDE.md](docs/REFERENCE_GUIDE.md), how the existing system works and how to verify it.
> - **Redevelopment plan:** [docs/SCENARIO3_REDEVELOPMENT_GUIDE.md](docs/SCENARIO3_REDEVELOPMENT_GUIDE.md), per-member responsibilities, AI-use categories and acceptance gates.
> - **All documents:** [docs/README.md](docs/README.md).

## What the system predicts

- **Unit:** route × direction × clock hour of a service day (service hours 24–26 are 00:00–02:00 the next morning).
- **Horizon:** day-ahead. Every slot of day D is forecast from service days strictly before D.
- **Targets:** `boardings` (demand) and `load_trip_peak_mean` (mean over the hour's trips of each trip's highest estimated load).
- **Not measured occupancy.** SUNT infers alightings from fare-card trip chaining, so load is an estimate. Nothing here is checked against counted passengers.

## Architecture

```
SUNT OD files (59 days, pinned commit, SHA-256)
  -> transit.data.download -> data/raw/ (git-ignored)
  -> transit.data.build    -> data/processed/route_hour.parquet + quality_report.json
  -> transit.models.run    -> slots (missing != zero) -> leak-free features -> baselines + LightGBM
                              -> data/predictions/*.parquet + reports/metrics.json
  -> transit.report        -> reports/RESULTS.md + figures + planning.json
  -> app/streamlit_app.py  (reads committed outputs only) -> web/ build -> GitHub Pages
```

The full diagram, the files each stage reads and writes, and the main functions are in [REFERENCE_GUIDE §B](docs/REFERENCE_GUIDE.md#b-system-architecture).

| Path | Role |
| --- | --- |
| `src/transit/config.py` | Paths, pinned SUNT commit, study and split dates |
| `src/transit/data/` | Manifest and verified download, aggregation, quality checks, service slots (missing records) |
| `src/transit/features.py` | Day-ahead features using only earlier days |
| `src/transit/models/` | Baselines, LightGBM, and `run.py` (tuning, refit, blend, intervals, scoring, next-day forecast) |
| `src/transit/metrics.py`, `crowding.py` | Metrics; crowding levels and capacity scenarios |
| `src/transit/report.py`, `verify.py` | RESULTS.md and figures; comparison of a rerun with the committed files |
| `app/` | Streamlit dashboard (`design.py`: look and bundled fonts) |
| `web/`, `.github/workflows/` | Public in-browser build; CI and publishing workflows |
| `tests/` | pytest suite (98 tests on 28 Oct 2026) |
| `data/`, `reports/` | Manifest, processed table, predictions, metrics, results, figures, project report |

The file-by-file code map with functions, tests and commands is in [REFERENCE_GUIDE §C](docs/REFERENCE_GUIDE.md#c-code-map).

## Data

**Salvador Urban Network Transportation (SUNT)**, Salvador, Brazil, licensed CC BY 4.0. Origin-destination files for 1 March to 28 April 2024 (59 days), pinned to SUNT commit `f8d90fb` with SHA-256 checksums.

- **Demand** comes from contactless fare-card validations matched to vehicles. Riders aged 65+ travel without a card and are not recorded.
- **Load** is an estimate (inferred alightings); there is no vehicle capacity in the data.
- **Scope:** one city, two months. The project makes no claim of validation for Indian or tier-2 cities.
- Hours with no SUNT record are treated as **missing, not zero** (decision D8).

Details: [docs/DATA.md](docs/DATA.md) and [REFERENCE_GUIDE §D](docs/REFERENCE_GUIDE.md#d-dataset-and-preprocessing).

**Attribution.** Ferreira, M. V., Souza, M., Rios, T. N., Fernandes, I. F. C., Nery, J., Gama, J., Bifet, A. & Rios, R. A. (2025). *Salvador Urban Network Transportation (SUNT): A Landmark Spatiotemporal Dataset for Public Transportation.* Scientific Data 12, 1320. https://doi.org/10.1038/s41597-025-05674-6. Dataset: https://doi.org/10.17632/85fdtx3kr5.1 (CC BY 4.0).

## Historical results (legacy implementation)

These are the numbers this implementation produced, stored in [reports/metrics.json](reports/metrics.json) and written up in [reports/RESULTS.md](reports/RESULTS.md). They are a reference for comparison, not results of the redevelopment. They were reproduced by a full rerun on 27–28 Oct 2026 ([REFERENCE_GUIDE §I.6](docs/REFERENCE_GUIDE.md#i6-verification-record-2728-october-2026)).

Test weeks 15–28 April 2024; observed route-hours only; WAPE = total absolute error ÷ total actual, lower is better.

| Method | Demand WAPE | Demand MAE (boardings) | Estimated-load WAPE | Load MAE (passengers) |
| --- | --- | --- | --- | --- |
| Final: 0.5 × LightGBM + 0.5 × historical average | 18.15% | 17.86 | 19.20% | 4.69 |
| LightGBM alone | 18.39% | 18.10 | 19.39% | 4.74 |
| Historical average (same day type and hour) | 18.35% | 18.06 | 19.35% | 4.73 |
| Mean of last 4 same weekdays | 20.75% | 20.42 | 21.45% | 5.24 |
| Same hour last week | 23.67% | 23.30 | 25.39% | 6.21 |

- About 23% lower WAPE than "same hour last week" for demand.
- Only slightly better than the historical average: −0.20 WAPE points for demand (95% bootstrap interval over route-directions −0.29 to −0.06), and **worse on RMSE** for demand (29.72 against 29.58).
- **LightGBM alone did not beat the historical average on the test weeks** (it was slightly better on validation). The blend was introduced after the first test scoring, so the test weeks were scored twice; both scorings are disclosed (decision D12).
- 80% prediction intervals cover 80.4% of test demand and 79.3% of test load overall, but only about 52% of estimated-load values between midnight and 2 AM (D13).
- Crowding at an assumed 70-passenger capacity: macro-F1 0.769 (historical average 0.766). Results for 40, 80 and 100 passengers are in RESULTS.md.

## Reproduce and test

Python 3.10 or newer. CI runs the tests on Ubuntu (Python 3.11 and 3.12) and Windows (Python 3.12). The repository records full pipeline runs on Linux only.

```bash
git clone https://github.com/jayvaghela779/cs3011-public-transport-demand-occupancy.git
cd cs3011-public-transport-demand-occupancy
python -m pip install -r requirements.txt     # or requirements-lock.txt for the exact versions
python -m pip install -e .

python -m pytest -q                 # 98 passed on 28 Oct 2026

# Full rerun (overwrites the committed outputs in your working copy; 11-13 minutes on 2 CPUs plus the download)
python -m transit.data.download     # 59 pinned files, about 510 MB, checksums verified
python -m transit.data.build        # route-hour table and quality report; fails if a check fails
python -m transit.models.run        # tune on validation, refit, score test, forecast 29 Apr
python -m transit.report            # RESULTS.md and figures; stops if numbers disagree
python -m transit.verify            # compare the rerun's table and metrics with git HEAD
```

`transit.verify` proves reproduction only after a rerun: on a fresh clone it compares the committed files with themselves, which is what the CI step does. It checks the route-hour table and `metrics.json`, not the prediction files or figures. See [REFERENCE_GUIDE §I](docs/REFERENCE_GUIDE.md#i-reproduction-and-verification).

## Dashboard

```bash
streamlit run app/streamlit_app.py      # http://localhost:8501; reads committed files only, works offline
```

Five pages: Forecast explorer, Model comparison, Crowding and capacity, Next-day forecast, Data and limitations ([REFERENCE_GUIDE §H](docs/REFERENCE_GUIDE.md#h-dashboard-reference)). Setup on team laptops, the demo script and troubleshooting: [docs/DEMO_RUNBOOK.md](docs/DEMO_RUNBOOK.md).

A public copy runs in the browser on GitHub Pages: **https://jayvaghela779.github.io/cs3011-public-transport-demand-occupancy/**. It uses stlite (Streamlit on Pyodide), so a first visit downloads about 85 MB; the local app is the dependable demo path. It is published by [`.github/workflows/pages.yml`](.github/workflows/pages.yml) from [`web/`](web/) ([runbook §5](docs/DEMO_RUNBOOK.md#5-public-dashboard-on-github-pages)).

## Provenance and AI assistance

- **AI assistance:** the code and documents in this repository were written in AI-assisted sessions with Claude (Anthropic), directed and reviewed by Jay. On 28 Oct 2026, 74 of the 76 commits on `main` carry a `Co-Authored-By: Claude` line; the other two are GitHub web-interface merge commits of PRs #15 and #16, whose merged commits carry it. This history is kept unchanged. It is not a record of who in the team wrote what, and it is not evidence of Scenario 3 work.
- **Team:** Jay Pravin Vaghela (lead), Akshar Jasoliya, Tirth Jasoliya, Disha Khushalani, Shivani Mahour. Their proposed responsibilities for the redevelopment are in the [redevelopment guide](docs/SCENARIO3_REDEVELOPMENT_GUIDE.md); the speaking split for presenting this implementation is in [docs/TEAM_PRESENTATION_GUIDE.md](docs/TEAM_PRESENTATION_GUIDE.md) (written 24 Oct, provisional).
- **Data:** SUNT, used under CC BY 4.0 with attribution. Derived files state what was changed. Raw files are never committed.
- **Fonts:** Newsreader and Overpass from the [Fontsource](https://fontsource.org) packages, under the SIL Open Font License 1.1 (licence texts in `app/fonts/`).
- **Ideas, not code:** the SUNT examples repository, an Aarhus University thesis on passenger forecasting and published bus-occupancy studies were read and cited, never copied (decision D6).

## Licence

The licence for this repository's own code has not been chosen yet. SUNT-derived data files remain under CC BY 4.0 (see [docs/DATA.md](docs/DATA.md)).
