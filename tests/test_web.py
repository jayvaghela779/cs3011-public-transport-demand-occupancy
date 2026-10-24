"""Checks for the public in-browser build (web/index.html, served on GitHub Pages).

The page fetches a fixed list of files from the repository and runs the app with
stlite. These tests fail if that list misses a file the dashboard reads or a
module it imports, so the public site cannot drift from the local app.
"""

import ast
import json
import re
import subprocess
import sys

from transit import config

INDEX = config.ROOT / "web" / "index.html"
APP = config.ROOT / "app" / "streamlit_app.py"


def listed_files() -> list[str]:
    html = INDEX.read_text(encoding="utf-8")
    block = re.search(r"const FILES = \[(.*?)\];", html, re.S).group(1)
    return re.findall(r'"([^"]+)"', block)


def test_every_listed_file_exists():
    files = listed_files()
    assert files, "no files listed in web/index.html"
    missing = [f for f in files if not (config.ROOT / f).is_file()]
    assert not missing, missing


def test_entrypoint_and_transit_modules_are_listed():
    files = set(listed_files())
    assert "app/streamlit_app.py" in files
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module
            and n.module.startswith("transit")}
    assert mods, "the app should import transit modules"
    for m in mods | {"transit"}:
        path = "src/" + m.replace(".", "/") + (".py" if m != "transit" else "/__init__.py")
        assert path in files, f"{path} (imported by the app) is not listed in web/index.html"


def test_every_data_file_the_app_reads_is_listed():
    files = set(listed_files())
    m = json.loads((config.ROOT / "reports" / "metrics.json").read_text(encoding="utf-8"))
    needed = {"reports/metrics.json", "reports/planning.json",
              f"data/predictions/forecast_{m['split']['forecast_demo']}.parquet"}
    needed |= {f"data/predictions/{t}_{s}.parquet" for t in ("demand", "load") for s in ("valid", "test")}
    assert needed <= files, sorted(needed - files)


def test_app_modules_do_not_load_scikit_learn():
    """scikit-learn and SciPy add tens of MB to every browser visit; the app does not need them."""
    code = ("import sys; sys.path.insert(0, 'src'); import transit.metrics, transit.crowding; "
            "print('sklearn' in sys.modules)")
    out = subprocess.run([sys.executable, "-c", code], cwd=config.ROOT, capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False"


def test_versions_are_pinned():
    html = INDEX.read_text(encoding="utf-8")
    assert re.search(r"@stlite/browser@\d+\.\d+\.\d+/", html), "pin an exact stlite version"
    assert re.search(r"pyodide/v[\d.]+/full/pyodide\.mjs", html), "pin an exact Pyodide version"
    reqs = re.search(r"requirements: \[(.*?)\]", html).group(1)
    assert all("==" in r for r in re.findall(r'"([^"]+)"', reqs)), "pin package versions"


def test_build_site_copies_every_listed_file(tmp_path):
    sys.path.insert(0, str(config.ROOT / "web"))
    try:
        import build_site
    finally:
        sys.path.pop(0)
    files = build_site.build(tmp_path)
    assert (tmp_path / "index.html").read_text(encoding="utf-8") == INDEX.read_text(encoding="utf-8")
    assert (tmp_path / ".nojekyll").exists()      # without it GitHub Pages drops __init__.py
    for f in files:
        assert (tmp_path / f).read_bytes() == (config.ROOT / f).read_bytes(), f


def test_page_loads_files_from_its_own_site():
    html = INDEX.read_text(encoding="utf-8")
    assert "https://raw.githubusercontent.com" not in html, "serve files from the Pages site (same origin)"
    assert "new URL(f, document.baseURI)" in html
