# AI Based Public Transport Demand and Occupancy Prediction

CS3011 Artificial Intelligence course project, PDPM IIITDM Jabalpur. Group 52.

The system analyses public-transport data to forecast passenger demand and estimated on-board load (our occupancy target), so that service planning can respond to demand.

> **Status (24 Oct 2026): work in progress.** The data pipeline is being built. No models or results exist yet. Every result reported later will be produced by a script committed in this repository.

## Team

| Member | Roll number | Module |
| --- | --- | --- |
| Jay Pravin Vaghela (lead) | 24BCS104 | Architecture, demand model, integration |
| Akshar Jasoliya | 24BCS101 | Data pipeline |
| Tirth Jasoliya | 24BCS102 | Occupancy model and evaluation |
| Disha Khushalani | 24BCS076 | Streamlit app |
| Shivani Mahour | 24BME054 | Presentation and documentation |

Module owners are a proposal and may change; see [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md).

## Data

We use the **Salvador Urban Network Transportation (SUNT)** dataset (Salvador, Brazil; bus, 2024 to 2025), licensed CC BY 4.0. We use its origin-destination (OD) tables for 1 March to 28 April 2024.

What the data does and does not tell us:

- **Demand:** boardings per stop per trip, from contactless fare-card validations.
- **Occupancy:** an **estimated on-board load**. Alightings are inferred by the dataset authors through fare-card trip chaining, and load is computed from boardings minus inferred alightings. It is **not directly measured occupancy**.
- **Known gaps:** riders aged 65+ travel without a card and are not recorded; there is no vehicle capacity in the data.
- **Scope:** the data is from Salvador, Brazil. This project makes **no claim of validation for Indian or tier-2 cities**.

Full provenance, licence and column definitions are in [docs/DATA.md](docs/DATA.md).

**Attribution.** Ferreira, M. V., Souza, M., Rios, T. N., Fernandes, I. F. C., Nery, J., Gama, J., Bifet, A. & Rios, R. A. (2025). *Salvador Urban Network Transportation (SUNT): A Landmark Spatiotemporal Dataset for Public Transportation.* Scientific Data 12, 1320. https://doi.org/10.1038/s41597-025-05674-6. Dataset: https://doi.org/10.17632/85fdtx3kr5.1 (CC BY 4.0).

## Quick start

Requires Python 3.10 or newer. Works in Google Colab, on Linux, and on Windows (PowerShell).

```bash
git clone https://github.com/jayvaghela779/cs3011-public-transport-demand-occupancy.git
cd cs3011-public-transport-demand-occupancy
pip install -r requirements.txt
pip install -e .

# 1. Download the 59 pinned SUNT OD files (about 510 MB) and verify checksums
python -m transit.data.download

# 2. Build the route x direction x hour table and the quality report
python -m transit.data.build

# 3. Run the tests
pytest
```

Raw files are cached in `data/raw/` and are never committed.

## Repository layout

```
docs/                 project plan, decision log, data card
data/manifest/        pinned list of SUNT source files with SHA-256 checksums
data/raw/             downloaded SUNT files (git-ignored)
data/processed/       derived tables and quality report
src/transit/          project code (installed as the `transit` package)
tests/                pytest tests
```

## How this project uses outside work

- **Data:** SUNT, used under CC BY 4.0 with attribution. Derived files state what we changed.
- **Ideas, not code:** we studied the SUNT examples repository, an Aarhus University thesis on passenger forecasting, and published bus-occupancy studies. Repositories without a licence are read and cited, never copied.
- **AI assistance:** parts of the code and documentation were drafted with the help of Claude (Anthropic) under the team's direction. Commits that include AI-assisted work carry a `Co-Authored-By` line.

## Licence

The licence for this repository's own code is still to be agreed by the team. SUNT-derived data files remain under CC BY 4.0 (see [docs/DATA.md](docs/DATA.md)).
