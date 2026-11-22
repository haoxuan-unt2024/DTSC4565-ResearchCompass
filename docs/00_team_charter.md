# 00 Team Charter: Research Compass

Phase 0 deliverable (Sommerville Ch 2, 3). Owner: Aayush Byanjankar (Process lead, Sprint 1). Date: 2026-11-22.

> Roles and tasks were **assigned automatically** from the team list on 2026-11-22, balancing the load across
> four people. Swap anything at the first stand-up and record the change here.

## Roles

Five roles, four people. Aayush holds two because Prompt engineer is the lightest role (three small se-agent runs)
and pairs naturally with running the board.

| Member | Role | Accountable for | Owns these files |
|---|---|---|---|
| **Haoxuan Zhang** | Product Owner, committer | The brief and requirements; priority and the MVP boundary; talks to the instructor and advisors | `docs/RUN_BRIEF.md`, `docs/01_requirements.md`, Full Spec §0 and §2, `survey.py` |
| **Dipesh Rayamajhi** | Architect | Models, architecture, decisions log; approves changes to `models.py`; leads the Sprint 3 change request | `docs/02_models.md`, `docs/03_architecture.md`, Full Spec §3–§5 and §7, `storage.py`, `sources.py`, `models.py` |
| **Sulav Ghimire** | Quality lead | Test plan, Definition of Done, mutation checks, usability test, CI | `docs/05_test_plan.md`, Full Spec §6, `tests/`, `topics.py`, `.github/workflows/tests.yml` |
| **Aayush Byanjankar** | Process lead (Sprint 1) and Prompt engineer | Board, stand-ups, retrospectives; se-agent prompts, run requests, run review | `docs/00_team_charter.md`, `docs/workbook.md`, `docs/06_evolution_and_retro.md`, Full Spec §1, §9–§11, `se-agent-prompts/`, `cli.py`, `proposal.py` |

Everyone writes code and reviews pull requests. "Owns" means accountable, not the only person who works on it.

**Process-lead rotation** (the course guide asks for the Scrum role to rotate each sprint):

| Sprint | Process lead |
|---|---|
| 1 — MVP | Aayush Byanjankar |
| 2 — Topic indicators | Sulav Ghimire |
| 3 — Proposal skeleton | Dipesh Rayamajhi |

**Review pairs** (who reviews whose PRs by default, so no one reviews their own module): Haoxuan → Dipesh's PRs,
Dipesh → Sulav's, Sulav → Aayush's, Aayush → Haoxuan's. Anyone may review when the default reviewer is busy.

## Tasks

Each task has one owner and a "done when" condition. These become GitHub Issues on the board.

### Sprint 1 — MVP (R1–R12, R26–R34)

| Owner | Task | Done when |
|---|---|---|
| Haoxuan | Confirm the MVP boundary (survey core first; topics and proposal later) with the instructor | Instructor's answer recorded in Full Spec §2 |
| Haoxuan | Review `survey.py` against R4–R10 and walk the user scenario end to end with `--offline` | Every R1–R12 acceptance test run by hand once; results in workbook §5 |
| Dipesh | Review the new `storage.py` (atomic save, `.bak`, validation, `restore`) and `sources.py` | PR approved; Full Spec §5.4 matches the code |
| Dipesh | Check the models in `02_models.md` against the running app | Every diagram element exists in the code, or the difference is logged |
| Sulav | Repeat two mutations by hand (R7 lower-casing, R10 unsorted-last) and fill the two `TODO` rows in the test plan | Both rows say "failed when broken" or a new test was added |
| Sulav | Turn on branch protection for `main` (1 approval + green CI) | A PR without approval cannot merge |
| Aayush | Set up the board (Backlog / Sprint / Doing / Review / Done) with one Issue per task in this table | Board link in workbook §0 |
| Aayush | Check that the README walkthrough works on a clean machine; file Issues for anything confusing | README run once from scratch; Issues filed |
| Aayush | File se-agent **Run 1** (prompts 01–03) and review the output against our requirements and architecture | Run logged in workbook §7 with what we adopted or rejected |
| All | Sprint review demo and retrospective | Workbook §8 row for Sprint 1 filled |

### Sprint 2 — Topic indicators (R13–R18, R30 user test)

| Owner | Task | Done when |
|---|---|---|
| Haoxuan | Advisor ranking check: 2 advisors rank the 3 demo topics plus 2 of their own, without seeing scores | Agreement recorded in `05_test_plan.md`; verdict wording changed if they disagree |
| Dipesh | Paperclip coverage check: 5 queries each from a social-science and an education student | Result and decision recorded under Open questions |
| Sulav | Run the usability test with 2 graduate students outside the team (protocol in `05_test_plan.md`) | Times, hints and errors recorded; pass/fail against R30 |
| Sulav | Own `topics.py`: R16 low-confidence and R17 sensitivity reviewed and demoed | Demo shows "5 of 5" on demo topics and a "4 of 5" case |
| Aayush | Improve `cli.py` messages from usability findings | Each finding is fixed or has an Issue |
| Aayush | File se-agent **Run 2** (prompt 05, tester) | Missing tests found by the run are added or rejected with a reason |
| All | Sprint review and retrospective | Workbook §8 row for Sprint 2 |

### Sprint 3 — Proposal skeleton (R19–R23) and change request

| Owner | Task | Done when |
|---|---|---|
| Haoxuan | Ask the graduate coordinator whether a department proposal template is required | Answer recorded; R19 updated if needed |
| Haoxuan | Accept R19–R23 against their acceptance tests | All pass by hand and in CI |
| Dipesh | Lead the change request "editable score weights" (`06_evolution_and_retro.md`) | Merged with schema v2 migration; real hours recorded vs the 8 h estimate |
| Sulav | Regression and migration tests for the change request | A v1 file loads under v2; tests seen to fail when the migration is removed |
| Aayush | Own `proposal.py` / `bib` demo; optional se-agent **Run 3** (prompt 06) | Demo script rehearsed; run logged or skipped with a reason |
| Aayush | Final retrospective and presentation slides (six beats, Full Spec §11) | Every member has rehearsed their beat |

## Process
- **Model:** incremental, Scrum-lite, three one-week sprints (reasons in Full Spec §1).
- **Stand-up:** three lines (done / next / blocked) in class, and in the sprint's Issue thread on other days by 9 pm.
- **Communication:** TODO: channel (e.g. Discord or Teams) and meeting time.
- **Definition of Done:** Full Spec §1 (PR approved by someone else, green CI, a test seen to fail, test plan and README updated, no secrets, AI parts named).
- **Branching:** `feature/<issue#>-short-name`, pull request, one approval from the review pair, squash merge.

## Resolving disagreements
Ten minutes of discussion with evidence (a test, a user comment, a requirement). If still split, the role owner
decides: Dipesh for structure, Haoxuan for scope, Sulav for whether something is Done. The decision goes into the
decisions log (Full Spec §4) with the reason.

## AI-use rules we agree to
- AI drafts; a named human owns and can explain every artifact.
- Every deliverable ends with an "AI contribution" note.
- No keys, personal data, or instructor-only material in prompts or briefs.
- An AI-written test counts only after it has been seen to fail with the code broken.
- The app's own AI reader output is saved as a labelled draft and never copied into notes automatically.

**AI contribution:** Claude assigned roles and tasks from the team list, balancing workload and matching
module ownership to roles. The team has not yet confirmed them.
