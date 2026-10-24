"""Crowding levels from estimated on-board load (decision D10).

SUNT has no vehicle capacity, so crowding needs an assumption. We take the
minimum capacities (seated plus standing, at 6 standing passengers per m2)
that the Brazilian urban bus standard ABNT NBR 15570 sets for each vehicle
class, and use the standard 12-14 m "onibus basico" as the base case:

    midionibus 40 | onibus basico 70 (base) | padron 80 | articulado 100

Levels use the load factor LF = estimated load / capacity:

    low     LF < 0.5
    medium  0.5 <= LF < 0.8
    high    LF >= 0.8   (near or over capacity)

The loads are SUNT estimates from fare-card trip chaining, not measured
occupancy, and the fleet mix per route is unknown. Results are therefore
reported for every capacity scenario, not only the base case.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

BASE_CAPACITY = 70
CAPACITY_SCENARIOS = {"midionibus": 40, "basico": 70, "padron": 80, "articulado": 100}
LEVELS = ["low", "medium", "high"]
THRESHOLDS = (0.5, 0.8)
SOURCE = ("ABNT NBR 15570:2009, Table 1 (minimum capacity by vehicle class) and "
          "Table 2 (6 standing passengers per m2)")


def crowding_level(load, capacity: float = BASE_CAPACITY) -> np.ndarray:
    lf = np.asarray(load, dtype="float64") / capacity
    out = np.where(lf < THRESHOLDS[0], "low", np.where(lf < THRESHOLDS[1], "medium", "high"))
    out = out.astype(object)
    out[np.isnan(lf)] = None
    return out


def level_shares(load: pd.Series, capacity: float) -> dict:
    lv = pd.Series(crowding_level(load, capacity)).value_counts(normalize=True)
    return {k: float(lv.get(k, 0.0)) for k in LEVELS}
