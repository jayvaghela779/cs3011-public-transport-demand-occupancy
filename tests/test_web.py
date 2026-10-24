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
    pins = [l.split()[0] for l in (config.ROOT / "web" / "wheels.txt").read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]
    lines = [l for l in (config.ROOT / "web" / "wheels.txt").read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")]
    assert all("==" in l and "--hash=sha256:" in l for l in lines), "pin every wheel with a hash"
    wheels = re.findall(r'"([^"]+\.whl)"', re.search(r"const WHEELS = \[(.*?)\];", html, re.S).group(1))
    expected = {p.split("==")[0].replace("-", "_") + "-" + p.split("==")[1] for p in pins}
    assert {"-".join(w.split("-")[:2]) for w in wheels} == expected, "WHEELS in index.html must match web/wheels.txt"


def test_build_site_copies_every_listed_file(tmp_path):
    sys.path.insert(0, str(config.ROOT / "web"))
    try:
        import build_site
    finally:
        sys.path.pop(0)
    files = build_site.build(tmp_path, wheels=False)   # no network in tests
    assert (tmp_path / "index.html").read_text(encoding="utf-8") == INDEX.read_text(encoding="utf-8")
    manifest = json.loads((tmp_path / "site-manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["files"]) == set(files)
    import hashlib
    for f, info in manifest["files"].items():
        data = (config.ROOT / f).read_bytes()
        assert info == {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}, f
    assert (tmp_path / ".nojekyll").exists()      # without it GitHub Pages drops __init__.py
    for f in files:
        assert (tmp_path / f).read_bytes() == (config.ROOT / f).read_bytes(), f


def test_page_loads_files_from_its_own_site():
    html = INDEX.read_text(encoding="utf-8")
    assert "https://raw.githubusercontent.com" not in html, "serve files from the Pages site (same origin)"
    assert "site-manifest.json" in html and "crypto.subtle.digest" in html, "check files against the manifest"
    assert "@gh-pages/" in html, "the CDN mirror must point at the published branch, not main"


def test_app_local_modules_and_fonts_are_listed():
    """The app imports app/design.py, which embeds the fonts in app/fonts; the public build needs all of them."""
    files = set(listed_files())
    app_dir = config.ROOT / "app"
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    local = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names
             if (app_dir / f"{a.name}.py").is_file()}
    assert "design" in local
    for m in local:
        assert f"app/{m}.py" in files, f"app/{m}.py (imported by the app) is not listed in web/index.html"
    design = (app_dir / "design.py").read_text(encoding="utf-8")
    fonts = set(re.findall(r'"([\w.-]+\.woff2)"', design))
    assert fonts, "design.py should name its font files"
    for f in fonts:
        assert (app_dir / "fonts" / f).is_file(), f
        assert f"app/fonts/{f}" in files, f"app/fonts/{f} is not listed in web/index.html"


def test_theme_matches_between_local_app_and_public_build():
    """.streamlit/config.toml (local app) and web/index.html (public build) must set the same theme."""
    tomllib = __import__("tomllib")
    cfg = tomllib.loads((config.ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    local = {f"theme.{k}": v for k, v in cfg["theme"].items() if k != "sidebar"}
    local |= {f"theme.sidebar.{k}": v for k, v in cfg["theme"].get("sidebar", {}).items()}
    local["client.toolbarMode"] = cfg["client"]["toolbarMode"]
    html = INDEX.read_text(encoding="utf-8")
    block = re.search(r"streamlitConfig: \{(.*?)\}", html, re.S).group(1)
    web = {k: json.loads(v) for k, v in re.findall(r'"((?:theme|client)\.[\w.]+)":\s*("[^"]*"|true|false)', block)}
    assert web == local
    import importlib.util
    spec = importlib.util.spec_from_file_location("design", config.ROOT / "app" / "design.py")
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    assert local["theme.primaryColor"] == design.LINE and local["theme.textColor"] == design.INK
