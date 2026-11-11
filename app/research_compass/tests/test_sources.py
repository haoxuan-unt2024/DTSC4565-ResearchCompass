from types import SimpleNamespace

import pytest

from research_compass.sources import OfflineSource, PaperclipSource, SourceError, normalize


def test_normalize_paperclip_record():
    p = normalize({"document_id": "PMC1", "title": " T ", "authors": "Smith J; Jones K",
                   "pub_date": "2024-03-01", "doi": "10.1/x", "abstract_snippet": "abs"})
    assert (p.id, p.title, p.year, p.authors, p.abstract) == ("PMC1", "T", 2024, ["Smith J", "Jones K"], "abs")
    assert p.url == "https://doi.org/10.1/x" and p.first_author_surname() == "Smith"


@pytest.mark.parametrize("raw,year", [({"pub_year": 2021}, 2021), ({"month_year": "May 2019"}, 2019), ({}, None)])
def test_normalize_year_variants(raw, year):
    assert normalize({"id": "a", "title": "t", **raw}).year == year


def test_normalize_rejects_missing_title():
    with pytest.raises(ValueError):
        normalize({"id": "a"})


class FakeClient:
    def __init__(self, papers=None, exc=None):
        self.papers, self.exc, self.calls = papers or [], exc, []

    def search(self, query, **kw):
        self.calls.append((query, kw))
        if self.exc:
            raise self.exc
        return SimpleNamespace(papers=self.papers, result_id="s_1")

    def map_(self, question, from_results, timeout):
        yield SimpleNamespace(total=2, completed=1)
        yield SimpleNamespace(output="answer text")


def test_paperclip_source_maps_results_and_skips_bad_records():
    client = FakeClient([{"id": "a", "title": "Good"}, {"id": "b"}])
    res = PaperclipSource(client=client, source="arxiv").search("q", limit=5, since="2y")
    assert [p.id for p in res.papers] == ["a"] and res.result_id == "s_1"
    assert client.calls[0][1]["source"] == "arxiv" and client.calls[0][1]["limit"] == 5


def test_paperclip_errors_become_friendly_source_errors():
    AuthError = type("AuthError", (Exception,), {})
    with pytest.raises(SourceError, match="paperclip login"):
        PaperclipSource(client=FakeClient(exc=AuthError("401"))).search("q")


def test_paperclip_ask_returns_final_output():
    assert PaperclipSource(client=FakeClient()).ask("q?", "s_1") == "answer text"


def test_paperclip_ask_needs_result_id():
    with pytest.raises(SourceError):
        PaperclipSource(client=FakeClient()).ask("q?", "")


def test_offline_source_is_deterministic():
    src = OfflineSource()
    a = src.search("federated learning medical imaging", limit=50)
    assert len(a.papers) >= 10 and a.papers == src.search("federated learning medical imaging", limit=50).papers
    assert OfflineSource().search("zzz qqq").papers == []
    with pytest.raises(SourceError):
        src.ask("q", "offline")
