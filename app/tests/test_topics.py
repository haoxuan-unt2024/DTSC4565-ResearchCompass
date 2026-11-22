import pytest

from research_compass import topics
from tests.conftest import make_paper

NOW = 2026


def many(n, year=2026, abstract="This remains unclear.", title="Federated method {i}"):
    return [make_paper(i, year=year, abstract=abstract, title=title.format(i=i)) for i in range(n)]


def test_validate_queries_dedups_and_trims():
    assert topics.validate_queries(["  a  b ", "A B", "", "c"]) == ["a b", "c"]


@pytest.mark.parametrize("bad", [[], ["", "  "], [f"t{i}" for i in range(9)]])
def test_validate_queries_rejects(bad):
    with pytest.raises(ValueError):
        topics.validate_queries(bad)


def test_too_few_hits_is_too_narrow():
    c = topics.score_topic("x", many(3), NOW)
    assert c.verdict == "too narrow"


def test_many_reviews_is_saturated():
    papers = many(10, title="A survey of thing {i}")
    c = topics.score_topic("x", papers, NOW)
    assert c.review_share == 1.0 and c.verdict == "saturated"


def test_recent_gappy_topic_is_promising():
    c = topics.score_topic("x", many(40), NOW)
    assert c.recent_share == 1.0 and c.gap_share == 1.0 and c.verdict == "promising"
    assert c.score == pytest.approx(100.0)


def test_old_topic_scores_lower_than_recent():
    old = topics.score_topic("old", many(20, year=2015), NOW)
    new = topics.score_topic("new", many(20, year=2026), NOW)
    assert new.score > old.score


def test_recent_share_ignores_undated_papers():
    papers = many(5, year=2026) + many(5, year=None)
    assert topics.score_topic("x", papers, NOW).recent_share == 1.0


def test_rank_puts_too_narrow_last():
    ranked = topics.rank_topics({"narrow": many(2), "ok": many(10, year=2010, abstract="")}, NOW)
    assert [c.query for c in ranked] == ["ok", "narrow"]


def test_reasons_explain_score():
    c = topics.score_topic("x", many(10), NOW)
    assert any("10 papers" in r for r in c.reasons)


def test_suggest_narrower_finds_repeated_phrases():
    papers = [make_paper(i, title=t) for i, t in enumerate([
        "Client drift in federated imaging", "Correcting client drift for hospitals", "Unrelated title here"])]
    assert topics.suggest_narrower("federated", papers) == ["federated client drift"]


def test_suggest_narrower_excludes_query_words():
    papers = [make_paper(i, title="Federated learning study") for i in range(3)]
    assert topics.suggest_narrower("federated learning", papers) == []


def test_recent_window_boundary():
    # RECENT_YEARS = 2 means this year and last year count; two years ago does not.
    papers = [make_paper(1, year=NOW), make_paper(2, year=NOW - 1), make_paper(3, year=NOW - 2), make_paper(4, year=NOW - 3)]
    assert topics.score_topic("x", papers, NOW).recent_share == 0.5


# --- Missing metadata and weight sensitivity (added after brief feedback, Full Spec R11/R12) ---

def test_missing_abstract_is_not_counted_as_no_gap():
    papers = many(5) + many(5, abstract="")
    c = topics.score_topic("x", papers, NOW)
    assert c.gap_share == 1.0
    assert any("5 have no abstract" in r for r in c.reasons)


@pytest.mark.parametrize("undated, expected", [(5, False), (6, True)])
def test_low_confidence_when_most_papers_lack_metadata(undated, expected):
    papers = many(10 - undated) + many(undated, year=None)
    c = topics.score_topic("x", papers, NOW)
    assert c.low_confidence is expected
    assert any("Low confidence" in r for r in c.reasons) is expected


def test_complete_metadata_adds_no_data_warning():
    assert len(topics.score_topic("x", many(10), NOW).reasons) == 4


def test_alternative_weights_each_sum_to_one():
    alts = topics.alternative_weights()
    assert len(alts) == 5
    for w in alts.values():
        assert sum(w.values()) == pytest.approx(1.0)


def test_weight_sensitivity_counts_weightings_that_agree():
    # "alpha" wins on recency; "beta" wins on stated gaps. Dropping recency flips the winner.
    results = {"alpha": many(40, year=2026, abstract="Plain."), "beta": many(40, year=2015)}
    assert topics.rank_topics(results, NOW)[0].query == "alpha"
    assert topics.weight_sensitivity(results, NOW) == (4, 5)


def test_weight_sensitivity_dominant_topic_is_stable():
    results = {"strong": many(40), "weak": many(10, year=2012, abstract="Plain.")}
    assert topics.weight_sensitivity(results, NOW) == (5, 5)
