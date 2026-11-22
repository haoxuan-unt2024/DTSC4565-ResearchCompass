# Project Brief: Research Compass (v2)

## What we want
A command-line tool that helps a graduate student turn a research interest into an organized literature survey: find papers, keep structured notes, export a matrix and outline. Later increments add topic indicators and a proposal skeleton. Search uses the Paperclip service.

## Users
One graduate student, own laptop, a few times a week for 1-2 semesters; may not be a programmer. Plain-text output that works with screen readers.

## Must do (first working version)
1. `init` creates a project (name, interest) in one JSON file; never overwrites one without `--force`.
2. `search` lists results numbered 1..N with title, author-year, and id.
3. `add 1 3` / `add all` adds results; a number outside 1..N is rejected.
4. A paper matching a surveyed one by id, DOI, or title is skipped, and the skip count is printed.
5. `note <id>` records theme, method, key finding, and limitation.
6. Relevance is an integer 1-5; any other value is rejected.
7. `matrix` exports a Markdown table, one row per paper.
8. `outline` groups papers by theme and ends with a "Gaps" section listing recorded limitations.
9. On any error: message on stderr, exit code 1, project file byte-identical.
10. `--offline` uses bundled fictional papers; every command but `ask` then needs no network or account.

## Should do (in this order)
1. `check` warns: under 10 papers, missing notes, one-paper themes, nothing from the last 3 years, no limitations.
2. Compare 1-8 topics: score 0-100, verdict, and its 4 indicators. Under 5 papers = "too narrow"; 40%+ review titles = "saturated". Missing year/abstract is left out of that share; over half missing = "low confidence". Report how many of 5 other weightings keep the same top topic.
3. Proposal skeleton from notes (citations, timeline with week totals, references); gaps show as `_TODO_`.
4. BibTeX export with unique keys.
5. `restore` undoes the last save.
6. AI reader (Paperclip `map`), saved as a file labelled unverified draft.

## Constraints
- Python 3.10+, standard library only; no server, no database.
- Paperclip SDK behind one adapter; key from `paperclip login` or PAPERCLIP_API_KEY only, never in the repo or project file.
- Only queries and AI-reader questions leave the laptop.
- Saves are atomic (temp file + rename) and keep the previous version as `.bak`.
- Cost: no paid model calls by the app; tests cost $0 and need no network.
- Each offline command finishes in under 2 s for 200 papers.

## Out of scope
Web/mobile UI, accounts, sharing, PDF download, finished proposal prose, non-author-year citation styles, plagiarism checks, editable score weights.

## Quality expectations
Layers: `cli.py` (I/O only) -> logic (`topics`, `survey`, `proposal`) -> `sources`, `storage`; logic never imports `cli`. Unit tests per module, a fake Paperclip client, a system test through `main()`; `uv run pytest` runs all. Every change: a pull request reviewed by another member, green tests, and a new test seen to fail when the feature is broken.

## Acceptance criteria
- `add 99` after 20 results: error, survey unchanged.
- `note <id> --relevance 7`: error, relevance unchanged.
- With `--offline`, comparing the three demo topics ranks federated learning first and marks the hallucination topic "saturated".
- Phases of 4, 8 and 4 weeks give a timeline ending at week 16.
- Without a Paperclip login, `search` says to sign in or use `--offline`; no traceback.

## Open questions (owner)
- Do the indicators match how advisors judge topics? (Product Owner: 2 advisors rank demo topics)
- Is Paperclip's coverage (arXiv, PMC, bioRxiv, medRxiv) enough for other fields? (Architect)
- Can non-programmers use a terminal? (Quality lead: usability test, 2 students)
- Must the proposal follow a department template? (Product Owner)
