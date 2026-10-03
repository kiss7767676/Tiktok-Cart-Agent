"""Shopee product details adapter.

The adapter is intentionally best-effort. Shopee's public web/API behavior can
change and may block unauthenticated requests. When live retrieval fails, the
adapter still returns a useful fallback based on the parsed URL identity.
"""

from __future__ import annotations

from typing import Any

import httpx
from bs4 import BeautifulSoup

from oss_my.domain.models import Platform, ProductDetails, ProductOptionGroup
from oss_my.platforms.shopee.links import parse_shopee_identity

SHOPEE_ITEM_API = "https://shopee.com.my/api/v4/item/get"
PRICE_SCALE = 100_000


def get_shopee_product_details(url: str, timeout_seconds: float = 10.0) -> ProductDetails:
    """Return Shopee product details, using live data when available."""

    identity = parse_shopee_identity(url)
    if identity is None or identity.shop_id is None or identity.item_id is None:
        return ProductDetails(
            platform=Platform.SHOPEE,
            url=url,
            title="Shopee product",
            price_label="Unknown",
            rating_label="Unknown",
            sold_label="Unknown",
            stock_label="Unknown",
            shop_label="Unknown",
            location_label="Unknown",
            description="Could not parse Shopee shop/item IDs from this URL.",
            warnings=("Use a Shopee product URL containing `-i.shop_id.item_id`.",),
            data_status="invalid_url",
        )

    try:
        data = _fetch_item_data(identity.shop_id, identity.item_id, timeout_seconds)
    except (httpx.HTTPError, TypeError, ValueError) as error:
        metadata_details = _page_metadata_details(url, str(error), timeout_seconds)
        if metadata_details is not None:
            return metadata_details
        return _fallback_details(url, str(error))

    if not data:
        return _fallback_details(url, "Shopee returned no product data.")

    return _details_from_api(url, data)


def _fetch_item_data(shop_id: str, item_id: str, timeout_seconds: float) -> dict[str, Any]:
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "referer": "https://shopee.com.my/",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
    }
    params = {"shopid": shop_id, "itemid": item_id}

    with httpx.Client(headers=headers, timeout=timeout_seconds, follow_redirects=True) as client:
        response = client.get(SHOPEE_ITEM_API, params=params)
        response.raise_for_status()
        payload = response.json()

    data = payload.get("data")
    if not isinstance(data, dict):
        raise TypeError(f"unexpected Shopee response shape: {payload!r}")
    return data


def _details_from_api(url: str, data: dict[str, Any]) -> ProductDetails:
    title = str(data.get("name") or "Shopee product")
    price_label = _price_label(data)
    rating_label = _rating_label(data)
    sold_label = _sold_label(data)
    stock_label = _stock_label(data)
    shop_label = _shop_label(data)
    location_label = str(data.get("shop_location") or data.get("item_location") or "Unknown")
    description = str(data.get("description") or "No description returned by Shopee.")
    option_groups = _option_groups(data)

    warnings = [
        "Confirm live price, vouchers, shipping, variation, and warranty on Shopee before payment.",
        "The app must stop before final payment confirmation.",
    ]

    return ProductDetails(
        platform=Platform.SHOPEE,
        url=url,
        title=title,
        price_label=price_label,
        rating_label=rating_label,
        sold_label=sold_label,
        stock_label=stock_label,
        shop_label=shop_label,
        location_label=location_label,
        description=description,
        option_groups=option_groups,
        warnings=tuple(warnings),
        data_status="live_api",
    )


def _fallback_details(url: str, reason: str) -> ProductDetails:
    identity = parse_shopee_identity(url)
    title = "Shopee product"
    if identity and identity.raw_slug:
        title = identity.raw_slug.replace("-", " ")

    shop_item = "Unknown"
    if identity and identity.shop_id and identity.item_id:
        shop_item = f"shop {identity.shop_id}, item {identity.item_id}"

    return ProductDetails(
        platform=Platform.SHOPEE,
        url=url,
        title=title,
        price_label="Open Shopee to confirm live price",
        rating_label="Open Shopee to confirm rating",
        sold_label="Open Shopee to confirm sold count",
        stock_label="Open Shopee to confirm stock",
        shop_label=shop_item,
        location_label="Open Shopee to confirm local/overseas shipping",
        description="Live Shopee details could not be retrieved. The parsed URL is still usable.",
        warnings=(
            f"Live Shopee request failed or was blocked: {reason}",
            "Open directly in Shopee to confirm price, options, stock, shipping, and seller profile.",
        ),
        data_status="fallback",
    )


def _page_metadata_details(
    url: str,
    api_error: str,
    timeout_seconds: float,
) -> ProductDetails | None:
    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            response = client.get(
                url,
                headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "accept-language": "en-US,en;q=0.9",
                    "user-agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/121.0.0.0 Safari/537.36"
                    ),
                },
            )
            response.raise_for_status()
    except httpx.HTTPError:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    title = _meta_content(soup, "og:title") or _title_text(soup)
    description = _meta_content(soup, "og:description") or "No page description found."

    if not title:
        return None

    return ProductDetails(
        platform=Platform.SHOPEE,
        url=url,
        title=title,
        price_label="Open Shopee to confirm live price",
        rating_label="Open Shopee to confirm rating",
        sold_label="Open Shopee to confirm sold count",
        stock_label="Open Shopee to confirm stock",
        shop_label="Open Shopee to confirm seller",
        location_label="Open Shopee to confirm local/overseas shipping",
        description=description,
        warnings=(
            f"Shopee API request failed or was blocked: {api_error}",
            "Recovered page metadata only. Open Shopee to confirm price, options, stock, shipping, and seller profile.",
        ),
        data_status="page_metadata",
    )


def _meta_content(soup: BeautifulSoup, property_name: str) -> str | None:
    tag = soup.find("meta", property=property_name)
    if tag is None:
        return None
    value = tag.get("content")
    return str(value).strip() if value else None


def _title_text(soup: BeautifulSoup) -> str | None:
    if soup.title is None or soup.title.string is None:
        return None
    return soup.title.string.strip()


def _price_label(data: dict[str, Any]) -> str:
    price = _scaled_price(data.get("price"))
    price_min = _scaled_price(data.get("price_min"))
    price_max = _scaled_price(data.get("price_max"))

    if price_min is not None and price_max is not None and price_min != price_max:
        return f"RM {price_min:g} - RM {price_max:g}"
    if price is not None:
        return f"RM {price:g}"
    if price_min is not None:
        return f"RM {price_min:g}"
    return "Unknown"


def _scaled_price(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return int(value) / PRICE_SCALE
    except (TypeError, ValueError):
        return None


def _rating_label(data: dict[str, Any]) -> str:
    item_rating = data.get("item_rating")
    if isinstance(item_rating, dict):
        rating = item_rating.get("rating_star")
        count = item_rating.get("rating_count")
        if rating is not None and count is not None:
            total_count = _rating_total(count)
            return f"{float(rating):.2f} / 5 ({total_count} ratings)"
        if rating is not None:
            return f"{float(rating):.2f} / 5"
    return "Unknown"


def _rating_total(count: Any) -> int:
    if isinstance(count, list) and count:
        try:
            return int(count[0])
        except (TypeError, ValueError):
            return 0
    try:
        return int(count)
    except (TypeError, ValueError):
        return 0


def _sold_label(data: dict[str, Any]) -> str:
    sold = data.get("historical_sold") or data.get("sold")
    if sold is None:
        return "Unknown"
    return f"{sold} sold"


def _stock_label(data: dict[str, Any]) -> str:
    stock = data.get("stock")
    if stock is None:
        return "Unknown"
    return f"{stock} available"


def _shop_label(data: dict[str, Any]) -> str:
    shop = data.get("shop_detailed") or data.get("shop")
    if isinstance(shop, dict):
        return str(shop.get("name") or shop.get("shop_name") or "Shopee seller")
    return "Shopee seller"


def _option_groups(data: dict[str, Any]) -> tuple[ProductOptionGroup, ...]:
    groups = []
    tier_variations = data.get("tier_variations")
    if not isinstance(tier_variations, list):
        return ()

    for variation in tier_variations:
        if not isinstance(variation, dict):
            continue
        name = str(variation.get("name") or "Option")
        raw_options = variation.get("options") or []
        options = tuple(str(option) for option in raw_options if option is not None)
        groups.append(ProductOptionGroup(name=name, options=options))

    return tuple(groups)
