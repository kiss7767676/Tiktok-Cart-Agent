from bs4 import BeautifulSoup

from oss_my.research.google import _extract_ai_overview, _extract_organic_sources


def test_extract_ai_overview_from_marker_text() -> None:
    soup = BeautifulSoup(
        "<html><body><div>AI Overview This product is often reviewed for battery life and warranty. "
        "Check seller reputation before buying.</div></body></html>",
        "html.parser",
    )

    overview = _extract_ai_overview(soup)

    assert overview is not None
    assert "battery life" in overview


def test_extract_organic_sources() -> None:
    soup = BeautifulSoup(
        """
        <html><body>
          <a href="https://example.com/review"><h3>Product Review</h3></a>
          <div>Snippet text about product quality.</div>
        </body></html>
        """,
        "html.parser",
    )

    sources = _extract_organic_sources(soup)

    assert len(sources) == 1
    assert sources[0].title == "Product Review"
    assert sources[0].url == "https://example.com/review"
