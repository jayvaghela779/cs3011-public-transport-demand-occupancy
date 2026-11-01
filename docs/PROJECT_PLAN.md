# Project plan

> **Status (28 Oct 2026): historical.** This plan tracked the build of the **legacy implementation** in this repository, up to 24 Oct 2026. It is kept as a record, including its review log, and is not updated for the human-led redevelopment. The current plan is [SCENARIO3_REDEVELOPMENT_GUIDE.md](SCENARIO3_REDEVELOPMENT_GUIDE.md); the technical reference is [REFERENCE_GUIDE.md](REFERENCE_GUIDE.md).

**Registered title:** AI Based Public Transport Demand and Occupancy Prediction
**Domain:** Machine Learning
**Group:** 52
**Evaluation:** Tuesday 3 November 2026, 6:00 PM (presentation plus fully functional running code)

Last updated: 24 Oct 2026, afternoon (final audit and team preparation; remaining actions are in [FINAL_READINESS_CHECKLIST.md](FINAL_READINESS_CHECKLIST.md)).

## Objective

Analyse public-transport data to predict passenger demand and occupancy, to support planning and efficiency (registered description). In this project, occupancy means **estimated on-board load** from SUNT fare-card trip chaining.

## Minimum viable product

1. **Data pipeline:** download pinned SUNT OD files, verify checksums, aggregate to route x direction x hour, run quality checks.
2. **Demand model:** day-ahead boardings per route-hour.
    - Baselines: same hour last week (seasonal naive); historical mean for route, weekday and hour.
    - Main model: LightGBM with lag, rolling, calendar and holiday features.
3. **Estimated-load model:** day-ahead estimated peak on-board load per route-hour; crowding levels under a documented capacity assumption, with a sensitivity analysis over alternative capacities.
4. **Streamlit app:** forecast vs actual, crowding strip, model comparison, data caveats. Public on GitHub Pages (in-browser, stlite) with the laptop app as the main demo; the original plan said Streamlit Community Cloud, laptop fallback.
5. **Tests and reproducibility:** pytest; every reported number comes from a committed script.

An "extra trips needed" figure is optional and illustrative only, under the stated capacity assumption. It will be dropped if it cannot be justified.

## Evaluation design

| Split | Dates (2024) | Use |
| --- | --- | --- |
| Train | 1 Mar to 7 Apr | Model fitting |
| Validation | 8 Apr to 14 Apr | Tuning |
| Test | 15 Apr to 28 Apr | Final scoring (scored twice in total; disclosed, decision D12) |

- 29 and 30 April 2024 are excluded: those files cover noticeably fewer routes than other days.
- Good Friday (29 Mar 2024) is inside the training period. It is **not** a held-out holiday test.
- The test window has no weekday national holiday (Tiradentes, 21 Apr 2024, fell on a Sunday). Holiday effects are described, not claimed as validated.
- Demand metrics: MAE, RMSE, WAPE; overall, peak vs off-peak, weekday vs weekend; improvement over each baseline.
- Load metrics: MAE of estimated peak load; macro-F1 and confusion matrix for crowding levels; sensitivity to the capacity assumption.

## Timeline

| Dates | Work | Lead |
| --- | --- | --- |
| 24 to 25 Oct | Plan, repository, data pipeline and checks | Jay, Akshar |
| 26 to 27 Oct | Baselines and demand model | Jay, Tirth |
| 27 to 28 Oct | Estimated-load model, capacity sensitivity | Tirth |
| 28 to 29 Oct | Streamlit app, public deployment (done 24 Oct on GitHub Pages) | Disha, Jay |
| 30 Oct | Error analysis, results tables | Tirth, Jay |
| 31 Oct (end of day) | **Core code freeze** | All |
| 31 Oct to 1 Nov | Slides, viva question sheet, backup demo video | Shivani, all |
| 1 to 2 Nov | Rehearsals on frozen code only | All |
| 3 Nov, 6:00 PM | Evaluation (local app running and public URL opened by 5:30 PM) | All |

The Victoria train-count dataset is a stretch goal only if the core is finished early.

## Task tracker

- [x] Decision report reviewed and approved (24 Oct)
- [x] SUNT licence confirmed on GitHub, Mendeley Data and Hugging Face (CC BY 4.0)
- [x] Repository skeleton and documentation
- [x] Data pipeline: download, aggregation, quality report (all 6 checks pass)
- [x] Missing-hour policy (D8), malformed trips (D9), capacity (D10), bursts (D11)
- [x] Baselines, LightGBM, validation tuning and ablation, final blend (D12)
- [x] Test evaluation, error analysis, crowding sensitivity, bootstrap intervals ([RESULTS.md](../reports/RESULTS.md))
- [x] Streamlit dashboard (5 pages) with smoke tests; checked in headless Chromium
- [x] Automated tests (pytest) on GitHub Actions: Ubuntu with Python 3.11 and 3.12, Windows with Python 3.12; `python -m transit.verify` checks a rerun against the committed results
- [x] Full rerun from a fresh clone (Linux, Python 3.12) reproduced every committed result ([record](ARCHITECTURE.md#reproduction-record))
- [x] Architecture document, viva preparation sheet, slide deck draft (claude.ai artifact; private until Jay shares it)
- [x] Backup demo video recorded; replaced on 24 Oct by a narrated version with captions, 3 min 18 s (in Jay's local project folder, not in the repository)
- [x] Slide exports (PowerPoint and PDF) brought up to date with the deck on 24 Oct
- [x] Project report drafted (24 Oct): Markdown source, Word and PDF in [`reports/project_report/`](../reports/project_report/), rebuilt with `python reports/project_report/build_report.py`; numbers checked against RESULTS.md
- [x] Code walkthrough with per-member reading paths and exercises: [PROJECT_CODE_WALKTHROUGH.md](PROJECT_CODE_WALKTHROUGH.md)
- [ ] **All:** read the report and correct anything you disagree with; each member works through their section of the code walkthrough (exercises first, answers second)
- [x] Public dashboard on GitHub Pages: https://jayvaghela779.github.io/cs3011-public-transport-demand-occupancy/ (24 Oct; published files byte-identical to `main`; all five pages checked in a real browser; README, runbook and report updated)
- [ ] **Jay:** share the slide deck with the team; agree the speaking split
- [ ] **Akshar:** run [`notebooks/reproduce_on_colab.ipynb`](../notebooks/reproduce_on_colab.ipynb) on Colab (or the README steps on his laptop) and post the `transit.verify` output in a GitHub issue
- [ ] **Tirth:** read RESULTS.md end to end; check the error-analysis claims against the dashboard
- [ ] **Disha:** rehearse the 3-minute demo; watch the narrated backup video once with sound
- [ ] **Shivani:** read DECISIONS.md D8–D13 and VIVA_PREP.md; own the limitations slide
- [ ] **All:** each member runs `pytest` and the app on their own laptop before 1 Nov
- [ ] **All:** code freeze at the end of 31 Oct; rehearsals 1–2 Nov
- [ ] **Team decision:** a licence for our own code (MIT proposed)
- [ ] **Team decision (optional):** fix the night-time load interval gap with a per-period conformal margin (D13). It would mean a third, disclosed look at the test weeks; leaving it as a reported limitation is also fine

### How the work was done

The pipeline, models, dashboard and documents in this repository were built in AI-assisted sessions directed by Jay (commits carry a `Co-Authored-By: Claude` line). Teammates' own reviews, runs and edits should be committed from their own accounts so the history shows each contribution.

## Open questions for the TA

These are unresolved. Work continues meanwhile, and nothing in the presentation will claim more than the data supports.

- [ ] Who is our assigned TA, and where is the evaluation held?
- [ ] What is the marking rubric? Is a written report, a code walkthrough or an individual viva required?
- [ ] Is a public dataset from Salvador, Brazil acceptable for our registered title?
- [ ] Is estimated on-board load (from fare-card trip chaining) acceptable as the occupancy label?
- [ ] May the demo run from a cloud URL, and will internet be available in the room?
- [ ] Must we submit a GitHub link or code before the evaluation, and by when?
- [ ] Is reusing open-source datasets and ideas, with citation, acceptable?
- [ ] How long is the presentation, and how long the demo?
- [ ] Our code was written with AI assistance (Claude), disclosed in every commit. Is that acceptable, and how should we declare it?

## Risks

| Risk | Mitigation |
| --- | --- |
| Little slack before 3 Nov | Core freeze 31 Oct; 1 to 2 Nov for rehearsals only |
| Occupancy label is an estimate | "Estimated on-board load" wording everywhere; caveats page in the app |
| No vehicle capacity in SUNT | Documented assumption plus sensitivity analysis |
| Public site slow on a weak network (first visit about 85 MB) | Local app is the main demo; open the public URL beforehand; narrated backup video |
| SUNT hosts unavailable | Team keeps a private copy of the 59 raw files (not in this public repo) |
| Time leakage | Chronological split; tests that features use only data at least 24 h old |
| Uneven contribution history | Feature branches; each member commits from their own account |

## Continuation notes (24 Oct 2026)

Jay asked for the AI-assisted session to stop at 7:30 AM IST and wait for him. State at the pause:

**Done and merged into `main`** (PRs #1–#6, all CI green):
- Pipeline, models, evaluation, dashboard, documents and tests as listed in the task tracker above.
- A fresh-clone rerun reproduced every committed result exactly ([record](ARCHITECTURE.md#reproduction-record)).
- CI runs `pytest` and `python -m transit.verify` on Ubuntu (Python 3.11, 3.12) and Windows (Python 3.12, with both `requirements.txt` and `requirements-lock.txt`).

**Next actions:** superseded by [FINAL_READINESS_CHECKLIST.md](FINAL_READINESS_CHECKLIST.md), which gives each remaining action an owner, a prerequisite and the evidence that shows it is done.

**Final audit (24 Oct 2026, afternoon).** No metric changed. Fixes:
- `transit.verify` now explains, instead of crashing, when there is no git clone.
- The README and the slides now state the AI assistance accurately.
- The baseline comparison now states its limits: RMSE, per-day wins, the bootstrap's scope and the alert list.
- The next-day caption now shows the historical average.
- D12's description of the archived experiments was corrected.

Team preparation material: [VIVA_QUESTION_BANK.md](VIVA_QUESTION_BANK.md), [TEAM_PRESENTATION_GUIDE.md](TEAM_PRESENTATION_GUIDE.md), [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md).

**Not started, deliberately:** an "extra trips needed" figure (D5, optional), the Victoria stretch dataset, and any change that would score the test weeks again.

### Review log (AI self-assessment against the rubric Jay set; not a course mark)

| Iteration | Problem, data, licence (4) | ML method and results (5) | Code and reproducibility (4) | Dashboard and demo (3) | Planning value (2) | Docs, slides, viva (2) | Total (20) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | | 15.5 |
| 2 | | | | | | | 16.5 |
| 3 | 3.5 | 4.0 | 3.75 | 2.5 | 1.75 | 1.5 | 17.0 |
| 4 | 3.75 | 4.0 | 3.75 | 2.5 | 1.75 | 1.5 | 17.25 |
| 5 | 3.75 | 4.0 | 4.0 | 2.5 | 1.75 | 1.5 | 17.5 |

Only the totals for iterations 1 and 2 are kept here. The five-iteration limit has been reached. What still costs points needs people, not code: no public deployment, slides never visually reviewed or rehearsed, the TA has not confirmed the dataset and the label, the test weeks have been scored twice, and the blend's gain over the historical average is small (0.2 WAPE points).

