"""Regression and classification metrics used in every results table."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support


def regression_metrics(y: pd.Series | np.ndarray, p: pd.Series | np.ndarray) -> dict:
    """MAE, RMSE, WAPE (sum of absolute errors / sum of actuals) and bias."""
    y = np.asarray(y, dtype="float64")
    p = np.asarray(p, dtype="float64")
    if np.isnan(y).any() or np.isnan(p).any():
        raise ValueError("metrics need complete actuals and predictions")
    e = p - y
    total = np.abs(y).sum()
    return {
        "n": int(len(y)),
        "mae": float(np.abs(e).mean()),
        "rmse": float(np.sqrt((e ** 2).mean())),
        "wape": float(np.abs(e).sum() / total) if total > 0 else float("nan"),
        "bias": float(e.mean()),
    }


def classification_metrics(y_true, y_pred, labels: list[str]) -> dict:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    prec, rec, f1, sup = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    return {
        "n": int(len(y_true)),
        "accuracy": float((y_true == y_pred).mean()),
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "per_class": {lab: {"precision": float(prec[i]), "recall": float(rec[i]), "f1": float(f1[i]),
                            "support": int(sup[i])} for i, lab in enumerate(labels)},
        "confusion": {"labels": labels,
                      "matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist()},
    }
