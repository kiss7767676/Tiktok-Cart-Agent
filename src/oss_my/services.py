"""Application services used by CLI and desktop UI.

Teaching note:
    Services combine domain models and platform helpers into user-facing
    actions. The Rust UI should call these actions through stable commands.
"""

from __future__ import annotations

from urllib.parse import quote_plus

import keyring

from oss_my.domain.models import (
    AccountSetupStatus,
    CheckoutPlan,
    EmulatorAppStatus,
    EmulatorScreenshot,
    EmulatorStatus,
    Platform,
    ProductDetails,
    ProductSummary,
    ResearchBrief,
)
from oss_my.emulator import (
    capture_screenshot,
    emulator_status,
    install_apk,
    launch_scrcpy,
    marketplace_app_statuses,
    open_marketplace_app,
    optimize_emulator,
    search_products_in_emulator,
    start_sdk_emulator,
    swipe_screen,
    tap_screen,
)
from oss_my.platforms import detect_link
from oss_my.platforms.shopee import get_shopee_product_details, search_shopee_products
from oss_my.research import (
    ask_ollama_research,
    scrape_google_research,
    search_youtube_review_videos,
)

KEYRING_SERVICE_PREFIX = "online-shopping-system-malaysia"


def best_buy_search(
    query: str,
    platforms: list[Platform],
    budget_min: float | None = None,
    budget_max: float | None = None,
) -> list[ProductSummary]:
    """Return Best Buy cards for the requested platforms.

    Current implementation creates high-quality platform handoff cards. Live
    product extraction will replace these cards platform-by-platform.
    """

    budget_note = _budget_note(budget_min, budget_max)
    results: list[ProductSummary] = []

    if Platform.SHOPEE in platforms:
        shopee_results = [
            *search_shopee_products(query, "relevancy", limit=6),
            *search_shopee_products(query, "top_sales", limit=6),
        ]
        results.extend(_apply_budget_note(shopee_results, budget_note))

    if Platform.TIKTOK in platforms:
        results.append(
            ProductSummary(
                id="tiktok-search",
                platform=Platform.TIKTOK,
                title=f"TikTok Shop search: {query}",
                product_url=f"https://www.tiktok.com/search?q={quote_plus(query)}",
                price_label=budget_note,
                shipping_label="TikTok checkout will use emulator/app automation later.",
                rating_label="Review signals pending TikTok adapter.",
                seller_label="Check shop profile inside TikTok before buying.",
                data_status="emulator_handoff_pending",
                result_group="Discovery",
                risk_notes=(
                    "TikTok Shop web checkout is not the target path.",
                    "Use this as discovery until emulator automation is implemented.",
                ),
                research_queries=(query, f"{query} TikTok Shop review", f"{query} Malaysia"),
            )
        )

    return results


def emulator_best_buy_search(query: str, group: str, device_serial: str | None = None) -> list[ProductSummary]:
    """Search products through a connected Android emulator/device."""

    return search_products_in_emulator(query, group, device_serial)


def get_emulator_status(device_serial: str | None = None) -> EmulatorStatus:
    return emulator_status(device_serial)


def open_emulator_display(device_serial: str | None = None) -> EmulatorStatus:
    return launch_scrcpy(device_serial)


def get_emulator_screenshot(device_serial: str | None = None) -> EmulatorScreenshot:
    return capture_screenshot(device_serial)


def start_emulator() -> EmulatorStatus:
    return start_sdk_emulator()


def tap_emulator(x: int, y: int, device_serial: str | None = None) -> EmulatorStatus:
    return tap_screen(x, y, device_serial)


def swipe_emulator(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    duration_ms: int = 350,
    device_serial: str | None = None,
) -> EmulatorStatus:
    return swipe_screen(x1, y1, x2, y2, duration_ms, device_serial)


def optimize_emulator_runtime(device_serial: str | None = None) -> EmulatorStatus:
    return optimize_emulator(device_serial)


def install_emulator_apk(apk_path: str, device_serial: str | None = None) -> EmulatorStatus:
    return install_apk(apk_path, device_serial)


def emulator_app_statuses(device_serial: str | None = None) -> list[EmulatorAppStatus]:
    return list(marketplace_app_statuses(device_serial))


def store_account_credentials(platform: Platform, username: str, password: str) -> AccountSetupStatus:
    service_name = _credential_service(platform)
    keyring.set_password(service_name, "__username__", username)
    keyring.set_password(service_name, username, password)
    return _account_status(platform)


def open_account_login(platform: Platform, device_serial: str | None = None) -> EmulatorStatus:
    return open_marketplace_app(platform.value, device_serial)


def _apply_budget_note(results: list[ProductSummary], budget_note: str) -> list[ProductSummary]:
    if budget_note == "No budget preference":
        return results

    adjusted = []
    for result in results:
        adjusted.append(
            ProductSummary(
                id=result.id,
                platform=result.platform,
                title=result.title,
                product_url=result.product_url,
                price_label=f"{result.price_label} ({budget_note})",
                shipping_label=result.shipping_label,
                rating_label=result.rating_label,
                stock_label=result.stock_label,
                seller_label=result.seller_label,
                data_status=result.data_status,
                result_group=result.result_group,
                risk_notes=result.risk_notes,
                research_queries=result.research_queries,
            )
        )
    return adjusted


def build_research_brief(
    query: str,
    scrape_google: bool = False,
    use_ollama: bool = True,
    ollama_model: str | None = None,
    use_youtube: bool = True,
) -> ResearchBrief:
    """Build a research helper around source links and buying questions."""

    encoded = quote_plus(query)
    ai_overview = None
    scraped_sources = ()
    scrape_status = "not_requested"
    ollama_response = None
    ollama_status = "not_requested"
    selected_ollama_model = ollama_model
    youtube_sources = search_youtube_review_videos(query, limit=2) if use_youtube else ()
    if scrape_google:
        ai_overview, scraped_sources, scrape_status = scrape_google_research(query)
    if use_ollama:
        ollama_response, ollama_status, selected_ollama_model = ask_ollama_research(
            query,
            model=ollama_model,
        )

    return ResearchBrief(
        query=query,
        overview=(
            "Use this page to slow down the purchase decision. Check independent reviews, "
            "common complaints, alternatives, and whether the listed price is actually good."
        ),
        key_questions=(
            "What are the common defects or failure points?",
            "Are negative reviews about product quality, shipping, or seller behavior?",
            "Is the local price meaningfully better after shipping and vouchers?",
            "Are there safer alternatives from better-rated sellers?",
        ),
        source_links=(
            f"https://www.google.com/search?q={encoded}",
            f"https://www.google.com/search?q={encoded}+review+Malaysia",
            f"https://www.google.com/search?q={encoded}+problem+complaint",
        ),
        cautions=(
            "Do not rely only on marketplace ratings; inspect 1-star reviews.",
            "Check whether the cheapest listing is overseas with long shipping.",
            "Confirm variation/options before adding to cart.",
        ),
        ollama_response=ollama_response,
        ollama_status=ollama_status,
        ollama_model=selected_ollama_model,
        google_ai_overview=ai_overview,
        scraped_sources=(*youtube_sources, *scraped_sources),
        scrape_status=scrape_status,
    )


def build_checkout_plan(urls: list[str]) -> CheckoutPlan:
    """Create a user-supervised checkout handoff plan from selected links."""

    detected = tuple(detect_link(url) for url in urls)
    platforms = {item.platform for item in detected}

    if len(platforms) == 1:
        platform = next(iter(platforms))
    else:
        platform = Platform.UNKNOWN

    checkout_url = _checkout_url_for(platform)
    warnings = [
        "This app must stop before final payment confirmation.",
        "Login, OTP, CAPTCHA, and payment are user-supervised checkpoints.",
    ]

    if platform == Platform.SHOPEE:
        warnings.append(
            "Shopee automatic add-to-cart is pending. Current handoff opens Shopee cart/search context."
        )
    elif platform == Platform.TIKTOK:
        warnings.append("TikTok checkout requires emulator/app automation, pending implementation.")
    else:
        warnings.append("Mixed or unsupported platforms should be handled one platform at a time.")

    return CheckoutPlan(
        platform=platform,
        item_count=len(urls),
        checkout_url=checkout_url,
        warnings=tuple(warnings),
        detected_links=detected,
    )


def get_product_details(urls: list[str]) -> list[ProductDetails]:
    """Resolve detailed product data for supported platform URLs."""

    details = []
    for url in urls:
        detected = detect_link(url)
        match detected.platform:
            case Platform.SHOPEE:
                details.append(get_shopee_product_details(url))
            case _:
                details.append(
                    ProductDetails(
                        platform=detected.platform,
                        url=url,
                        title=f"{detected.platform.value} product",
                        price_label="Unsupported for product details",
                        rating_label="Unsupported for product details",
                        sold_label="Unsupported for product details",
                        stock_label="Unsupported for product details",
                        shop_label="Unsupported for product details",
                        location_label="Unsupported for product details",
                        description="Product detail extraction is currently implemented for Shopee only.",
                        warnings=("Open this link directly on the platform.",),
                        data_status="unsupported_platform",
                    )
                )

    return details


def account_setup_statuses() -> list[AccountSetupStatus]:
    """Return account setup status without exposing credential values."""

    return [_account_status(Platform.SHOPEE), _account_status(Platform.TIKTOK)]


def _account_status(platform: Platform) -> AccountSetupStatus:
    username = keyring.get_password(_credential_service(platform), "__username__")
    configured = bool(username)
    if configured:
        next_action = "Credentials stored. App login automation can use them after app-specific selectors are added."
    else:
        next_action = f"Store {platform.value} credentials in OS keyring."

    return AccountSetupStatus(
        platform=platform,
        configured=configured,
        credential_storage="OS keyring",
        next_action=next_action,
    )


def _credential_service(platform: Platform) -> str:
    return f"{KEYRING_SERVICE_PREFIX}:{platform.value}"


def parse_platforms(raw_platforms: list[str]) -> list[Platform]:
    if not raw_platforms:
        return [Platform.SHOPEE, Platform.TIKTOK]

    parsed = []
    for raw in raw_platforms:
        normalized = raw.strip().lower()
        try:
            platform = Platform(normalized)
        except ValueError:
            continue
        if platform in {Platform.SHOPEE, Platform.TIKTOK}:
            parsed.append(platform)

    return parsed or [Platform.SHOPEE, Platform.TIKTOK]


def _budget_note(budget_min: float | None, budget_max: float | None) -> str:
    if budget_min is None and budget_max is None:
        return "No budget preference"
    if budget_min is not None and budget_max is not None:
        return f"Target budget: RM {budget_min:g} - RM {budget_max:g}"
    if budget_min is not None:
        return f"Target minimum: RM {budget_min:g}+"
    return f"Target maximum: RM {budget_max:g}"


def _checkout_url_for(platform: Platform) -> str:
    match platform:
        case Platform.SHOPEE:
            return "https://shopee.com.my/cart/"
        case Platform.TIKTOK:
            return "https://www.tiktok.com/"
        case _:
            return ""
