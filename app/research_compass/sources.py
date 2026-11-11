"""Paper sources (Adapter + Strategy).

`PaperclipSource` adapts the Paperclip SDK (https://github.com/GXL-ai/paperclip) to the small
`PaperSource` interface the rest of the app uses. `OfflineSource` reads a bundled JSON file so
the app can be demoed and tested with no network, no account, and no cost.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from importlib import resources
from typing import Any, Protocol

from .models import Paper

_YEAR = re.compile(r"\b(19|20)\d{2}\b")


class SourceError(Exception):
    """A search failed. The message is safe to show to the user."""


@dataclass
class SearchResult:
    papers: list[Paper] = field(default_factory=list)
    result_id: str = ""


class PaperSource(Protocol):
    def search(self, query: str, limit: int = 20, since: str | None = None) -> SearchResult: ...


def _parse_year(raw: dict[str, Any]) -> int | None:
    for key in ("pub_year", "year", "pub_date", "month_year", "date"):
        value = raw.get(key)
        if value is None:
            continue
        m = _YEAR.search(str(value))
        if m:
            return int(m.group(0))
    return None


def _parse_authors(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(a).strip() for a in value if str(a).strip()]
    text = str(value)
    sep = ";" if ";" in text else ","
    return [a.strip() for a in text.split(sep) if a.strip()]


def normalize(raw: dict[str, Any]) -> Paper:
    """Turn one Paperclip hit (keys vary by source) into a Paper."""
    pid = str(raw.get("document_id") or raw.get("id") or raw.get("paper_id") or "").strip()
    title = str(raw.get("title") or "").strip()
    if not pid or not title:
        raise ValueError("paper record needs an id and a title")
    doi = str(raw.get("doi") or "").strip()
    url = str(raw.get("url") or "") or (f"https://doi.org/{doi}" if doi else "")
    return Paper(
        id=pid,
        title=title,
        authors=_parse_authors(raw.get("authors")),
        year=_parse_year(raw),
        source=str(raw.get("source") or ""),
        doi=doi,
        journal=str(raw.get("journal") or ""),
        abstract=str(raw.get("abstract") or raw.get("abstract_snippet") or ""),
        url=url,
    )


def _normalize_all(raws: list[dict[str, Any]]) -> list[Paper]:
    papers = []
    for raw in raws:
        try:
            papers.append(normalize(raw))
        except ValueError:
            continue  # skip malformed hits rather than failing the whole search
    return papers


class PaperclipSource:
    """Live search through the Paperclip SDK. Needs `paperclip login` or PAPERCLIP_API_KEY."""

    def __init__(self, client: Any = None, source: str | None = None, timeout: float = 60):
        self._client = client
        self._source = source  # e.g. "arxiv", "pmc"; None = Paperclip's default mix
        self._timeout = timeout

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from gxl_paperclip import PaperclipClient
            except ImportError as e:
                raise SourceError(
                    "Paperclip SDK is not installed. Run: pip install https://paperclip.gxl.ai/paperclip.whl"
                ) from e
            try:
                self._client = PaperclipClient.from_env()
            except Exception as e:  # SDK raises when no key and no saved login
                raise SourceError(
                    "Not signed in to Paperclip. Run `paperclip login` or set PAPERCLIP_API_KEY. "
                    "Use --offline to try the app with sample data."
                ) from e
        return self._client

    def search(self, query: str, limit: int = 20, since: str | None = None) -> SearchResult:
        client = self._get_client()
        try:
            result = client.search(query, limit=limit, since=since, source=self._source, timeout=self._timeout)
        except Exception as e:
            raise SourceError(_friendly(e)) from e
        return SearchResult(papers=_normalize_all(result.papers), result_id=result.result_id or "")

    def ask(self, question: str, result_id: str) -> str:
        """Run Paperclip's AI reader (`map`) over a saved search. Output is a DRAFT for the student to check."""
        if not result_id:
            raise SourceError("No saved search to read. Run `search` first.")
        client = self._get_client()
        try:
            final = ""
            for event in client.map_(question, from_results=result_id, timeout=300):
                if hasattr(event, "output"):
                    final = event.output
        except Exception as e:
            raise SourceError(_friendly(e)) from e
        if not final.strip():
            raise SourceError("Paperclip returned an empty answer.")
        return final


def _friendly(e: Exception) -> str:
    name = type(e).__name__
    hints = {
        "AuthError": "Paperclip sign-in failed or expired. Run `paperclip login`.",
        "RateLimitError": "Paperclip rate limit reached. Wait a minute and try again.",
        "RequestTimeoutError": "Paperclip took too long. Try a smaller --limit.",
        "NetworkError": "Cannot reach Paperclip. Check your connection or use --offline.",
        "ServerError": "Paperclip had a server error. Try again later or use --offline.",
    }
    return hints.get(name, f"Paperclip search failed ({name}): {e}")


class OfflineSource:
    """Keyword search over bundled sample data. Deterministic: used for demos and tests."""

    def __init__(self, papers: list[Paper] | None = None):
        if papers is None:
            text = resources.files("research_compass").joinpath("sample_papers.json").read_text("utf-8")
            papers = _normalize_all(json.loads(text))
        self._papers = papers

    def search(self, query: str, limit: int = 20, since: str | None = None) -> SearchResult:
        words = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 2]
        if not words:
            return SearchResult()
        scored = []
        for p in self._papers:
            text = f"{p.title} {p.abstract}".lower()
            hits = sum(1 for w in words if w in text)
            if hits >= max(1, (len(words) + 1) // 2):
                scored.append((hits, p.year or 0, p))
        scored.sort(key=lambda t: (-t[0], -t[1], t[2].id))
        return SearchResult(papers=[p for _, _, p in scored[:limit]], result_id="offline")

    def ask(self, question: str, result_id: str) -> str:
        raise SourceError("AI reading needs Paperclip; it is not available in --offline mode. Write notes with `note`.")
