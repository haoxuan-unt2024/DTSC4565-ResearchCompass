"""Domain data classes. No I/O here, so everything is easy to unit-test."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

_INITIALS = re.compile(r"^[A-Z]{1,3}\.?$")


@dataclass
class Paper:
    id: str
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    source: str = ""
    doi: str = ""
    journal: str = ""
    abstract: str = ""
    url: str = ""

    def first_author_surname(self) -> str:
        if not self.authors:
            return "Anon"
        parts = self.authors[0].replace(",", " ").split()
        if not parts:
            return "Anon"
        # "Smith J" / "Smith JK" style: surname comes first.
        if len(parts) > 1 and _INITIALS.match(parts[-1]):
            return parts[0]
        return parts[-1]

    def citation(self) -> str:
        """In-text citation, author-year style: (Smith et al., 2023)."""
        name = self.first_author_surname()
        if len(self.authors) == 2:
            second = Paper(id="", title="", authors=self.authors[1:]).first_author_surname()
            name = f"{name} & {second}"
        elif len(self.authors) > 2:
            name = f"{name} et al."
        return f"({name}, {self.year or 'n.d.'})"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Paper":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})


@dataclass
class SurveyEntry:
    """One paper in the literature survey plus the student's reading notes."""

    paper: Paper
    theme: str = ""
    method: str = ""
    finding: str = ""
    limitation: str = ""
    relevance: int = 0  # 0 = not rated, else 1..5

    def is_complete(self) -> bool:
        return bool(self.theme and self.finding and self.relevance)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["paper"] = self.paper.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "SurveyEntry":
        rest = {k: d[k] for k in cls.__dataclass_fields__ if k in d and k != "paper"}
        return cls(paper=Paper.from_dict(d["paper"]), **rest)


@dataclass
class TopicCandidate:
    query: str
    hits: int
    recent_share: float
    review_share: float
    gap_share: float
    score: float
    verdict: str
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TopicCandidate":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})


@dataclass
class Phase:
    name: str
    weeks: int


@dataclass
class Project:
    name: str
    interest: str = ""
    chosen_topic: str = ""
    candidates: list[TopicCandidate] = field(default_factory=list)
    entries: list[SurveyEntry] = field(default_factory=list)
    research_questions: list[str] = field(default_factory=list)
    method: str = ""
    timeline: list[Phase] = field(default_factory=list)
    last_search: list[Paper] = field(default_factory=list)
    last_result_id: str = ""

    def find_entry(self, paper_id: str) -> SurveyEntry:
        for e in self.entries:
            if e.paper.id == paper_id:
                return e
        raise KeyError(f"No paper with id '{paper_id}' in the survey. Run `list` to see ids.")
