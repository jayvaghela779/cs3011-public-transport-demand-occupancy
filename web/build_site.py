"""Assemble the GitHub Pages site for the in-browser dashboard.

    python web/build_site.py OUT_DIR

Copies web/index.html and every file it lists (the app, the transit modules it
imports and the committed result files) into OUT_DIR, keeping their repository
paths, and writes site-manifest.json with each file's size and SHA-256. The page
downloads the files (from a CDN mirror of the site, or the site itself) and only
uses a copy whose hash matches the manifest. The list lives only in
web/index.html; tests/test_web.py checks it against what the app reads.
The pages workflow (.github/workflows/pages.yml) runs this on every relevant
push to main and commits the result to the gh-pages branch.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"

README = """# gh-pages: public dashboard (generated)

This branch is written by `.github/workflows/pages.yml` from `main`; do not edit it by hand.
It holds `web/index.html` and the files it lists, copied from `main`, for
https://jayvaghela779.github.io/cs3011-public-transport-demand-occupancy/
Each commit message names the `main` commit it was built from.
"""


def listed_files(index: Path = INDEX) -> list[str]:
    block = re.search(r"const FILES = \[(.*?)\];", index.read_text(encoding="utf-8"), re.S)
    if not block:
        raise SystemExit("web/index.html has no FILES list")
    return re.findall(r'"([^"]+)"', block.group(1))


def source_commit() -> str:
    """The main commit the site is built from (GITHUB_SHA in Actions, else git)."""
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def build(out: Path) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    files = listed_files()
    for f in files:
        src = ROOT / f
        if not src.is_file():
            raise SystemExit(f"{f} is listed in web/index.html but does not exist")
        (out / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out / f)
    manifest = {"source_commit": source_commit(),
                "files": {f: {"bytes": (ROOT / f).stat().st_size,
                              "sha256": hashlib.sha256((ROOT / f).read_bytes()).hexdigest()} for f in files}}
    (out / "site-manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    shutil.copy2(INDEX, out / "index.html")
    (out / ".nojekyll").write_text("", encoding="utf-8")   # serve files as they are (keeps __init__.py)
    (out / "README.md").write_text(README, encoding="utf-8")
    return files


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    done = build(Path(sys.argv[1]))
    print(f"Site written to {sys.argv[1]}: index.html and {len(done)} files")
