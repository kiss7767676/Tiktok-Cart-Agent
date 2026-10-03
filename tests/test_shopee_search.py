from oss_my.domain.models import Platform
from oss_my.platforms.shopee.search import _product_from_item


def test_shopee_search_item_maps_to_product_summary() -> None:
    product = _product_from_item(
        "pentel p205",
        "relevancy",
        {
            "shopid": 123,
            "itemid": 456,
            "name": "Pentel P205 Mechanical Pencil",
            "price": 12_500_000,
            "stock": 15,
            "shop_location": "Selangor",
            "item_rating": {"rating_star": 4.9, "rating_count": [100, 0, 1, 2, 10, 87]},
            "shop_name": "Stationery Store",
        },
    )

    assert product is not None
    assert product.platform == Platform.SHOPEE
    assert product.title == "Pentel P205 Mechanical Pencil"
    assert product.product_url == "https://shopee.com.my/product/123/456"
    assert product.price_label == "RM 125"
    assert product.shipping_label == "Ships from Selangor"
    assert product.rating_label == "4.90 / 5 (100 ratings)"
    assert product.stock_label == "15 available"
    assert product.seller_label == "Stationery Store"
    assert product.result_group == "Most relevant"
