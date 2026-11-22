# 01 Requirements: Research Compass

Phase 1 deliverable (Sommerville Ch 4). Owner: Haoxuan Zhang (Product Owner). Date: 2026-11-22.

**The requirements table (R1–R35) lives in one place only: [FULL_SPEC.md §2](FULL_SPEC.md).**
This file holds what the table does not: acceptance criteria in Given/When/Then form, how the v1 brief maps to the
new IDs, the ambiguity log, and what we cut.

## Priorities at a glance

| Tier | Delivered in | Requirements |
|---|---|---|
| **Must — MVP** | Sprint 1 | Functional R1–R12 (survey core, error contract, offline mode); non-functional R26–R34 |
| **Should** | Sprint 2 | R13 coverage check, R14–R18 topic indicators |
| **Should** | Sprint 3 | R19–R22 proposal skeleton and BibTeX, R23 `restore`; R35 portability |
| **Could** | if time remains | R24 AI reader, R25 corpus filter |

The order inside "Should" follows user value: a coverage check helps every student every week; topic indicators
help once, at the start; a proposal skeleton helps only after the survey is mostly done.

## Acceptance criteria (Given / When / Then)

### US1 — Search and add papers (R3–R6)
- **Given** a project and an offline search for "federated learning" with N results, **when** I run `add 1,2 3`, **then** exactly results 1, 2, 3 are in the survey and the message says "Added 3 paper(s)".
- **Given** the same search, **when** I run `add 99`, `add 0`, or `add abc`, **then** I see `error: '…' is not a result number between 1 and N`, the exit code is 1, and the survey is unchanged.
- **Given** a new project with no search, **when** I run `add 1`, **then** I see ``error: Nothing to add. Run `search` first.``
- **Given** result 1 is already in the survey, **when** I search again, **then** its line starts with `*`; **when** I run `add 1`, **then** the message says "skipped 1 duplicate(s)".
- **Given** a surveyed paper with DOI `10.1/ABC`, **when** I add a different-id paper with DOI `10.1/abc`, or a different-id paper titled the same apart from case and punctuation, **then** it is skipped.

### US2 — Reading notes (R7, R8, R11)
- **Given** a surveyed paper `demo_002`, **when** I run `note demo_002 --theme "  Client  Drift "`, **then** its theme is `client drift` and its other fields are unchanged.
- **When** I run `note demo_002 --relevance 0` (or 6, or −1), **then** I see `error: Relevance must be between 1 and 5.` and the stored relevance is what it was before; `--relevance 1` and `--relevance 5` are accepted.
- **When** I run `note no_such_id --theme x`, **then** I see ``error: No paper with id 'no_such_id' in the survey. Run `list` to see ids.`` and the project file is byte-identical.

### US3 — Exports (R9, R10)
- **Given** 3 surveyed papers, **when** I run `matrix`, **then** the table has a header, a separator, and 3 rows of 7 cells, even if a finding contains `|`.
- **Given** 2 papers themed "privacy" and 1 with no theme, **when** I run `outline`, **then** section 1 is "Privacy (2 paper(s))", section 2 is "Unsorted (1 paper(s))", and the last section is "Gaps reported in the literature" listing each recorded limitation with its citation, or a TODO if none.

### US4 — Data protection (R11, R23, R26–R28)
- **Given** any command that fails, **then** the project file's bytes are unchanged and the exit code is 1.
- **Given** a save during which the final rename fails, **then** the old file is unchanged, no `.tmp` file remains, and the message says the file was not changed.
- **Given** two saves, **then** `project.json.bak` holds the first; **when** I run `restore`, **then** the project is back to the first save; **when** I run `restore` again, **then** it is back to the second.
- **Given** a project file edited into invalid JSON while a backup exists, **when** I run any command, **then** the error names the problem and says to run `restore`.
- **Given** a project file with the same paper twice, relevance 7, or a 0-week phase, **when** I load it, **then** the error names the paper or phase and the problem.

### US5 — Topic indicators (R14–R18)
- **Given** the offline demo data, **when** I compare "federated learning medical imaging", "llm hallucination detection", and "graph neural networks drug discovery", **then** federated learning ranks first, hallucination detection is "saturated", each topic shows 4 indicator lines, the first output line says the numbers do not judge research value, and the robustness line reads "5 of 5".
- **When** I compare 9 topics, **then** I see `error: Compare at most 8 topics at once (got 9).`
- **Given** 10 papers of which 6 have no year, **then** the topic shows "Low confidence"; with 5 of 10, it does not.

### US6 — Proposal skeleton (R19–R22)
- **Given** phases `Review:4`, `Experiments:8`, `Writing:4`, **when** I run `proposal`, **then** the timeline's "Ends week" column reads 4, 12, 16 and the text says "Total: 16 weeks."
- **Given** a project with no research questions, **then** section 4 shows `_TODO: add research questions_` and a warning is printed on stderr.
- **When** I run `plan --phase Review:0` or `--phase Review:53`, **then** I see an error and the timeline is unchanged.

### US7 — Offline trial (R12, R32)
- **Given** no network and no Paperclip account, **when** I run the README walkthrough with `--offline`, **then** every command except `ask` succeeds.
- **Given** the Paperclip SDK is not installed, **when** I run `search` without `--offline`, **then** I see one line telling me how to install it and that `--offline` exists, and no traceback.

## Brief coverage (v2 brief → requirements)

| Brief item | Requirements |
|---|---|
| Must 1 `init` | R1, R2 |
| Must 2 `search` | R3 |
| Must 3 `add` | R4, R5 |
| Must 4 duplicates | R6 |
| Must 5 `note` | R7 |
| Must 6 relevance | R8 |
| Must 7 `matrix` | R9 |
| Must 8 `outline` | R10 |
| Must 9 error contract | R11 |
| Must 10 `--offline` | R12 |
| Should 1 `check` | R13 |
| Should 2 topics | R14, R15, R16, R17 (R18 suggestions) |
| Should 3 proposal | R19, R20, R21 |
| Should 4 BibTeX | R22 |
| Should 5 `restore` | R23 |
| Should 6 AI reader | R24 |
| Constraint: Python, stdlib | R35, R33 |
| Constraint: adapter, key handling | R31, R32, R34 |
| Constraint: only queries leave | R31 |
| Constraint: atomic saves, `.bak` | R26, R27 (R28 validation) |
| Constraint: cost | R33 |
| Constraint: 2 s for 200 papers | R29 |
| Users: screen readers, non-programmers | R30 |
| Quality expectations | R34, Definition of Done (Full Spec §1) |
| (from v1, kept as Could) corpus filter | R25 |

## ID map
How the requirement IDs in the earlier workbook (v1) map to the Full Spec IDs. Use the new IDs everywhere from now on.

| v1 ID | v1 requirement | New ID(s) | What changed |
|---|---|---|---|
| R1 | Create a project | R1, R2 | split: create / refuse to overwrite |
| R2 | Compare topics with score, verdict, reasons | R14 | now Should (Increment 2) |
| R3 | Too narrow / saturated | R15 | now Should |
| R4 | Narrower wordings | R18 | Should |
| R5 | Search, list, add, dedup | R3, R4, R5, R6 | split into four |
| R6 | Notes and relevance | R7, R8 | split |
| R7 | Matrix and outline | R9, R10 | split |
| R8 | Coverage report | R13 | now Should (first in order) |
| R9 | Proposal draft | R19, R20, R21 | split; now Should (Increment 3) |
| R10 | BibTeX | R22 | Should |
| R11 | AI reader | R24 | Could |
| R12 | Error contract | R11 | now explicitly byte-identical |
| R13 | Offline mode, tests without network | R12, R33 | split functional / cost |
| R14 | Key handling | R31 | adds "never in exports"; now tested |
| R15 | Sign-in hint | R32 | covers SDK missing, rate limit, timeout too |
| R16 | Logic separated from CLI | R34 | now checked by a test |
| R17 | Atomic saves, version check | R26, R27, R28 | split; adds backup and load validation |
| — | (new) | R16, R17 | missing-metadata handling, weight sensitivity (feedback B) |
| — | (new) | R23 | `restore` (feedback E) |
| — | (new) | R25 | corpus filter, previously only in the brief's Should list |
| — | (new) | R29, R30, R35 | performance, usability, portability with numbers |

## Ambiguity log

| Phrase | Why ambiguous | Readings | Decision |
|---|---|---|---|
| "duplicate paper" | preprint and journal versions have different ids | (a) same id only (b) same id, DOI, or title | (b); title is normalized (lower case, letters and digits only). A preprint with a changed title is **not** caught — accepted limitation |
| "recent" | fields move at different speeds | 2 years / 5 years / field-specific | 2 years for topics (R14), 3 years for the coverage warning (R13); open question for advisors |
| "papers missing notes" | which fields count? | any empty field / theme, finding, relevance | theme + finding + relevance (`is_complete()`); method and limitation are optional |
| "unchanged" after an error | same content or same bytes? | semantic / byte-identical | byte-identical, because it is easier to test and stricter |
| "fast" (v1 implied) | no number | — | R29: under 2 s for 200 papers |
| "usable by non-programmers" | no measure | — | R30: 2 students, 6 tasks, ≤ 30 min, ≤ 2 hints |
| "saturated" | sounds like a judgement of the field | indicator / verdict | an indicator label; the output says it does not judge research value |

## Removed or merged (YAGNI)
- Web UI, accounts, sharing, PDF download, citation styles beyond author-year, plagiarism checks: out of scope (Full Spec §2).
- Editable weights: out of scope now, the planned change request (Full Spec §7).
- A separate "export to Word" command: Markdown opens in Word and Google Docs already.
- A `remove` command exists in the code but is not a requirement and has no dedicated test; it stays because it is three lines, and it is not listed so nobody spends time on it. TODO (Sulav): add one test or delete the command.

**AI contribution:** Claude wrote the Given/When/Then criteria from the existing tests and error messages, built the
ID map, and proposed the ambiguity decisions. Haoxuan to confirm the "duplicate" and "recent" decisions with the instructor.
