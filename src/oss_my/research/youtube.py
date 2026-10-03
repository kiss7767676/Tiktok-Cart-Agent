"""Best-effort YouTube video search for research sources."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.parse import quote_plus

import httpx

from oss_my.domain.models import ResearchSource

YOUTUBE_SEARCH_URL = "https://www.youtube.com/results"
VIDEO_URL_PREFIX = "https://www.youtube.com/watch?v="
SHORTS_URL_PREFIX = "https://www.youtube.com/shorts/"


@dataclass(frozen=True, slots=True)
class _YoutubeCandidate:
    video_id: str
    title: str
    views: int
    is_short: bool
    relevance_score: int


def search_youtube_review_videos(
    query: str,
    limit: int = 2,
    timeout_seconds: float = 10.0,
) -> tuple[ResearchSource, ...]:
    """Return real YouTube video URLs for a product review query."""

    search_query = f"{query} review"
    url = f"{YOUTUBE_SEARCH_URL}?search_query={quote_plus(search_query)}"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
    }

    try:
        response = httpx.get(url, headers=headers, timeout=timeout_seconds, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError:
        return ()

    return youtube_sources_from_html(response.text, query, limit=limit)


def youtube_sources_from_html(html: str, query: str, limit: int = 2) -> tuple[ResearchSource, ...]:
    candidates = _youtube_candidates_from_html(html, query)
    ranked = sorted(
        candidates,
        key=lambda item: (item.is_short, -item.relevance_score, -item.views),
    )

    sources = []
    seen_video_ids: set[str] = set()
    for candidate in ranked:
        if candidate.video_id in seen_video_ids:
            continue
        seen_video_ids.add(candidate.video_id)
        sources.append(
            ResearchSource(
                title=candidate.title,
                url=f"{VIDEO_URL_PREFIX}{candidate.video_id}",
                snippet=_view_label(candidate.views),
                source_type="youtube",
            )
        )
        if len(sources) >= limit:
            break

    return tuple(sources)


def _youtube_candidates_from_html(html: str, query: str) -> list[_YoutubeCandidate]:
    initial_data = _extract_yt_initial_data(html)
    if initial_data is not None:
        candidates = _walk_youtube_renderers(initial_data, query)
        if candidates:
            return candidates
    return _regex_youtube_candidates(html, query)


def _extract_yt_initial_data(html: str) -> object | None:
    marker = "var ytInitialData = "
    start = html.find(marker)
    if start == -1:
        marker = "ytInitialData = "
        start = html.find(marker)
    if start == -1:
        return None

    start += len(marker)
    end = _matching_json_object_end(html, start)
    if end is None:
        return None

    try:
        return json.loads(html[start:end])
    except json.JSONDecodeError:
        return None


def _matching_json_object_end(text: str, start: int) -> int | None:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
    return None


def _walk_youtube_renderers(value: object, query: str) -> list[_YoutubeCandidate]:
    candidates: list[_YoutubeCandidate] = []
    if isinstance(value, dict):
        renderer = value.get("videoRenderer")
        if isinstance(renderer, dict):
            candidate = _candidate_from_renderer(renderer, query)
            if candidate is not None:
                candidates.append(candidate)
        for item in value.values():
            candidates.extend(_walk_youtube_renderers(item, query))
    elif isinstance(value, list):
        for item in value:
            candidates.extend(_walk_youtube_renderers(item, query))
    return candidates


def _candidate_from_renderer(renderer: dict[str, object], query: str) -> _YoutubeCandidate | None:
    video_id = renderer.get("videoId")
    if not isinstance(video_id, str) or not _valid_video_id(video_id):
        return None

    title = _text_from_runs(renderer.get("title"))
    if not title:
        return None

    navigation_url = _navigation_url(renderer)
    is_short = "/shorts/" in navigation_url
    relevance_score = _relevance_score(title, query)
    if relevance_score <= 0 and not is_short:
        return None

    return _YoutubeCandidate(
        video_id=video_id,
        title=title,
        views=_view_count(renderer),
        is_short=is_short,
        relevance_score=relevance_score,
    )


def _text_from_runs(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    if isinstance(value.get("simpleText"), str):
        return str(value["simpleText"]).strip()
    runs = value.get("runs")
    if not isinstance(runs, list):
        return ""
    return " ".join(str(run.get("text", "")).strip() for run in runs if isinstance(run, dict)).strip()


def _navigation_url(renderer: dict[str, object]) -> str:
    navigation = renderer.get("navigationEndpoint")
    if not isinstance(navigation, dict):
        return ""
    command = navigation.get("commandMetadata")
    if not isinstance(command, dict):
        return ""
    web = command.get("webCommandMetadata")
    if not isinstance(web, dict):
        return ""
    url = web.get("url")
    return str(url) if isinstance(url, str) else ""


def _view_count(renderer: dict[str, object]) -> int:
    for key in ("viewCountText", "shortViewCountText"):
        text = _text_from_runs(renderer.get(key))
        if text:
            return _parse_views(text)
    return 0


def _regex_youtube_candidates(html: str, query: str) -> list[_YoutubeCandidate]:
    candidates = []
    seen_video_ids: set[str] = set()
    for match in re.finditer(r'"videoId":"(?P<id>[A-Za-z0-9_-]{11})"', html):
        video_id = match.group("id")
        if video_id in seen_video_ids:
            continue
        seen_video_ids.add(video_id)
        window = html[match.start() : match.start() + 2400]
        title = _regex_title(window) or f"YouTube video: {query}"
        is_short = "/shorts/" in window
        candidates.append(
            _YoutubeCandidate(
                video_id=video_id,
                title=title,
                views=_parse_views(window),
                is_short=is_short,
                relevance_score=_relevance_score(title, query),
            )
        )
    return [candidate for candidate in candidates if candidate.relevance_score > 0 or candidate.is_short]


def _regex_title(text: str) -> str | None:
    match = re.search(r'"title":\{"runs":\[\{"text":"(?P<title>.*?)"', text)
    if match is None:
        match = re.search(r'"title":\{"simpleText":"(?P<title>.*?)"', text)
    if match is None:
        return None
    return match.group("title").encode("utf-8").decode("unicode_escape").strip()


def _relevance_score(title: str, query: str) -> int:
    title_words = _words(title)
    query_words = _words(query)
    review_words = {"review", "tested", "testing", "test", "unboxing", "comparison", "vs"}
    score = sum(2 for word in query_words if word in title_words)
    score += sum(1 for word in review_words if word in title_words)
    return score


def _words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) >= 2}


def _parse_views(text: str) -> int:
    match = re.search(r"([\d,.]+)\s*([KMB])?\s*views?", text, re.IGNORECASE)
    if match is None:
        return 0
    number = float(match.group(1).replace(",", ""))
    multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get(
        (match.group(2) or "").upper(),
        1,
    )
    return int(number * multiplier)


def _view_label(views: int) -> str:
    if views <= 0:
        return "YouTube review video"
    return f"YouTube review video - {_compact_number(views)} views"


def _compact_number(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M".rstrip("0").rstrip(".")
    if value >= 1_000:
        return f"{value / 1_000:.1f}K".rstrip("0").rstrip(".")
    return str(value)


def _valid_video_id(video_id: str) -> bool:
    return len(video_id) == 11 and all(
        char.isascii() and (char.isalnum() or char in {"-", "_"})
        for char in video_id
    )
