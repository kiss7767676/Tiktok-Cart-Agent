"""Research scraping helpers."""

from oss_my.research.google import scrape_google_research
from oss_my.research.ollama import ask_ollama_research
from oss_my.research.youtube import search_youtube_review_videos, youtube_sources_from_html

__all__ = [
    "ask_ollama_research",
    "scrape_google_research",
    "search_youtube_review_videos",
    "youtube_sources_from_html",
]
