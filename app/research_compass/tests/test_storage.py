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
