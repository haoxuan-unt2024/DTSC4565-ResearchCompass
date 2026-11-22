"""Save and load a project as one JSON file (human-readable, easy to version in git)."""

from __future__ import annotations

import json
import os
import shutil
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


def backup_path(path: Path) -> Path:
    path = Path(path)
    return path.with_suffix(path.suffix + ".bak")


def _validate(project: Project) -> None:
    """Rules the rest of the app relies on. A file that breaks one was edited by hand or damaged."""
    seen: set[str] = set()
    for e in project.entries:
        if e.paper.id in seen:
            raise StorageError(f"Project file is damaged: paper '{e.paper.id}' appears twice in the survey.")
        seen.add(e.paper.id)
        if not isinstance(e.relevance, int) or not 0 <= e.relevance <= 5:
            raise StorageError(f"Project file is damaged: paper '{e.paper.id}' has relevance {e.relevance!r} (must be 0-5).")
    for ph in project.timeline:
        if ph.weeks < 1:
            raise StorageError(f"Project file is damaged: phase '{ph.name}' has {ph.weeks} weeks.")


def from_dict(d: dict) -> Project:
    if not isinstance(d, dict):
        raise StorageError("Project file is damaged: the top level is not a JSON object.")
    version = d.get("schema_version")
    if version != SCHEMA_VERSION:
        raise StorageError(f"Unsupported project file version {version!r} (expected {SCHEMA_VERSION}).")
    try:
        project = Project(
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
    except (KeyError, TypeError, ValueError, AttributeError) as e:
        raise StorageError(f"Project file is damaged: {e}") from e
    _validate(project)
    return project


def save(project: Project, path: Path) -> None:
    """Crash-safe save.

    1. Write the new version to `<file>.tmp` and flush it to disk.
    2. Copy the current file to `<file>.bak` (so the last change can be undone with `restore`).
    3. Atomically rename the temp file over the project file.
    If any step fails, the project file is left exactly as it was and the temp file is removed.
    """
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(to_dict(project), indent=2, ensure_ascii=False)
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        if path.exists():
            shutil.copy2(path, backup_path(path))
        os.replace(tmp, path)
    except OSError as e:
        tmp.unlink(missing_ok=True)
        raise StorageError(f"Could not save {path} ({e}). The project file was not changed.") from e


def _read(path: Path) -> Project:
    if not path.exists():
        raise StorageError(f"No project at {path}. Create one with `init`.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise StorageError(f"{path} is not valid JSON: {e}") from e
    except (OSError, UnicodeDecodeError) as e:
        raise StorageError(f"Cannot read {path}: {e}") from e
    return from_dict(data)


def load(path: Path) -> Project:
    path = Path(path)
    try:
        return _read(path)
    except StorageError as e:
        bak = backup_path(path)
        if path.exists() and bak.exists():
            raise StorageError(f"{e} A copy from before your last change is in {bak}; "
                               "run `restore` to go back to it.") from e
        raise


def restore(path: Path) -> Project:
    """Swap the project file with its backup. Running it twice gets the original back."""
    path = Path(path)
    bak = backup_path(path)
    if not bak.exists():
        raise StorageError(f"No backup at {bak}. A backup is made each time the project is saved.")
    project = _read(bak)  # refuse to restore a backup that is itself damaged
    save(project, path)   # the current file becomes the new backup
    return project
