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
| Test | 15 Apr to 28 Apr | Used once, after tuning |

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
- [ ] Data pipeline: download, aggregation, quality report
- [ ] Unit tests for the pipeline
- [ ] Baselines
- [ ] LightGBM demand model
- [ ] Estimated-load model and capacity sensitivity
- [ ] Streamlit app and cloud deployment
- [ ] Error analysis and results tables
- [ ] Code freeze
- [ ] Slides, viva sheet, demo video
- [ ] Rehearsals

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
