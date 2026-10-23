"""Read and (for maintainers) create the pinned manifest of SUNT OD files.

The manifest lists every daily file we use with its size and SHA-256 hash, so
the downloader can prove it received exactly the files the project was built on.

Maintainer use only (needs a local clone of SUNT checked out at SUNT_COMMIT):

    python -m transit.data.manifest --sunt-od-dir path/to/SUNT/data/od
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import date, timedelta
from pathlib import Path

from transit import config

FIELDS = ["date", "filename", "bytes", "sha256"]


def od_filename(day: date) -> str:
    return f"od-{day.isoformat()}.parquet"


def study_dates(start: date = config.START_DATE, end: date = config.END_DATE) -> list[date]:
    n = (end - start).days + 1
    return [start + timedelta(days=i) for i in range(n)]


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def read_manifest(path: Path = config.MANIFEST_PATH) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["bytes"] = int(r["bytes"])
    return rows


def write_manifest(sunt_od_dir: Path, path: Path = config.MANIFEST_PATH) -> list[dict]:
    rows = []
    for day in study_dates():
        fp = sunt_od_dir / od_filename(day)
        if not fp.exists():
            raise FileNotFoundError(f"Missing SUNT file for {day}: {fp}")
        rows.append({"date": day.isoformat(), "filename": fp.name,
                     "bytes": fp.stat().st_size, "sha256": sha256_of(fp)})
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sunt-od-dir", type=Path, required=True, help="SUNT clone's data/od folder")
    args = p.parse_args()
    rows = write_manifest(args.sunt_od_dir)
    total = sum(r["bytes"] for r in rows) / 1e6
    print(f"Wrote {len(rows)} entries ({total:.0f} MB) to {config.MANIFEST_PATH}")


if __name__ == "__main__":
    main()
