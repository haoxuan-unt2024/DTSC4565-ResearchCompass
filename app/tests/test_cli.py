"""System tests: drive the CLI end to end with the offline source (no network, no cost)."""

import datetime as dt

from research_compass import storage
from research_compass.cli import main

NOW = dt.datetime(2026, 11, 11)


def run(tmp_path, *args):
    return main(["--project", str(tmp_path / "p.json"), "--offline", *args], now=NOW)


def test_full_workflow(tmp_path, capsys):
    assert run(tmp_path, "init", "thesis", "--interest", "medical AI") == 0
    assert run(tmp_path, "topics", "federated learning medical imaging", "llm hallucination detection",
               "graph neural networks drug discovery") == 0
    out = capsys.readouterr().out
    assert out.index("federated learning medical imaging") < out.index("graph neural networks drug discovery")
    assert "saturated" in out  # the hallucination demo topic is review-heavy

    assert run(tmp_path, "choose", "federated learning medical imaging") == 0
    assert run(tmp_path, "search") == 0
    assert run(tmp_path, "add", "1,2", "3") == 0
    assert run(tmp_path, "add", "1") == 0
    assert "skipped 1 duplicate" in capsys.readouterr().out

    pid = storage.load(tmp_path / "p.json").entries[0].paper.id
    assert run(tmp_path, "note", pid, "--theme", "Privacy", "--finding", "It works.",
               "--limitation", "Small sites.", "--relevance", "4") == 0
    assert run(tmp_path, "plan", "--rq", "Does it help small sites?", "--method", "Simulation",
               "--phase", "Review:4", "--phase", "Experiments:8") == 0
    assert run(tmp_path, "proposal", "-o", str(tmp_path / "proposal.md")) == 0
    text = (tmp_path / "proposal.md").read_text()
    assert "RQ1. Does it help small sites?" in text and "It works." in text
    assert run(tmp_path, "bib", "-o", str(tmp_path / "refs.bib")) == 0
    assert (tmp_path / "refs.bib").read_text().count("@") == 3


def test_errors_return_1_and_do_not_change_project(tmp_path, capsys):
    run(tmp_path, "init", "t")
    before = (tmp_path / "p.json").read_text()
    assert run(tmp_path, "add", "1") == 1                       # nothing searched yet
    assert run(tmp_path, "note", "missing", "--theme", "x") == 1
    assert run(tmp_path, "plan", "--phase", "bad") == 1
    assert run(tmp_path, "init", "t") == 1                      # refuses to overwrite
    assert (tmp_path / "p.json").read_text() == before
    assert "error:" in capsys.readouterr().err


def test_add_rejects_out_of_range(tmp_path):
    run(tmp_path, "init", "t")
    run(tmp_path, "search", "federated learning")
    assert run(tmp_path, "add", "99") == 1
    assert storage.load(tmp_path / "p.json").entries == []


def test_ask_offline_fails_gracefully(tmp_path, capsys):
    run(tmp_path, "init", "t")
    assert run(tmp_path, "ask", "What methods?") == 1
    assert "not available in --offline" in capsys.readouterr().err


def test_topics_output_labels_scores_as_indicators(tmp_path, capsys):
    run(tmp_path, "init", "t")
    assert run(tmp_path, "topics", "federated learning medical imaging", "llm hallucination detection") == 0
    out = capsys.readouterr().out
    assert "do not judge research value" in out
    assert "alternative weightings" in out


def test_restore_undoes_the_last_change(tmp_path, capsys):
    run(tmp_path, "init", "t")
    run(tmp_path, "search", "federated learning")
    run(tmp_path, "add", "1")
    assert len(storage.load(tmp_path / "p.json").entries) == 1
    assert run(tmp_path, "restore") == 0
    assert storage.load(tmp_path / "p.json").entries == []


def test_unwritable_output_path_is_an_error_not_a_crash(tmp_path, capsys):
    run(tmp_path, "init", "t")
    assert run(tmp_path, "matrix", "-o", str(tmp_path / "no_such_dir" / "m.md")) == 1
    assert "error:" in capsys.readouterr().err
