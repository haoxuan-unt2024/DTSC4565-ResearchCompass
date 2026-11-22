# 05 Test Plan: Research Compass

Phase 5 deliverable (Sommerville Ch 8). Owner: Sulav Ghimire (Quality lead). Date: 2026-11-22.

## 1. How to run

```
cd app
uv sync --extra dev
uv run pytest                                              # 88 tests, ~0.2 s, no network, $0
uv run pytest --cov=research_compass --cov-report=term-missing
```

CI (`.github/workflows/tests.yml`) runs the same on every push and pull request, on Python 3.10 and 3.12.

**Coverage on 2026-11-22:** 94% of lines — `topics` 100%, `models` 99%, `proposal` 98%, `storage` 97%,
`survey` 96%, `sources` 95%, `cli` 84%, `__main__` 0%.

## 2. Test levels

| Level | What | Files |
|---|---|---|
| Unit | domain rules: dedup, notes, matrix, outline, coverage, scoring, verdicts, sensitivity, proposal, BibTeX | `test_survey.py`, `test_topics.py`, `test_proposal.py` |
| Component | storage (save/load/backup/restore/validation), sources (Paperclip adapter with a fake client, offline source) | `test_storage.py`, `test_sources.py` |
| System | the CLI through `main()` with `--offline`: full workflow, error contract, restore, output files | `test_cli.py`, `test_nonfunctional.py` |
| Static | layering rules read from the source code with `ast` | `test_nonfunctional.py` |
| Manual | one live Paperclip smoke test per sprint; review checklist (key handling, plain-text output) | workbook §5 |
| User | usability test (R30); advisor ranking check (R14–R17) | §5 and §6 below |

## 3. Requirement-to-test map (all requirements)

"Fails when broken" = we changed the code on purpose (a mutation), ran the suite, saw a failure, and reverted.
Mutations marked *(v1)* were done on 2026-11-11; the rest on 2026-11-22.

| Req | Test(s) (file::name) | Level | Fails when broken? |
|---|---|---|---|
| R1 | test_cli::test_full_workflow | system | ✓ indirectly (every later step needs the file) |
| R2 | test_cli::test_errors_return_1_and_do_not_change_project | system | ✓ removed the `--force` check → 1 failed |
| R3 | test_nonfunctional::test_search_lists_numbered_results_and_marks_surveyed | system | ✓ removed the `*` mark → 1 failed |
| R4 | test_cli::test_full_workflow (`add 1,2 3`, `bib` has 3 entries) | system | ✓ indirectly |
| R5 | test_cli::test_add_rejects_out_of_range; test_errors_return_1_… (`add` before search) | system | ✓ *(v1)* removed the range check |
| R6 | test_survey::test_add_skips_duplicates_by_id_doi_and_title | unit | ✓ *(v1)* disabled dedup; *(v1 bug)* DOI-or-title key found by this test |
| R7 | test_survey::test_update_note_sets_fields_and_lowercases_theme, test_update_note_unknown_paper, test_update_note_none_leaves_field | unit | ☐ **TODO (Sulav):** remove `.lower()` and confirm a failure |
| R8 | test_survey::test_update_note_rejects_bad_relevance | unit | ✓ *(v1)* allowed relevance 0 |
| R9 | test_survey::test_matrix_escapes_pipes | unit | ✓ *(v1)* removed pipe escaping |
| R10 | test_survey::test_outline_groups_by_theme_unsorted_last | unit | ☐ **TODO (Sulav):** sort "unsorted" first and confirm a failure |
| R11 | test_cli::test_errors_return_1_and_do_not_change_project, test_unwritable_output_path_is_an_error_not_a_crash | system | ✓ returned 0 on error → 4 failed; stopped catching `OSError` → 1 failed |
| R12 | test_sources::test_offline_source_is_deterministic, test_offline_search_ranks_best_match_first; test_cli::test_full_workflow | component, system | ✓ reversed offline result order → **not caught at first**; added the ranking test → 1 failed |
| R13 | test_survey::test_coverage_report_flags_problems, test_coverage_report_clean | unit | ✓ removed the no-limitation warning → 1 failed; removed the single-theme warning → 1 failed |
| R14 | test_topics::test_validate_queries_rejects, test_reasons_explain_score, test_recent_gappy_topic_is_promising; test_cli::test_full_workflow | unit, system | ✓ *(v1)* recency `>=` → `>` was **not caught at first**; boundary test added, now caught |
| R15 | test_topics::test_too_few_hits_is_too_narrow, test_many_reviews_is_saturated, test_rank_puts_too_narrow_last | unit | ✓ *(v1)* removed the saturation check; removed the too-narrow sort key |
| R16 | test_topics::test_missing_abstract_is_not_counted_as_no_gap, test_low_confidence_when_most_papers_lack_metadata, test_complete_metadata_adds_no_data_warning, test_recent_share_ignores_undated_papers | unit | ✓ gap share over all papers → 1 failed; `>` → `>=` at the 50% boundary → 1 failed |
| R17 | test_topics::test_weight_sensitivity_counts_weightings_that_agree, test_weight_sensitivity_dominant_topic_is_stable, test_alternative_weights_each_sum_to_one; test_cli::test_topics_output_labels_scores_as_indicators | unit, system | ✓ made every weighting "agree" → 1 failed |
| R18 | test_topics::test_suggest_narrower_finds_repeated_phrases, test_suggest_narrower_excludes_query_words | unit | ✓ lowered the threshold from 2 papers to 1 → 1 failed |
| R19 | test_proposal::test_proposal_has_all_sections_and_citations, test_citation_styles | unit | ☐ not yet tried |
| R20 | test_proposal::test_proposal_marks_missing_parts_todo, test_readiness_empty_project_lists_everything, test_readiness_full_project_ok | unit | ✓ replaced the missing-RQ TODO with text → 1 failed |
| R21 | test_proposal::test_parse_phase, test_parse_phase_rejects, test_proposal_has_all_sections_and_citations | unit | ✓ *(v1)* timeline total not cumulative |
| R22 | test_proposal::test_cite_keys_are_unique, test_bibtex_entry | unit | ✓ changed the key suffix from letters to digits → 1 failed (a mutation that stopped the suffix from changing made the code loop forever, which is a test of its own: it would hang CI) |
| R23 | test_storage::test_restore_swaps_file_and_backup, test_restore_refuses_damaged_backup, test_restore_without_backup; test_cli::test_restore_undoes_the_last_change | component, system | ✓ restore read the current file instead of the backup → 3 failed |
| R24 | test_sources::test_paperclip_ask_returns_final_output, test_paperclip_ask_needs_result_id; test_cli::test_ask_offline_fails_gracefully | component, system | ✓ ignored the reader's output → 1 failed |
| R25 | test_sources::test_paperclip_source_maps_results_and_skips_bad_records (asserts `source="arxiv"`) | component | ☐ not yet tried |
| R26 | test_storage::test_failed_save_leaves_project_unchanged, test_round_trip | component | ✓ removed temp-file clean-up → 1 failed |
| R27 | test_storage::test_save_keeps_previous_version_as_backup | component | ✓ removed the backup copy → 4 failed |
| R28 | test_storage::test_corrupt_json, test_wrong_version, test_damaged_entry, test_duplicate_paper_in_file_is_rejected, test_bad_relevance_in_file_is_rejected (7, −1, "high"), test_zero_week_phase_in_file_is_rejected, test_top_level_must_be_an_object, test_load_error_points_to_backup, test_missing_file | component | ✓ removed the duplicate check → 1 failed; widened the relevance range → 2 failed; ✓ *(v1)* removed the version check |
| R29 | test_nonfunctional::test_200_paper_project_is_fast | component | n/a — timing bound (measured 20 ms vs 2 s limit) |
| R30 | usability test (§5); review checklist | user | n/a |
| R31 | test_nonfunctional::test_api_key_never_written_to_project_or_exports | system | ✓ wrote the env key into the JSON → 1 failed |
| R32 | test_nonfunctional::test_missing_sdk_gives_install_hint_not_traceback, test_not_signed_in_gives_login_hint; test_sources::test_paperclip_errors_become_friendly_source_errors | component, system | ✓ dropped the `--offline` hint → 1 failed; *(v1)* removed the AuthError hint |
| R33 | whole suite runs in CI with no secrets and no network | system | n/a |
| R34 | test_nonfunctional::test_logic_modules_do_not_import_the_cli, test_only_the_adapter_imports_the_paperclip_sdk | static | ✓ `from . import cli` in `topics.py` → **not caught by the first version of the test**; scanner fixed → 1 failed; `from .cli import main` in `survey.py` → collection error; SDK import in `storage.py` → 1 failed |
| R35 | CI matrix (Python 3.10, 3.12 on Linux) | system | ☐ TODO: one manual run on Windows |

**What mutation testing taught us:** three times a test that "passed" could not catch a real bug — the recency
boundary (v1), the offline result order, and `from . import cli`. Each time we added or fixed a test. That is why
"a test seen to fail" is part of the Definition of Done.

## 4. The three most important tests
1. **A failed command never changes the file** (`test_errors_return_1_and_do_not_change_project`): `init`, then a bad `add`, an unknown `note`, a bad `plan --phase`, and a second `init` → every one exits 1, prints `error:`, and the file's bytes are identical.
2. **A crash during save loses nothing** (`test_failed_save_leaves_project_unchanged`): the final rename is forced to fail → old bytes unchanged, no `.tmp`, message says "not changed".
3. **Duplicates are caught by any identity** (`test_add_skips_duplicates_by_id_doi_and_title`): same id; different id but same DOI in different case; different id and DOI but same title → all skipped and counted.

## 5. Usability test (R30) — Sprint 2

- **Participants:** 2 graduate students from outside the team; at least one has never used a terminal. Recruited by Sulav; consent to note times and comments, no recording.
- **Setup:** their own laptop, the repository README, `--offline` mode, 30 minutes. A team member observes and only answers when asked (each answer = one hint).
- **Tasks** (from the user scenario in Full Spec §2):
  1. Install and create a project.
  2. Search for "federated learning medical imaging" and add 3 papers.
  3. Record a theme, finding, limitation and relevance for one paper.
  4. Enter relevance 7 by mistake, read the error, and fix it.
  5. Export the matrix and open it.
  6. Run `check` and explain one warning in their own words.
- **Measures:** completion per task, minutes per task, hints, errors, and one sentence on what they expected each command to do. After the session: "What would make you stop using this?"
- **Pass:** both participants finish all 6 tasks in ≤ 30 minutes with ≤ 2 hints each.
- **Decision rule:** if either participant fails tasks 1–3, the team writes a change request for a minimal web front end (only `cli.py` is replaced; see `03_architecture.md`).

| Participant | Terminal experience | Tasks done | Minutes | Hints | Main difficulty |
|---|---|---|---|---|---|
| P1 | TODO | | | | |
| P2 | TODO | | | | |

## 6. Advisor ranking check (R14–R17) — Sprint 2
Two advisors each rank five topics (the three demo topics plus two from their own field, searched live) from "most
worth a new student's time" to "least", without seeing the scores. We compare their order with the app's.
Agreement = number of topic pairs ordered the same way (out of 10). Owner: Haoxuan.

| Advisor | Pairs agreeing with the app (of 10) | Where they disagreed and why |
|---|---|---|
| A1 | TODO | |
| A2 | TODO | |

If agreement is 5 or lower for both, we change how verdicts are worded (e.g. "many recent papers" instead of
"promising") before touching the weights.

## 7. Edge cases we try to break each Must with
- `add`: 0, N+1, 99, `abc`, `1,,2`, `all` before any search.
- `note`: unknown id; relevance 0, 6, −1, 1, 5; whitespace-only theme; `|` and line breaks in a finding.
- Exports: empty survey; one paper; all papers unthemed.
- Storage: missing file, invalid JSON, a JSON list, schema version 99, duplicate ids, relevance 7 / −1 / "high", 0-week phase, rename failure, 200 papers.
- Paperclip: SDK missing, not signed in, expired login, rate limit, timeout, malformed records.

## 8. Not tested, and why
- Real Paperclip calls: need an account and may cost; one manual smoke test per sprint is logged in the workbook.
- `__main__.py` (two lines that call `main`).
- Exact column alignment of `list` and `topics` output.
- Whether the scores are "correct": there is no ground truth; §6 measures agreement with advisors instead.
- Windows: not yet run (R35 TODO).

**AI contribution:** Claude wrote 30 of the 88 test cases (2026-11-22) and ran the mutations above. It also produced two
weak tests at first (offline ranking untested; the layering scanner missed `from . import cli`); both were found by
mutation and fixed. Sulav to repeat the R7 and R10 mutations by hand.
