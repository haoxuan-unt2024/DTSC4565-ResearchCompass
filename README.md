# Research Compass

A command-line helper for graduate students. Its core job, and the first increment we deliver, is to
**organize a literature survey**: collect papers, keep structured reading notes, and export a matrix and outline.
Later increments add:

- **Topic indicators.** Compare candidate topics by how active, open, and review-heavy their literature is.
- **A proposal skeleton.** Build a proposal outline and BibTeX file from your own notes.

Paper search uses [Paperclip](https://github.com/GXL-ai/paperclip). Its corpus is **bioRxiv, medRxiv,
arXiv and PubMed Central**, so the app works best for biomedical, life-science, CS, physics and math topics.

> The app drafts; you decide. Topic scores are indicators of what the search results look like, not a judgement
> of research value, and every generated sentence must be checked.

## Install

Python 3.10+.

```
cd app
uv sync --extra dev                 # or: pip install -e ".[dev]"
uv run pytest                       # 88 tests, no network, no cost
```

For live search, also install and sign in to Paperclip:

```
uv pip install https://paperclip.gxl.ai/paperclip.whl    # or: pip install ...
paperclip login                     # or: export PAPERCLIP_API_KEY=pk_...
```

Never commit an API key. Without Paperclip, add `--offline` to any command to use the bundled
**fictional** demo papers (`research_compass/sample_papers.json`; ids start with `demo_`).

## Walkthrough

```
rc() { uv run python -m research_compass "$@"; }   # add --offline to try it without Paperclip

rc init thesis --interest "privacy-preserving ML in healthcare"

# 1. Topic
rc topics "federated learning medical imaging" "llm hallucination detection" --since 5y
rc choose "federated learning medical imaging"

# 2. Survey
rc search --limit 20                # searches the chosen topic
rc add 1 3 5                        # or: add all
rc list
rc note demo_002 --theme "client drift" --method "FedProx variant" \
    --finding "Drift correction improves non-IID accuracy." --limitation "Unseen scanners untested." --relevance 5
rc check                            # coverage and readiness warnings
rc matrix -o matrix.md
rc outline -o outline.md

# Optional AI reader (Paperclip `map`) over the last search; saved as a clearly-labelled draft.
# Needs Paperclip: with --offline it prints an error and suggests `note` instead.
rc ask "What dataset and evaluation metric does this paper use?"

# 3. Proposal
rc plan --rq "How can small hospitals benefit from federated training?" \
        --method "Simulate 5 sites on a public dataset" \
        --phase "Literature review:4" --phase "Experiments:8" --phase "Writing:4"
rc proposal -o proposal.md
rc bib -o refs.bib

# Made a mistake? Every save keeps the previous version in project.json.bak
rc restore                          # undo the last change (run again to redo)
```

Use `--corpus arxiv` (or `pmc`, `biorxiv`, `medrxiv`) to restrict Paperclip to one source.
Everything is stored in `project.json` (change with `--project path.json`), so it can live in git.

## How topic scores work

`score = 100 × (0.35·recent + 0.30·gap + 0.20·volume + 0.15·unsaturated)` where *recent* is the share of
papers from the last 2 years, *gap* is the share of abstracts with phrases like "remains unclear" or
"future work", *volume* is hits capped at 40, and *unsaturated* falls as review/survey titles approach 40%.
Fewer than 5 hits is "too narrow"; 40%+ reviews is "saturated". Papers without a year or abstract are left out of
that share (and the count is shown); if over half lack either, the topic is marked "low confidence". Because the
weights are a judgement, every comparison also reports how many of 5 alternative weightings keep the same topic first.
Weights are in `topics.py`; the reasoning is in [docs/FULL_SPEC.md §5.3](docs/FULL_SPEC.md).

## Layout

```
research_compass/
  cli.py        presentation: argument parsing and printing only
  topics.py     topic scoring and narrower-topic suggestions
  survey.py     dedup, notes, matrix, outline, coverage checks
  proposal.py   proposal draft, readiness checks, BibTeX
  models.py     data classes
  sources.py    PaperclipSource (adapter over the SDK) and OfflineSource
  storage.py    JSON save/load: atomic writes, .bak backup, validation, restore
tests/          unit, component, system and non-functional tests
```

## Your data

Everything lives in one JSON file. Saves are atomic (write a temp file, flush, rename), the previous version is
kept as `project.json.bak`, and a damaged file is refused with a message telling you to run `restore`. For a longer
history, keep `project.json` in git. Only search queries and `ask` questions are sent to Paperclip.

## Project documents

| File | What |
|---|---|
| [docs/RUN_BRIEF.md](docs/RUN_BRIEF.md) | Project brief v2 (what se-agent reads; under 4,000 characters) |
| [docs/FULL_SPEC.md](docs/FULL_SPEC.md) | Full Spec: requirements R1–R35, models, architecture, tests, run plan |
| [docs/00_team_charter.md](docs/00_team_charter.md) | Roles, per-sprint tasks, Definition of Done |
| [docs/01_requirements.md](docs/01_requirements.md) – [docs/06_evolution_and_retro.md](docs/06_evolution_and_retro.md) | Phase deliverables |
| [docs/workbook.md](docs/workbook.md) | Running team log |
| [se-agent-prompts/prompts/](se-agent-prompts/prompts/) | Our 8-section se-agent prompts |

## Known limits

- The live Paperclip path is tested with a fake client, not against the real service.
- Only one step of undo (`restore`).
- Gap detection is phrase matching on abstracts, so it misses gaps stated in other words.
- Proposal text is a skeleton built from your notes, not finished prose.
