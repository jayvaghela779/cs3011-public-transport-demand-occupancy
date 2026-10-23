"""Project-wide paths, dates and data-source settings.

Everything that defines *which* data we use and *how* we split it lives here,
so that a reviewer can check it in one place.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

# Repository root: src/transit/config.py -> parents[2]
ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "sunt_od"
PROCESSED_DIR = DATA_DIR / "processed"
MANIFEST_PATH = DATA_DIR / "manifest" / "sunt_od_manifest.csv"

# SUNT source, pinned to one commit so the downloaded files never change.
SUNT_REPO = "LabIA-UFBA/SUNT"
SUNT_COMMIT = "f8d90fb38f3b1a6f74a18f0298d72fe0c6eaa54c"
SUNT_RAW_URL = f"https://raw.githubusercontent.com/{SUNT_REPO}/{SUNT_COMMIT}/data/od/{{filename}}"

# Study period: 1 Mar to 28 Apr 2024 (59 days). 29-30 Apr are excluded because
# those files cover noticeably fewer routes than other weekdays.
START_DATE = date(2024, 3, 1)
END_DATE = date(2024, 4, 28)

# Chronological split (decision D3). The test window is used once, after tuning.
TRAIN_END = date(2024, 4, 7)
VALID_END = date(2024, 4, 14)
# Test: 15 Apr to END_DATE.
