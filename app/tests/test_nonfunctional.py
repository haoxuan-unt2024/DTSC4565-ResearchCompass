"""Tests for non-functional requirements (Full Spec R3, R29, R31, R32, R34)."""

import ast
import datetime as dt
import json
import sys
import time
import types
from pathlib import Path

from research_compass import proposal, storage, survey, topics
from research_compass.cli import main
from research_compass.models import Phase, Project, SurveyEntry
from tests.conftest import make_paper

PKG = Path(__file__).resolve().parents[1] / "research_compass"
NOW = dt.datetime(2026, 11, 11)


def run(tmp_path, *args, offline=True):
    flags = ["--offline"] if offline else []
    return main(["--project", str(tmp_path / "p.json"), *flags, *args], now=NOW)


def test_search_lists_numbered_results_and_marks_surveyed(tmp_path, capsys):   # R3
    run(tmp_path, "init", "t")
    run(tmp_path, "search", "federated learning")
    run(tmp_path, "add", "2")
    capsys.readouterr()
    run(tmp_path, "search", "federated learning")
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("   1. ")
    assert lines[2].startswith("*  2. ")                 # already in the survey
    assert "demo_" in lines[1] and "(" in lines[1]       # id and author-year citation


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            base = ("." * node.level) + (node.module or "")
            names.add(base)
            names |= {f"{base}.{a.name}" if node.module else base + a.name for a in node.names}
    return names


def test_logic_modules_do_not_import_the_cli():                                # R34
    for name in ("models", "topics", "survey", "proposal", "storage", "sources"):
        imported = _imports(PKG / f"{name}.py")
        assert not any(i.endswith("cli") for i in imported), name


def test_only_the_adapter_imports_the_paperclip_sdk():                         # R34
    for path in PKG.glob("*.py"):
        if path.name != "sources.py":
            assert "gxl_paperclip" not in _imports(path), path.name


def test_api_key_never_written_to_project_or_exports(tmp_path, monkeypatch):   # R31
    secret = "pk_test_DO_NOT_STORE_123"
    monkeypatch.setenv("PAPERCLIP_API_KEY", secret)
    run(tmp_path, "init", "t")
    run(tmp_path, "search", "federated learning")
    run(tmp_path, "add", "all")
    for cmd in ("matrix", "outline", "proposal", "bib"):
        run(tmp_path, cmd, "-o", str(tmp_path / f"{cmd}.out"))
    for f in tmp_path.iterdir():
        assert secret not in f.read_text(encoding="utf-8"), f.name


def test_missing_sdk_gives_install_hint_not_traceback(tmp_path, capsys, monkeypatch):  # R32
    monkeypatch.setitem(sys.modules, "gxl_paperclip", None)   # import fails
    run(tmp_path, "init", "t")
    assert run(tmp_path, "search", "anything", offline=False) == 1
    err = capsys.readouterr().err
    assert "pip install" in err and "--offline" in err and "Traceback" not in err


def test_not_signed_in_gives_login_hint(tmp_path, capsys, monkeypatch):        # R32
    class Client:
        @staticmethod
        def from_env():
            raise RuntimeError("no key")
    monkeypatch.setitem(sys.modules, "gxl_paperclip", types.SimpleNamespace(PaperclipClient=Client))
    run(tmp_path, "init", "t")
    before = (tmp_path / "p.json").read_bytes()
    assert run(tmp_path, "search", "anything", offline=False) == 1
    err = capsys.readouterr().err
    assert "paperclip login" in err and "--offline" in err
    assert (tmp_path / "p.json").read_bytes() == before


def test_200_paper_project_is_fast(tmp_path):                                  # R29
    pr = Project(name="perf", chosen_topic="t", research_questions=["q"], method="m", timeline=[Phase("a", 4)])
    for i in range(200):
        pr.entries.append(SurveyEntry(make_paper(i, year=2015 + i % 11, abstract="remains unclear", doi=f"10.1/{i}",
                                                 authors=["A B", "C D", "E F"]),
                                      theme=f"t{i % 8}", finding="f", limitation="l", relevance=3))
    path = tmp_path / "p.json"
    start = time.perf_counter()
    storage.save(pr, path)
    loaded = storage.load(path)
    survey.literature_matrix(loaded), survey.outline(loaded), survey.coverage_report(loaded, 2026)
    proposal.build_proposal(loaded), proposal.to_bibtex([e.paper for e in loaded.entries])
    results = {f"q{k}": [e.paper for e in loaded.entries] for k in range(8)}
    topics.rank_topics(results, 2026), topics.weight_sensitivity(results, 2026)
    assert time.perf_counter() - start < 2.0
    assert json.loads(path.read_text())["schema_version"] == storage.SCHEMA_VERSION
