# Viva question bank

Harder questions an examiner may ask, with short answers grounded in the code and the committed results. [VIVA_PREP.md](VIVA_PREP.md) has the basic answers; this file goes further and adds the follow-ups.

Every number here comes from [reports/RESULTS.md](../reports/RESULTS.md), [reports/metrics.json](../reports/metrics.json), [docs/DATA.md](DATA.md) or [docs/DECISIONS.md](DECISIONS.md). Check it there before you quote it. Answers are tagged:

- **[Measured]** we ran it and the output is committed.
- **[Assumption]** a choice we made that the data cannot confirm.
- **[Not tested]** an idea or a likely explanation that we have not run. Say so if asked.

Test results below are for the test weeks, 15–28 April 2024, unless stated.

---

## A. Problem statement and architecture

**1. What exactly does the system predict, and when?**
Before service day D starts (about 03:00), it predicts two things for every slot of day D, that is every route, direction and hour the route regularly runs:
- boardings (demand);
- estimated peak load per bus: for each trip in that hour, take its highest estimated on-board load, then average over the hour's trips (`load_trip_peak_mean`).

It also gives an 80% prediction interval for each, and a crowding level (low, medium, high) derived from the load forecast. *Evidence: `src/transit/features.py` docstring, `src/transit/models/run.py`.*

**2. Why route × direction × hour, and not stop by stop?**
Planners set frequencies per route and hour, so that is the decision level. Stop-level hourly counts are sparse and noisy. The route-hour table also stays small: 541,611 rows, about 12.5 MB, which a free cloud app can load (decision D7). **[Assumption]** that this is the most useful level for a planner.

**3. What is a "service hour", and why does it run from 3 to 26?**
A SUNT service day runs from about 03:45 to about 02:15 the next morning. Service hour 24 means 00:00 to 01:00 on the next calendar day. Using the clock hour inside the service day keeps a late-night trip with the day it belongs to (D7).

**4. Why is this AI and not just statistics?**
It is a learning problem in the T/E/P sense: a model learns a mapping from past observations to future demand and is judged on unseen weeks. It also deals with uncertainty, through prediction intervals, estimated labels and an assumed capacity. Be honest that the strongest single ingredient is a statistical baseline, the historical average. Our contribution is the learned model, a careful evaluation that shows how much it adds, and uncertainty estimates.

**5. Walk through the architecture in one breath.**
Download 59 pinned files and check their SHA-256 → aggregate to route-hours and run 6 quality checks → build modelling slots (observed or missing record) → build features using only earlier days → train, tune on validation, score test → write the report and figures → the dashboard reads those committed files. *Evidence: [ARCHITECTURE.md](ARCHITECTURE.md).*

**6. Why does the dashboard not run the model live?**
So that the demo can only show numbers that were evaluated. The app reads `reports/metrics.json` and `data/predictions/*.parquet`, needs no download or internet, and `tests/test_app.py` checks that the displayed metrics match the prediction files.

**7. Who wrote the code? What did each of you do?**
Answer plainly. The code and documents were written in AI-assisted sessions with Claude, directed and reviewed by Jay, and every commit says so with a `Co-Authored-By` line. Each member has studied, checked and rehearsed their own part. *Follow-up: "Then what is your contribution?"* Say what you actually did, for example "I ran the tests and the app on my laptop, checked the error-analysis numbers against the dashboard, and I can explain how the missing-hours rule works". Never claim you wrote code you did not write.

## B. Dataset, licence, data quality, missing records, estimated occupancy

**8. Why data from Brazil rather than India? (expect this first)**
We needed open data with both demand and on-board load. None of the Indian sources we checked had both:
- Bengaluru metro publishes hourly entries and exits only, for about 7 weeks, with no load.
- We found no tier-2 city data.
- The Ahmedabad–Gandhinagar dataset on Mendeley (doi 10.17632/39hjn56wkp.1), going by its published description, holds smartphone GPS and accelerometer traces from commuters inside buses, with crowdedness inferred from whether those commuters sat or stood. It has no route-level passenger counts. Our records show we read its description but did not download and inspect its files; say exactly that if asked.

SUNT has both labels, is peer-reviewed (Scientific Data, 2025) and is CC BY 4.0. *Follow-up: "Then your title's 'tier-2 cities' is not met?"* The method transfers; the results do not. We make no claim for Indian or tier-2 cities, and we have asked the TA to confirm the dataset is acceptable.

**9. What is in the SUNT files you used?**
One row per vehicle stop event: route, direction, stop, vehicle, trip, time, boardings, inferred alightings, and the load before and after the stop. We used 59 daily origin-destination files (1 Mar to 28 Apr 2024): 37,600,997 stop events, 410 routes, 713 route-directions and 51,353,180 boardings. *Evidence: DATA.md.*

**10. Why is the load only an estimate? (expect this)**
- Boardings come from fare-card taps. Salvador has no exit validators, so SUNT infers where each passenger got off from their next tap (trip chaining, within 1.1 km walking distance).
- Load is boardings minus inferred alightings, accumulated along the trip, so inference errors carry forward.
- Riders aged 65 and over travel free without a card and are missing.
- Unmatched taps are dropped or spread across buses.

*Follow-up: "So what does your load model's accuracy mean?"* It measures agreement with SUNT's estimate, not with true occupancy. That is why we never call it measured occupancy.

**11. How much demand does SUNT miss?**
**[Measured]** SUNT's mean over the 40 ordinary weekdays is 1,061,538 boardings. Salvador's mobility department reports about 1.25 million passengers per day in 2024, so SUNT holds about 85% of that. The gap fits the documented exclusions. The city figure is rounded and its day basis is not stated, so this is a sanity check, not a reconciliation (DATA.md).

**12. What does CC BY 4.0 oblige you to do, and did you?**
Credit the authors, link the licence and say what we changed. We do this in the README, DATA.md, and the notes in `data/processed/` and `data/predictions/`. Raw files are not committed; the pipeline downloads them. The paper itself carries a different licence (CC BY-NC-ND), so we cite it and do not reproduce it. Our own code has no licence yet: that is a pending team decision, and until then the code is not licensed for reuse.

**13. What happens when data is missing? (expect this)**
An absent hour is not zero demand (D8). It could mean no bus was scheduled, or that a bus ran with no record, and SUNT's timetable covers 21 May to 21 Jun 2024, so it cannot tell us which.
- From training days only, each route, direction, day type and hour is marked *regular* if it was observed on at least 80% of training days of that day type.
- An absent hour in a regular cell is a **missing record**. It is predicted (the dashboard shows it as an open circle), but it is never scored and is NaN in features: 3,309 training, 1,060 validation and 2,797 test slots.
- An absent hour in a non-regular cell is treated as no service and is not predicted.
- Route-directions seen on fewer than 10 training days are out of scope: 38 of 713.

**14. What if a route runs outside its usual hours? (expect this)**
**[Measured]** An observed hour in a non-regular cell is still a target and is scored. There are 2,254 such test rows, and the final forecast's WAPE on them is 55.83%, against 18.08% in regular cells. *Follow-up: "But you only know a bus ran after the fact."* Yes. The forecast is conditional on the route running that hour. In use, a timetable would supply that, and this is a stated limitation. It is a choice of which slots to score, not leakage: no feature uses day D's values.

**15. How do you treat hours with zero boardings?**
If a bus was recorded and nobody tapped, the zero is real and stays a target: 22,674 such rows (4.2%). On the 5,165 zero-boarding test rows, the final forecast's MAE is 2.95 and the last-week rule's is 2.81, so the simple rule is slightly better there.

**16. What data-quality problems did you find?**
- 222 malformed trips on 2–3 April that repeat stop numbers; their loads are unusable (D9).
- 2,685 burst validations (D11).
- An apparent partial outage on 2 April: 18 regularly running route-directions have no records.
- One negative raw alighting value.
- A timetable for the wrong months.

The build runs 6 checks (unique keys, all 59 days, boardings conserved exactly, no negative aggregated values, malformed trips under 0.1%, no events outside the service window), and it exits with an error if any fails.

**17. Why keep burst validations instead of capping them?**
99.8% of them are at 10 terminal stops, at the first stop of a trip, mostly at peak times. That looks like real station crowds attributed to the departing bus, so capping would invent data. They are flagged and reported separately: 446 test load rows, final MAE 9.98 with bursts against 4.67 without.

## C. Pipeline, features, chronological split and leakage

**18. Which features does the model use?**
19 for demand, 21 for load:
- route and direction (categorical);
- service hour, day of week, weekend, holiday, and "was 7 days ago a holiday";
- the same hour 1, 7, 14, 21 and 28 days earlier;
- the 4-week same-weekday mean, the 7-day mean, and the expanding same-day-type mean;
- trips 7 days earlier, and the 4-week trip mean;
- route-direction daily totals 1 and 7 days earlier;
- load only: boardings 7 days earlier and their 4-week mean.

*Evidence: `model_feature_names` in `features.py`.*

**19. Why are you allowed to use yesterday (lag 1)?**
Day D−1's last trips end around 02:15, before day D's first trips around 03:45. A forecast issued at about 03:00 can use all of D−1.

**20. How do you prevent temporal leakage? (expect this)**
- Every feature for day D comes only from days before D.
- The split is by date.
- The service profile and the fallback medians come from training data only (training plus validation for the test weeks).
- Settings and the blend weight are chosen on validation only.

`tests/test_features_and_baselines.py` multiplies every value from day D onward by 50 and checks that day D's features do not change while its target does.

**21. Test-week features use earlier test-week actuals. Isn't that leakage?**
No. On test day D the features use days before D, which can include earlier test days, exactly as an operator would have yesterday's data. The model's parameters are not refit during the test weeks. Leakage would be using day D's own values, and the test above rules that out.

**22. Why not a random split or k-fold cross-validation?**
Hours next to each other are strongly correlated. A random split would put future days in training and give optimistic scores. A forward-in-time split mimics how the system would be used.

**23. Why these dates?**
- Train: 1 Mar to 7 Apr (38 days).
- Validation: one full week, so every day type appears (8–14 Apr).
- Test: two full weeks (15–28 Apr).
- 29–30 Apr are excluded because those files cover noticeably fewer routes.
- Good Friday (29 Mar) is in training, so holidays are not tested (D3).

**24. Define the historical-average baseline exactly.**
The mean of all earlier observed values for the same route, direction, service hour and day type (weekday, Saturday, Sunday or holiday). It is expanding, so it grows by one day each day. If that is missing, it falls back to the 7-day mean, then to the training median for that hour. **[Measured]** On test, 127,820 of 127,935 demand rows use the primary rule (`metrics.json`, `baseline_fallbacks`).

**25. You tuned the number of rounds on validation, then refit on train + validation. Is that sound?**
It is the standard approach. The settings and the round count are fixed from the train-only model; the refit sees one more week. The validation predictions in the report come from the train-only model, and the test predictions from the refit. One small risk: the best round count for a larger training set may differ.

## D. Regression, LightGBM, baselines, blending and model selection

**26. Why LightGBM?**
- Gradient-boosted trees handle missing values (NaN) natively, a categorical route, and non-linear interactions such as route × hour.
- They train in seconds on 348,243 training rows on a laptop.
- They are deterministic with a fixed seed.

The Aarhus thesis we studied also compared tree ensembles with seasonal-naive and neural models, though its results are on its own data.

**27. What did you tune?**
Six settings per target, chosen by validation WAPE:
- demand: squared error, absolute error, Poisson, Tweedie, and two settings with larger trees;
- load: also Huber.

Learning rate 0.05, early stopping after 100 rounds without improvement. The winner for both targets was absolute error (`regression_l1`) with 63 leaves: 130 rounds for demand, 140 for load (`lgbm.py`, `tuning_*.csv`).

**28. Why did the absolute-error objective win?**
WAPE is a sum of absolute errors, so an objective that minimises absolute error (it predicts a median) matches the metric we select on. **[Not tested]** that this is the only reason.

**29. Why is LightGBM alone not better than the historical average? (expect this)**
**[Measured]** On test, LightGBM scored 18.39% and the historical average 18.35%; on validation 18.84% and 18.99%.
- The same-day-type history feature takes 72.9% of the model's gain, so the model mostly re-learns the historical average.
- In the ablation, history features cut validation WAPE from 21.64% to 18.89%, and everything else adds only 0.05 points.
- Models of the residual from the historical average stopped after 11–31 rounds.

With 38 training days, most of what is predictable is a stable weekly profile, and the extra flexibility adds variance. We report this as a finding (D12).

**30. Why blend, and why 50/50?**
Two forecasts with different errors usually average to a smaller error. We tried weights 0, 0.25, 0.5, 0.75 and 1 on LightGBM, on validation only: WAPE 18.99%, 18.76%, 18.65%, 18.68% and 18.84%. 0.5 was best for both targets. *Follow-up: "Is that not just hedging?"* It is a simple ensemble chosen without test data, and its gain is small, which we state.

**31. Why not an LSTM, Transformer or graph neural network?**
With 38 training days and a baseline that already captures most of the structure, we expected little gain for much more cost, and we chose a reliable working system. **[Not tested]** We cannot say they would be worse, because we did not run them. The SUNT examples repository has such models, and this is future work.

**32. Why not SARIMA per route?**
It would need a separate model for each of about 660 hourly series with gaps. A global model learns across routes. **[Not tested]**: do not claim it would be worse.

**33. What does feature importance tell you?**
Gain shares for demand: same-day-type history 72.9%, 7-day mean 11.8%, 4-week same-weekday mean 5.2%, route 4.1%, yesterday 1.4%. The model leans on history averages, which explains the near-tie with the historical average. Gain importance shows what the trees split on, not causation.

## E. WAPE, MAE, RMSE, bootstrap intervals, error analysis and interpretation

**34. Define the four regression metrics.**
With forecast ŷ and actual y over the scored rows:
- MAE = mean |ŷ − y|.
- RMSE = √mean (ŷ − y)².
- WAPE = Σ|ŷ − y| / Σ|y|, which equals MAE divided by mean y.
- Bias = mean (ŷ − y); negative means under-forecasting.

Final demand: MAE 17.86 boardings, RMSE 29.72, WAPE 18.15%, bias −0.49. The average scored route-hour has about 98 boardings (17.86 / 0.1815).

**35. Why WAPE rather than MAPE?**
MAPE divides by each actual, so it is undefined on the 5,165 zero-boarding test rows and explodes on quiet hours. WAPE weights errors by volume, which matches planning: it is the share of passengers mis-forecast.

**36. What is WAPE's weakness?**
Busy hours dominate it, so errors on quiet routes and at night count little. That is why we also report WAPE by period, day type and route volume.

**37. Is a 0.20-point improvement meaningful? (expect this)**
**[Measured]** Final 18.15% against historical average 18.35%. A paired bootstrap over 664 route-directions (2,000 resamples) gives a 95% interval of −0.29 to −0.06 points, and 99.65% of resamples favour the blend. The blend is lower on 13 of 14 test days. So the gain is statistically detectable but practically small, about 1% of the error.

Four caveats:
1. It holds for absolute error only. On RMSE the historical average is slightly better for demand: 29.58 against 29.72.
2. The bootstrap stays within the same 14 days.
3. The test weeks were scored twice.
4. The big, robust gain is against the last-week rule: −5.52 points (95% interval −5.79 to −5.26).

**38. How does the bootstrap work, and why resample route-directions?**
We draw route-directions with replacement, recompute both methods' WAPE on the same draw (paired), take the difference, and read off the 2.5% and 97.5% percentiles. Hours of one route are correlated, so resampling single hours would understate the uncertainty.

**39. What does the bootstrap not capture?**
Other weeks or seasons, holidays, and the fact that the test weeks were looked at twice. It is a frequentist confidence interval for the WAPE difference over these 14 days, not a probability that the blend is better in general.

**40. Why does the blend lose on RMSE for demand?**
**[Measured]** The fact: RMSE 29.72 for the blend against 29.58 for the historical average. **[Not tested]** A likely reason: the LightGBM half was tuned for absolute error and predicts medians, so a few large peak errors stay large, and RMSE squares them.

**41. Where does the forecast fail?**
**[Measured]** Final-forecast demand WAPE:
- night 00–02: 82.58%;
- evening 20–23: 26.72%;
- Sundays: 29.05%, against 17.18% on weekdays;
- the lowest-volume third of route-hours: 29.72%;
- non-regular hours: 55.83%;
- worst day: Sunday 21 Apr, at 32.21%.

The final forecast beats the last-week rule in every period.

**42. Is 21 April bad because it was the Tiradentes holiday?**
We cannot tell. It was a Sunday and a holiday, and the model treats it as an ordinary Sunday, because our holiday list holds only Good Friday. The other test Sunday, 28 April, also had a high WAPE (about 26%). With one example we cannot separate a holiday effect from a Sunday effect.

**43. Did you cherry-pick route 137 on 17 April for the example slide?**
No. `report.py` picks it by a fixed rule: the busiest route-direction and the first test Wednesday. It is in fact unflattering:
- on that route, the last-week rule beat us that day (day WAPE 7.7% against 15.3%);
- 17 April is the only test day on which the blend's overall demand WAPE was worse than the historical average's (16.74% against 16.59%, from `metrics.json`).

**44. Why were the test weeks scored twice, and what does that cost? (expect this)**
- **v1:** the first full run scored LightGBM alone. It tied the historical average (18.39% against 18.35%).
- We then tried two ideas on validation only, and chose a blend weight on validation only.
- **v2:** the blend was scored on test.

Both runs are reported (D12, `reports/archive/metrics_v1_lightgbm_only.json`). The cost: knowing v1's result influenced the decision to try a blend, so the test weeks are no longer untouched. The 0.20-point gain may be slightly optimistic. The mitigations are that the weight was chosen on validation, validation showed the same pattern beforehand, and we disclose both runs. The 5.5-point gain over the last-week rule is far larger than any such effect.

**45. Why is test WAPE (18.15%) lower than validation WAPE (18.65%)?**
They are different weeks, and the test model was refit on one more week of data. Nothing guarantees which is lower. The validation week is still the honest place to choose settings.

## F. Crowding, capacity sensitivity, prediction intervals and planning value

**46. How do you classify crowding?**
There is no separate classifier. The predicted load is divided by the bus capacity: low below 0.5, medium 0.5 to 0.8, high 0.8 and above. The same rule turns SUNT's estimated load into the "actual" class. We score with macro-F1 and a confusion matrix.

**47. Where do the capacities and the thresholds come from?**
The capacities are the minimum seated-plus-standing figures of the Brazilian bus standard ABNT NBR 15570 (6 standing passengers per m²): midiônibus 40, básico 70 (base case), padron 80, articulado 100. **[Assumption]** The 0.5 and 0.8 thresholds are our choice, not taken from the standard, and SUNT does not say which bus served which route.

**48. Why macro-F1 and not accuracy?**
The classes are imbalanced: at capacity 70 the actual shares are 76.64% low, 18.17% medium and 5.19% high. Accuracy would reward predicting "low" everywhere. Macro-F1 averages the F1 of each class equally.

**49. What does the capacity sensitivity show?**
**[Measured]** As the assumed bus grows from 40 to 100 seats:
- the share of high hours falls from 28.23% to 0.51%;
- recall for "high" falls from 0.787 to 0.250;
- precision stays between 0.77 and 0.85;
- macro-F1 falls from 0.772 to 0.683.

The capacity choice changes how many alerts there are far more than how good each alert is. At 70, the historical average reaches 0.766 against our 0.769. On busy routes estimated loads exceed 70: on route 137 on 17 April they reach about 98 between 06:00 and 08:00 (`data/predictions/load_test.parquet`). That could be an overloaded bus, a larger vehicle, or estimation error, and we cannot tell which.

**50. How are the 80% prediction intervals built?**
1. Two quantile LightGBM models (10% and 90%) are early-stopped on validation and refit on train + validation.
2. A split-conformal margin is set on validation: the ⌈(n+1)·0.8⌉/n quantile of max(lo − y, y − hi).

The raw models were already near 80% on validation, so the margin is about 0.0003 boardings for demand and 0 for load. **[Measured]** Test coverage is 80.39% for demand (mean width 59.6 boardings) and 79.30% for load (mean width 15.2 passengers).

**51. What is the difference between your prediction interval and your bootstrap interval?**
A prediction interval is about one future value: 80% of actual route-hours should fall inside it. The bootstrap interval is a confidence interval for one summary number, the WAPE difference between two methods. Do not mix them up.

**52. What does the night-time coverage problem imply? (expect this)**
**[Measured]** Load intervals cover only 52.11% of night (00–02) test hours, and 49.86% in the validation week. 39.96% of actual night loads fall below the band (mean width 4.6), so the band is too narrow and set too high at night. Demand intervals at night are fine (84.26%).

What it implies:
- 80% coverage overall does not mean 80% in every subgroup (marginal versus conditional coverage).
- A planner should not trust night-time load bands.
- It affects only 2,157 test rows (1.7%), but it is a real defect of the method, since validation showed it too.

A fix would set a separate conformal margin per period on the validation week. We have not applied it, because it would be a third look at the test weeks (D13).

**53. What is the practical planning value?**
**[Measured]** Each test day we take the 50 route-hours with the highest forecast load (capacity 70). 92.14% of them were truly high, against 91.43% for the historical average and 78.57% for the last-week rule. The median test day had 580 high route-hours, so the list is a short priority list, not full coverage. The clear gain is over the last-week rule. Against the historical average the difference is at most 2.0 points, and at K = 100 the historical average is slightly ahead (87.50% against 87.07%).

**54. Can the system say how many extra buses to add?**
No. We did not compute it (D5): it would need the real fleet per route, costs and timetables. The dashboard flags hours to check first; it does not prescribe trips.

## G. Dashboard, reproducibility, deployment, GitHub, tests and software engineering

**55. How do we know the dashboard shows the evaluated numbers?**
It reads the committed `metrics.json` and prediction files. The Model comparison page has a check that recomputes every test WAPE from the prediction files. `tests/test_app.py` asserts the same, plus interval coverage and alert precision, and `transit.report` stops if any number disagrees.

**56. Why should the professor trust the results and the reproducibility claim? (expect this)**
**[Measured]**
- The SUNT source is pinned to one commit, and every file is checked by SHA-256.
- LightGBM runs with a fixed seed in deterministic mode.
- On 24 Oct 2026, a full rerun from a fresh clone (Python 3.12) reproduced the route-hour table cell by cell, all 2,326 numbers in `metrics.json`, all 5 prediction files, and byte-identical `RESULTS.md` and `planning.json` (ARCHITECTURE.md, "Reproduction record").
- `python -m transit.verify` repeats the comparison for anyone.
- GitHub Actions runs 93 tests and the verify step on Ubuntu (Python 3.11, 3.12) and Windows (Python 3.12, with and without the locked versions).

Limits:
- The full pipeline has not been rerun on Windows or Colab.
- A teammate's own independent rerun is pending.

*Follow-up: "Couldn't you have edited metrics.json?"* Anyone can rerun the pipeline in about 11 minutes and verify will list any difference.

**57. What do the 93 tests cover, and what don't they?**
They cover:
- aggregation and conservation of boardings (`test_aggregate`);
- input checks and time windows;
- an end-to-end pipeline on a synthetic SUNT-like fixture;
- the missing-hours policy (`test_service`);
- pinned facts about the processed table (`test_processed`);
- the leakage test and the baselines;
- a synthetic end-to-end training run, including the blend formula and the fact that the blend weight is chosen on validation;
- every dashboard page rendering, with displayed numbers matching the files (`test_app`);
- the verify tool;
- the public web build: the page lists every file the app reads, the site copies them byte for byte, and versions are pinned (`test_web`).

They do not re-check real-data model accuracy (that needs the 510 MB download and about 8 minutes), and they do not click through the app in a real browser.

**58. Why Streamlit?**
It is free and pure Python, runs locally, can run inside a browser through stlite (which is how our public site works), and has a test harness (`AppTest`) that we use in CI.

**59. Is the dashboard deployed? How?**
**[Measured]** Yes, on GitHub Pages: https://jayvaghela779.github.io/cs3011-public-transport-demand-occupancy/. It is a static page that runs the unchanged app inside the visitor's browser with stlite (Streamlit 1.65 on Pyodide, that is, Python compiled to WebAssembly).
- A GitHub Actions workflow copies the app code and the committed result files from `main` to the `gh-pages` branch, with a SHA-256 manifest.
- The page downloads them through jsDelivr's mirror, checks every hash, and re-fetches any mismatching copy from GitHub Pages.
- On 24 Oct the published files were byte-identical to `main`, and all five pages matched the local app in a real browser.

*Follow-up: "Why not Streamlit Community Cloud?"* It would send less data to viewers, but it needs a separate account sign-in and its free apps sleep after 12 hours idle. GitHub Pages needs neither.

*Follow-up: "What is the catch?"* A first visit downloads about 85 MB: 83 s at 10 Mbit/s, about 5 min 40 s at 2 Mbit/s. A repeat visit takes about 40 s. That is why the local app is our main demo and the narrated video our backup. Say "live" only if you opened the URL that day.

**60. How did you use Git?**
Feature branches, pull requests, CI on every pull request, merges into `main`, no force-pushes or rewritten history. The history shows the AI co-author on every commit. Teammates' reviews and fixes should be committed from their own accounts.

**61. How do you manage dependencies?**
`requirements.txt` gives version ranges. `requirements-lock.txt` pins the exact versions that reproduced the results, and CI installs it on Windows. Python 3.12 is the safest version, since CI tests it on both systems.

## H. Limitations, alternatives, ethics and future work

**62. What are your three most important limitations?**
1. The occupancy label is an estimate, from one Brazilian city, over 59 days, with an assumed capacity.
2. The gain over a strong baseline is small, and the test weeks were scored twice.
3. The intervals fail for night-time load, and the forecast assumes we know which hours a route runs.

**63. Would this work for Jabalpur or another tier-2 city?**
The pipeline would, if the city has per-trip boardings with stop and time. Estimating load also needs either exit data or a way to infer alightings, or on-board passenger counters. **[Not tested]**: we have no Indian data, so any accuracy for an Indian city is unknown.

**64. What are the ethical risks?**
- Older riders (65+) are invisible in the data, so plans based on it could under-serve them.
- Errors are largest on quiet routes and at night, exactly where cuts would hurt the people with fewest alternatives.
- The capacity assumption changes how crowded things look.

So the system should prioritise checks, with a human deciding. Our repository holds only route-hour aggregates: no card IDs, stops or vehicles.

**65. What would you try next, in order?**
1. A per-period conformal margin for the night gap (D13), calibrated on validation.
2. Holiday-aware features once more holidays are available.
3. A timetable for the same months, to confirm missing hours.
4. A city with counted loads, to validate the occupancy part.
5. Weather and event data.
6. Deep or hierarchical models, compared on the same rows.

**66. What would change if you had real passenger counts?**
We could check SUNT's load estimates directly, measure how wrong trip chaining is, and evaluate crowding against real occupancy instead of an estimate.

**67. If the examiner says "your model is basically an average": how do you reply?**
For this data, mostly yes, and we show it rather than hide it. The learned model plus the blend gives a small, consistent gain. The system around it is what makes it usable and trustworthy: leak-free day-ahead features, honest missing-data handling, calibrated intervals with known failure modes, capacity sensitivity, a dashboard, and an evaluation anyone can reproduce.
