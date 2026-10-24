# Team presentation guide

One section per speaker: your slides, what to say, the three ideas you must understand, and the questions you should expect.

> **Provisional.** The speaking split comes from the slide deck's speaker notes and its team slide. The team has not confirmed it. Change it to match what each person actually rehearses, and update the deck's team slide to match.

**Timing (assumption).** We do not know the official time limit; it is one of the TA questions. This guide assumes about 12 minutes of talk plus a 3-minute demo. Scale each part if the limit differs.

| Order | Slides | Speaker | About |
| --- | --- | --- | --- |
| 1 | 1 Cover, 2 Problem | Jay | 1.5 min |
| 2 | 3 Data, 4 Data problems | Akshar | 2 min |
| 3 | 5 Pipeline | Jay | 1 min |
| 4 | 6 Method, 7 Example, 8 Results | Tirth | 3 min |
| 5 | 9 Honest finding | Jay (the deck says "Tirth or Jay"; the team slide gives Jay the blend decision) | 1 min |
| 6 | 10 Where it fails | Tirth | 1 min |
| 7 | 11 Crowding | Shivani | 1.5 min |
| 8 | 12 Live demo | Disha | 3 min |
| 9 | 13 Limitations | Shivani | 1 min |
| 10 | 14 Team and questions | Jay | 0.5 min, then Q&A |

## Rules for everyone

1. **Who wrote the code.** The code and documents were written in AI-assisted sessions with Claude, directed and reviewed by Jay, and every commit is marked. Say this if asked. Describe your own part as what you did, for example "I checked", "I ran", "I can explain"; do not say "I built" or "I coded" unless you did.
2. **Numbers.** Quote only numbers on the slides or in [reports/RESULTS.md](../reports/RESULTS.md). If you are unsure of one, say where it is rather than guessing.
3. **Estimated load.** Always say "estimated on-board load", never "occupancy was measured".
4. **"I don't know".** "I don't know, but here is what we measured" is better than inventing an answer. Hand over to the teammate who owns that part.
5. **Before the day.** Run `pytest` and the dashboard on your own laptop at least once ([DEMO_RUNBOOK.md](DEMO_RUNBOOK.md)).

Deeper answers for all sections: [VIVA_QUESTION_BANK.md](VIVA_QUESTION_BANK.md). Question numbers below (Q8 and so on) refer to it.

---

## Jay Pravin Vaghela: framing, architecture, the blend decision, close

**Slides:** 1 Cover, 2 Problem, 5 Pipeline, 9 The honest finding (provisional), 14 Team and questions.

### What to say

**Slide 1.**
- "Our registered title is *AI Based Public Transport Demand and Occupancy Prediction*."
- "We built day-ahead forecasts of passenger demand and estimated on-board load, for every bus route and hour."
- "The data is open fare-card data from Salvador, Brazil: 59 days, with the last two weeks held out for testing. We used Brazilian data because no Indian dataset we found had both demand and load. Akshar will explain."

**Slide 2.**
- "In the task–experience–performance terms from the lectures:
  - the task is to predict, before each day starts, boardings and estimated peak load per bus for every route, direction and hour;
  - the experience is 38 training days and one validation week;
  - performance is WAPE, MAE and RMSE on two unseen test weeks."
- "Demand and load are regression problems. Crowding is a classification we derive from the predicted load."

**Slide 5.**
- "Each stage is one command that reads the previous stage's saved output."
- Walk left to right:
  1. download with checksums;
  2. aggregate to 541,611 route-hours with 6 quality checks;
  3. mark each slot as observed or missing;
  4. build features from earlier days only;
  5. train and evaluate;
  6. report and dashboard.
- "Two things make this trustworthy:
  - a leakage test: we multiply every value from day D onward by 50, and day D's features must not change;
  - a full rerun from a fresh clone reproduced every committed number, which `python -m transit.verify` checks."

**Slide 9.**
- "This is the honest result. LightGBM alone only tied the historical average: 18.39% against 18.35% WAPE. The validation week had shown the same."
- "So, using validation only, we blended them 50/50. The blend reaches 18.15%. The gain is 0.20 points, with a 95% bootstrap interval of 0.06 to 0.29: small but consistent, lower on 13 of the 14 test days."
- "We scored the test weeks twice, once before the blend and once after, and we report both."

**Slide 14.**
- "The code, data card, decisions and results are in the repository."
- "The code was written in AI-assisted sessions that I directed, and every commit discloses it."
- "We are happy to take questions."

### Three ideas you must understand

1. **Day-ahead without leakage:** features for day D come only from days before D, and how the leakage test proves it (Q19–Q21).
2. **Why the historical average is hard to beat:** the weekly profile carries most of the signal (72.9% of the model's gain), so the blend is a small, honest improvement (Q29, Q30, Q37).
3. **Test scored twice:** what happened, why it is disclosed, and what it costs (Q44).

### Questions to expect

| Question | Short answer |
| --- | --- |
| Why is this AI and not just averaging? | It is a learned model judged on unseen weeks, with uncertainty estimates. The finding that a simple average is nearly as good is itself the result of a proper evaluation (Q4, Q67). |
| Why LightGBM? | It handles missing values, categorical routes and non-linear effects, trains in seconds, and is deterministic (Q26). |
| Why a 50/50 blend? | Five weights were tried on validation; 0.5 was best: 18.65%, against 18.84% for LightGBM alone and 18.99% for the historical average (Q30). |
| Is 0.20 points meaningful? | It is statistically detectable but practically small, and only in absolute error; the big gain is 5.5 points over last week's rule (Q37). |
| Who wrote the code? | AI-assisted sessions directed by me; every commit is marked (Q7). |

**Check your understanding** (ask each other):
- Why can lag 1 be used at all?
- What would happen to the scores with a random split?
- Why does choosing the weight on validation matter, if we then score on test anyway?

---

## Akshar Jasoliya: data, licence, pipeline and quality rules

**Slides:** 3 The data, 4 Data problems.

### What to say

**Slide 3.**
- "SUNT is an open, peer-reviewed bus dataset from Salvador, Brazil: 37.6 million stop events, 59 days, 410 routes. Its licence is CC BY 4.0, and we pin it to one version with SHA-256 checks."
- "For every stop of every trip it gives fare-card boardings, the inferred alightings and the load on board."
- "The important point: occupancy here is an *estimate*. There are no exit validators, so SUNT guesses where each passenger got off from their next tap. Riders aged 65 and over travel without cards and are missing. So we always say estimated on-board load."
- "Why not Indian data: the one Indian source with ridership, Bengaluru metro, has about 7 weeks of hourly entries and no load at all, and we found no tier-2 city data. We make no Indian or tier-2 claim."

**Slide 4.**
- "Every data problem gets a written rule."
- "The most important rule: an hour with no record is *missing*, never zero demand. It could be a data gap, and the timetable file is for the wrong months, so we cannot tell. In the test weeks, 2,797 of 130,732 slots are missing records. We forecast them but never score them."
- "We also found 222 malformed trips on 2–3 April, which we flag; burst validations at terminals, which we keep rather than cap; and a partial outage on 2 April."
- "Six automatic checks run on every build, and the build fails if any fails."

### Three ideas you must understand

1. **How SUNT estimates load** (trip chaining), and what that means for what we can claim (Q10).
2. **Missing versus zero:** the 80%-of-training-days rule for a regular hour, missing records, and out-of-scope routes (Q13–Q15).
3. **The licence:** what CC BY 4.0 requires and how we meet it (Q12).

### Questions to expect

| Question | Short answer |
| --- | --- |
| Why Brazil, not India? | No Indian source had both labels. The Ahmedabad–Gandhinagar dataset infers crowdedness from smartphone sensors of a few commuters and has no route counts; we read its description but did not inspect its files (Q8). |
| Is the load measured? | No, it is inferred by trip chaining; 65+ riders are missing (Q10). |
| How much ridership does SUNT miss? | SUNT's weekday mean of 1,061,538 is about 85% of the city's published 1.25 million per day for 2024; a sanity check only (Q11). |
| What if a bus runs in an unusual hour? | It is still scored (2,254 test rows, WAPE 55.83%). Unrecorded unusual hours are not predicted (Q14). |
| Why not cap burst validations? | 99.8% are at 10 terminal stops at peak times, so they look like real crowds. They are reported separately (Q17). |

**Check your understanding:**
- What is the difference between a zero-boarding hour and a missing record?
- Why is the service profile built from training days only?
- What does the build do if boardings are not conserved?

---

## Tirth Jasoliya: evaluation protocol, results and error analysis

**Slides:** 6 Method, 7 One forecast, 8 Test results, 10 Where the forecast fails. Slide 9 if the team gives it to you.

### What to say

**Slide 6.**
- "The features use the same hour 1, 7, 14, 21 and 28 days earlier, recent averages, the history of the same day type, and trips and route totals from earlier days."
- "We compare five forecasters on exactly the same rows:
  - three simple baselines (same hour last week, mean of the last 4 same weekdays, historical average);
  - LightGBM;
  - the final blend."
- "The split is by date: train 1 March to 7 April, validate 8 to 14 April, test 15 to 28 April. Settings and the blend weight were chosen on validation only."

**Slide 7.**
- "One real test day: route 137, direction I, Wednesday 17 April. It is picked by a fixed rule, the busiest route-direction on the first test Wednesday."
- "The forecast gets the shape right but under-forecasts the morning peak."
- "On this day last week's numbers were actually closer, 7.7% against 15.3%. One day is an anecdote, so next we score all 127,935 test route-hours."

**Slide 8.**
- "Demand WAPE is 18.15%, against 23.67% for last week's rule: about 23% less error. Estimated load: 19.20% against 25.39%."
- "WAPE is total absolute error divided by total actual."
- "Notice that the historical average is almost as good, 18.35%. That is the next slide."
- "80.4% of actual demand values fall inside our 80% prediction interval."

**Slide 10.**
- "Error grows when counts are small: at night (82.6% WAPE), on Sundays (29.1% against 17.2% on weekdays), on quiet routes (29.7%) and in hours outside regular service (55.8%)."
- "The worst day was Sunday 21 April, the Tiradentes holiday. The model had only seen Good Friday as a holiday."
- "The final forecast still beats last week's rule in every period."

### Three ideas you must understand

1. **The metrics:** WAPE, MAE, RMSE and bias, and why WAPE rather than MAPE (Q34–Q36).
2. **Train, validation, test:** why a chronological split, and what was chosen where (Q22–Q25).
3. **The bootstrap:** what the interval means, why it resamples route-directions, and what it does not cover (Q37–Q39).

### Questions to expect

| Question | Short answer |
| --- | --- |
| Did you cherry-pick the example? | No, it is chosen by a fixed rule, and it is unflattering: on that route last week's rule beat us, and 17 Apr is the only demand day on which the blend lost to the historical average (Q43). |
| Why is test WAPE lower than validation? | Different weeks, and the test model is refit on more data. Nothing guarantees the order (Q45). |
| Is RMSE also better? | Not for demand: 29.72 for the blend against 29.58 for the historical average. The gain is in absolute error (Q37, Q40). |
| Was 21 April bad because of the holiday? | We cannot separate holiday from Sunday with one example; 28 April, a normal Sunday, was also high at about 26% (Q42). |
| How many route-hours are scored? | 127,935 observed test route-hours for demand and 127,855 for load. Missing records are never scored. |

**Check your understanding:**
- Compute WAPE for actuals (10, 30) and forecasts (12, 24). Answer: (2 + 6) / 40 = 20%.
- Why would MAPE break on this data?
- What does a bias of −0.49 mean?

---

## Disha Khushalani: live dashboard demo and deployment

**Slide:** 12 Live demo. The exact click order and the fallbacks are in [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md).

### What to say (under 3 minutes)

- "This dashboard runs on this laptop from the committed result files. It needs no download and no internet, and it shows exactly the numbers we evaluated."
- **Forecast explorer.** "Here is route 137 on Wednesday 17 April. The dark line is what happened; blue is our forecast; the dotted orange line is last week's rule; the shaded band is the 80% interval. Below is the estimated load, with lines at 50% and 80% of the bus capacity."
- **Capacity.** "If I change the bus size from 70 to 40 seats, the crowding strip turns more red. The crowding level depends on an assumption about the bus, which is why we report four sizes."
- **Model comparison.** "These are the test-week tables. If I open this check, it recomputes every WAPE from the saved predictions; they all match."
- **Next-day forecast.** "This is a genuine forecast for 29 April, the day after our data ends. It lists the hours most likely to be crowded. It has no actuals, so it is a demonstration, not an evaluated result."
- **Missing records** (if one appears): "An open circle is an hour the route normally runs but has no record that day. We treat it as missing data, never as zero."

**Deployment.** "It is not deployed publicly yet. Deploying needs Jay's GitHub sign-in on Streamlit Community Cloud." Only if Jay has deployed it and you opened it that day, say instead: "It is also live at this address."

### Three ideas you must understand

1. **Where the numbers come from:** the app only reads `reports/metrics.json` and `data/predictions/`, and the test suite checks they agree (Q55).
2. **Crowding = estimated load ÷ assumed capacity,** with thresholds of 0.5 and 0.8 (Q46, Q47).
3. **The interval band,** and where it fails: night-time load (Q50, Q52).

### Questions to expect

| Question | Short answer |
| --- | --- |
| Is the model running live? | No. The app shows the saved, evaluated predictions; retraining takes about 8 minutes and is done by a separate command (Q6). |
| What if the internet fails? | The local app needs no internet. If the laptop fails, play the 68-second video. |
| Why is the next-day forecast not scored? | 29 April is outside our study window. We excluded 29–30 April because those files cover noticeably fewer routes than other days, so they would not be a fair test. |
| Can I pick any route? | Yes: every in-scope route-direction, busiest first, for the validation or test days. |
| How do you know the numbers match the report? | The check on the Model comparison page, plus automated tests (Q55). |

**Check your understanding:**
- What does an open circle mean?
- Why does the crowding strip change but the forecast line does not when you move the slider?
- What do you do if `streamlit` is not recognised on the demo laptop?

---

## Shivani Mahour: crowding, capacity assumption and limitations

**Slides:** 11 Crowding, 13 Limitations.

### What to say

**Slide 11.**
- "SUNT has no vehicle capacity, so we use the minimum capacities in the Brazilian bus standard ABNT NBR 15570: 40, 70, 80 and 100 passengers. Seventy is our base case."
- "Crowding level is estimated load divided by capacity: low below 50%, high from 80%. Those two thresholds are our own choice."
- "At 70 passengers, macro-F1 is 0.769. When we say 'high', we are right 79% of the time, and we catch 61% of high hours."
- "The bigger the bus, the rarer high crowding becomes: from 28.2% of hours at 40 seats to 0.5% at 100, and recall for 'high' falls from 0.79 to 0.25."
- "The practical test: of the 50 route-hours we flag each day, 92% were really high crowding, against 79% for last week's rule. The historical average's list is almost as good, at 91%."

**Slide 13.**
- "These are the limits of our evidence:
  - one Brazilian city and 59 days;
  - an estimated load and an assumed capacity;
  - a small gain over the historical average;
  - test weeks scored twice;
  - a forecast that assumes we know which hours a route runs;
  - no public deployment yet."
- "One limitation we found ourselves: the load intervals cover only about 52% of night hours, and the validation week shows the same. We report it rather than tune it on the test weeks."
- "Next steps: calibrate intervals per time of day, add holiday features, get a timetable for the same months, and test on a city with counted loads."

### Three ideas you must understand

1. **Why macro-F1 and not accuracy,** given the class shares at 70 seats: 76.6% low, 18.2% medium, 5.2% high (Q48).
2. **The capacity sensitivity:** what changes and what does not when the bus size changes (Q49).
3. **Marginal versus conditional coverage:** why 80% overall can still be 52% at night, and why we did not fix it on test (Q52).

### Questions to expect

| Question | Short answer |
| --- | --- |
| Where do 0.5 and 0.8 come from? | They are our choice. Only the capacities come from the standard (Q47). |
| Which bus size is right? | Unknown: SUNT does not say which vehicle runs each route, so we report all four (Q47, Q49). |
| Is the crowding model a classifier? | No. It thresholds the predicted load; there is no separate classifier (Q46). |
| What does the night interval problem mean for a planner? | Do not trust night-time load bands. It affects about 2,000 test rows (1.7%) (Q52). |
| Why not fix it now? | The fix would be tuned after seeing test results, a third look at the test weeks, so it is listed as future work (Q52). |
| What are the ethical risks? | Older riders are invisible, and errors are largest where cuts hurt most, so a human should decide (Q64). |
| Your estimated load on route 137 reaches about 98 on a 70-seat bus. Is that possible? | It could be an overloaded bus, a larger vehicle on that route, or estimation error in SUNT's trip chaining. We cannot tell which, which is one reason we show four capacities (Q49). |

**Check your understanding:**
- If capacity doubles, what happens to recall for "high", and why?
- Why does the alert list's precision matter more to a planner than macro-F1?
- What is the difference between a prediction interval and the bootstrap interval?
