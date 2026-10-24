"""Baselines computed from the same leak-free features as the model.

Each baseline has a primary rule and a fixed fallback chain, so every scored
row gets a prediction and the comparison with the model is on identical rows.
The fallback used is recorded so it can be reported.

    seasonal_naive   same hour, same weekday, 7 days earlier
    dow4_mean        mean of the same hour on the last 4 same weekdays
    hist_average     mean of all earlier days of the same day type and hour

Fallback chain after the primary rule: same-day-type history, then the
last-7-days mean at that hour, then the training median for that hour.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PRIMARY = {
    "seasonal_naive": "y_lag7",
    "dow4_mean": "y_mean_dow4",
    "hist_average": "y_hist_daytype",
}
FALLBACKS = ["y_hist_daytype", "y_roll7"]


def hour_medians(train: pd.DataFrame) -> pd.Series:
    """Training-period median of the target for each service hour."""
    return train.groupby("service_hour")["target"].median()


def predict(X: pd.DataFrame, name: str, medians: pd.Series) -> tuple[np.ndarray, pd.Series]:
    """Predictions and the column each prediction came from."""
    cols = [PRIMARY[name]] + [c for c in FALLBACKS if c != PRIMARY[name]]
    pred = pd.Series(np.nan, index=X.index)
    source = pd.Series("", index=X.index, dtype="object")
    for c in cols:
        take = pred.isna() & X[c].notna()
        pred[take] = X.loc[take, c]
        source[take] = c
    take = pred.isna()
    overall = float(medians.median()) if len(medians) else 0.0
    pred[take] = X.loc[take, "service_hour"].map(medians).fillna(overall).to_numpy()
    source[take] = "hour_median"
    return pred.to_numpy(dtype="float64"), source
