# Demo and installation runbook

How to install, check and run the dashboard on a team laptop, the 3-minute demo, and what to do when something breaks.

**Status on 24 Oct 2026.**
- The dashboard runs locally (the main plan for the demo).
- It is also public on GitHub Pages: **https://jayvaghela779.github.io/cs3011-public-transport-demand-occupancy/** (section 5). It runs in the visitor's browser and was checked on all five pages that day.
- Before you call it live in the evaluation, open it yourself that day.

## 1. Install and check (once per laptop, with internet)

Use **Python 3.12**. That is the version tested on Windows and Ubuntu in GitHub Actions (Python 3.11 is also tested on Ubuntu). Python 3.13 worked on our Linux machine; newer versions are untested. You also need **git**: `transit.verify` compares your copy with the committed files, so it needs a git clone, not a ZIP download.

### Windows (PowerShell)

```powershell
git clone https://github.com/jayvaghela779/cs3011-public-transport-demand-occupancy.git
cd cs3011-public-transport-demand-occupancy
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -q
python -m transit.verify
python -m streamlit run app/streamlit_app.py
```

In Command Prompt (cmd), activate with `.venv\Scripts\activate.bat` instead. The other commands are the same.

### macOS or Linux

```bash
git clone https://github.com/jayvaghela779/cs3011-public-transport-demand-occupancy.git
cd cs3011-public-transport-demand-occupancy
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt && python -m pip install -e .
python -m pytest -q
python -m transit.verify
python -m streamlit run app/streamlit_app.py
```

### What you should see

| Command | Expected result |
| --- | --- |
| `python -m pytest -q` | `93 passed` (the count grows if tests are added; nothing should fail) |
| `python -m transit.verify` | `data/processed/route_hour.parquet: all 541,611 rows x 12 columns match.` then `Reproduced: all 2326 values match ...` |
| `python -m streamlit run app/streamlit_app.py` | A browser tab opens at http://localhost:8501 with the title "AI Based Public Transport Demand and Occupancy Prediction" in the sidebar, above five pages drawn as stops on a route line |

On a fresh clone, verify only confirms that your copy of the results equals the committed one. To check that the results really come from the code, rerun the whole pipeline (optional, about 11 minutes plus a 510 MB download):

```bash
python -m transit.data.download
python -m transit.data.build
python -m transit.models.run
python -m transit.report
python -m transit.verify
```

If a future package release ever changes the results, install the exact versions that reproduced them: `python -m pip install -r requirements-lock.txt`, then `python -m pip install -e .` (tested with Python 3.12).

## 2. The 3-minute demo (Disha)

**Before the examiners arrive:**
- The app is already running, the browser shows the **Forecast explorer**, and other tabs are closed.
- Browser zoom is about 90% so the charts fit.
- The backup video is open in a player, paused.

| Time | Click | What should appear | What to say |
| --- | --- | --- | --- |
| 0:00–0:45 | **Forecast explorer**. Period "Test, 15–28 Apr 2024" (default). Route "137 · I" (default, busiest first). Service day: choose **Wed 17 Apr 2024** (the default is Mon 15 Apr). | Three numbers: boardings that day **8,760**, final forecast WAPE this day **15.3%**, last-week WAPE this day **7.7%**. The hourly boardings chart with a shaded 80% band. The estimated-load chart with dashed lines at 35 and 56 (50% and 80% of 70). A crowding strip, actual against forecast. | "Dark line: actual. Teal: our forecast. Dotted amber: last week's rule. Shaded: the 80% interval. On this day last week was closer; across all test days we are about 23% better." |
| 0:45–1:15 | Move **Capacity assumption for crowding lines** from `Ônibus básico (70)` to `Midiônibus (40)`, then back. | The dashed lines move to 20 and 32; the strip shows more red (H, high) and yellow (M, medium) hours. The forecast line does not change. | "Crowding depends on the assumed bus size, so we report four sizes." |
| 1:15–2:00 | **Model comparison**. Open **"Check: recompute the test metrics from the committed prediction files"**. | Two tables (demand, estimated load). In the check, every row shows `Match` ticked (10 rows). Below: WAPE by time of day and by test day. | "These are the evaluated numbers; the app recomputes them from the saved predictions and they all match. The historical average is almost as good as our blend, which we report openly." |
| 2:00–2:40 | **Next-day forecast**. | A yellow warning that it is a demonstration. **Route-hours forecast 9,566**, **Forecast high crowding 481** (at 70). A list of the most crowded hours. Caption: 92.1% top-50 precision on test, historical average 91.4%, last-week rule 78.6%. | "A genuine forecast for 29 April, the day after our data. No actuals exist, so it is not an evaluated result." |
| 2:40–3:00 | Back to **Forecast explorer**. Route **1637 · V**, day **Mon 15 Apr 2024**. | An open grey circle at 05:00. | "An open circle is an hour this route normally runs but has no record that day. We treat it as missing, never as zero, and never score it." |

If time is short, skip the last step and say the open-circle sentence while on the first page.

### What the numbers mean (one line each)

| Term | Meaning |
| --- | --- |
| WAPE | Total absolute error ÷ total actual. 18.15% means the forecast was off by about 18 boardings per 100 boardings. Lower is better. |
| MAE | Average absolute error per route-hour: 17.86 boardings for demand, 4.69 passengers for estimated load. |
| RMSE | Like MAE but punishes big misses more. |
| Bias | Average of forecast minus actual; negative means a slight under-forecast. |
| "WAPE vs last week" | Relative change in WAPE against the same-hour-last-week rule; −23.3% means 23.3% less error. |
| 80% interval | The range where 80% of actual values should fall. On test: 80.4% for demand and 79.3% for load, but only about 52% for night-time load. |
| Macro-F1 | The average of the F1 scores for low, medium and high crowding; 0.769 at 70 seats. |
| Precision / recall (high) | When we say "high" we are right 79% of the time; we catch 61% of the high hours (70 seats). |

## 3. Troubleshooting

Problems are listed with their usual cause. Items marked *(seen in our checks)* were reproduced in this project; the rest are common Windows and Python issues.

| Symptom | Fix |
| --- | --- |
| `python` is not recognised, or it opens the Microsoft Store | Install Python 3.12 from python.org and tick "Add python.exe to PATH". Then use `py -3.12` as in the commands above. |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that PowerShell window (it lasts for that window only), or use Command Prompt with `.venv\Scripts\activate.bat`. |
| `streamlit` is not recognised | Use `python -m streamlit run app/streamlit_app.py`, which works whenever the virtual environment is active. |
| `pip install` tries to compile `lightgbm`, `pyarrow` or `numpy` and fails | Usually a Python version without ready-made packages. Use Python 3.12. |
| `python -m transit.verify` says it "needs a git clone" *(seen in our checks)* | You downloaded a ZIP, or git is not installed. Clone with git. The tests and the dashboard still work from a ZIP. |
| On first run the terminal asks for an email | Press Enter to skip. |
| `Port 8501 is already in use` | Another copy is running. Close it, or add `--server.port 8502` and open http://localhost:8502. |
| The browser does not open | Open http://localhost:8501 yourself. |
| A Windows Firewall prompt appears | You can cancel it; the app on `localhost` still works on this laptop. |
| Very slow install or file errors inside OneDrive | Clone into a folder outside OneDrive, for example `C:\projects\`. |
| A path with spaces breaks a command | Put the path in double quotes. |
| `ModuleNotFoundError: transit` when running the app | Run the command from the repository's top folder. The app adds `src/` to the path itself. |

If anything fails on the day, do not debug in front of the examiners. Switch to the fallback below.

## 4. Fallbacks, in order

1. **The local app** (the main plan). It needs no internet once installed. Install everything the day before; `pip install` itself needs internet.
2. **A second laptop** with the app already installed and tested (one teammate besides Disha).
3. **The narrated video:** `group52_dashboard_demo.mp4` (3 min 18 s, 1080p, spoken narration with captions burned in: title, data, a walkthrough of the local dashboard, key results, limitations). It is in Jay's local project folder, not in the repository. Copy it to the demo laptop and a USB stick and play it in any video player. The captions keep it usable if the room's sound fails.
4. **The screenshots on slide 12**, as a last resort.

The public site (section 5) is an extra, not a fallback for a broken laptop: it needs internet and a long first load. If you want to show it, open it on the demo laptop by 5:30 PM so the browser cache is warm.

## 5. Public dashboard on GitHub Pages

**URL:** https://jayvaghela779.github.io/cs3011-public-transport-demand-occupancy/

**What it is.** A static page (`web/index.html`) that runs the same `app/streamlit_app.py` inside the browser with stlite 1.12.0 (Streamlit 1.65 on Pyodide). No server and no account beyond GitHub. It never sleeps. It needs a recent Chrome, Edge, Firefox or Safari with JavaScript.

**What a visitor sees.**
1. A loading page with a progress line: "Downloading results: x of 27.2 MB", then Python starts with stlite's own messages ("Loading Pyodide", "Installing packages").
2. Then the same five pages as the local app, with the same numbers.

**How long it takes (measured 24 Oct 2026).**

| Visit | Time |
| --- | --- |
| First visit, connection throttled to 10 Mbit/s | 83 s |
| First visit, throttled to 2 Mbit/s (a slow home line) | about 5 min 40 s |
| Repeat visit (browser cache) | about 40 s |

If the loading messages stop for two minutes, the page shows a yellow notice: reload. Downloaded files are kept, so the next attempt is faster.

**How it stays up to date.** `.github/workflows/pages.yml` runs on every push to `main` that changes `web/`, `app/`, `src/transit/`, `reports/metrics.json`, `reports/planning.json` or `data/predictions/`. It runs `python web/build_site.py`, commits the result to the `gh-pages` branch (never force-pushing) and refreshes jsDelivr's copy. GitHub Pages then redeploys within a minute or two. Nothing needs to be done by hand. Do not edit the `gh-pages` branch; edit `web/index.html` on `main`.

**How we know it shows the committed results.** `site-manifest.json` on the site lists every file's SHA-256 from `main`. The page checks each downloaded file against it before using it. `tests/test_web.py` fails if the page's file list misses anything the app reads.

**Troubleshooting.**

| Symptom | What to do |
| --- | --- |
| Stuck on "Downloading results" | The network is slow or blocks jsDelivr. Wait, or use the local app. |
| Yellow "Loading has not moved" notice | Reload the page. |
| "Loading failed: ..." on the start page | Reload; if it repeats, the network blocks jsDelivr or GitHub. Use the local app. |
| Blank page | JavaScript is disabled or the browser is too old. Use a current Chrome or Edge. |

**Not used: Streamlit Community Cloud.** It would send far less data to each viewer, but it needs a separate Streamlit account sign-in and its free apps sleep after 12 hours without visitors. If the team ever wants it, point it at `app/streamlit_app.py` on `main`; `requirements.txt` at the root is enough.
