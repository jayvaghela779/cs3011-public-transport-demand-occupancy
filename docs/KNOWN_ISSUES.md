# Known issues found in the documentation review (27–28 October 2026)

Found while writing [REFERENCE_GUIDE.md](REFERENCE_GUIDE.md) against `main` at `3d0440b`. Each entry gives the evidence, the possible impact and a proposed correction.

Documentation errors were corrected on the `docs/scenario3-reference-guide` branch. **No code, results, dependency, CI or deployment file was changed**. Code-level items are recorded here for the team to decide on, because changing behaviour is outside a documentation task. The redevelopment should treat them as requirements to get right, not as faults to copy.

## Code and test behaviour (not changed)

### 1. `crowding_level` accepts invalid capacities

- **Evidence:** `src/transit/crowding.py` divides by `capacity` without checking it. Run on 27–28 Oct:

  ```text
  crowding_level([0.0, 10.0], 0)     -> [None, 'high']     (0/0 is NaN; 10/0 is infinite)
  crowding_level([10.0, 60.0], -70)  -> ['low', 'low']
  crowding_level([-5.0], 70)         -> ['low']
  ```
- **Impact on the legacy results:** none. The code only calls it with the four fixed capacities (40, 70, 80, 100), and the load target is never negative (the quality check `no_negative_aggregated_values` passed).
- **Proposed correction:** raise `ValueError` for a capacity that is not a positive finite number, and decide what a negative load means. Add the boundary tests named in the rulebook (S2): below, on and above each threshold; zero, negative and invalid capacity; missing load; load above capacity.

### 2. The dashboard has no error states for missing result files

- **Evidence:** `app/streamlit_app.py` reads `reports/metrics.json` and `data/predictions/*.parquet` directly (`load_metrics`, `load_predictions`). A missing file raises a Python exception in the page. Only `reports/planning.json` is checked with `exists()`. Checked on 27–28 Oct: running the app with Streamlit's `AppTest` in a copy without `reports/` shows `FileNotFoundError: ... reports/metrics.json`.
- **Impact:** a broken checkout shows a stack trace instead of a clear message. The committed files are present, so the normal demo is not affected.
- **Proposed correction:** check the files at start-up and show a plain message naming the missing file and the command that creates it (rulebook D2, D3).

### 3. Output-dependent tests skip instead of failing when outputs are missing

- **Evidence:** `tests/test_app.py` uses `pytestmark = pytest.mark.skipif(not METRICS.exists(), ...)`, and `tests/test_processed.py` follows the same pattern for the processed table.
- **Impact:** in a copy without the committed outputs, pytest reports skips and still exits 0, so a missing output could go unnoticed. Checked on 27–28 Oct in such a copy: `tests/test_app.py` and `tests/test_processed.py` gave `31 skipped`, exit status 0.
- **Proposed correction:** in CI, fail if these tests are skipped (for example by checking the skip count), or split them into a separately required job.

### 4. `transit.verify` covers two files, and the CI step does not reproduce anything

- **Evidence:** `src/transit/verify.py` compares only `data/processed/route_hour.parquet` and `reports/metrics.json` with git `HEAD`. In `.github/workflows/tests.yml`, the step "Committed results are self-consistent" runs it on a fresh checkout, where the working files *are* the committed files, so it always passes.
- **Impact:** nobody is misled by the CI step's name, but README text such as "GitHub Actions runs the tests and `python -m transit.verify`" could be read as continuous reproduction. Prediction files, `RESULTS.md`, `planning.json` and figures are not compared by `verify` (`transit.report` and `tests/test_app.py` cover parts of them).
- **Proposed correction:** documentation now states this precisely (README, REFERENCE_GUIDE §I.4). For the redevelopment: compare every reported output after a rerun, and run at least a small fixture pipeline end to end in CI.

### 5. The conformal "calibration" had essentially no effect

- **Evidence:** `reports/metrics.json` → `targets.*.intervals.conformal_margin` is 0.00026 for demand and 0.0 for load. Load coverage is 79.30% both before and after calibration.
- **Impact:** decision D13 and some documents describe intervals as "widened by a conformal margin". That is what the code does, but in the committed run the widening is negligible; coverage comes from the quantile models. Night-time load coverage stays at about 52%.
- **Proposed correction:** none needed for the legacy results; REFERENCE_GUIDE §E.4 and §J.3 now state it. In a rebuild, keep a calibration set separate from the early-stopping set, or calibrate per period if intervals are kept.

## Documentation inconsistencies (corrected on this branch)

| # | What was wrong | Evidence | Correction |
| --- | --- | --- | --- |
| 6 | Several documents gave the test count as a current fact (93 in the runbook, readiness checklist, walkthrough and viva bank; 86 in the report abstract, while the report body said 93) | `python -m pytest -q` on `3d0440b`: **98 passed**. PRs #15 and #16 added tests after those documents were written | Current-state statements now say 98 and the date; historical records (for example the 24 Oct reproduction record) keep their original counts. The report abstract now matches the report body (93 on its 24 Oct date) |
| 7 | README said every commit carries a `Co-Authored-By` line "as of 24 Oct 2026" | `git log`: 74 of 76 commits on `main` carry it; the two GitHub web-interface merge commits of PRs #15 and #16 do not (their merged commits do) | README states the exact position on 28 Oct 2026 |
| 8 | README presented the repository as the current project; the human-led redevelopment was not mentioned | README at `3d0440b` | README rewritten as the landing page of the legacy reference |
| 9 | Planning and preparation documents written for presenting the legacy system on 3 Nov read as current instructions | `docs/PROJECT_PLAN.md`, `FINAL_READINESS_CHECKLIST.md`, `TEAM_PRESENTATION_GUIDE.md`, `VIVA_PREP.md`, `VIVA_QUESTION_BANK.md`, `PROJECT_CODE_WALKTHROUGH.md` | Each now starts with a status note saying when and for what it was written; none was deleted. [docs/README.md](README.md) indexes them |
| 10 | The demo runbook still described the next-day page from before the redesign (PR #15): "a yellow warning" and a caption, and it expected `93 passed` | In the local app on 27–28 Oct the page shows a red-edged note ("Demonstration, not an evaluated result.") and the top-50 precision as a third figure; pytest reports 98 | [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md) section 1 and the demo table updated. Also confirmed in the app: 8,760 / 15.3% / 7.7% for 137 · I on 17 Apr, dashed lines at 20 and 32 at capacity 40, ten Match rows in the recompute check, 9,566 and 481 on the next-day page, and an open-circle trace for 1637 · V on 15 Apr |
| 11 | The report's dashboard screenshot shows the design before PR #15 | `reports/project_report/figures/dashboard_explorer.png`, taken 24 Oct | Noted in REFERENCE_GUIDE §H.4; the screenshot was not replaced |
