"""Shopee search adapter.

The adapter tries Shopee's search endpoint and maps products into comparison
cards. Shopee may return anti-bot/traffic-verification responses for
unauthenticated requests; that status is surfaced to the UI as a card instead
of hidden.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

import httpx

from oss_my.domain.models import Platform, ProductSummary
from oss_my.platforms.shopee.details import PRICE_SCALE

SHOPEE_SEARCH_API = "https://shopee.com.my/api/v4/search/search_items"


def search_shopee_products(query: str, group: str, limit: int = 6) -> list[ProductSummary]:
    sort_mode = "sales" if group == "top_sales" else "relevancy"
    try:
        payload = _fetch_search_payload(query, sort_mode, limit)
    except (httpx.HTTPError, TypeError, ValueError) as error:
        return [_blocked_card(query, group, str(error))]

    items = payload.get("items")
    if not isinstance(items, list) or not items:
        return [_blocked_card(query, group, "Shopee returned no parseable search items.")]

    products = []
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        item_basic = item.get("item_basic")
        if not isinstance(item_basic, dict):
            item_basic = item
        product = _product_from_item(query, group, item_basic)
        if product is not None:
            products.append(product)

    return products or [_blocked_card(query, group, "Shopee search items did not contain product data.")]


def _fetch_search_payload(query: str, sort_mode: str, limit: int) -> dict[str, Any]:
    params = {
        "by": sort_mode,
        "keyword": query,
        "limit": limit,
        "newest": 0,
        "order": "desc",
        "page_type": "search",
        "scenario": "PAGE_GLOBAL_SEARCH",
        "version": 2,
    }
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "referer": f"https://shopee.com.my/search?keyword={quote_plus(query)}",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
    }

    with httpx.Client(headers=headers, timeout=12.0, follow_redirects=True) as client:
        response = client.get(SHOPEE_SEARCH_API, params=params)
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise TypeError(f"unexpected Shopee search response shape: {payload!r}")
    if payload.get("error") or payload.get("redirect_to_error_page"):
        raise ValueError(f"Shopee search blocked or returned error: {payload!r}")
    return payload


def _product_from_item(query: str, group: str, item: dict[str, Any]) -> ProductSummary | None:
    shop_id = item.get("shopid")
    item_id = item.get("itemid")
    name = item.get("name")
    if shop_id is None or item_id is None or not name:
        return None

    product_url = f"https://shopee.com.my/product/{shop_id}/{item_id}"
    return ProductSummary(
        id=f"shopee-{group}-{shop_id}-{item_id}",
        platform=Platform.SHOPEE,
        title=str(name),
        product_url=product_url,
        price_label=_price_label(item),
        shipping_label=_shipping_label(item),
        rating_label=_rating_label(item),
        stock_label=_stock_label(item),
        seller_label=_seller_label(item),
        data_status="live_search",
        result_group=_group_label(group),
        risk_notes=_risk_notes(item),
        research_queries=(str(name), f"{name} review", f"{query} Malaysia"),
    )


def _blocked_card(query: str, group: str, reason: str) -> ProductSummary:
    return ProductSummary(
        id=f"shopee-{group}-blocked",
        platform=Platform.SHOPEE,
        title=f"Shopee {_group_label(group)} results unavailable",
        product_url=f"https://shopee.com.my/search?keyword={quote_plus(query)}",
        price_label="Blocked by Shopee search",
        shipping_label="Open Shopee directly or use logged-in browser session later.",
        rating_label="Unavailable",
        stock_label="Unavailable",
        seller_label="Unavailable",
        data_status="blocked_by_shopee",
        result_group=_group_label(group),
        risk_notes=(
            reason,
            "Shopee search currently blocks unauthenticated/headless requests from this environment.",
        ),
        research_queries=(query, f"{query} review", f"{query} Malaysia"),
    )


def _price_label(item: dict[str, Any]) -> str:
    price = _scaled_price(item.get("price"))
    price_min = _scaled_price(item.get("price_min"))
    price_max = _scaled_price(item.get("price_max"))
    if price_min is not None and price_max is not None and price_min != price_max:
        return f"RM {price_min:g} - RM {price_max:g}"
    if price is not None:
        return f"RM {price:g}"
    if price_min is not None:
        return f"RM {price_min:g}"
    return "Price unavailable"


def _scaled_price(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return int(value) / PRICE_SCALE
    except (TypeError, ValueError):
        return None


def _shipping_label(item: dict[str, Any]) -> str:
    location = item.get("shop_location") or item.get("item_location")
    if location:
        return f"Ships from {location}"
    return "Shipping location unavailable"


def _rating_label(item: dict[str, Any]) -> str:
    rating = item.get("item_rating")
    if isinstance(rating, dict):
        star = rating.get("rating_star")
        count = rating.get("rating_count")
        if star is not None:
            total = 0
            if isinstance(count, list) and count:
                total = int(count[0] or 0)
            elif count is not None:
                total = int(count)
            suffix = f" ({total} ratings)" if total else ""
            return f"{float(star):.2f} / 5{suffix}"
    return "Rating unavailable"


def _stock_label(item: dict[str, Any]) -> str:
    stock = item.get("stock")
    if stock is None:
        return "Stock unavailable"
    return f"{stock} available"


def _seller_label(item: dict[str, Any]) -> str:
    shop_name = item.get("shop_name") or item.get("shopid")
    if shop_name is None:
        return "Seller unavailable"
    return str(shop_name)


def _risk_notes(item: dict[str, Any]) -> tuple[str, ...]:
    notes = ["Confirm variation, vouchers, shipping, and warranty before checkout."]
    if item.get("is_adult"):
        notes.append("Shopee marked this item as adult/restricted.")
    if item.get("is_preferred_plus_seller"):
        notes.append("Preferred Plus seller signal present.")
    return tuple(notes)


def _group_label(group: str) -> str:
    return "Top sales" if group == "top_sales" else "Most relevant"
