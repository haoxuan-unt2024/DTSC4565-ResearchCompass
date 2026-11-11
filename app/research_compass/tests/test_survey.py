import pytest

from research_compass import survey
from research_compass.models import SurveyEntry
from tests.conftest import make_paper


def test_add_skips_duplicates_by_id_doi_and_title(project):
    a = make_paper(1, doi="10.1/X")
    same_doi = make_paper(2, doi="10.1/x", title="Different title")
    same_title = make_paper(3, title=a.title.upper() + "!")
    added, skipped = survey.add_papers(project, [a, same_doi, same_title, a])
    assert (added, skipped) == (1, 3)


def test_update_note_sets_fields_and_lowercases_theme(project):
    survey.add_papers(project, [make_paper(1)])
    e = survey.update_note(project, "p1", relevance=5, theme="  Privacy  Attacks ", finding="X works.")
    assert e.theme == "privacy attacks" and e.relevance == 5 and e.is_complete()


@pytest.mark.parametrize("rel", [0, 6, -1])
def test_update_note_rejects_bad_relevance(project, rel):
    survey.add_papers(project, [make_paper(1)])
    with pytest.raises(ValueError):
        survey.update_note(project, "p1", relevance=rel)
    assert project.entries[0].relevance == 0


def test_update_note_unknown_paper(project):
    with pytest.raises(KeyError):
        survey.update_note(project, "nope", theme="x")


def test_update_note_none_leaves_field(project):
    survey.add_papers(project, [make_paper(1)])
    survey.update_note(project, "p1", method="CNN")
    survey.update_note(project, "p1", method=None, finding="F")
    assert project.entries[0].method == "CNN"


def test_matrix_escapes_pipes(project):
    project.entries.append(SurveyEntry(make_paper(1, title="A | B"), finding="x|y"))
    m = survey.literature_matrix(project)
    assert "A \\| B" in m and "x\\|y" in m
    assert m.count("\n") == 5  # title, blank, header, rule, one row


def test_outline_groups_by_theme_unsorted_last(project):
    project.entries += [SurveyEntry(make_paper(1)), SurveyEntry(make_paper(2), theme="privacy", finding="F2"),
                        SurveyEntry(make_paper(3), theme="privacy", limitation="Small n")]
    text = survey.outline(project)
    assert text.index("Privacy (2 paper(s))") < text.index("Unsorted (1 paper(s))")
    assert "TODO: add key finding" in text and "Small n" in text


def test_coverage_report_flags_problems(project):
    project.entries.append(SurveyEntry(make_paper(1, year=2015), theme="solo"))
    warnings = " ".join(survey.coverage_report(project, 2026))
    for expected in ["Only 1 paper(s)", "lack a theme", "single paper", "last 3 years", "No limitations"]:
        assert expected in warnings


def test_coverage_report_clean():
    from research_compass.models import Project
    pr = Project(name="x")
    for i in range(10):
        pr.entries.append(SurveyEntry(make_paper(i), theme="t", finding="f", limitation="l", relevance=3))
    assert survey.coverage_report(pr, 2026) == []
