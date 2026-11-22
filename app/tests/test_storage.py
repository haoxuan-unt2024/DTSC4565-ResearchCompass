import json

import pytest

from research_compass import storage


def test_round_trip(tmp_path, full_project):
    path = tmp_path / "p.json"
    storage.save(full_project, path)
    assert storage.load(path) == full_project
    assert not (tmp_path / "p.json.tmp").exists()


def test_missing_file(tmp_path):
    with pytest.raises(storage.StorageError, match="init"):
        storage.load(tmp_path / "none.json")


def test_corrupt_json(tmp_path):
    path = tmp_path / "p.json"
    path.write_text("{not json")
    with pytest.raises(storage.StorageError, match="not valid JSON"):
        storage.load(path)


def test_wrong_version(tmp_path):
    path = tmp_path / "p.json"
    path.write_text(json.dumps({"schema_version": 99, "name": "x"}))
    with pytest.raises(storage.StorageError, match="version"):
        storage.load(path)


def test_damaged_entry(tmp_path):
    path = tmp_path / "p.json"
    path.write_text(json.dumps({"schema_version": 1, "name": "x", "entries": [{"no_paper": 1}]}))
    with pytest.raises(storage.StorageError, match="damaged"):
        storage.load(path)


# --- Data protection (added after brief feedback, Full Spec R9/R18-R20) ---

def test_save_keeps_previous_version_as_backup(tmp_path, project):
    path = tmp_path / "p.json"
    storage.save(project, path)
    first = path.read_text()
    project.interest = "changed"
    storage.save(project, path)
    assert storage.backup_path(path).read_text() == first
    assert storage.load(path).interest == "changed"


def test_failed_save_leaves_project_unchanged(tmp_path, project, monkeypatch):
    path = tmp_path / "p.json"
    storage.save(project, path)
    before = path.read_bytes()

    def broken_replace(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(storage.os, "replace", broken_replace)
    project.interest = "lost"
    with pytest.raises(storage.StorageError, match="not changed"):
        storage.save(project, path)
    assert path.read_bytes() == before
    assert not (tmp_path / "p.json.tmp").exists()


def _write(path, **extra):
    data = {"schema_version": 1, "name": "x"}
    data.update(extra)
    path.write_text(json.dumps(data))


def _entry(pid, relevance=0):
    return {"paper": {"id": pid, "title": f"T {pid}"}, "relevance": relevance}


def test_duplicate_paper_in_file_is_rejected(tmp_path):
    path = tmp_path / "p.json"
    _write(path, entries=[_entry("a"), _entry("a")])
    with pytest.raises(storage.StorageError, match="appears twice"):
        storage.load(path)


@pytest.mark.parametrize("bad", [7, -1, "high"])
def test_bad_relevance_in_file_is_rejected(tmp_path, bad):
    path = tmp_path / "p.json"
    _write(path, entries=[_entry("a", relevance=bad)])
    with pytest.raises(storage.StorageError, match="relevance"):
        storage.load(path)


def test_zero_week_phase_in_file_is_rejected(tmp_path):
    path = tmp_path / "p.json"
    _write(path, timeline=[{"name": "Review", "weeks": 0}])
    with pytest.raises(storage.StorageError, match="0 weeks"):
        storage.load(path)


def test_top_level_must_be_an_object(tmp_path):
    path = tmp_path / "p.json"
    path.write_text("[1, 2]")
    with pytest.raises(storage.StorageError, match="damaged"):
        storage.load(path)


def test_load_error_points_to_backup(tmp_path, project):
    path = tmp_path / "p.json"
    storage.save(project, path)
    storage.save(project, path)          # creates p.json.bak
    path.write_text("{oops")
    with pytest.raises(storage.StorageError, match="restore"):
        storage.load(path)


def test_restore_swaps_file_and_backup(tmp_path, project):
    path = tmp_path / "p.json"
    storage.save(project, path)
    project.interest = "second"
    storage.save(project, path)
    assert storage.restore(path).interest == "privacy in medical AI"
    assert storage.restore(path).interest == "second"     # running it again undoes the restore


def test_restore_refuses_damaged_backup(tmp_path, project):
    path = tmp_path / "p.json"
    storage.save(project, path)
    before = path.read_bytes()
    storage.backup_path(path).write_text("{oops")
    with pytest.raises(storage.StorageError, match="not valid JSON"):
        storage.restore(path)
    assert path.read_bytes() == before


def test_restore_without_backup(tmp_path, project):
    path = tmp_path / "p.json"
    storage.save(project, path)
    with pytest.raises(storage.StorageError, match="No backup"):
        storage.restore(path)
