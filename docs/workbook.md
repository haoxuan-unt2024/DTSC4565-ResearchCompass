# Team Workbook: Research Compass

Copied from se-agent `docs/TEAM_WORKBOOK.md`. Each section = one Sommerville phase. Date and initial every entry.
Long content lives in the linked files; this workbook is the running log.

> **Status (2026-11-22):** updated after the Project Brief evaluation (92/100). Requirement IDs now follow
> [FULL_SPEC.md §2](FULL_SPEC.md) (old→new map in [01_requirements.md](01_requirements.md#id-map)).
> Entries marked `[__]` still need the owner's initials after they have read and corrected them.

**Team name:** Research Compass  **App:** Research Compass (literature-survey organizer for graduate students, with topic indicators and a proposal skeleton in later increments)
**Members & roles:** Haoxuan Zhang – Product Owner · Dipesh Rayamajhi – Architect · Sulav Ghimire – Quality lead · Aayush Byanjankar – Process lead (Sprint 1, rotates) and Prompt engineer. Details and tasks: [00_team_charter.md](00_team_charter.md).

---
## 0. Charter (Ch 2, 3) · 2026-11-22 · AB [__]
- **Process model chosen and why:** incremental, Scrum-lite, three one-week sprints. The survey core is well understood and ships first; the risky questions (do topic indicators help? can non-programmers use a terminal?) need working increments in front of users. Plan-driven documents only where graded or read by se-agent.
- **Agile practices we use:** ☑ user stories ☑ sprints ☑ daily stand-up (3 lines) ☑ retrospective ☑ pair/peer review (fixed review pairs) ☑ CI tests (GitHub Actions, added 2026-11-22)
- **Definition of Done:** PR approved by someone else · CI green · a test seen to fail with the feature broken · test plan and README updated · no secrets · AI parts named in the PR. (Full Spec §1)
- **How we communicate / meeting times:** TODO: channel and stand-up time. Board: TODO link (Aayush, Sprint 1 task).
- **How we resolve disagreements:** 10 minutes with evidence; then the role owner decides (Dipesh structure, Haoxuan scope, Sulav Done); logged in the decisions log.
- **AI-use rules:** see [00_team_charter.md](00_team_charter.md#ai-use-rules-we-agree-to).

## 1. Requirements (Ch 4) · 2026-11-22 · HZ [__]
MVP = survey core. 35 requirements: 12 Must functional (R1–R12), 11 Should functional (R13–R23), 2 Could (R24–R25), 9 Must non-functional (R26–R34), 1 Should non-functional (R35). Full table: [FULL_SPEC.md §2](FULL_SPEC.md).

| ID | Type (F/NF) | Requirement (short) | Priority | Acceptance test | Owner |
|---|---|---|---|---|---|
| R1–R2 | F | `init` creates; refuses to overwrite without `--force` | Must | second `init` → error, file unchanged | Haoxuan |
| R3–R6 | F | search list, add, reject bad numbers, skip duplicates | Must | `add 99` after 20 results → error, survey unchanged | Haoxuan |
| R7–R8 | F | notes; relevance 1–5 only | Must | `--relevance 7` → error, unchanged | Haoxuan |
| R9–R10 | F | matrix; outline with Gaps section | Must | `\|` in a finding keeps 7 cells | Haoxuan |
| R11 | F | error contract: stderr, exit 1, byte-identical file | Must | bad add/note/plan/init → bytes unchanged | Aayush |
| R12 | F | `--offline` with fictional demo papers | Must | full workflow with no network | Dipesh |
| R13 | F | `check` coverage warnings | Should (Inc 2) | 1 old unnoted paper → 5 warnings | Haoxuan |
| R14–R18 | F | topic indicators, verdicts, missing data, sensitivity, suggestions | Should (Inc 2) | demo topics: federated first, hallucination saturated, "5 of 5" | Sulav |
| R19–R22 | F | proposal skeleton, TODO markers, timeline, BibTeX | Should (Inc 3) | 4+8+4 weeks → "Total: 16 weeks." | Aayush |
| R23 | F | `restore` | Should (Inc 3) | add, restore → 0 papers | Dipesh |
| R24–R25 | F | AI reader; corpus filter | Could | offline `ask` → clear error | Dipesh |
| R26–R28 | NF reliability / integrity | atomic save, `.bak`, validation on load | Must | failed rename → bytes unchanged | Dipesh |
| R29 | NF performance | 200 papers < 2 s | Must | measured 20 ms | Sulav |
| R30 | NF usability | 2 outside students, 6 tasks, ≤ 30 min, ≤ 2 hints | Must (test in Inc 2) | usability test | Sulav |
| R31 | NF privacy | key never written anywhere | Must | env key absent from every file | Dipesh |
| R32 | NF availability | Paperclip failures → one-line hint | Must | SDK missing → install + `--offline` hint | Dipesh |
| R33 | NF cost | no paid calls; tests $0 | Must | CI with no secrets | Sulav |
| R34 | NF maintainability | layering enforced | Must | AST tests | Dipesh |
| R35 | NF portability | Python 3.10+ on all OSes | Should | CI 3.10/3.12; Windows TODO | Sulav |

- **Stakeholders & what each wants:** student (less bookkeeping, never lose notes, honest topic signals); advisor (broad, current survey; correct citations; know what the AI wrote); instructor (small testable product, traceable process, low AI cost); Paperclip (use within limits); team (finishable scope).
- **Ambiguities / questions for the customer:** see [01_requirements.md](01_requirements.md#ambiguity-log); open questions with owners in Full Spec §2.
- **Requirements removed as unnecessary and why:** web UI, editable weights (now the change request), "score as a judgement", proposal as one Must (split), suggestions as a Must (now Should).
- **AI contribution note:** Claude split the Musts, proposed the MVP boundary and NF numbers; the 2 s limit was measured. Haoxuan to confirm the MVP boundary with the instructor.

## 2. Models (Ch 5) · 2026-11-22 · DR [__]
- Context model: [FULL_SPEC.md §3](FULL_SPEC.md)
- Use cases / sequence models: [02_models.md](02_models.md) §1, §3–§5; search-and-add in Full Spec §3
- Class (structural) model: Full Spec §3 (with invariants)
- State (behavioral) model: [02_models.md §6](02_models.md)
- Inconsistencies found and how resolved: MVP path skipped *TopicChosen* (added `Created → Surveying`); `restore` missing from models (added); `low_confidence` missing from class model (added); the draft claim that `note` cannot clear a field was wrong (diagram fixed). Details in 02_models.md §8.

## 3. Architecture (Ch 6) · 2026-11-22 · DR [__]
- **Chosen pattern(s):** layered (presentation → domain → data access) with Adapter + Strategy for paper sources.
- **NFRs that drove it:** R34 maintainability, R12/R33 offline and $0 tests, R32 friendly failures, R11/R26–R28 data integrity.
- **Alternatives rejected and why:** web app (no evidence of need yet), Paperclip CLI via subprocess (fragile), SQLite (JSON + atomic rename + `.bak` suffices), LLM ranking (unexplainable, costly).
- **Decisions log:** D1–D7 in [FULL_SPEC.md §4](FULL_SPEC.md); layer rules, interfaces and trade-offs in [03_architecture.md](03_architecture.md).
- **AI model/service in the app:** only the optional `ask` (Paperclip `map`, Could): 300 s timeout; output saved as "AI DRAFT (unverified)"; offline → error naming `note`; no cost to the app.

## 4. Design & implementation (Ch 7) · 2026-11-22 · DR [__]
- **Modules and owners:** `cli.py` Aayush · `survey.py` Haoxuan · `topics.py` Sulav · `proposal.py` Aayush · `sources.py`, `storage.py` Dipesh · `models.py` shared (Dipesh approves).
- **Patterns used and where:** Adapter (`PaperclipSource`), Strategy (`PaperclipSource`/`OfflineSource`), command dispatch (`cmd_*`), lazy initialization (SDK client).
- **Reused code / libraries and licenses:** Python stdlib (PSF); Paperclip SDK (Apache-2.0, optional, installed separately); pytest, pytest-cov (MIT). Our code MIT (TODO: confirm with course rules).
- **Branching & review rules:** `feature/<issue#>-name` → PR → 1 approval from the review pair → green CI → squash merge.
- **Technical debt we knowingly took on:** English phrase-matching for gaps; constant weights; one-step undo; `cli.py` at 84% coverage; live Paperclip tested only with a fake; no schema v2 migration yet.
- **Changes on 2026-11-22 (after the brief evaluation):** missing-metadata handling and `low_confidence` (R16); weight sensitivity (R17); `fsync`, temp clean-up, `.bak`, validation on load, `restore` (R23, R26–R28); `OSError` caught in the CLI (R11); clearer missing-SDK message (R32); tests moved from `app/research_compass/tests/` to `app/tests/` (they could not be collected); `app/download` restored as `app/.gitignore`; the unversioned Paperclip wheel removed from `pyproject.toml` extras because it made `uv sync` fail; CI added.

## 5. Testing (Ch 8) · 2026-11-22 · SG [__]
Full map with mutation results for R1–R35: [05_test_plan.md](05_test_plan.md).

| Requirement | Test (file::name) | Type | Passes? | Fails when code is broken? (tried it) |
|---|---|---|---|---|
| R2 | test_cli::test_errors_return_1_and_do_not_change_project | system | ✓ | ✓ |
| R5 | test_cli::test_add_rejects_out_of_range | system | ✓ | ✓ (v1) |
| R6 | test_survey::test_add_skips_duplicates_by_id_doi_and_title | unit | ✓ | ✓ (v1) |
| R7 | test_survey::test_update_note_sets_fields_and_lowercases_theme | unit | ✓ | ☐ TODO Sulav |
| R8 | test_survey::test_update_note_rejects_bad_relevance | unit | ✓ | ✓ (v1) |
| R10 | test_survey::test_outline_groups_by_theme_unsorted_last | unit | ✓ | ☐ TODO Sulav |
| R11 | test_cli::test_errors_return_1_…, test_unwritable_output_path_… | system | ✓ | ✓ |
| R12 | test_sources::test_offline_search_ranks_best_match_first | component | ✓ | ✓ (added after a missed mutation) |
| R16–R17 | test_topics (6 new tests) | unit | ✓ | ✓ |
| R26–R28 | test_storage (13 new cases) | component | ✓ | ✓ |
| R31, R32, R34 | test_nonfunctional | system, static | ✓ | ✓ |

- **Test command:** `cd app && uv run pytest` — 88 passed, ~0.2 s, 94% coverage (2026-11-22). **Not tested:** real Paperclip calls (manual smoke test per sprint), `__main__.py`, column alignment, "correctness" of scores (advisor check instead), Windows.
- **User testing:** planned for Sprint 2 — protocol in [05_test_plan.md §5](05_test_plan.md). TODO results.
- **Live Paperclip smoke test log:** TODO (one per sprint: date, query, result count, any error).
- **Bugs found after "done" and their cause:** (v1) DOI-or-title dedup key; empty-author test helper; demo abstracts missing query words. (2026-11-22) tests uploaded into the package so pytest collected nothing; `.gitignore` uploaded as `download`; `uv sync` failed on the unversioned wheel; `-o` into a missing folder crashed with a traceback; papers without abstracts lowered the gap score.

## 6. Evolution & retrospective (Ch 9) · 2026-11-22 · DR / AB [__]
- **Most likely future changes:** editable weights; second paper source; web front end; department template; citation styles. Ranked in [06_evolution_and_retro.md](06_evolution_and_retro.md).
- **Change request carried out:** CR-1 editable weights, planned for Sprint 3 (impact analysis and ~8 h estimate in 06). TODO: actual files and hours.
- **What would have made the change easier:** TODO after CR-1.

## 7. AI & prompt log
| Run # | Date | Prompts used | Model | Tokens / cost | What was useful | What was wrong / rejected |
|---|---|---|---|---|---|---|
| 0 | 2026-11-11 | none (chat with Claude, outside se-agent) | Claude | not tracked | first drafts of brief, workbook, app, tests | tests missed a recency off-by-one and a dedup bug; fixed via mutation |
| 0b | 2026-11-22 | none (Claude Code session, outside se-agent) | Claude | not tracked | brief v2, Full Spec and phase docs; code for R16, R17, R23, R26–R28; 30 test cases; found the broken test layout and `uv sync` failure | two weak tests (caught by mutation); a wrong claim in the models draft (caught by reading the code); role assignment is a proposal until the team confirms |
| 1 | TODO | 01, 02, 03 | gpt-6-luna | est. ≈ $0.01 | | |

- **Prompt review checklist (PROMPT_TEMPLATE) for `se-agent-prompts/prompts/01–07` · AB [__]:**
  ☑ Role and Task specific enough for the router to tell them apart ☑ Output formats checkable in five minutes (tables + `Status:` line) ☑ Constraints stop scope creep ("do not add features…") ☑ Verification asks for assumptions and gaps ☑ No secrets or personal data ☐ Tested on `examples/water-tracker.md` with the cheap model (TODO before Run 1)
- **Changes we made to our prompts after reviewing runs and why:** 2026-11-22, before any run: prompts 01 and 04 now keep the brief's priority order and increment tags (Must = MVP first, Should in the listed order), so agents do not treat every feature as equal.

## 8. Sprint retrospectives
| Sprint | Went well | Went badly | One improvement we will try |
|---|---|---|---|
| 0 | acceptance criteria with failure cases; offline demo mode | scope crept to 10 Musts; broken repo layout went unnoticed | CI on every push (done) |
| 1 | TODO | TODO | TODO |

## 9. Final demo checklist
☐ App runs from the README steps on a clean machine ☑ Tests pass (88/88, 2026-11-22) ☑ Each requirement traced to a test (R29–R30, R33 by measurement, user test, or CI) ☐ Every team member can explain the architecture ☐ AI contribution notes complete ☐ No secrets in the repo history (TODO: Sulav to run a secret scan)
