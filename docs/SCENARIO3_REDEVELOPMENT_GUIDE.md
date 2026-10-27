# Scenario 3 redevelopment guide

How the five members of CS3011 Group 52 can rebuild the project themselves in the new repository, [jayvaghela779/transit-demand-occupancy](https://github.com/jayvaghela779/transit-demand-occupancy), using this repository only as a reference for behaviour, decisions and historical results.

> **Read this first.**
> - **Planning basis:** the team's *Human-Led Project Rulebook & Redevelopment Plan* (team working rulebook, 26 Oct 2026). It is not stored in this repository.
> - **Scenario 3** ("AI may assist; students must do the substantive work") is a working assumption the team chose. It has **not** been confirmed as the instructor's policy. Ask the instructor or TA. If the written course policy is stricter, it wins, and tasks move to a stricter AI category.
> - **Everything below is a proposed future responsibility.** Nothing here says who did what in the past, and nothing here says that any new work has been done. A task is done only when its owner has produced it, tested it and can explain it.
> - **The legacy implementation was written in AI-assisted sessions** ([REFERENCE_GUIDE.md §J.5](REFERENCE_GUIDE.md#j5-provenance-of-the-legacy-implementation)). Do not present it, or anything copied from it, as your own Scenario 3 work.

## Contents

1. [How to use the legacy repository](#1-how-to-use-the-legacy-repository)
2. [AI-use categories under Scenario 3](#2-ai-use-categories-under-scenario-3)
3. [Behaviours to understand and rebuild](#3-behaviours-to-understand-and-rebuild)
4. [Shared contracts to agree before coding](#4-shared-contracts-to-agree-before-coding)
5. [Jay: project lead, architecture and forecasting](#5-jay-project-lead-architecture-and-forecasting)
6. [Akshar: dataset and data pipeline](#6-akshar-dataset-and-data-pipeline)
7. [Tirth: evaluation and statistical analysis](#7-tirth-evaluation-and-statistical-analysis)
8. [Disha: dashboard and application engineering](#8-disha-dashboard-and-application-engineering)
9. [Shivani: estimated load, crowding and limitations](#9-shivani-estimated-load-crowding-and-limitations)
10. [Shared responsibilities](#10-shared-responsibilities)
11. [Acceptance gates](#11-acceptance-gates)
12. [Git workflow, pull requests and contribution evidence](#12-git-workflow-pull-requests-and-contribution-evidence)
13. [Schedule, risks and scope control](#13-schedule-risks-and-scope-control)
14. [Decisions the team still has to make](#14-decisions-the-team-still-has-to-make)

---

## 1. How to use the legacy repository

**Use it for:**
- **Understanding:** what the system does and why. Start with [REFERENCE_GUIDE.md](REFERENCE_GUIDE.md), then [DECISIONS.md](DECISIONS.md) and [DATA.md](DATA.md).
- **Specifying behaviour:** for example "an absent hour is missing, not zero", "features for day D use only days before D", "every method is scored on the same rows". These are requirements you can write down, implement and test yourselves.
- **Comparison values:** numbers such as 541,611 route-hour rows or 18.15% demand WAPE are a check on your own implementation. If yours differ, trace and explain the difference. Never adjust your code or data to make them match.
- **A working fallback:** `main` here, its local dashboard and its public site stay untouched until the new version passes its gates (rulebook, section 3).

**Do not:**
- Copy the legacy source into the new repository, wholesale or module by module, and present it as new work.
- Reuse legacy result files (predictions, `metrics.json`, figures, RESULTS.md) as results of the new implementation.
- Quote a legacy number in the new report as if the rebuilt code produced it. Recompute every reported number from the new code's saved outputs.
- Edit, rebase or force-push this repository's history.

If the team decides to reuse a specific piece of legacy code (for example a small utility), record the decision, the reason and the source file in an issue, disclose it as required by the course, and make sure the owner can explain it line by line.

---

## 2. AI-use categories under Scenario 3

The rulebook uses five illustrative categories. **They are planning labels, not a measure of authorship and not an official policy.** A category being listed here does not mean the course allows it.

| Category | Typical uses in the rulebook | Restriction | Human accountability |
| --- | --- | --- | --- |
| **100% AI** | Routine mechanical formatting, spelling and grammar, table-of-contents formatting, repetitive document styling | Only if permitted. Never for technical content, results or analysis | A human checks that the factual and technical meaning did not change |
| **70% AI / 30% human** | Boilerplate, a non-core utility template, routine test scaffolding, a standard outline | **Not the default for assessed technical work.** Only where the specific task is explicitly permitted | A human selects, adapts, verifies, integrates and can explain the output |
| **50% AI / 50% human** | Debugging exploration, test-case brainstorming, comparing architecture alternatives, outline drafting, UI ideas | Shared problem-solving only; the decision stays with the student | A human evaluates the options, chooses, implements or adapts the solution, and tests it |
| **30% AI / 70% human** | Human-led data processing, core model implementation, substantive testing, evaluation, integration and report analysis | The default for the main implementation under Scenario 3 | The human performs most of the substantive work and independently verifies the results |
| **0% AI / 100% human** | Work the instructor requires to be independent; original judgement where required; contribution records; viva answers | No AI help where the policy requires independent work | The student personally performs the assessed work |

### 2.1 What this means in practice

Under the assistant-only assumption, the **main implementation, the experimental analysis and the important engineering decisions stay human-led**. Where the course permits it, AI may:
- explain an unfamiliar concept, library or error ("concept tutor");
- help diagnose a specific error from a minimal example, without replacing the module ("debugging partner");
- suggest edge cases that the student then selects and checks ("test brainstormer");
- list trade-offs between alternatives that the team then decides between ("design critic");
- improve clarity without changing facts, results or claims ("proofreader").

### 2.2 If an AI-suggested change is accepted

- The responsible student understands the resulting code and can explain it without help.
- The student verifies its behaviour with relevant tests and keeps the actual test output.
- The student can say why the implementation is appropriate, including its limits.
- The contribution record (issue, PR, report) says what the student actually did.
- The team's AI disclosure follows the real course requirements.

### 2.3 Not acceptable under the rulebook

- Asking an agent to build an assigned subsystem and then claiming to have implemented it.
- Submitting generated code, report text or analysis where the instructor requires independent work.
- Accepting code because it runs, because tests pass superficially, or because the UI looks good.
- Inventing contributions, authorship, tests, data sources, results, citations or review approvals.
- Rewriting, backdating or force-pushing shared history to hide how work was done.
- Using AI-written viva scripts instead of understanding; sharing credentials, personal records or restricted course material with AI tools.

### 2.4 The owner-verification loop (rulebook, section 2)

1. Understand the task and write acceptance criteria before using AI.
2. Attempt the core reasoning or implementation yourself, as far as the policy requires.
3. Use AI narrowly: an explanation, a diagnostic hypothesis, an alternative or a permitted draft.
4. Inspect any proposed output line by line: dependencies, edge cases, security, data leakage, licences.
5. Run focused tests, then the relevant integration tests.
6. Record material AI assistance where the instructor or the project rules require it.
7. Explain the final change to your reviewer without relying on AI.

### 2.5 AI-use log (one row per material use, if the course requires it)

| Date / owner | Task and purpose | AI assistance used | What I independently checked or changed | Evidence (test, issue, PR, file) |
| --- | --- | --- | --- | --- |
| | | | | |

Use it to describe the real workflow, never to create the appearance of human work.

---

## 3. Behaviours to understand and rebuild

Each row is a behaviour of the legacy system that the rebuild should either reproduce or consciously change. "Reference" points to where it is explained. "Comparison value" is the legacy number to compare against, not a target to hit.

| Area | Behaviour to understand | Rebuild expectation | Reference | Comparison value (legacy) |
| --- | --- | --- | --- | --- |
| Source | 59 SUNT OD files, 1 Mar–28 Apr 2024, pinned commit, SHA-256 checks | Re-derive the coverage and licence from the source itself | REFERENCE_GUIDE §D.1 | 59 files, about 510 MB |
| Aggregation | Route × direction × clock hour; 30-hour service window; nothing capped | Reimplement; test by hand on a tiny fixture | §D.3–D.4 | 541,611 rows; 51,353,180 boardings |
| Quality | Six checks (unique keys, all days, conservation, no negatives, malformed trips, window) | Write your own checks, at least these | §D.5 | all six pass |
| Missing hours | Absent ≠ zero; training-only service profile; missing records never scored | Agree the rule first (contract), then implement and test | §D.6, D8 | 2,797 missing test slots |
| Malformed trips | Flag, keep, exclude their loads | Decide and document the policy | §D.7, D9 | 222 trips, 116 route-hours |
| Load target | Mean over trips of each trip's peak estimated load in the hour | Confirm from SUNT's documentation what `loading` means | §A.2, §G.1 | |
| Features | Only days before D; lags 1/7/14/21/28, rolling and same-day-type means | Design your own feature set; prove no leakage with a test | §E.1 | |
| Baselines | Same hour last week; last-4-weekday mean; historical average; fallback chain | Implement at least two strong baselines with explicit fallbacks | §E.2 | demand test WAPE 23.67% and 18.35% |
| Model | LightGBM, small grid, early stopping on validation, refit on train + validation | Choose and justify the learned method; select on validation only | §E.3–E.4 | demand test WAPE 18.39% (alone) |
| Evaluation | Chronological split; identical scored rows; WAPE, MAE, RMSE, bias | Freeze the protocol before test scoring | §F | |
| Weak results | LightGBM alone tied the historical average on test, after a small validation lead | Report whatever your model does, including a baseline win | §F.6–F.7, D12 | 18.39% against 18.35% (demand, test) |
| Crowding | LF = load / capacity; low < 0.5, high ≥ 0.8; four capacities | Agree thresholds and sources; test boundaries and invalid capacity | §G | macro-F1 0.769 at 70 |
| Dashboard | Five pages; reads only saved outputs; recompute check | Build from verified outputs; visible error states | §H | |
| Reproducibility | Command sequence; compare a rerun with stored outputs | Own end-to-end run and comparison, with saved terminal output | §I | |

The legacy design has known weaknesses that a rebuild can avoid rather than copy: two test scorings, one reused validation week, a conformal step with no effect, no capacity validation, no dashboard error states, and a verify command that covers only two files ([KNOWN_ISSUES.md](KNOWN_ISSUES.md), REFERENCE_GUIDE §J.3).

---

## 4. Shared contracts to agree before coding

From rulebook section 10. Write each one down (for example in one short schema document in the new repository), get every affected owner to approve it, and only then work in parallel. The legacy names are a starting point to discuss, not a decision.

| Contract | What must be agreed | Owners | Legacy equivalent (reference only) |
| --- | --- | --- | --- |
| Processed data table | Unique key; column types and units; target columns; missing-value meaning; quality flags | Akshar + Jay | `route_hour.parquet`: key `(route, direction, ts_hour)` with `service_date`; 12 columns ([DATA.md](DATA.md)) |
| Feature matrix | Feature names; target day; allowed history window; categorical identifiers; no-future-data rule | Jay | `build_features`, `model_feature_names` |
| Prediction table | Keys; truth column; prediction columns; method label; split label; observed/scored flag | Jay + Tirth | `data/predictions/*.parquet` (REFERENCE_GUIDE §E.5) |
| Metrics artefact | Metric name, value, unit, direction of improvement, scored row count, split, method version | Tirth | `reports/metrics.json` |
| Crowding artefact | Load field; capacity value; load-factor thresholds; labels; sensitivity scenario | Shivani + Tirth | `crowding.py`; `crowding_test` in `metrics.json` |
| Dashboard input | Stable paths and schema; labels and units; behaviour when empty or missing; allowed filters | Disha + all owners | files listed in `web/index.html` `FILES` |
| Run configuration | Split dates; random seeds; package versions; commands; output paths | Jay + all | `config.py`, `requirements-lock.txt`, `lgbm.BASE_PARAMS` |

**Integration rule:** nobody changes a shared column name, metric definition or date convention without telling the downstream owners. A schema change comes with updated tests and documentation. Prefer an explicit failure over silently accepting incompatible data.

---

## 5. Jay: project lead, architecture and forecasting

**Primary reviewer:** Tirth (rulebook, section 4).

### Tasks
1. **Specification (J1):** one page stating the prediction target, horizon, unit (route × direction × hour), data coverage and expected outputs; the baseline methods and metrics written down before any comparison; the minimal vertical slice (one data slice through features, prediction, evaluation and display); a recorded team design review.
2. **Architecture and contracts (J2):** the contracts in section 4 agreed with each owner; an architecture diagram; module responsibilities; the command sequence for a full run.
3. **Baselines and forecasting pipeline (J3):** a seasonal-naive baseline using only data available at the forecast origin; a historical-average baseline with defined comparable days/hours and fallback; the training and inference workflow, with feature creation separate from model fitting; a time-aware split; model selection on validation only; predictions saved in the agreed schema with configuration and seeds.
4. **Leadership and integration (J4):** task issues and small PRs; interface and integration reviews (the module reviewer checks the substantive logic); merge windows and a known-good build; the old `main` kept as the fallback until the gates pass.

### Deliverables (suggested names; agree them at the contract freeze)
- A specification document and a schema/contract document in the new repository.
- An architecture diagram and the run order.
- Baseline and forecasting modules, and the saved prediction tables they write.
- An integration checklist and a reproducible end-to-end command sequence.

### Tests and verification
- Prediction shape, valid (finite, non-negative) values and agreement between output labels and model metadata.
- Date cut-offs: a leakage test that changes everything from day D onward and shows day D's features unchanged.
- Baselines on a toy series whose answer you can compute by hand, including the fallback path.
- Deterministic behaviour with fixed seeds, where expected.
- A clean end-to-end run from the documented setup, with the terminal output saved.

### Evidence to record
Issues for J1–J4 with acceptance criteria; PRs with the commands run and their actual output; the reviewed specification; the design-review notes; the saved end-to-end run log.

### Viva questions to be able to answer
- What exactly is predicted, for which unit and how far ahead?
- For each feature, what is the latest data it may use, and why is it available before day D?
- Why is a simple seasonal or historical baseline a necessary comparison? What do you report if it wins?
- Why must model selection use validation and not test? What did you choose, and on what evidence?
- How would a teammate recreate your main result from a fresh environment?

### Legacy reference
REFERENCE_GUIDE §A, §B, §E, §F.2; `src/transit/features.py`, `src/transit/models/`; decisions D3, D7, D12.

### AI boundary (rulebook)
Acceptable if allowed: concept explanations, the meaning of model parameters, possible diagnostics, edge cases. Not acceptable: submitting a generated forecasting subsystem as independent work, or adopting an unverified feature or model choice.

---

## 6. Akshar: dataset and data pipeline

**Primary reviewer:** Jay.

### Tasks
1. **Source inspection and provenance (A1):** read the SUNT documentation and the actual files; write a column dictionary (meaning, type, unit, caveats); confirm the licence and attribution from the dataset page and the paper; confirm coverage, the date/time convention and which values are observed or inferred; list missing records, duplicates, malformed rows and other issues **before** choosing a policy.
2. **Ingestion and transformation (A2):** the agreed input-loading path, with any manifest or checksum logic separate and testable; required-column validation with understandable errors; consistent timestamp and identifier parsing with the time-zone and service-day conventions documented; aggregation to the agreed grain; the agreed rules for missing hours and malformed trips (never silently zero); a machine-readable quality report.
3. **Testing (A3):** see below.

### Deliverables
- Source and provenance note, licence citation, data dictionary and a list of observed quality issues.
- Ingestion and aggregation code; the processed table; the quality report.
- Hand-off note: stable schema, key-uniqueness rule, missing-value meaning and the exact build command. Notify Jay and Tirth before any schema change.

### Tests and verification
- A tiny hand-checkable fixture that tests the aggregation arithmetic.
- Absent columns, invalid timestamps, duplicate inputs and empty input.
- Missing-hour handling and the malformed-record policy.
- Checksum mismatch, if checksums are used.
- Running the build twice from a clean state and comparing the substantive outputs.
- Compare your row count, route count and total boardings with the legacy values (REFERENCE_GUIDE §D.5) and explain any difference.

### Evidence to record
Issues for A1–A3; the data dictionary; PRs with test output; the quality report; the record of the two clean builds and their comparison.

### Viva questions
- Where does the dataset come from, what is its licence, and what limits its labels?
- Trace one raw stop event through every aggregation step to a route-hour row.
- Why is an unrecorded hour not automatically zero demand?
- Which records did you flag or exclude, and why?

### Legacy reference
REFERENCE_GUIDE §D; [DATA.md](DATA.md); `src/transit/data/`; decisions D1, D7, D8, D9, D11.

### AI boundary
AI may explain pandas functions, suggest test cases or diagnose an error. Akshar implements or adapts the substantive transformations, inspects the data, decides and documents policies with the team, and verifies the output values.

---

## 7. Tirth: evaluation and statistical analysis

**Primary reviewer:** Akshar.

### Tasks
1. **Evaluation protocol (T1):** the train/validation/test split and the role of each, written before final model selection; which rows are scored and how missing or unobserved route-hours are treated; the baselines and metrics, each defined precisely with unit and direction of improvement; where tuning is allowed and how test results are handled to avoid optimistic selection; any subgroup analyses agreed before reading the test results.
2. **Metric implementation (T2):** MAE, RMSE and WAPE for the continuous targets (bias or others only if justified); the crowding classification metrics, with Shivani; row alignment that rejects mismatched prediction/truth keys instead of joining them silently.
3. **Comparison and error analysis (T3):** every method scored on comparable observed rows, with the counts shown; the learned method compared with each baseline, reporting when a baseline wins; errors examined by a justified dimension (hour of day, weekday/weekend, route) only where the data supports it; tables and plots produced from the saved predictions by scripts; confidence intervals only where the method is implemented correctly and its assumptions are stated.
4. **Consistency audit (T4):** a script or test that recomputes the headline metrics from saved predictions; README, report, slides and dashboard compared against the audited outputs; repeated test-set use, changed methods or discrepancies flagged openly; exact commands and output files for a teammate to reproduce.

### Deliverables
- A short evaluation protocol document, frozen before test scoring.
- Metric code with unit tests; evaluation tables and plots generated from saved predictions.
- An error-analysis note and the consistency-audit script or test.
- Hand-off: a stable summary table and metric definitions to Disha; crowding metrics coordinated with Shivani; the verified output schema to Jay.

### Tests and verification
- Hand-calculated toy arrays for every metric (for example y = [10, 0, 30], ŷ = [12, 1, 27] gives MAE 2, WAPE 0.15).
- Zero-denominator and empty-input behaviour, defined and tested.
- Mismatched keys or lengths raise an error.
- Recomputed headline metrics equal the reported ones.

### Evidence to record
The frozen protocol (with its date and commit, before test scoring); a log of every test-set evaluation; PRs with metric test output; the audit output.

### Viva questions
- Explain MAE, RMSE and WAPE. When can they tell different stories? (The legacy demand results are an example: the blend wins on WAPE but loses to the historical average on RMSE.)
- Calculate a small MAE and WAPE by hand.
- Why does repeatedly tuning on the test set undermine the evaluation? How many times was your test set scored?
- What does your confidence interval resample, and what does it not cover?

### Legacy reference
REFERENCE_GUIDE §F; `src/transit/metrics.py`, `src/transit/report.py` (`bootstrap_wape_diff`, `recompute_check`); decisions D3, D12, D13.

### AI boundary
AI may explain metrics, suggest diagnostic views or name statistical pitfalls. Tirth defines and implements the metric calculations, runs the analysis and reaches the findings from evidence.

---

## 8. Disha: dashboard and application engineering

**Primary reviewer:** Jay.

### Tasks
1. **User requirements (D1):** what each page must answer for an evaluator (forecast against actual, baseline comparison, crowding, error evidence, caveats); filters and interactions (route, direction, time, capacity); how the interface distinguishes prediction, observed value, estimate, missing data and invalid state; input schemas agreed with every owner before connecting live outputs.
2. **Application implementation (D2):** the local app first; data access, display logic and calculations kept apart where practical; readable titles, axis labels, units, legends and notes; honest baseline comparisons; the estimated-load caveat, capacity assumption and limitations shown near the relevant results; clear handling of missing files, invalid selections, empty rows and failed computations; no metric computed differently from Tirth's unless the difference is explicit and tested.
3. **Quality checks and demo (D3):** see below. Public hosting is secondary to a dependable local demo.

### Deliverables
- A short requirements and page specification.
- The dashboard application in the new repository, reading only verified outputs.
- Application tests; setup and demo instructions; a tested local fallback.

### Tests and verification
- Every page renders with the current outputs, and navigation works.
- Route, date and capacity interactions change the values as expected.
- Selected displayed values equal the source prediction and metric files.
- Missing or invalid files produce a visible error, never fabricated defaults shown as results.
- The app runs from the documented clean setup on the demo laptop; the full demo is timed and the local fallback rehearsed.

### Evidence to record
The page specification; PRs with test output and screenshots of real runs; a value-tracing note (displayed headline number → file → field); the timed rehearsal record.

### Viva questions
- Where does each displayed metric come from? Trace one number to its file and field.
- What happens when a source file or field is missing?
- How does the interface show that load is estimated and capacity is assumed?

### Legacy reference
REFERENCE_GUIDE §H; `app/streamlit_app.py`, `app/design.py`; [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md); `tests/test_app.py`.

### AI boundary
AI may critique a layout, explain framework errors or brainstorm accessibility checks. Disha implements the interface, validates the data wiring, exercises real browser interactions and owns the demo.

---

## 9. Shivani: estimated load, crowding and limitations

**Primary reviewer:** Tirth.

### Tasks
1. **Target and assumptions (S1):** from the dataset documentation, identify exactly how estimated load is derived; distinguish boardings, estimated on-board load and directly measured occupancy; list missing populations, data gaps and assumptions; check external capacity standards or dataset sources directly and cite them (not from AI summaries).
2. **Crowding logic (S2):** agree the load-factor formula and the thresholds before comparing results; implement classification as a small function with explicit input and output semantics; coordinate class labels with Disha and metrics with Tirth.
3. **Capacity sensitivity (S3):** several plausible capacity scenarios from justified sources or declared assumptions; labels recomputed under each, using the same predictions and evaluation rows; the number and share of high-crowding cases and the agreed metrics; which conclusions change with capacity and which do not; an illustrative alert kept distinct from a validated operational recommendation.
4. **Limitations and interpretation (S4):** the limitations section written after inspecting the actual findings; the Salvador-only scope, with no claim for Indian cities without evidence; unrecorded riders, estimated load and capacity assumptions; weak periods or intervals reported honestly (including night-time under-coverage if it reproduces); the same definitions in code, dashboard, report and slides.

### Deliverables
- A target and assumptions note with citations; the capacity table with its sources.
- The crowding function and its tests; the sensitivity results.
- The limitations section.
- Hand-off: target/threshold definitions agreed with Akshar; classification fields to Disha; metric requirements to Tirth.

### Tests and verification
- Values below, exactly on and above each threshold.
- Zero, negative or invalid capacity, missing values and load above capacity. (The legacy function does not reject invalid capacity: [KNOWN_ISSUES.md](KNOWN_ISSUES.md).)
- Sensitivity scenarios use the same rows as the base case.

### Evidence to record
The source citations; PRs with test output; the sensitivity table generated by a script; the reviewed limitations section.

### Viva questions
- Why is estimated on-board load not measured occupancy?
- Compute a load factor and classify it; explain what happens exactly at 0.5 and 0.8.
- How do capacity assumptions change the labels and the metrics? What stays stable?
- What does the project not establish, and what evidence would a stronger claim need?

### Legacy reference
REFERENCE_GUIDE §A.5, §G, §J; `src/transit/crowding.py`; decisions D4, D10, D11, D13.

### AI boundary
AI may explain classification metrics or suggest sensitivity scenarios. Shivani verifies the sources, implements the calculations and interprets the outputs herself.

---

## 10. Shared responsibilities

| Responsibility | What it means | Who |
| --- | --- | --- |
| **Integration** | One vertical slice working early; shared contracts respected; a known-good build kept at all times | Jay coordinates; every owner |
| **Code review** | A different teammate reads the change, checks the tests and asks questions; the author does not approve their own PR | Primary reviewers in sections 5–9 |
| **Documentation consistency** | Commands, dates, numbers, definitions and limitations agree across code, README, report, slides and dashboard | Each owner for their part; Tirth audits the numbers |
| **AI-use disclosure** | Disclosure that follows the actual course policy and the real workflow; AI-use log kept if required | Every member for their own work |
| **Reproducibility** | A clean environment reproduces the outputs with documented commands; terminal evidence saved | Jay coordinates; an independent teammate repeats it |
| **Report verification** | Every claim in the report traces to code, sources or output files | Each section owner; Tirth for results |
| **Understanding the whole system** | Every member can explain the full data flow, not only their module, and answers the rulebook's Appendix A questions in their own words | All |

**Reviewer load (Proposal).** The rulebook's primary reviewers give Jay and Tirth two reviews each and Disha and Shivani none. The team may want to add secondary reviewers, for example Disha for Shivani's crowding labels (she displays them) and Shivani for Disha's limitation notes. This is a suggestion for the team to decide.

---

## 11. Acceptance gates

Tick an item only when its evidence exists (a test output, a reviewed PR, a document or a saved run). The rulebook's gates G0–G6 are shown in brackets.

### Requirements gate (G0 policy and scope, G1 contract freeze)
- [ ] The instructor's AI policy and submission requirements are asked and recorded. *Evidence: written answer, filed privately.*
- [ ] Scope is agreed (minimum viable scope from the rulebook, section 3). *Evidence: reviewed specification.*
- [ ] Dataset and target definitions are understood by all five members. *Evidence: data dictionary and target note reviewed by each owner.*
- [ ] The evaluation methodology is recorded before any test scoring. *Evidence: dated protocol document.*
- [ ] Module interfaces are agreed. *Evidence: the section 4 contracts approved by every affected owner.*

### Data gate (G2 for data)
- [ ] Input validation and aggregation work. *Evidence: tests on a hand-checkable fixture pass.*
- [ ] Every data-quality rule has a test. *Evidence: test names mapped to rules.*
- [ ] The output schema is documented. *Evidence: schema document matches the produced table.*
- [ ] Results are reproducible, or the differences are explained. *Evidence: two clean builds compared; comparison with the legacy counts explained.*

### Forecasting gate (G2 for models, G3 vertical slice)
- [ ] Baselines work. *Evidence: toy-series tests including fallbacks.*
- [ ] The main model trains and predicts. *Evidence: a clean run saves predictions in the agreed schema.*
- [ ] Feature leakage is checked. *Evidence: the leakage test passes.*
- [ ] Model selection uses validation appropriately. *Evidence: selection log on validation only; number of test scorings recorded.*
- [ ] At least one end-to-end path (data → forecast → score) works. *Evidence: saved run output.*

### Evaluation gate (G4 results integrity)
- [ ] Metric calculations pass independent hand-calculated examples. *Evidence: metric unit tests.*
- [ ] All models are scored on comparable observations. *Evidence: identical scored row counts per method.*
- [ ] Results are generated from actual saved predictions. *Evidence: the recompute script or test passes.*
- [ ] Weak or negative results are reported honestly. *Evidence: the results section states where a baseline wins or ties.*

### Dashboard gate (G5 demo readiness)
- [ ] Every page renders. *Evidence: app tests.*
- [ ] Inputs and outputs work correctly. *Evidence: interaction tests and a manual check list.*
- [ ] Displayed values match the underlying data. *Evidence: value-tracing note.*
- [ ] The demo works from the setup instructions on the demo laptop, with a fallback ready. *Evidence: timed rehearsal record.*

### Submission gate (G6 submission review)
- [ ] Code, report, diagrams and presentation describe the same implementation. *Evidence: consistency audit.*
- [ ] Every performance claim is verifiable. *Evidence: each number traced to a script and an output file.*
- [ ] Known limitations are stated. *Evidence: reviewed limitations section.*
- [ ] Every member can explain their actual contribution. *Evidence: rehearsal with follow-up questions.*
- [ ] AI assistance is disclosed as the course requires. *Evidence: disclosure checked against the policy.*

---

## 12. Git workflow, pull requests and contribution evidence

From the rulebook, section 11:

1. Keep this repository's `main` and the public site intact while the redevelopment is unverified.
2. Work in the new repository on feature branches (suggested: `feature/data-aggregation`, `feature/baselines`, `feature/forecasting`, `feature/evaluation`, `feature/crowding`, `feature/dashboard`, `test/reproducibility`, `docs/report-and-runbook`). Do not rewrite or backdate shared history.
3. One issue per substantive task, with owner, reviewer, acceptance criteria and the evidence required.
4. Small commits that describe the actual change and why, **from the account of the person doing the work**.
5. A PR that explains the implementation, decisions, tests run, limitations and any AI assistance the course requires.
6. A reviewer reads the code, checks the tests and asks questions; the author revises and can explain the code.
7. Merge only after checks pass and the reviewer approves. Authors do not approve their own PRs.

**PR description template**

```
Purpose / problem:
What I changed and why:
Key design decisions:
Tests run (exact commands and actual results):
Evidence or output files:
Known limitations / remaining work:
AI assistance (if required by policy):
Reviewer questions:
```

**Daily owner status (post in the team group)**

```
Owner:
Task / issue:
What I implemented or analysed today:
What I tested (command and actual result):
Evidence link (commit/PR/file):
What I can now explain independently:
Blocker / help needed:
Next step:
```

A commit count is not a measure of contribution. Do not invent past contributions or force an equal-looking history.

---

## 13. Schedule, risks and scope control

The rulebook's plan (dated 26 Oct 2026) assumes evaluation on **Tuesday 3 November 2026, 6:00 PM**; confirm the date, time and submission requirements with the instructor or TA. This guide does not record which milestones have been met.

| Date | Focus | Exit condition |
| --- | --- | --- |
| 26 Oct | Policy clarification, scope freeze, owner agreement, interface design | G0 and G1 complete |
| 27 Oct | Parallel implementation of the smallest substantive modules | Individual tests and first module outputs exist |
| 28 Oct | Integrate one end-to-end vertical slice | Data → forecast → score works once |
| 29–30 Oct | Essential tests, error analysis, crowding, dashboard integration | G2–G4 pass or blockers documented |
| 31 Oct | Code freeze; critical fixes only | A clean, identified candidate version reproduces |
| 1 Nov | Report, README and slides factual audit | All headline claims match code and outputs |
| 2 Nov | Full rehearsals and fallback test | Everyone can explain their component; local demo works |
| 3 Nov | Evaluation | Present the verified version and its evidence |

**If time slips, cut in this order:** optional UI refinement; new hosting work; extra models or datasets; secondary analysis not in the rubric. **Do not cut:** core data checks, the baseline comparison, held-out evaluation, accurate limitations, reproducibility evidence or individual learning.

**Fallback:** if the full rewrite cannot finish, the rulebook suggests a limited, transparent human-led improvement of the existing system rather than destroying it, with honest disclosure of what is legacy and what is new. That decision belongs to the team and must follow the instructor's policy.

---

## 14. Decisions the team still has to make

- What the instructor's AI policy actually allows, what must be disclosed, and which deliverables must be independent (gate G0).
- Whether the new repository rebuilds everything or improves a defined part of the legacy system (section 13, fallback).
- The contracts in section 4, including the missing-hour rule and the capacity sources.
- Whether to add secondary reviewers (section 10).
- Whether to keep LightGBM, prediction intervals and the public site in the rebuilt scope, or treat them as optional.
- A licence for the team's own code (the legacy repository has none yet).
