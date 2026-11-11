"""Command-line interface (presentation layer). All logic lives in the other modules."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from . import proposal, storage, survey, topics
from .models import Project
from .sources import OfflineSource, PaperclipSource, SourceError

DEFAULT_PROJECT = "project.json"


def _source(args):
    return OfflineSource() if args.offline else PaperclipSource(source=args.corpus)


def _write_or_print(text: str, out: str | None) -> None:
    if out:
        Path(out).write_text(text, encoding="utf-8")
        print(f"Wrote {out}")
    else:
        print(text)


def _parse_picks(picks: list[str], n: int) -> list[int]:
    if picks == ["all"]:
        return list(range(n))
    chosen = []
    for raw in picks:
        for part in raw.split(","):
            if not part.strip():
                continue
            if not part.strip().isdigit() or not 1 <= int(part) <= n:
                raise ValueError(f"'{part}' is not a result number between 1 and {n}.")
            chosen.append(int(part) - 1)
    return sorted(set(chosen))


# ---- commands -------------------------------------------------------------------------------

def cmd_init(args, _now):
    path = Path(args.project)
    if path.exists() and not args.force:
        raise ValueError(f"{path} already exists. Use --force to overwrite.")
    storage.save(Project(name=args.name, interest=args.interest or ""), path)
    print(f"Created {path}. Next: compare topics with `topics \"idea one\" \"idea two\"`.")


def cmd_topics(args, now):
    project = storage.load(args.project)
    queries = topics.validate_queries(args.queries)
    src = _source(args)
    results = {q: src.search(q, limit=args.limit, since=args.since).papers for q in queries}
    ranked = topics.rank_topics(results, now.year)
    project.candidates = ranked
    storage.save(project, args.project)

    print(f"{'Score':>5}  {'Verdict':<11} Topic")
    for c in ranked:
        print(f"{c.score:>5.1f}  {c.verdict:<11} {c.query}")
        for r in c.reasons:
            print(f"{'':18}- {r}")
    best = ranked[0]
    ideas = topics.suggest_narrower(best.query, results[best.query])
    if ideas:
        print(f"\nNarrower angles on '{best.query}' (frequent title phrases):")
        for idea in ideas:
            print(f"  - {idea}")
    print("\nScores are a starting point. Discuss them with your advisor, then run `choose \"<topic>\"`.")


def cmd_choose(args, _now):
    project = storage.load(args.project)
    topic = " ".join(args.topic.split())
    if not topic:
        raise ValueError("Topic cannot be empty.")
    known = {c.query.lower() for c in project.candidates}
    project.chosen_topic = topic
    storage.save(project, args.project)
    print(f"Chosen topic: {topic}")
    if topic.lower() not in known:
        print("Note: this topic was not scored. Consider running `topics` on it first.")


def cmd_search(args, _now):
    project = storage.load(args.project)
    query = args.query or project.chosen_topic
    if not query:
        raise ValueError("Give a query, or choose a topic first.")
    result = _source(args).search(query, limit=args.limit, since=args.since)
    project.last_search = result.papers
    project.last_result_id = result.result_id
    storage.save(project, args.project)
    if not result.papers:
        print("No results. Try broader wording.")
        return
    in_survey = {e.paper.id for e in project.entries}
    for i, p in enumerate(result.papers, 1):
        mark = "*" if p.id in in_survey else " "
        print(f"{mark}{i:>3}. {p.title}\n       {p.citation()} · {p.id} · {p.source or 'unknown source'}")
    print("\n* = already in your survey. Add with `add 1 3 5` or `add all`.")


def cmd_add(args, _now):
    project = storage.load(args.project)
    if not project.last_search:
        raise ValueError("Nothing to add. Run `search` first.")
    idx = _parse_picks(args.picks, len(project.last_search))
    added, skipped = survey.add_papers(project, [project.last_search[i] for i in idx])
    storage.save(project, args.project)
    print(f"Added {added} paper(s); skipped {skipped} duplicate(s). Survey now has {len(project.entries)}.")


def cmd_remove(args, _now):
    project = storage.load(args.project)
    survey.remove_paper(project, args.paper_id)
    storage.save(project, args.project)
    print(f"Removed {args.paper_id}.")


def cmd_note(args, _now):
    project = storage.load(args.project)
    e = survey.update_note(project, args.paper_id, relevance=args.relevance, theme=args.theme,
                           method=args.method, finding=args.finding, limitation=args.limitation)
    storage.save(project, args.project)
    status = "complete" if e.is_complete() else "needs theme, finding and relevance"
    print(f"Updated notes for {e.paper.citation()} ({status}).")


def cmd_list(args, _now):
    project = storage.load(args.project)
    if not project.entries:
        print("Survey is empty. Use `search` then `add`.")
        return
    for e in project.entries:
        flag = "✓" if e.is_complete() else "·"
        print(f"{flag} {e.paper.id:<22} {e.paper.citation():<26} [{e.theme or 'no theme'}] {e.paper.title[:60]}")


def cmd_matrix(args, _now):
    _write_or_print(survey.literature_matrix(storage.load(args.project)), args.out)


def cmd_outline(args, _now):
    _write_or_print(survey.outline(storage.load(args.project)), args.out)


def cmd_check(args, now):
    project = storage.load(args.project)
    warnings = survey.coverage_report(project, now.year) + proposal.readiness(project)
    if not warnings:
        print("No problems found. Still: read every generated sentence before submitting.")
    for w in warnings:
        print(f"- {w}")


def cmd_plan(args, _now):
    project = storage.load(args.project)
    if args.clear_rq:
        project.research_questions = []
    if args.rq:
        project.research_questions += [" ".join(q.split()) for q in args.rq if q.strip()]
    if args.method:
        project.method = args.method.strip()
    if args.phase:
        project.timeline = [proposal.parse_phase(p) for p in args.phase]
    storage.save(project, args.project)
    print(f"{len(project.research_questions)} research question(s); "
          f"method {'set' if project.method else 'missing'}; {len(project.timeline)} timeline phase(s).")


def cmd_proposal(args, _now):
    project = storage.load(args.project)
    for p in proposal.readiness(project):
        print(f"warning: {p}", file=sys.stderr)
    _write_or_print(proposal.build_proposal(project), args.out)


def cmd_bib(args, _now):
    project = storage.load(args.project)
    _write_or_print(proposal.to_bibtex([e.paper for e in project.entries]), args.out)


def cmd_ask(args, now):
    project = storage.load(args.project)
    text = _source(args).ask(args.question, project.last_result_id)
    out = Path(args.out or f"ai_draft_{now:%Y%m%d_%H%M%S}.md")
    out.write_text(f"# AI DRAFT (unverified): {args.question}\n\n"
                   "_Generated by Paperclip `map`. Check every claim against the paper before using it._\n\n"
                   + text, encoding="utf-8")
    print(f"Saved AI draft to {out}. Copy verified points into your notes with `note`.")


# ---- parser ---------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="research-compass", description=__doc__)
    p.add_argument("--project", default=DEFAULT_PROJECT, help="project file (default: project.json)")
    p.add_argument("--offline", action="store_true", help="use bundled sample papers instead of Paperclip")
    p.add_argument("--corpus", default=None, help="Paperclip source filter, e.g. arxiv, pmc, biorxiv")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="create a project")
    s.add_argument("name"); s.add_argument("--interest"); s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("topics", help="compare candidate topics")
    s.add_argument("queries", nargs="+"); s.add_argument("--limit", type=int, default=40)
    s.add_argument("--since", help="e.g. 5y"); s.set_defaults(fn=cmd_topics)

    s = sub.add_parser("choose", help="set the chosen topic"); s.add_argument("topic"); s.set_defaults(fn=cmd_choose)

    s = sub.add_parser("search", help="search papers (defaults to chosen topic)")
    s.add_argument("query", nargs="?"); s.add_argument("--limit", type=int, default=20)
    s.add_argument("--since"); s.set_defaults(fn=cmd_search)

    s = sub.add_parser("add", help="add results from the last search"); s.add_argument("picks", nargs="+")
    s.set_defaults(fn=cmd_add)
    s = sub.add_parser("remove", help="remove a paper"); s.add_argument("paper_id"); s.set_defaults(fn=cmd_remove)

    s = sub.add_parser("note", help="record reading notes for a paper")
    s.add_argument("paper_id")
    for f in survey.NOTE_FIELDS:
        s.add_argument(f"--{f}")
    s.add_argument("--relevance", type=int); s.set_defaults(fn=cmd_note)

    sub.add_parser("list", help="list surveyed papers").set_defaults(fn=cmd_list)
    for name, fn in (("matrix", cmd_matrix), ("outline", cmd_outline), ("proposal", cmd_proposal), ("bib", cmd_bib)):
        s = sub.add_parser(name, help=f"export the {name}"); s.add_argument("-o", "--out"); s.set_defaults(fn=fn)
    sub.add_parser("check", help="survey coverage and proposal readiness").set_defaults(fn=cmd_check)

    s = sub.add_parser("plan", help="research questions, method, timeline")
    s.add_argument("--rq", action="append"); s.add_argument("--clear-rq", action="store_true")
    s.add_argument("--method"); s.add_argument("--phase", action="append", help="'Name:weeks', repeatable")
    s.set_defaults(fn=cmd_plan)

    s = sub.add_parser("ask", help="AI reader over the last search (Paperclip map); saves a draft")
    s.add_argument("question"); s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_ask)
    return p


def main(argv: list[str] | None = None, now: dt.datetime | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.fn(args, now or dt.datetime.now())
    except (ValueError, KeyError, SourceError, storage.StorageError) as e:
        msg = e.args[0] if isinstance(e, KeyError) and e.args else str(e)
        print(f"error: {msg}", file=sys.stderr)
        return 1
    return 0
