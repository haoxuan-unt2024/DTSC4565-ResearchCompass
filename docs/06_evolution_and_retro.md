# 06 Evolution and Retrospective: Research Compass

Phase 6 deliverable (Sommerville Ch 9). Owners: Dipesh Rayamajhi (change request), Aayush Byanjankar (retrospective).
Date started: 2026-11-22. Sections marked TODO are filled in during Sprint 3.

## 1. Likely changes, ranked

| # | Change | Why it is likely | Trigger | Size |
|---|---|---|---|---|
| 1 | Student-editable score weights | Advisors in different fields will weigh recency and reviews differently | Advisor ranking check (test plan §6) | ~8 h |
| 2 | Second paper source (OpenAlex or Semantic Scholar) | Paperclip covers arXiv, PMC, bioRxiv, medRxiv only | Coverage check by Dipesh in Sprint 2 | ~6 h |
| 3 | Minimal web front end | Non-programmers may not manage a terminal | Usability test fails (test plan §5) | ~15 h |
| 4 | Department proposal template | Graduate programs often prescribe sections | Coordinator's answer (Haoxuan, Sprint 3) | ~3 h |
| 5 | APA / IEEE citation styles | Journals and departments differ | User request | ~4 h |

## 2. Change request CR-1: editable score weights (Sprint 3)

**Request.** "As a student whose advisor cares most about open problems, I want to set the weight of each topic
indicator, so that the ranking reflects what my field values." Requested by: Product Owner (Haoxuan), from the
expected advisor feedback.

**New requirement.** R36 (Should): `weights --recent R --gap G --volume V --unsaturated U` stores four non-negative
numbers that sum to 1 (±0.001) in the project; `topics` uses them, prints them above the table, and R17's
sensitivity line compares against them. Invalid weights → `error:` + exit 1, file unchanged.

**Impact analysis.**

| Artifact | Change | Estimate | Actual |
|---|---|---|---|
| Requirements (`01_requirements.md`, Full Spec §2) | add R36; update R14 and R17 text | 0.5 h | TODO |
| Models (`02_models.md`) | `Project.weights` attribute; new `weights` use case | 0.5 h | TODO |
| `models.py` | `weights: dict[str, float]` defaulting to `topics.WEIGHTS` | 0.5 h | TODO |
| `storage.py` | `schema_version` 2; a `migrate_v1(d)` that adds default weights; load accepts 1 and 2, always saves 2; validate the weights | 2 h | TODO |
| `topics.py` | none — `score_topic`, `rank_topics` already take `weights`; `alternative_weights` takes the base weights as an argument | 0.5 h | TODO |
| `cli.py` | `weights` command with validation; print weights in `topics` | 1.5 h | TODO |
| Tests | weight validation; a v1 file loads and gains defaults; ranking uses stored weights; sensitivity relative to stored weights; each seen to fail when broken | 2 h | TODO |
| Docs | README "How topic scores work", Full Spec §5.3 | 0.5 h | TODO |
| **Total** | | **~8 h** | TODO |

**Risks.** (1) A migration bug could make old project files unreadable — mitigated by the `.bak` backup, a
migration test on a real v1 file from the repo, and refusing (not guessing) unknown versions. (2) Students may set
weights to make a favourite topic win — the sensitivity line still reports how fragile the ranking is.

**Design choice that makes it easier.** Passing `weights` as a parameter (added for R17 on 2026-11-22) means the
scoring logic and its tests do not change; and `schema_version` was in the file from the start, so the migration
has something to switch on.

**Outcome.** TODO (Sprint 3): files touched, hours, and what was harder than expected.

## 3. What would have made the change easier
TODO after CR-1. Prompt for the discussion: which assumption in the code did the change break, and could a test
have warned us earlier?

## 4. Retrospectives

| Sprint | Went well | Went badly | One improvement we will try |
|---|---|---|---|
| 0 (brief, before the team sprints) | Acceptance criteria with failure cases scored highest; offline mode made demos reliable | Scope grew to 10 Musts because the AI-drafted prototype already did everything; repo upload broke the test layout without anyone noticing | Run `uv run pytest` in CI on every push (done 2026-11-22) |
| 1 | TODO | TODO | TODO |
| 2 | TODO | TODO | TODO |
| 3 | TODO | TODO | TODO |

## 5. Retrospective on the AI
- **Useful:** first drafts of requirements, models and tests; finding the broken test layout and the `uv sync` failure; mutation checks that exposed weak tests.
- **Wrong or rejected:** its first tests missed the recency off-by-one (v1), the offline result order, and one import form in the layering test; its first models draft claimed `note` cannot clear a field, which the code contradicts. All were caught by running the code, not by reading the AI's output.
- **Rule we keep:** the AI's output is a draft until a human has run it and seen a test fail.
- TODO (Sprint 3): each member adds one sentence.

**AI contribution:** Claude drafted the change list, CR-1 and its estimates, and the Sprint 0 retrospective row.
Dipesh owns CR-1; Aayush runs the retrospectives.
