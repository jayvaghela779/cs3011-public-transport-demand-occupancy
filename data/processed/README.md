# Processed data

Files in this folder are derived from the **Salvador Urban Network Transportation (SUNT)** dataset by Ferreira et al. (2025), https://doi.org/10.17632/85fdtx3kr5.1, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Changes: 59 daily OD files (1 Mar to 28 Apr 2024) aggregated from stop events to route, direction and hour. See [docs/DATA.md](../../docs/DATA.md) for column definitions, caveats and the full list of changes.

Loads are SUNT's estimates from fare-card trip chaining, not directly measured occupancy.

Regenerate with:

```bash
python -m transit.data.download
python -m transit.data.build
```
