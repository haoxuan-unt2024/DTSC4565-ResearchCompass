import pytest

from research_compass.models import Paper, Project, SurveyEntry


def make_paper(i=1, year=2025, title=None, abstract="", doi="", authors=None):
    return Paper(id=f"p{i}", title=title or f"Paper number {i} on federated imaging", authors=["Maria Garcia"] if authors is None else authors,
                 year=year, doi=doi, abstract=abstract)


@pytest.fixture
def paper():
    return make_paper


@pytest.fixture
def project():
    return Project(name="demo", interest="privacy in medical AI")


@pytest.fixture
def full_project():
    """A project that satisfies every readiness rule."""
    pr = Project(name="demo", chosen_topic="federated learning medical imaging")
    for i in range(1, 6):
        pr.entries.append(SurveyEntry(make_paper(i), theme="privacy", finding=f"Finding {i}.",
                                      limitation="Small sites underserved." if i == 1 else "", relevance=4))
    pr.research_questions = ["How can small sites benefit?"]
    pr.method = "Simulate five sites."
    from research_compass.models import Phase
    pr.timeline = [Phase("Review", 4), Phase("Experiments", 8)]
    return pr
