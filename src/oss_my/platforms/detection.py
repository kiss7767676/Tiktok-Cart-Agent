"""Marketplace URL detection.

Teaching note:
    This module answers a small question: "what platform is this link?"
    It delegates platform-specific parsing to platform-specific modules.
"""

from __future__ import annotations

from urllib.parse import urlparse

from oss_my.domain.models import DetectedLink, Platform
from oss_my.platforms.shopee.links import parse_shopee_identity

SHOPEE_HOST_MARKERS = ("shopee.", "shp.ee")
TIKTOK_HOST_MARKERS = ("tiktok.com", "tiktokshop.", "vt.tiktok.com")
LAZADA_HOST_MARKERS = ("lazada.", "lzd.co")


def detect_link(url: str) -> DetectedLink:
    """Detect marketplace and parse product identity where supported."""

    host = urlparse(url).netloc.lower()

    if _host_matches(host, SHOPEE_HOST_MARKERS):
        identity = parse_shopee_identity(url)
        notes: list[str] = []
        if identity is None:
            notes.append("Shopee link detected, but shop/item IDs were not found in the URL.")
        return DetectedLink(
            original_url=url,
            platform=Platform.SHOPEE,
            product_identity=identity,
            is_supported_for_mvp=True,
            notes=tuple(notes),
        )

    if _host_matches(host, TIKTOK_HOST_MARKERS):
        return DetectedLink(
            original_url=url,
            platform=Platform.TIKTOK,
            is_supported_for_mvp=True,
            notes=("TikTok is in MVP scope, but product parsing will use the Android path later.",),
        )

    if _host_matches(host, LAZADA_HOST_MARKERS):
        return DetectedLink(
            original_url=url,
            platform=Platform.LAZADA,
            is_supported_for_mvp=False,
            notes=("Lazada detected, but it is deferred until Shopee and TikTok are stable.",),
        )

    return DetectedLink(
        original_url=url,
        platform=Platform.UNKNOWN,
        is_supported_for_mvp=False,
        notes=("Unknown or unsupported shopping platform.",),
    )


def _host_matches(host: str, markers: tuple[str, ...]) -> bool:
    return any(marker in host for marker in markers)
