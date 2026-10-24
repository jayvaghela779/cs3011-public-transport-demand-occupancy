# Predictions

Validation, test and next-day forecasts written by `python -m transit.models.run`. The report (`python -m transit.report`) and the dashboard read these files; nothing in them is edited by hand.

The `target` column and the features behind every forecast are derived from the **Salvador Urban Network Transportation (SUNT)** dataset by Ferreira et al. (2025), https://doi.org/10.17632/85fdtx3kr5.1, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes from SUNT are listed in [docs/DATA.md](../../docs/DATA.md).

| File | Rows | What it holds |
| --- | --- | --- |
| `demand_valid.parquet`, `load_valid.parquet` | one per slot, 8–14 Apr 2024 | forecasts from the model trained on the training weeks only |
| `demand_test.parquet`, `load_test.parquet` | one per slot, 15–28 Apr 2024 | forecasts from the model refit on training plus validation |
| `forecast_2024-04-29.parquet` | one per regular slot, 29 Apr 2024 | next-day demonstration forecast; no actuals, not evaluated |

In the validation and test files, `status` is `observed` or `missing_record`; missing records have no `target` and are never scored (decision D8). Loads are SUNT estimates from fare-card trip chaining, not measured occupancy.
