"""Shopee-specific parsing and automation code."""

from oss_my.platforms.shopee.details import get_shopee_product_details
from oss_my.platforms.shopee.links import parse_shopee_identity
from oss_my.platforms.shopee.search import search_shopee_products

__all__ = ["get_shopee_product_details", "parse_shopee_identity", "search_shopee_products"]
