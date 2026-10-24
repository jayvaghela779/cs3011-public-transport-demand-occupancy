# Project plan

**Registered title:** AI Based Public Transport Demand and Occupancy Prediction
**Domain:** Machine Learning
**Group:** 52
**Evaluation:** Tuesday 3 November 2026, 6:00 PM (presentation plus fully functional running code)

Last updated: 24 Oct 2026.

## Objective

Analyse public-transport data to predict passenger demand and occupancy, to support planning and efficiency (registered description). In this project, occupancy means **estimated on-board load** from SUNT fare-card trip chaining.

## Minimum viable product

1. **Data pipeline:** download pinned SUNT OD files, verify checksums, aggregate to route x direction x hour, run quality checks.
2. **Demand model:** day-ahead boardings per route-hour.
    - Baselines: same hour last week (seasonal naive); historical mean for route, weekday and hour.
    - Main model: LightGBM with lag, rolling, calendar and holiday features.
3. **Estimated-load model:** day-ahead estimated peak on-board load per route-hour; crowding levels under a documented capacity assumption, with a sensitivity analysis over alternative capacities.
4. **Streamlit app:** forecast vs actual, crowding strip, model comparison, data caveats. Deployed on Streamlit Community Cloud with a laptop fallback.
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
| 28 to 29 Oct | Streamlit app, cloud deployment | Disha, Jay |
| 30 Oct | Error analysis, results tables | Tirth, Jay |
| 31 Oct (end of day) | **Core code freeze** | All |
| 31 Oct to 1 Nov | Slides, viva question sheet, backup demo video | Shivani, all |
| 1 to 2 Nov | Rehearsals on frozen code only | All |
| 3 Nov, 6:00 PM | Evaluation (wake the cloud app by 5:30 PM) | All |

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
- [x] Backup demo video recorded (68 s, no narration; saved in Jay's local project folder, not in the repository)
- [ ] **Jay:** deploy on Streamlit Community Cloud (needs his GitHub sign-in); add the URL to the README
- [ ] **Jay:** share the slide deck with the team; agree the speaking split
- [ ] **Akshar:** run [`notebooks/reproduce_on_colab.ipynb`](../notebooks/reproduce_on_colab.ipynb) on Colab (or the README steps on his laptop) and post the `transit.verify` output in a GitHub issue
- [ ] **Tirth:** read RESULTS.md end to end; check the error-analysis claims against the dashboard
- [ ] **Disha:** rehearse the 3-minute demo; re-record the backup video with narration if the team wants one
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

## Risks

| Risk | Mitigation |
| --- | --- |
| Little slack before 3 Nov | Core freeze 31 Oct; 1 to 2 Nov for rehearsals only |
| Occupancy label is an estimate | "Estimated on-board load" wording everywhere; caveats page in the app |
| No vehicle capacity in SUNT | Documented assumption plus sensitivity analysis |
| Cloud app asleep or over memory | Small committed artifacts; wake early; laptop fallback; demo video |
| SUNT hosts unavailable | Team keeps a private copy of the 59 raw files (not in this public repo) |
| Time leakage | Chronological split; tests that features use only data at least 24 h old |
| Uneven contribution history | Feature branches; each member commits from their own account |
