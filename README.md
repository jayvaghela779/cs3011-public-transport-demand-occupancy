# AI Based Public Transport Demand and Occupancy Prediction

CS3011 Artificial Intelligence course project, PDPM IIITDM Jabalpur. Group 52.

The system analyses public-transport data to forecast passenger demand and estimated on-board load (our occupancy target), so that service planning can respond to demand.

> **Status (24 Oct 2026):** data pipeline, models, evaluation and dashboard work end to end. Full results: [reports/RESULTS.md](reports/RESULTS.md). Every number comes from a committed script and its output files.
>
> **Public dashboard:** https://jayvaghela779.github.io/cs3011-public-transport-demand-occupancy/. It runs in your browser; the first visit downloads about 85 MB, see [Public dashboard](#public-dashboard-github-pages) below.
>
> **Documents:** project report ([source](reports/project_report/CS3011_Group52_Project_Report.md), [PDF](reports/project_report/CS3011_Group52_Project_Report.pdf), [Word](reports/project_report/CS3011_Group52_Project_Report.docx)); code walkthrough for the team ([docs/PROJECT_CODE_WALKTHROUGH.md](docs/PROJECT_CODE_WALKTHROUGH.md)).

## Results (test weeks, 15–28 April 2024)

Day-ahead forecasts per route, direction and hour, scored on observed route-hours only. WAPE is total absolute error divided by total actual; lower is better.

| Method | Demand WAPE | Demand MAE (boardings) | Estimated-load WAPE | Load MAE (passengers) |
| --- | --- | --- | --- | --- |
| **Final: 0.5 × LightGBM + 0.5 × historical average** | **18.15%** | **17.86** | **19.20%** | **4.69** |
| LightGBM alone | 18.39% | 18.10 | 19.39% | 4.74 |
| Historical average (same day type and hour) | 18.35% | 18.06 | 19.35% | 4.73 |
| Mean of last 4 same weekdays | 20.75% | 20.42 | 21.45% | 5.24 |
| Same hour last week | 23.67% | 23.30 | 25.39% | 6.21 |

- **Against the usual baseline:** the final forecast cuts error by 23% versus "same hour last week".
- **Against a strong baseline:** against the historical average the gain is small: −0.20 WAPE points for demand (95% bootstrap interval over route-directions −0.29 to −0.06), lower on 13 of the 14 test days. It is a gain in absolute error only; on RMSE the historical average is slightly better for demand (29.58 vs 29.72).
- **LightGBM alone does not beat the historical average.** We report this as a finding (decision D12). The test weeks were scored twice, and both runs are disclosed.
- **Uncertainty:** each forecast has an 80% prediction interval (quantile models plus conformal calibration on validation). It covers 80.4% of actual test demand and 79.3% of test load overall, but only about 52% of estimated-load values between midnight and 2 AM (see RESULTS.md, decision D13).
- **Crowding levels** (load ÷ capacity: low < 50%, high ≥ 80%) for a standard 70-passenger bus: macro-F1 0.769. "High crowding" alerts are right 79% of the time and catch 61% of high hours. Results for 40, 80 and 100-passenger buses are in the results file.

## Team

| Member | Presents and answers questions on (provisional) |
| --- | --- |
| Jay Pravin Vaghela (lead) | Framing, architecture, models and the blend decision |
| Akshar Jasoliya | Data, licence, pipeline and quality rules |
| Tirth Jasoliya | Evaluation protocol, results and error analysis |
| Disha Khushalani | Dashboard demo, public site and local fallback |
| Shivani Mahour | Crowding, capacity assumption and limitations |

This is the speaking split in the slides, not a record of who wrote which code; see "How this project uses outside work" below and [docs/TEAM_PRESENTATION_GUIDE.md](docs/TEAM_PRESENTATION_GUIDE.md).

## Data

We use the **Salvador Urban Network Transportation (SUNT)** dataset (Salvador, Brazil; bus, 2024 to 2025), licensed CC BY 4.0. We use its origin-destination (OD) tables for 1 March to 28 April 2024.

What the data does and does not tell us:

- **Demand:** boardings per stop per trip, from contactless fare-card validations.
- **Occupancy:** an **estimated on-board load**. Alightings are inferred by the dataset authors through fare-card trip chaining, and load is computed from boardings minus inferred alightings. It is **not directly measured occupancy**.
- **Known gaps:** riders aged 65+ travel without a card and are not recorded; there is no vehicle capacity in the data.
- **Scope:** the data is from Salvador, Brazil. This project makes **no claim of validation for Indian or tier-2 cities**.

Full provenance, licence and column definitions are in [docs/DATA.md](docs/DATA.md); how the parts fit together is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

**Attribution.** Ferreira, M. V., Souza, M., Rios, T. N., Fernandes, I. F. C., Nery, J., Gama, J., Bifet, A. & Rios, R. A. (2025). *Salvador Urban Network Transportation (SUNT): A Landmark Spatiotemporal Dataset for Public Transportation.* Scientific Data 12, 1320. https://doi.org/10.1038/s41597-025-05674-6. Dataset: https://doi.org/10.17632/85fdtx3kr5.1 (CC BY 4.0).

## Quick start

Requires Python 3.10 or newer. GitHub Actions runs the tests and `python -m transit.verify` on Ubuntu (Python 3.11 and 3.12) and on Windows (Python 3.12). The committed results were produced on Linux with Python 3.13 (pandas 3.0, LightGBM 4.7). A full rerun from a fresh clone with Python 3.12 (pandas 3.1, LightGBM 4.7) reproduced them exactly; see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#reproduction-record). The data build also gives the same table under pandas 2.2. The commands are the same in Windows PowerShell and in Google Colab. The full pipeline has not yet been run on Windows or Colab, only the tests.

```bash
git clone https://github.com/jayvaghela779/cs3011-public-transport-demand-occupancy.git
cd cs3011-public-transport-demand-occupancy
pip install -r requirements.txt
pip install -e .

# 1. Download the 59 pinned SUNT OD files (about 510 MB) and verify checksums
python -m transit.data.download

# 2. Build the route x direction x hour table and the quality report
python -m transit.data.build

# 3. Train, tune on validation, score test, forecast 29 Apr (about 8 min on 2 CPUs)
python -m transit.models.run

# 4. Write reports/RESULTS.md and figures (stops if numbers disagree)
python -m transit.report

# 5. Check the rerun against the committed table and metrics
python -m transit.verify

# 6. Run the tests, then the dashboard
pytest
streamlit run app/streamlit_app.py
```

`requirements.txt` allows newer releases. If a future release ever changes the results, install the exact versions that reproduced them instead: `pip install -r requirements-lock.txt` (tested on Python 3.12).

Step-by-step setup for team laptops (including Windows), the 3-minute demo script and troubleshooting are in [docs/DEMO_RUNBOOK.md](docs/DEMO_RUNBOOK.md).

The dashboard reads only committed files, so `pip install -r requirements.txt` and `streamlit run app/streamlit_app.py` are enough for the demo. No download is needed, and it works offline.

## Public dashboard (GitHub Pages)

**https://jayvaghela779.github.io/cs3011-public-transport-demand-occupancy/**

The same app runs as a static site on GitHub Pages. [`web/index.html`](web/index.html) runs the unchanged `app/streamlit_app.py` inside the visitor's browser with [stlite](https://github.com/whitphx/stlite) 1.12.0 (Streamlit 1.65 on Pyodide 314.0.3, Python compiled to WebAssembly). There is no server, so nothing sleeps and no account beyond GitHub is involved.

- **Publishing:** [`.github/workflows/pages.yml`](.github/workflows/pages.yml) runs [`web/build_site.py`](web/build_site.py) whenever the app, its modules or the committed results change on `main`. It copies the app code, the result files and a SHA-256 manifest to the `gh-pages` branch, plus three pinned, hash-checked wheels ([`web/wheels.txt`](web/wheels.txt)).
- **Loading:** the page downloads every file through jsDelivr's mirror of `gh-pages`, checks each SHA-256, and re-fetches any mismatching copy from GitHub Pages. So it shows exactly the committed results. On the Indian home network we tested, `raw.githubusercontent.com` and `files.pythonhosted.org` were throttled to almost nothing and `github.io` was slow for large files; jsDelivr was not.
- **Checked on 24 Oct 2026:**
  - the published files are byte-identical to `main`;
  - in a real browser all five pages worked and matched the local app (for example route 137 I on 17 Apr, 15.3% against 7.7%; next day 9,566 route-hours, 481 high);
  - the in-browser recompute matched all ten reported test WAPEs.
- **Load time:** a first visit downloads about 85 MB. It took 83 s on a connection throttled to 10 Mbit/s and about 5 min 40 s at 2 Mbit/s. Repeat visits use the browser cache and were ready in about 40 s. If loading stops for two minutes the page suggests a reload.

**For the demo, run the app locally**: it starts instantly and needs no internet. If you show the public site, open it once on that laptop beforehand. The runbook has the details and the narrated backup video: [docs/DEMO_RUNBOOK.md](docs/DEMO_RUNBOOK.md).

Raw files are cached in `data/raw/` and are never committed. To reproduce everything in a browser, open [`notebooks/reproduce_on_colab.ipynb`](notebooks/reproduce_on_colab.ipynb) in Google Colab (not yet tried by the team).

## Repository layout

```
docs/                 plan, decisions (D1-D13), data card, architecture, viva question bank,
                      team presentation guide, demo runbook, final readiness checklist,
                      code walkthrough
data/manifest/        pinned list of SUNT source files with SHA-256 checksums
data/raw/             downloaded SUNT files (git-ignored)
data/processed/       route-hour table and quality report
data/predictions/     validation, test and next-day predictions used by the report and the app
reports/              metrics.json, RESULTS.md, figures, archived first test scoring, project report
src/transit/          project code (installed as the `transit` package)
app/                  Streamlit dashboard (design.py: look and fonts)
tests/                pytest tests
```

## How this project uses outside work

- **Data:** SUNT, used under CC BY 4.0 with attribution. Derived files state what we changed.
- **Fonts:** the dashboard bundles Newsreader and Overpass from the [Fontsource](https://fontsource.org) packages, both under the SIL Open Font License 1.1 (licence texts in `app/fonts/`).
- **Ideas, not code:** we studied the SUNT examples repository, an Aarhus University thesis on passenger forecasting, and published bus-occupancy studies. Repositories without a licence are read and cited, never copied.
- **AI assistance:** the code and documents in this repository were written in AI-assisted sessions with Claude (Anthropic), directed and reviewed by Jay. Every such commit carries a `Co-Authored-By` line; as of 24 Oct 2026 that is every commit. Teammates' own reviews and changes are committed from their own accounts.

## Licence

The licence for this repository's own code is still to be agreed by the team. SUNT-derived data files remain under CC BY 4.0 (see [docs/DATA.md](docs/DATA.md)).
