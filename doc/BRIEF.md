# Project Brief: Research Compass

## What we want
A command-line app that takes a graduate student from a vague research interest to a draft proposal: compare candidate topics, organize a literature survey, and assemble a proposal from the student's own notes. Papers come from the Paperclip search service.

## Users
One graduate student on their own laptop, in a terminal, a few times a week over a semester or two. Not necessarily a programmer. Output must work with screen readers (plain text, no color-only meaning).

## Must do
1. Create a project from a name and a one-line research interest; store it in one JSON file.
2. Compare 1 to 8 candidate topics. For each, show a score from 0 to 100, a verdict (promising, possible, weak, saturated, too narrow), and the reasons behind it (number of papers, share from the last 2 years, share of abstracts naming a limitation or open problem, share of review titles).
3. Fewer than 5 papers gives "too narrow"; 40% or more review titles gives "saturated".
4. Suggest narrower topic wordings from phrases that repeat in result titles.
5. Search papers with Paperclip, list them numbered, and add chosen ones to the survey. Adding the same paper twice (same id, DOI, or title) is skipped and reported.
6. Record notes per paper: theme, method, key finding, limitation, relevance 1 to 5. Relevance outside 1 to 5 is rejected and nothing changes.
7. Export a literature matrix (Markdown table) and an outline grouped by theme, with a section listing reported gaps.
8. Report coverage problems: fewer than 10 papers, papers missing notes, themes with one paper, nothing from the last 3 years, no limitations.
9. Generate a proposal draft (introduction, related work by theme with author-year citations, research gap, research questions, methodology, timeline table with week totals, references) and a BibTeX file. Missing parts appear as visible TODO markers.
10. Every error prints a clear message, exits with code 1, and leaves the project file unchanged.

## Should do
- Run Paperclip's AI reader over a search and save the answer as a file labelled as an unverified draft.
- Restrict searches to one corpus (arXiv, PMC, bioRxiv, medRxiv).

## Constraints
- Platform: Python 3.10+, command line, no web server, no database.
- Paper search: Paperclip Python SDK (Apache-2.0), signed in by `paperclip login` or a PAPERCLIP_API_KEY environment variable. The key never goes in the repo or the project file.
- An `--offline` mode with bundled fictional sample papers, so tests and demos need no network or account.
- Data: notes stay in a local JSON file; only queries and AI-reader questions go to Paperclip.
- Cost: the app makes no paid model calls itself; the AI reader is optional.

## Out of scope
Web or mobile UI, accounts, sharing, PDF download, finished proposal prose, citation styles other than author-year, plagiarism checks.

## Quality expectations
Logic (scoring, survey, proposal, storage) in modules separate from the command-line code, each with unit tests. Paperclip behind an adapter so tests use a fake. One command runs all tests.

## Acceptance criteria
- With `--offline`, comparing the three demo topics ranks the federated-learning topic first and marks the review-heavy topic "saturated".
- Adding search result 99 when there are 20 results prints an error and the survey is unchanged.
- `note <id> --relevance 7` prints an error and the paper's relevance is unchanged.
- A project with one RQ and phases of 4, 8 and 4 weeks produces a proposal whose timeline ends at week 16.
- Without a Paperclip login, a live search prints how to sign in or use `--offline`, and does not crash.

## Open questions
- Are the score weights sensible? Should a student be able to change them?
- Paperclip covers biomedical sources and arXiv only. Is that acceptable for students outside those fields?
- Is a terminal acceptable to real users, or do they need a web page?
- Should the proposal follow a department template?
