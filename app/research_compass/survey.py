"""Literature survey: collect papers, keep structured reading notes, and organize them."""

from __future__ import annotations

import re
from collections import defaultdict

from .models import Paper, Project, SurveyEntry

MIN_PAPERS = 10
NOTE_FIELDS = ("theme", "method", "finding", "limitation")


def _keys(p: Paper) -> set[str]:
    """Identity keys: a paper is a duplicate if ANY key matches (id, DOI, or normalized title)."""
    keys = {"id:" + p.id, "title:" + re.sub(r"[^a-z0-9]", "", p.title.lower())}
    if p.doi:
        keys.add("doi:" + p.doi.lower().strip())
    return keys


def add_papers(project: Project, papers: list[Paper]) -> tuple[int, int]:
    """Add papers, skipping duplicates (same DOI, same id, or same title). Returns (added, skipped)."""
    seen: set[str] = set()
    for e in project.entries:
        seen |= _keys(e.paper)
    added = skipped = 0
    for p in papers:
        keys = _keys(p)
        if keys & seen:
            skipped += 1
            continue
        project.entries.append(SurveyEntry(paper=p))
        seen |= keys
        added += 1
    return added, skipped


def remove_paper(project: Project, paper_id: str) -> None:
    entry = project.find_entry(paper_id)
    project.entries.remove(entry)


def update_note(project: Project, paper_id: str, relevance: int | None = None, **fields: str | None) -> SurveyEntry:
    entry = project.find_entry(paper_id)
    unknown = set(fields) - set(NOTE_FIELDS)
    if unknown:
        raise ValueError(f"Unknown note field(s): {', '.join(sorted(unknown))}")
    if relevance is not None:
        if not 1 <= relevance <= 5:
            raise ValueError("Relevance must be between 1 and 5.")
        entry.relevance = relevance
    for name, value in fields.items():
        if value is not None:
            value = " ".join(value.split())
            setattr(entry, name, value.lower() if name == "theme" else value)
    return entry


def _cell(text: str) -> str:
    return (text or "—").replace("|", "\\|").replace("\n", " ")


def literature_matrix(project: Project) -> str:
    rows = sorted(project.entries, key=lambda e: (e.theme or "~", -(e.paper.year or 0), e.paper.title))
    lines = [
        f"# Literature matrix: {project.chosen_topic or project.name}",
        "",
        "| Ref | Title | Theme | Method | Key finding | Limitation / gap | Rel. |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in rows:
        lines.append(
            f"| {_cell(e.paper.citation())} | {_cell(e.paper.title)} | {_cell(e.theme)} | {_cell(e.method)} "
            f"| {_cell(e.finding)} | {_cell(e.limitation)} | {e.relevance or '—'} |"
        )
    return "\n".join(lines) + "\n"


def group_by_theme(project: Project) -> dict[str, list[SurveyEntry]]:
    groups: dict[str, list[SurveyEntry]] = defaultdict(list)
    for e in project.entries:
        groups[e.theme or "unsorted"].append(e)
    for entries in groups.values():
        entries.sort(key=lambda e: (e.paper.year or 0, e.paper.title))
    # Biggest themes first; "unsorted" always last.
    return dict(sorted(groups.items(), key=lambda kv: (kv[0] == "unsorted", -len(kv[1]), kv[0])))


def outline(project: Project) -> str:
    lines = [f"# Literature survey outline: {project.chosen_topic or project.name}", ""]
    for n, (theme, entries) in enumerate(group_by_theme(project).items(), 1):
        lines.append(f"## {n}. {theme.capitalize()} ({len(entries)} paper(s))")
        for e in entries:
            finding = e.finding or "TODO: add key finding"
            lines.append(f"- {e.paper.citation()} {finding}")
        lines.append("")
    gaps = [e for e in project.entries if e.limitation]
    lines.append("## Gaps reported in the literature")
    lines += [f"- {e.limitation} {e.paper.citation()}" for e in gaps] or ["- TODO: record limitations with `note --limitation`"]
    return "\n".join(lines) + "\n"


def coverage_report(project: Project, now_year: int) -> list[str]:
    """Warnings a supervisor would raise. Empty list = no problems found."""
    warnings = []
    n = len(project.entries)
    if n < MIN_PAPERS:
        warnings.append(f"Only {n} paper(s); aim for at least {MIN_PAPERS} before writing the survey.")
    incomplete = [e.paper.id for e in project.entries if not e.is_complete()]
    if incomplete:
        warnings.append(f"{len(incomplete)} papers lack a theme, finding, or relevance: {', '.join(incomplete[:5])}"
                        + (" ..." if len(incomplete) > 5 else ""))
    for theme, entries in group_by_theme(project).items():
        if theme != "unsorted" and len(entries) == 1:
            warnings.append(f"Theme '{theme}' rests on a single paper; find more or merge it.")
    if n and not any(e.paper.year and e.paper.year >= now_year - 2 for e in project.entries):
        warnings.append("No papers from the last 3 years; the survey may be out of date.")
    if n and not any(e.limitation for e in project.entries):
        warnings.append("No limitations recorded; the proposal's research gap will be unsupported.")
    return warnings
