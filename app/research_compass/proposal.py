"""Research proposal draft built from the project's own notes. Missing parts become TODO markers."""

from __future__ import annotations

import re

from .models import Paper, Phase, Project
from .survey import group_by_theme

MIN_NOTED_PAPERS = 5
MAX_WEEKS = 52


def parse_phase(text: str) -> Phase:
    """'Literature review:4' -> Phase('Literature review', 4)."""
    name, sep, weeks = text.rpartition(":")
    name = name.strip()
    if not sep or not name:
        raise ValueError(f"Phase must look like 'Name:weeks', got '{text}'.")
    try:
        n = int(weeks)
    except ValueError:
        raise ValueError(f"Weeks must be a whole number in '{text}'.") from None
    if not 1 <= n <= MAX_WEEKS:
        raise ValueError(f"Weeks must be between 1 and {MAX_WEEKS} in '{text}'.")
    return Phase(name, n)


def readiness(project: Project) -> list[str]:
    """What is still missing before the proposal is worth showing to a supervisor."""
    problems = []
    if not project.chosen_topic:
        problems.append("No topic chosen (run `choose`).")
    noted = [e for e in project.entries if e.finding]
    if len(noted) < MIN_NOTED_PAPERS:
        problems.append(f"Only {len(noted)} paper(s) have a key finding; need {MIN_NOTED_PAPERS}.")
    if not any(e.limitation for e in project.entries):
        problems.append("No limitations recorded, so the research gap is unsupported.")
    if not project.research_questions:
        problems.append("No research questions (run `plan --rq`).")
    if not project.method:
        problems.append("No methodology (run `plan --method`).")
    if not project.timeline:
        problems.append("No timeline (run `plan --phase 'Name:weeks'`).")
    return problems


def cite_keys(papers: list[Paper]) -> dict[str, str]:
    """Unique BibTeX keys: smith2023deep, smith2023deepb, ..."""
    keys: dict[str, str] = {}
    used: set[str] = set()
    for p in papers:
        surname = re.sub(r"[^a-z]", "", p.first_author_surname().lower()) or "anon"
        word = next((w for w in re.findall(r"[a-z]+", p.title.lower()) if len(w) > 3), "paper")
        base = f"{surname}{p.year or 'nd'}{word}"
        key, n = base, 1
        while key in used:
            n += 1
            key = f"{base}{chr(ord('a') + n - 1)}"
        used.add(key)
        keys[p.id] = key
    return keys


def _bib_escape(s: str) -> str:
    return s.replace("{", "\\{").replace("}", "\\}")


def to_bibtex(papers: list[Paper]) -> str:
    keys = cite_keys(papers)
    out = []
    for p in papers:
        kind = "article" if p.journal else "misc"
        fields = [("title", "{" + _bib_escape(p.title) + "}"), ("author", " and ".join(p.authors) or "Anonymous")]
        if p.year:
            fields.append(("year", str(p.year)))
        if p.journal:
            fields.append(("journal", p.journal))
        if p.doi:
            fields.append(("doi", p.doi))
        if p.url:
            fields.append(("url", p.url))
        body = ",\n".join(f"  {k} = {{{_bib_escape(v) if k != 'title' else v}}}" for k, v in fields)
        out.append(f"@{kind}{{{keys[p.id]},\n{body}\n}}")
    return "\n\n".join(out) + ("\n" if out else "")


def _reference(p: Paper) -> str:
    authors = ", ".join(p.authors[:6]) + (", et al." if len(p.authors) > 6 else "") or "Anonymous"
    venue = p.journal or p.source or "Preprint"
    link = f" https://doi.org/{p.doi}" if p.doi else (f" {p.url}" if p.url else "")
    return f"{authors} ({p.year or 'n.d.'}). {p.title}. *{venue}*.{link}"


def build_proposal(project: Project) -> str:
    todo = "_TODO: {}_"
    topic = project.chosen_topic or todo.format("choose a topic")
    out = [f"# Research Proposal: {topic}", "", f"_Draft generated from project '{project.name}'. "
           "Every sentence below must be checked and rewritten by the student._", ""]

    out += ["## 1. Introduction and motivation", ""]
    if project.interest:
        out.append(f"This proposal grows out of an interest in {project.interest}.")
    out += [todo.format("explain why this problem matters and who benefits"), ""]

    out += ["## 2. Background and related work", ""]
    themes = group_by_theme(project)
    if not themes:
        out += [todo.format("add papers with `search` and `add`"), ""]
    for theme, entries in themes.items():
        out.append(f"### 2.{list(themes).index(theme) + 1} {theme.capitalize()}")
        noted = [e for e in entries if e.finding]
        for e in noted:
            out.append(f"- {e.finding} {e.paper.citation()}")
        if len(noted) < len(entries):
            out.append(f"- {todo.format(f'{len(entries) - len(noted)} papers in this theme have no finding yet')}")
        out.append("")

    out += ["## 3. Research gap", ""]
    gaps = [e for e in project.entries if e.limitation]
    out += [f"- {e.limitation} {e.paper.citation()}" for e in gaps] or [todo.format("record limitations")]
    out += ["", todo.format("state in one sentence the gap this work fills"), ""]

    out += ["## 4. Research questions", ""]
    out += [f"RQ{i}. {q}" for i, q in enumerate(project.research_questions, 1)] or [todo.format("add research questions")]
    out += ["", "## 5. Methodology", "", project.method or todo.format("describe data, methods, and evaluation"), ""]

    out += ["## 6. Timeline", ""]
    if project.timeline:
        out += ["| Phase | Weeks | Ends week |", "|---|---|---|"]
        end = 0
        for ph in project.timeline:
            end += ph.weeks
            out.append(f"| {ph.name} | {ph.weeks} | {end} |")
        out.append(f"\nTotal: {end} weeks.")
    else:
        out.append(todo.format("add phases"))
    out += ["", "## 7. Expected contributions", "", todo.format("list the expected contributions"), ""]

    out += ["## References", ""]
    papers = sorted((e.paper for e in project.entries), key=lambda p: (p.first_author_surname().lower(), p.year or 0))
    out += [f"- {_reference(p)}" for p in papers] or [todo.format("no references yet")]
    return "\n".join(out) + "\n"
