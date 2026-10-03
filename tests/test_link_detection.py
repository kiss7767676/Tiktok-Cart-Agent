from oss_my.domain.models import Platform
from oss_my.platforms import detect_link


def test_detects_shopee_i_url_and_extracts_ids() -> None:
    result = detect_link("https://shopee.com.my/Good-Product-i.12345.67890")

    assert result.platform == Platform.SHOPEE
    assert result.is_supported_for_mvp is True
    assert result.product_identity is not None
    assert result.product_identity.shop_id == "12345"
    assert result.product_identity.item_id == "67890"
    assert result.product_identity.raw_slug == "Good-Product"


def test_detects_shopee_product_url_and_extracts_ids() -> None:
    result = detect_link("https://shopee.com.my/product/12345/67890")

    assert result.platform == Platform.SHOPEE
    assert result.product_identity is not None
    assert result.product_identity.shop_id == "12345"
    assert result.product_identity.item_id == "67890"


def test_detects_tiktok_as_mvp_platform() -> None:
    result = detect_link("https://www.tiktok.com/@shop/video/123")

    assert result.platform == Platform.TIKTOK
    assert result.is_supported_for_mvp is True


def test_lazada_is_detected_but_deferred() -> None:
    result = detect_link("https://www.lazada.com.my/products/example.html")

    assert result.platform == Platform.LAZADA
    assert result.is_supported_for_mvp is False


def test_unknown_platform_is_unsupported() -> None:
    result = detect_link("https://example.com/product/1")

    assert result.platform == Platform.UNKNOWN
    assert result.is_supported_for_mvp is False
