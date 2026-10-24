# Final readiness checklist

Everything still to do before the evaluation on **Tuesday 3 November 2026, 6:00 PM**. Each action has one owner, what it needs first, the evidence that shows it is done, and who can do it. Dates are suggestions within the plan: code freeze at the end of 31 Oct, rehearsals on 1–2 Nov.

**Who can do it:**
- **Human**: it needs a person, their account or their judgement.
- **Claude, after X**: Claude can do it in a session once X is given.

Tick an item only when its evidence exists. Last updated 24 Oct 2026.

## A. Accounts, deployment and the TA

| # | Action | Owner | Prerequisite | Evidence it is done | Who | By |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | ~~Deploy the dashboard publicly~~ **Done 24 Oct:** GitHub Pages, https://jayvaghela779.github.io/cs3011-public-transport-demand-occupancy/, all five pages checked in a real browser ([runbook §5](DEMO_RUNBOOK.md#5-public-dashboard-on-github-pages)) | Claude | none | Published files byte-identical to `main`; pages verified | Done | 24 Oct |
| A2 | ~~Add the live URL to the README and the demo slide~~ **Done 24 Oct** (README, runbook, report, slides 12–13) | Claude | A1 | Commit on `main`; deck updated | Done | 24 Oct |
| A7 | Open the public URL once on the campus network or the venue Wi-Fi, and note how long the first load takes (our measurement is from one home network) | Disha | Being on campus | Time written in the team issue | Human | 31 Oct |
| A3 | Send the TA email (draft is in Jay's local `ai_project\team_prep` folder, not in this repository) | Jay | The TA's name from the evaluation schedule spreadsheet | Email sent; the reply saved privately | Human | 26 Oct |
| A4 | Record the TA's answers: Brazilian dataset acceptable; estimated-load label acceptable; marking rubric; submission requirements; venue and slot; internet and projector; time limit; AI-assistance policy | Jay | A3 answered | "Open questions for the TA" in [PROJECT_PLAN.md](PROJECT_PLAN.md) ticked, with the answers (no private email text) | Human; Claude can update the docs once told the answers | 29 Oct |
| A5 | If the TA requires a submission (GitHub link, ZIP, report), submit it | Jay | A4 | Confirmation of submission | Human | TA's deadline |
| A6 | Check the registered title and the members' official names against the registration form | Jay | Access to the form or its confirmation email | Cover slide and README match the form exactly | Human | 28 Oct |

## B. Independent checks by each teammate

Each member runs the [runbook §1](DEMO_RUNBOOK.md#1-install-and-check-once-per-laptop-with-internet) steps on their own laptop. Each posts a comment, from their own GitHub account, on a GitHub issue named "Team install check", with their OS, their Python version, and the last lines of `pytest` and `transit.verify`.

| # | Action | Owner | Prerequisite | Evidence it is done | Who | By |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | Run the tests, verify and the dashboard | Jay | Python 3.12, git | Issue comment showing `93 passed` and `Reproduced` | Human | 28 Oct |
| B2 | Same | Akshar | Same | Issue comment | Human | 28 Oct |
| B3 | Same | Tirth | Same | Issue comment | Human | 28 Oct |
| B4 | Same, on the laptop that will run the demo | Disha | Same | Issue comment | Human | 28 Oct |
| B5 | Same | Shivani | Same | Issue comment | Human | 28 Oct |
| B6 | Full reproducibility check: run [`notebooks/reproduce_on_colab.ipynb`](../notebooks/reproduce_on_colab.ipynb) on Colab, or the five pipeline commands locally | Akshar | A Google account, or about 1 GB of free disk; allow about 20 minutes | Issue comment with the `transit.verify` output | Human | 29 Oct |
| B7 | Optional: download the Ahmedabad–Gandhinagar Mendeley dataset and confirm what its files contain, so the "why not India" answer rests on the files and not only on the description | Akshar | Internet; about an hour | A short note in the issue (file list, whether it has route counts) | Human | 30 Oct |

## C. Content checks by the section owners

| # | Action | Owner | Prerequisite | Evidence it is done | Who | By |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | Check every number on slides 6–10 against [RESULTS.md](../reports/RESULTS.md) and the dashboard; read Q34–Q45 of the [question bank](VIVA_QUESTION_BANK.md) | Tirth | B3 done | Issue comment "slides 6–10 checked", or a list of corrections | Human | 30 Oct |
| C2 | Rehearse the 3-minute demo three times on the demo laptop, timed, including one run with the video fallback | Disha | B4 done | Times written in the issue; all under 3:15 | Human | 1 Nov |
| C3 | Prepare the limitations and crowding answers: DECISIONS D8–D13, Q46–Q54 and Q62–Q66 | Shivani | None | Answers Q47, Q49 and Q52 aloud in rehearsal without notes | Human | 1 Nov |
| C4 | Prepare the data answers: Q8–Q17 | Akshar | None | Answers Q8, Q10 and Q13 aloud in rehearsal | Human | 1 Nov |
| C5 | Prepare the framing and model answers: Q19–Q30 and Q44 | Jay | None | Answers Q29, Q37 and Q44 aloud in rehearsal | Human | 1 Nov |
| C6 | Each member can say honestly how the code was written and what they did (Q7) | All | None | Said aloud in rehearsal | Human | 1 Nov |

## D. Team decisions

| # | Action | Owner | Prerequisite | Evidence it is done | Who | By |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | Choose a licence for our own code (MIT proposed). Until then the code is not licensed for reuse | Team, Jay records it | Agreement of all five | A `LICENSE` file on `main`, and the README "Licence" section updated | Decision: Human. File: Claude, after the decision | 29 Oct |
| D2 | Night-time interval gap: leave it documented (the current state), or fix it with a per-period conformal margin, which would be a third, disclosed look at the test weeks | Team | Read D13 and Q52 | The decision written in DECISIONS.md D13 | Decision: Human. A fix, if chosen: Claude, with full disclosure | 29 Oct |
| D3 | Confirm the speaking split, or change it | Team | Read [TEAM_PRESENTATION_GUIDE.md](TEAM_PRESENTATION_GUIDE.md) | The team slide and the guide's table match what is rehearsed | Human; Claude can update both after being told | 30 Oct |
| D4 | Decide whether anything should be said about the one early merge commit that shows Jay's personal email address. It cannot be removed without rewriting public history, which we do not do. Turning on GitHub's "Keep my email address private" protects future commits | Jay | None | Setting turned on; decision noted | Human | 26 Oct |

## E. Presentation, freeze and rehearsal

| # | Action | Owner | Prerequisite | Evidence it is done | Who | By |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | Review the slide deck visually, every slide. Nobody has checked the rendered slides yet | Jay | None | Issue comment or a list of fixes | Human | 29 Oct |
| E2 | Re-export the PowerPoint and PDF. The copies in the local `ai_project` folder are older than the 24 Oct audit edits to slides 5, 9 (speaker notes), 11 and 14 | Jay | E1 | New files dated after E1 | Human | 31 Oct |
| E3 | Code freeze: no changes to `main` except fixes found in rehearsal | Jay | B1–B5 and C1 done | A git tag such as `v1.0-evaluation` on `main` | Claude, after Jay asks; or Jay | 31 Oct |
| E4 | Full rehearsals with a timer, then 10 minutes of questions from the question bank asked by teammates | All | E1–E3 | Two rehearsals done on 1–2 Nov, with times noted | Human | 2 Nov |
| E5 | Backup demo ready: the video on the demo laptop and on a USB stick; a second laptop with the app installed and tested | Disha, plus one more member | B4 | The video plays on both; the second laptop shows the app | Human | 2 Nov |

## F. On 3 November

| # | Action | Owner | Evidence |
| --- | --- | --- | --- |
| F1 | Laptop charged; charger and display adapter packed | Disha | Packed |
| F2 | The local app running and on the Forecast explorer by 5:30 PM; the public URL opened once on the demo laptop by 5:30 PM, if the team will show it | Disha, Jay | Both open in the browser |
| F3 | The local app still works with Wi-Fi off | Disha | Checked once on the day |
| F4 | The slides open in presentation mode on the room's display | Jay | Checked before the start |

## What Claude can still do on request

- Add a `LICENSE` file or a git tag.
- Update the docs with the TA's answers.
- Edit slide text.
- Apply the night-interval fix with disclosure, if the team chooses it.
- Run mock viva questions.

Claude cannot sign in to GitHub or Streamlit as Jay, contact the TA, or run anything on teammates' laptops.
