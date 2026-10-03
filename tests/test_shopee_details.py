from oss_my.domain.models import Platform
from oss_my.platforms.shopee.details import _details_from_api, get_shopee_product_details


def test_shopee_details_fallback_for_invalid_url() -> None:
    details = get_shopee_product_details("https://shopee.com.my/not-a-product")

    assert details.platform == Platform.SHOPEE
    assert details.data_status == "invalid_url"
    assert details.warnings


def test_shopee_details_from_api_maps_core_fields() -> None:
    details = _details_from_api(
        "https://shopee.com.my/Product-i.123.456",
        {
            "name": "Mechanical Keyboard",
            "price": 12_990_000,
            "stock": 42,
            "historical_sold": 120,
            "shop_location": "Selangor",
            "description": "A keyboard.",
            "item_rating": {"rating_star": 4.8123, "rating_count": [80, 1, 2, 3, 10, 64]},
            "shop_detailed": {"name": "Keyboard Store"},
            "tier_variations": [
                {"name": "Switch", "options": ["Red", "Brown"]},
                {"name": "Layout", "options": ["TKL", "Full Size"]},
            ],
        },
    )

    assert details.platform == Platform.SHOPEE
    assert details.data_status == "live_api"
    assert details.title == "Mechanical Keyboard"
    assert details.price_label == "RM 129.9"
    assert details.rating_label == "4.81 / 5 (80 ratings)"
    assert details.sold_label == "120 sold"
    assert details.stock_label == "42 available"
    assert details.shop_label == "Keyboard Store"
    assert details.location_label == "Selangor"
    assert details.option_groups[0].name == "Switch"
    assert details.option_groups[0].options == ("Red", "Brown")
