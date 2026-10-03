import oss_my.services
from oss_my.domain.models import Platform
from oss_my.services import (
    account_setup_statuses,
    best_buy_search,
    build_checkout_plan,
    build_research_brief,
    get_product_details,
    parse_platforms,
)


def test_best_buy_returns_shopee_and_tiktok_handoff_cards() -> None:
    original = oss_my.services.search_shopee_products
    oss_my.services.search_shopee_products = lambda query, group, limit=6: []
    try:
        results = best_buy_search("wireless mouse", [Platform.SHOPEE, Platform.TIKTOK], 20, 80)
    finally:
        oss_my.services.search_shopee_products = original

    assert [result.platform for result in results] == [Platform.TIKTOK]
    assert "wireless+mouse" in results[0].product_url
    assert results[0].price_label == "Target budget: RM 20 - RM 80"


def test_research_brief_contains_source_links_and_cautions() -> None:
    brief = build_research_brief(
        "mechanical keyboard",
        scrape_google=False,
        use_ollama=False,
        use_youtube=False,
    )

    assert brief.query == "mechanical keyboard"
    assert len(brief.source_links) >= 3
    assert not any("youtube.com/results" in link for link in brief.source_links)
    assert brief.cautions
    assert brief.ollama_status == "not_requested"
    assert brief.scrape_status == "not_requested"


def test_research_brief_can_include_ollama_response() -> None:
    original = oss_my.services.ask_ollama_research
    oss_my.services.ask_ollama_research = lambda query, model=None: (
        "Check reviews for switch chatter before buying.",
        "ok",
        "qwen3:4b",
    )
    try:
        brief = build_research_brief("mechanical keyboard", scrape_google=False, use_youtube=False)
    finally:
        oss_my.services.ask_ollama_research = original

    assert brief.ollama_status == "ok"
    assert brief.ollama_model == "qwen3:4b"
    assert "switch chatter" in (brief.ollama_response or "")


def test_checkout_plan_for_single_platform_shopee() -> None:
    plan = build_checkout_plan(["https://shopee.com.my/Product-i.123.456"])

    assert plan.platform == Platform.SHOPEE
    assert plan.item_count == 1
    assert plan.checkout_url == "https://shopee.com.my/cart/"
    assert plan.detected_links[0].product_identity is not None


def test_parse_platforms_defaults_to_mvp_platforms() -> None:
    assert parse_platforms([]) == [Platform.SHOPEE, Platform.TIKTOK]
    assert parse_platforms(["shopee"]) == [Platform.SHOPEE]
    assert parse_platforms(["lazada"]) == [Platform.SHOPEE, Platform.TIKTOK]


def test_account_statuses_cover_mvp_platforms() -> None:
    statuses = account_setup_statuses()

    assert {status.platform for status in statuses} == {Platform.SHOPEE, Platform.TIKTOK}


def test_product_details_returns_unsupported_for_non_shopee() -> None:
    details = get_product_details(["https://www.tiktok.com/@shop/video/123"])

    assert len(details) == 1
    assert details[0].platform == Platform.TIKTOK
    assert details[0].data_status == "unsupported_platform"
