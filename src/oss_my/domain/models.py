"""Core domain models.

Teaching note:
    A domain model is a plain representation of an idea in the system.
    It should not perform browser automation or call network APIs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Platform(StrEnum):
    """Marketplace platforms the system understands."""

    SHOPEE = "shopee"
    TIKTOK = "tiktok"
    LAZADA = "lazada"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ProductIdentity:
    """Stable platform-specific product reference.

    For Shopee, `shop_id` and `item_id` are usually the most useful identifiers.
    TikTok will likely need different IDs later, so all fields are optional.
    """

    platform: Platform
    item_id: str | None = None
    shop_id: str | None = None
    raw_slug: str | None = None


@dataclass(frozen=True, slots=True)
class DetectedLink:
    """Result of inspecting a user-provided shopping URL."""

    original_url: str
    platform: Platform
    product_identity: ProductIdentity | None = None
    is_supported_for_mvp: bool = False
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProductSummary:
    """Product/search card shown in Best Buy.

    Early cards may represent a platform search entry instead of a fully scraped
    product. The `data_status` field makes that explicit to the UI.
    """

    id: str
    platform: Platform
    title: str
    product_url: str
    price_label: str = "Open platform to confirm live price"
    shipping_label: str = "Open platform to confirm shipping"
    rating_label: str = "Not collected yet"
    stock_label: str = "Not collected yet"
    seller_label: str = "Not collected yet"
    data_status: str = "search_handoff"
    result_group: str = "general"
    risk_notes: tuple[str, ...] = ()
    research_queries: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EmulatorStatus:
    """ADB state for emulator-assisted shopping."""

    adb_path: str | None
    scrcpy_path: str | None
    devices: tuple[str, ...]
    ready: bool
    message: str


@dataclass(frozen=True, slots=True)
class EmulatorScreenshot:
    """Inline phone screenshot captured through ADB."""

    path: str | None
    ready: bool
    message: str


@dataclass(frozen=True, slots=True)
class EmulatorAppStatus:
    """Installed-package state for a marketplace app inside the emulator."""

    platform: str
    package_name: str
    installed: bool
    message: str


@dataclass(frozen=True, slots=True)
class ProductOptionGroup:
    """A group of selectable product options, such as color or size."""

    name: str
    options: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProductDetails:
    """Detailed product data rendered in the app's single-pane view."""

    platform: Platform
    url: str
    title: str
    price_label: str
    rating_label: str
    sold_label: str
    stock_label: str
    shop_label: str
    location_label: str
    description: str
    option_groups: tuple[ProductOptionGroup, ...] = ()
    warnings: tuple[str, ...] = ()
    data_status: str = "fallback"


@dataclass(frozen=True, slots=True)
class ResearchSource:
    """A source discovered by the research scraper."""

    title: str
    url: str
    snippet: str
    source_type: str = "web"


@dataclass(frozen=True, slots=True)
class ResearchBrief:
    """Research guidance for a product or shopping intent."""

    query: str
    overview: str
    key_questions: tuple[str, ...]
    source_links: tuple[str, ...]
    cautions: tuple[str, ...]
    ollama_response: str | None = None
    ollama_status: str = "not_requested"
    ollama_model: str | None = None
    google_ai_overview: str | None = None
    scraped_sources: tuple[ResearchSource, ...] = ()
    scrape_status: str = "not_requested"


@dataclass(frozen=True, slots=True)
class CheckoutPlan:
    """User-supervised checkout handoff plan."""

    platform: Platform
    item_count: int
    checkout_url: str
    warnings: tuple[str, ...]
    detected_links: tuple[DetectedLink, ...]


@dataclass(frozen=True, slots=True)
class AccountSetupStatus:
    """Local account setup state for a platform."""

    platform: Platform
    configured: bool
    credential_storage: str
    next_action: str
