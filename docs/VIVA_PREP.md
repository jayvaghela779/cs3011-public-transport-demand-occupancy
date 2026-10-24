# Viva preparation

Short answers every member should be able to give, with the evidence to point at. Numbers come from [reports/RESULTS.md](../reports/RESULTS.md); check them there before quoting.

## 1. Framing

**What is the learning problem? (task, experience, performance measure)**
- **Task T:** before a service day starts, predict for every route, direction and hour (a) the number of boardings and (b) the estimated peak load per bus.
- **Experience E:** 38 training days of SUNT fare-card data from Salvador, plus one validation week.
- **Performance P:** WAPE, MAE and RMSE on two unseen test weeks; macro-F1 for crowding levels.

**Supervised regression or classification?** Both are supervised. Demand and load are regression targets (real values). Crowding (low, medium, high) is a classification derived from the predicted load, evaluated with a confusion matrix.

**Why is this "AI"?** The system learns a mapping from past observations to future demand from data (machine learning, a subfield of AI). It acts under uncertainty: the future is unknown and the occupancy labels are themselves estimates.

## 2. Data

**Why Brazilian data?** We searched for open data with real demand and load labels, including Indian sources. None of the Indian sources had both. Bengaluru metro has hourly entries only, for about 7 weeks, and our Indian tier-2 search found nothing. SUNT is open (CC BY 4.0), peer-reviewed (Scientific Data, 2025) and has both. We make no claim about Indian or tier-2 cities.

**Is the load measured?** No. SUNT infers where each passenger gets off from their next tap (trip chaining). Load is boardings minus inferred alightings. We always call it "estimated on-board load".

**What did you do about missing hours?** A missing hour is not zero demand (D8). We build a service profile from training days only. Hours a route normally runs but has no record are "missing records": predicted, never scored. That is 2,797 of 130,732 test slots.

**What were the data-quality problems?**
- 222 malformed trips on 2–3 April (D9).
- Burst validations at terminal stations (D11).
- A partial outage on 2 April.
- A timetable file that covers the wrong months.
- Each is counted in the quality report and handled by a written rule.

## 3. Method

**Why train, validation and test?**
- Training fits the model.
- Validation chooses settings: objective, tree size, number of rounds, blend weight.
- Test gives the unbiased estimate.
- Because we forecast the future, the split is by date, never random. A random split would leak future information.

**How do you know there is no leakage?** Every feature for day D comes from days before D. `tests/test_features_and_baselines.py` changes all data from day D onward and checks that day D's features do not change.

**Why baselines?** A model is only useful if it beats simple rules. "Same hour last week" is the usual planning rule. The historical average is a strong statistical baseline.

**Why LightGBM?**
- Gradient-boosted trees handle mixed features, missing values (NaN) and non-linear effects.
- They train in seconds on 350,000 rows on a laptop.
- Published bus-occupancy studies found tree ensembles strong for this task.

**Why is the final forecast a blend?** LightGBM alone tied the historical average on validation and on test (D12). Averaging two forecasts with different errors usually reduces error. The 50/50 weight was chosen on validation.

## 4. Results (quote from RESULTS.md)

- **Demand test WAPE:** final 18.15%; historical average 18.35%; same hour last week 23.67%.
- **Estimated-load test WAPE:** final 19.20%; historical average 19.35%; same hour last week 25.39%.
- **Is 0.2 points meaningful?** A paired bootstrap over route-directions gives a 95% interval of −0.29 to −0.06 points. It is small but consistently negative. The large gain is over the last-week rule (about 23%).
- **Crowding, 70-passenger bus:** macro-F1 0.769. High-crowding alerts have precision 0.79 and recall 0.61.

**Where does it fail?**
- Late evening and night hours, and low-volume routes (higher WAPE).
- Sundays, especially 21 Apr, when Tiradentes fell on a Sunday.
- Hours outside a route's regular service.

**Honest limitations**
- One city and 59 days.
- No holiday in the test weeks.
- Estimated labels and an assumed capacity.
- The test weeks were scored twice (disclosed).

## 5. Uncertainty (links to the uncertainty lectures)

- **Uncertain labels:** load is inferred, not observed, so even "actual" crowding is uncertain. That is why we never call it measured occupancy.
- **Uncertain capacity:** results are reported under four capacities, not one.
- **Uncertain improvement:** the bootstrap interval expresses our degree of belief that the blend beats the baseline, not just a single number.
- **Possible extension:** quantile forecasts (for example a 10–90% band) would give planners a probability range rather than a point.

## 6. Who explains what (proposal; swap as agreed)

| Member | Part of the demo and viva |
| --- | --- |
| Jay | Problem framing, architecture, model and blend decision (D12) |
| Akshar | Data, licence, pipeline, quality checks, missing hours (D8, D9) |
| Tirth | Evaluation protocol, baselines, metrics, bootstrap, error analysis |
| Disha | Dashboard walkthrough, deployment and local fallback |
| Shivani | Crowding and capacity assumption (D10), limitations, future work |

Each member should be able to run `pytest` and `streamlit run app/streamlit_app.py` on their own laptop.
