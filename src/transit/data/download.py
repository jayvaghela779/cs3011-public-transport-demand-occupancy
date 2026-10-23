"""Download the pinned SUNT OD files and verify each one against the manifest.

    python -m transit.data.download            # all 59 days (about 510 MB)
    python -m transit.data.download --limit 3  # first 3 days, for a quick try

Files already present with the right checksum are skipped, so the command is
safe to re-run after an interrupted download.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests

from transit import config
from transit.data.manifest import read_manifest, sha256_of


def fetch(url: str, dest: Path, retries: int = 3, timeout: int = 120) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                with open(tmp, "wb") as f:
                    for block in r.iter_content(chunk_size=1 << 20):
                        f.write(block)
            tmp.replace(dest)
            return
        except requests.RequestException as e:
            if attempt == retries:
                raise
            wait = 5 * attempt
            print(f"  retry {attempt}/{retries - 1} in {wait}s ({e})", file=sys.stderr)
            time.sleep(wait)


def download_all(raw_dir: Path = config.RAW_DIR, limit: int | None = None,
                 manifest_path: Path = config.MANIFEST_PATH) -> list[Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    entries = read_manifest(manifest_path)
    if limit is not None:
        entries = entries[:limit]
    paths = []
    for i, e in enumerate(entries, 1):
        dest = raw_dir / e["filename"]
        label = f"[{i}/{len(entries)}] {e['filename']}"
        if dest.exists() and dest.stat().st_size == e["bytes"] and sha256_of(dest) == e["sha256"]:
            print(f"{label} already verified")
        else:
            fetch(config.SUNT_RAW_URL.format(filename=e["filename"]), dest)
            got = sha256_of(dest)
            if got != e["sha256"]:
                dest.unlink()
                raise RuntimeError(f"{label}: checksum mismatch (expected {e['sha256']}, got {got})")
            print(f"{label} downloaded and verified ({e['bytes'] / 1e6:.1f} MB)")
        paths.append(dest)
    return paths


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--limit", type=int, default=None, help="only the first N days")
    args = p.parse_args()
    paths = download_all(limit=args.limit)
    print(f"{len(paths)} files ready in {config.RAW_DIR}")


if __name__ == "__main__":
    main()
