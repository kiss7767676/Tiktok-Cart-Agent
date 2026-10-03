"""Shopee URL parsing.

Shopee product links commonly contain both shop ID and item ID. We parse those
IDs first because they are more stable than the product title slug.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from oss_my.domain.models import Platform, ProductIdentity

SHOPEE_I_PATTERN = re.compile(r"-i\.(?P<shop_id>\d+)\.(?P<item_id>\d+)")
SHOPEE_PRODUCT_PATTERN = re.compile(r"/product/(?P<shop_id>\d+)/(?P<item_id>\d+)")


def parse_shopee_identity(url: str) -> ProductIdentity | None:
    """Extract Shopee shop/item IDs from common URL formats.

    Supported examples:
        https://shopee.com.my/Product-Name-i.123.456
        https://shopee.com.my/product/123/456
    """

    parsed = urlparse(url)
    path = parsed.path

    match = SHOPEE_I_PATTERN.search(path) or SHOPEE_PRODUCT_PATTERN.search(path)
    if match is None:
        return None

    return ProductIdentity(
        platform=Platform.SHOPEE,
        shop_id=match.group("shop_id"),
        item_id=match.group("item_id"),
        raw_slug=_slug_before_identity(path),
    )


def _slug_before_identity(path: str) -> str | None:
    """Return the readable product slug when a Shopee `-i.shop.item` URL has one."""

    if "-i." not in path:
        return None

    slug = path.rsplit("-i.", maxsplit=1)[0].strip("/")
    return slug or None
