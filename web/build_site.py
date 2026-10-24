"""Assemble the GitHub Pages site for the in-browser dashboard.

    python web/build_site.py OUT_DIR

Copies web/index.html and every file it lists (the app, the transit modules it
imports and the committed result files) into OUT_DIR, keeping their repository
paths, so the site serves them from the same origin. The list lives only in
web/index.html; tests/test_web.py checks it against what the app reads.
The pages workflow (.github/workflows/pages.yml) runs this on every relevant
push to main and commits the result to the gh-pages branch.
"""

from __future__ import annotations

import re
import shutil
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


def build(out: Path) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    files = listed_files()
    for f in files:
        src = ROOT / f
        if not src.is_file():
            raise SystemExit(f"{f} is listed in web/index.html but does not exist")
        (out / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out / f)
    shutil.copy2(INDEX, out / "index.html")
    (out / ".nojekyll").write_text("", encoding="utf-8")   # serve files as they are (keeps __init__.py)
    (out / "README.md").write_text(README, encoding="utf-8")
    return files


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    done = build(Path(sys.argv[1]))
    print(f"Site written to {sys.argv[1]}: index.html and {len(done)} files")
