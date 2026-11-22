"""Topic finding: score candidate topics from search results, with reasons a student can check.

The score is a heuristic, not a verdict. It rewards topics that are active (recent papers),
have stated open problems (gap phrases in abstracts), have enough literature to survey, and
are not already saturated by review articles.
"""

from __future__ import annotations

import re
from collections import Counter

from .models import Paper, TopicCandidate

MAX_CANDIDATES = 8
MIN_HITS = 5            # fewer results than this: too little literature for a thesis survey
ENOUGH_HITS = 40        # beyond this, more hits do not raise the score
RECENT_YEARS = 2        # "recent" = published in the last 2 years (inclusive of this year)
SATURATED_REVIEWS = 0.4

# Weights are a judgement call, not a fitted model (see docs/FULL_SPEC.md, "Scoring method").
# `weight_sensitivity` reports whether the top topic survives other reasonable weightings.
WEIGHTS = {"recent": 0.35, "gap": 0.30, "volume": 0.20, "unsaturated": 0.15}
LOW_DATA_SHARE = 0.5    # if more than half the papers lack a year or an abstract, flag low confidence

GAP_PHRASES = (
    "remains unclear", "remain unclear", "remains unknown", "poorly understood", "little is known",
    "open question", "open problem", "future work", "future research", "further research",
    "limitation", "challenge", "gap", "not yet", "understudied", "under-explored", "unexplored",
)
_REVIEW = re.compile(r"\b(review|survey|meta-analysis|overview|systematic)\b", re.I)
_STOP = set(
    "a an the of for and or in on to with by from via using based towards toward its their is are "
    "as at be new study analysis approach approaches method methods model models data".split()
)


def validate_queries(queries: list[str]) -> list[str]:
    cleaned, seen = [], set()
    for q in queries:
        q = " ".join(q.split())
        if not q:
            continue
        if q.lower() in seen:
            continue
        seen.add(q.lower())
        cleaned.append(q)
    if not cleaned:
        raise ValueError("Give at least one candidate topic.")
    if len(cleaned) > MAX_CANDIDATES:
        raise ValueError(f"Compare at most {MAX_CANDIDATES} topics at once (got {len(cleaned)}).")
    return cleaned


def _share(papers: list[Paper], pred) -> float:
    return round(sum(1 for p in papers if pred(p)) / len(papers), 2) if papers else 0.0


def has_gap_signal(paper: Paper) -> bool:
    text = paper.abstract.lower()
    return any(phrase in text for phrase in GAP_PHRASES)


def score_topic(query: str, papers: list[Paper], now_year: int, weights: dict[str, float] = WEIGHTS) -> TopicCandidate:
    hits = len(papers)
    # Missing metadata is left out of the share rather than counted as "no": a paper with no
    # abstract is not evidence that the topic has no open problems.
    dated = [p for p in papers if p.year]
    with_abstract = [p for p in papers if p.abstract.strip()]
    recent = _share(dated, lambda p: p.year >= now_year - RECENT_YEARS + 1)
    reviews = _share(papers, lambda p: bool(_REVIEW.search(p.title)))
    gaps = _share(with_abstract, has_gap_signal)
    volume = min(hits, ENOUGH_HITS) / ENOUGH_HITS
    unsaturated = 1 - min(reviews / SATURATED_REVIEWS, 1.0)

    score = 100 * (
        weights["recent"] * recent
        + weights["gap"] * gaps
        + weights["volume"] * volume
        + weights["unsaturated"] * unsaturated
    )
    reasons = [
        f"{hits} papers found",
        f"{recent:.0%} of dated papers are from the last {RECENT_YEARS} years",
        f"{gaps:.0%} of abstracts mention a limitation or open problem",
        f"{reviews:.0%} of titles are reviews/surveys",
    ]
    no_year, no_abstract = hits - len(dated), hits - len(with_abstract)
    low_confidence = bool(hits) and max(no_year, no_abstract) / hits > LOW_DATA_SHARE
    if no_year or no_abstract:
        reasons.append(f"{no_year} of {hits} papers have no year and {no_abstract} have no abstract; "
                       "those shares use only the papers that do")
    if low_confidence:
        reasons.append("Low confidence: over half the papers lack a year or an abstract.")
    if hits < MIN_HITS:
        verdict = "too narrow"
        reasons.append("Too little literature: broaden the wording or the field.")
    elif reviews >= SATURATED_REVIEWS:
        verdict = "saturated"
        reasons.append("Many reviews already exist: narrow to a sub-problem (see suggestions).")
    elif score >= 60:
        verdict = "promising"
    elif score >= 40:
        verdict = "possible"
    else:
        verdict = "weak"
    return TopicCandidate(query, hits, recent, reviews, gaps, round(score, 1), verdict, reasons, low_confidence)


def rank_topics(results: dict[str, list[Paper]], now_year: int,
                weights: dict[str, float] = WEIGHTS) -> list[TopicCandidate]:
    scored = [score_topic(q, papers, now_year, weights) for q, papers in results.items()]
    # Topics flagged too narrow sort last regardless of score.
    return sorted(scored, key=lambda c: (c.verdict == "too narrow", -c.score, c.query.lower()))


def alternative_weights() -> dict[str, dict[str, float]]:
    """Equal weights, plus each indicator dropped in turn (the rest rescaled to sum to 1)."""
    alts = {"equal weights": {k: 1 / len(WEIGHTS) for k in WEIGHTS}}
    for dropped in WEIGHTS:
        rest = sum(w for k, w in WEIGHTS.items() if k != dropped)
        alts[f"without {dropped}"] = {k: (0.0 if k == dropped else w / rest) for k, w in WEIGHTS.items()}
    return alts


def weight_sensitivity(results: dict[str, list[Paper]], now_year: int) -> tuple[int, int]:
    """How many alternative weightings keep the same topic in first place: (agreeing, total)."""
    top = rank_topics(results, now_year)[0].query
    alts = alternative_weights()
    agree = sum(1 for w in alts.values() if rank_topics(results, now_year, w)[0].query == top)
    return agree, len(alts)


def suggest_narrower(base_query: str, papers: list[Paper], k: int = 5) -> list[str]:
    """Frequent two-word phrases in titles that are not already in the query."""
    base = set(re.findall(r"[a-z0-9]+", base_query.lower()))
    counts: Counter[str] = Counter()
    for p in papers:
        words = [w for w in re.findall(r"[a-z0-9-]+", p.title.lower()) if w not in _STOP and len(w) > 2]
        bigrams = {f"{a} {b}" for a, b in zip(words, words[1:]) if a not in base and b not in base}
        counts.update(bigrams)  # a set per title: one vote per paper
    phrases = [phrase for phrase, n in counts.most_common() if n >= 2]
    return [f"{base_query} {phrase}" for phrase in phrases[:k]]
