from oss_my.emulator.android import _is_physical_phone_serial, _parse_products_from_texts


def test_physical_phone_serial_filter_excludes_emulators() -> None:
    assert not _is_physical_phone_serial("emulator-5554")
    assert not _is_physical_phone_serial("127.0.0.1:5555")
    assert not _is_physical_phone_serial("localhost:5555")
    assert _is_physical_phone_serial("R58M123ABCD")


def test_parse_products_from_visible_texts() -> None:
    products = _parse_products_from_texts(
        "pentel p205",
        "relevancy",
        [
            "Pentel P205 Mechanical Pencil 0.5mm",
            "RM 18.90",
            "1.2k sold",
            "Ships from Selangor",
            "Pentel GraphGear unrelated",
            "RM 29.90",
        ],
    )

    assert len(products) == 2
    assert products[0].title == "Pentel P205 Mechanical Pencil 0.5mm"
    assert products[0].price_label == "RM 18.90"
    assert products[0].shipping_label == "Ships from Selangor"
    assert products[0].stock_label == "1.2k sold"
    assert products[0].result_group == "Most relevant"


def test_parse_shopee_phone_rows_keeps_price_and_rating_separate() -> None:
    products = _parse_products_from_texts(
        "pentel p205",
        "relevancy",
        [
            "Filter",
            "Relevance",
            "!!Pentel Mechanical Pencil 0.3mm.P203 / 0.5mm.P205",
            "RM22.99",
            "RM29.15",
            "-21%",
            "4.9",
            "3k+ sold",
            "Thailand",
            "(KTS) Pentel Mechanical Pencil - P205-A 0.5 Mm. Black Color",
            "RM18.59",
            "5.0",
            "186 sold",
            "Thailand",
        ],
    )

    assert products[0].price_label == "RM22.99"
    assert products[0].rating_label == "4.9"
    assert products[0].stock_label == "3k+ sold"
    assert products[0].shipping_label == "Thailand"
    assert products[1].price_label == "RM18.59"
    assert products[1].rating_label == "5.0"
