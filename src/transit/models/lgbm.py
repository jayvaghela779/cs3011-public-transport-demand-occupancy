"""LightGBM training with early stopping on the validation week."""

from __future__ import annotations

import lightgbm as lgb
import numpy as np
import pandas as pd

BASE_PARAMS = {
    "learning_rate": 0.05,
    "min_data_in_leaf": 50,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l2": 1.0,
    "max_bin": 255,
    "seed": 42,
    "deterministic": True,
    "force_col_wise": True,
    "num_threads": 2,
    "verbose": -1,
}

# Small, documented grid. Selection uses validation WAPE only.
GRID = {
    "boardings": [
        {"objective": "regression", "num_leaves": 63},
        {"objective": "regression_l1", "num_leaves": 63},
        {"objective": "poisson", "num_leaves": 63},
        {"objective": "tweedie", "tweedie_variance_power": 1.3, "num_leaves": 63},
        {"objective": "poisson", "num_leaves": 255},
        {"objective": "regression", "num_leaves": 255},
    ],
    "load_trip_peak_mean": [
        {"objective": "regression", "num_leaves": 63},
        {"objective": "regression_l1", "num_leaves": 63},
        {"objective": "huber", "alpha": 15.0, "num_leaves": 63},
        {"objective": "poisson", "num_leaves": 63},
        {"objective": "regression_l1", "num_leaves": 255},
        {"objective": "regression", "num_leaves": 255},
    ],
}

MAX_ROUNDS = 3000
EARLY_STOP = 100


def _dataset(X: pd.DataFrame, features: list[str], reference=None) -> lgb.Dataset:
    return lgb.Dataset(X[features], label=X["target"], categorical_feature=["route", "direction"],
                       reference=reference, free_raw_data=False)


def fit_with_early_stopping(train: pd.DataFrame, valid: pd.DataFrame, features: list[str],
                            config: dict) -> lgb.Booster:
    params = {**BASE_PARAMS, **config, "metric": "l1"}
    dtr = _dataset(train, features)
    dva = _dataset(valid, features, reference=dtr)
    return lgb.train(params, dtr, num_boost_round=MAX_ROUNDS, valid_sets=[dva],
                     callbacks=[lgb.early_stopping(EARLY_STOP, verbose=False)])


def fit_fixed_rounds(train: pd.DataFrame, features: list[str], config: dict, rounds: int) -> lgb.Booster:
    params = {**BASE_PARAMS, **config, "metric": "l1"}
    return lgb.train(params, _dataset(train, features), num_boost_round=rounds)


def predict(model: lgb.Booster, X: pd.DataFrame, features: list[str]) -> np.ndarray:
    # Loads and boardings cannot be negative; L2/L1 objectives can go slightly below 0.
    return np.clip(model.predict(X[features], num_iteration=model.best_iteration or None), 0, None)
