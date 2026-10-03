"""Best-effort Google research scraper.

This is intentionally conservative. Google often renders AI Overview
dynamically, personalizes results, or blocks automated requests. The scraper
returns status and partial organic result data instead of fabricating content.
"""

from __future__ import annotations

from urllib.parse import quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup

from oss_my.domain.models import ResearchSource


def scrape_google_research(query: str, timeout_seconds: float = 10.0) -> tuple[str | None, tuple[ResearchSource, ...], str]:
    url = f"https://www.google.com/search?q={quote_plus(query)}&hl=en&gl=my"
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
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as error:
        return None, (), f"blocked_or_failed: {error}"

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    if "unusual traffic" in text or "our systems have detected" in text:
        return None, (), "blocked_by_google"

    ai_overview = _extract_ai_overview(soup)
    sources = _extract_organic_sources(soup)
    status = "ok"
    if ai_overview is None:
        status = "ok_no_ai_overview_found"
    if not sources and ai_overview is None:
        status = "ok_no_parseable_results"

    return ai_overview, sources, status


def _extract_ai_overview(soup: BeautifulSoup) -> str | None:
    markers = ("AI Overview", "Search Labs", "Generative AI is experimental")
    page_text = soup.get_text("\n", strip=True)
    for marker in markers:
        marker_index = page_text.find(marker)
        if marker_index == -1:
            continue
        candidate = page_text[marker_index : marker_index + 1400].strip()
        if len(candidate) > len(marker) + 40:
            return candidate
    return None


def _extract_organic_sources(soup: BeautifulSoup) -> tuple[ResearchSource, ...]:
    sources: list[ResearchSource] = []
    seen_urls: set[str] = set()

    for heading in soup.find_all("h3"):
        title = heading.get_text(" ", strip=True)
        if not title:
            continue

        link_tag = heading.find_parent("a") or heading.find_previous("a")
        if link_tag is None:
            continue
        raw_url = link_tag.get("href")
        if not raw_url:
            continue
        url = str(raw_url)
        if not url.startswith("http"):
            continue
        if "google." in urlparse(url).netloc:
            continue
        if url in seen_urls:
            continue

        container = heading.find_parent("div")
        snippet = ""
        if container is not None:
            snippet = container.get_text(" ", strip=True)
            snippet = snippet.replace(title, "", 1).strip()
            snippet = snippet[:320]

        sources.append(ResearchSource(title=title, url=url, snippet=snippet))
        seen_urls.add(url)
        if len(sources) >= 8:
            break

    return tuple(sources)
