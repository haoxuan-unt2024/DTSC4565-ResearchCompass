"""Save and load a project as one JSON file (human-readable, easy to version in git)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import Paper, Phase, Project, SurveyEntry, TopicCandidate

SCHEMA_VERSION = 1


class StorageError(Exception):
    pass


def to_dict(project: Project) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "name": project.name,
        "interest": project.interest,
        "chosen_topic": project.chosen_topic,
        "candidates": [c.to_dict() for c in project.candidates],
        "entries": [e.to_dict() for e in project.entries],
        "research_questions": project.research_questions,
        "method": project.method,
        "timeline": [{"name": p.name, "weeks": p.weeks} for p in project.timeline],
        "last_search": [p.to_dict() for p in project.last_search],
        "last_result_id": project.last_result_id,
    }


def from_dict(d: dict) -> Project:
    version = d.get("schema_version")
    if version != SCHEMA_VERSION:
        raise StorageError(f"Unsupported project file version {version!r} (expected {SCHEMA_VERSION}).")
    try:
        return Project(
            name=d["name"],
            interest=d.get("interest", ""),
            chosen_topic=d.get("chosen_topic", ""),
            candidates=[TopicCandidate.from_dict(c) for c in d.get("candidates", [])],
            entries=[SurveyEntry.from_dict(e) for e in d.get("entries", [])],
            research_questions=list(d.get("research_questions", [])),
            method=d.get("method", ""),
            timeline=[Phase(p["name"], int(p["weeks"])) for p in d.get("timeline", [])],
            last_search=[Paper.from_dict(p) for p in d.get("last_search", [])],
            last_result_id=d.get("last_result_id", ""),
        )
    except (KeyError, TypeError, ValueError) as e:
        raise StorageError(f"Project file is damaged: {e}") from e


def save(project: Project, path: Path) -> None:
    """Write to a temp file then rename, so a crash never leaves a half-written project."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(to_dict(project), indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def load(path: Path) -> Project:
    path = Path(path)
    if not path.exists():
        raise StorageError(f"No project at {path}. Create one with `init`.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise StorageError(f"{path} is not valid JSON: {e}") from e
    return from_dict(data)
