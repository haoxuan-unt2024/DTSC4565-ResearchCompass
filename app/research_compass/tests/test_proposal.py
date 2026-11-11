import pytest

from research_compass import proposal
from tests.conftest import make_paper


@pytest.mark.parametrize("text,name,weeks", [("Lit review:4", "Lit review", 4), ("Phase: 2 :3", "Phase: 2", 3)])
def test_parse_phase(text, name, weeks):
    ph = proposal.parse_phase(text)
    assert (ph.name, ph.weeks) == (name, weeks)


@pytest.mark.parametrize("bad", ["no colon", ":4", "x:0", "x:53", "x:two"])
def test_parse_phase_rejects(bad):
    with pytest.raises(ValueError):
        proposal.parse_phase(bad)


def test_readiness_empty_project_lists_everything(project):
    assert len(proposal.readiness(project)) == 6


def test_readiness_full_project_ok(full_project):
    assert proposal.readiness(full_project) == []


def test_proposal_has_all_sections_and_citations(full_project):
    text = proposal.build_proposal(full_project)
    for h in ["## 1.", "## 2.", "## 3. Research gap", "## 4.", "## 5.", "## 6. Timeline", "## 7.", "## References"]:
        assert h in text
    assert "(Garcia, 2025)" in text and "RQ1." in text and "Total: 12 weeks." in text


def test_proposal_marks_missing_parts_todo(project):
    text = proposal.build_proposal(project)
    assert "_TODO: choose a topic_" in text and "_TODO: add research questions_" in text


def test_citation_styles():
    assert make_paper(authors=["Maria Garcia"]).citation() == "(Garcia, 2025)"
    assert make_paper(authors=["Maria Garcia", "Wei Zhang"]).citation() == "(Garcia & Zhang, 2025)"
    assert make_paper(authors=["Garcia M", "Zhang W", "Kim D"]).citation() == "(Garcia et al., 2025)"
    assert make_paper(authors=[], year=None).citation() == "(Anon, n.d.)"


def test_cite_keys_are_unique():
    papers = [make_paper(i, title="Federated imaging") for i in range(3)]
    keys = list(proposal.cite_keys(papers).values())
    assert keys == ["garcia2025federated", "garcia2025federatedb", "garcia2025federatedc"]


def test_bibtex_entry():
    p = make_paper(1, doi="10.1/abc", title="Deep {nets}")
    bib = proposal.to_bibtex([p])
    assert bib.startswith("@misc{garcia2025deep,") and "doi = {10.1/abc}" in bib and "\\{nets\\}" in bib
