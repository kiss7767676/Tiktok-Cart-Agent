from oss_my.research.youtube import youtube_sources_from_html


def test_youtube_sources_extract_real_watch_urls_and_prefer_relevant_views() -> None:
    html = """
    <html><script>
    var ytInitialData = {
      "contents": [
        {"videoRenderer": {
          "videoId": "AAA111BBB22",
          "title": {"runs": [{"text": "Logitech G502 HERO Review and Test"}]},
          "viewCountText": {"simpleText": "1.2M views"},
          "navigationEndpoint": {"commandMetadata": {"webCommandMetadata": {"url": "/watch?v=AAA111BBB22"}}}
        }},
        {"videoRenderer": {
          "videoId": "CCC333DDD44",
          "title": {"runs": [{"text": "Huge gaming setup tour"}]},
          "viewCountText": {"simpleText": "9M views"},
          "navigationEndpoint": {"commandMetadata": {"webCommandMetadata": {"url": "/watch?v=CCC333DDD44"}}}
        }},
        {"videoRenderer": {
          "videoId": "EEE555FFF66",
          "title": {"runs": [{"text": "Logitech G502 vs G502 X Comparison"}]},
          "viewCountText": {"simpleText": "800K views"},
          "navigationEndpoint": {"commandMetadata": {"webCommandMetadata": {"url": "/watch?v=EEE555FFF66"}}}
        }}
      ]
    };
    </script></html>
    """

    sources = youtube_sources_from_html(html, "Logitech G502", limit=2)

    assert [source.url for source in sources] == [
        "https://www.youtube.com/watch?v=AAA111BBB22",
        "https://www.youtube.com/watch?v=EEE555FFF66",
    ]
    assert all(source.source_type == "youtube" for source in sources)


def test_youtube_sources_deduplicate_video_ids() -> None:
    html = """
    <script>
    var ytInitialData = {"contents": [
      {"videoRenderer": {
        "videoId": "AAA111BBB22",
        "title": {"runs": [{"text": "Logitech G502 Review"}]},
        "viewCountText": {"simpleText": "1M views"},
        "navigationEndpoint": {"commandMetadata": {"webCommandMetadata": {"url": "/watch?v=AAA111BBB22"}}}
      }},
      {"videoRenderer": {
        "videoId": "AAA111BBB22",
        "title": {"runs": [{"text": "Logitech G502 Review duplicate"}]},
        "viewCountText": {"simpleText": "900K views"},
        "navigationEndpoint": {"commandMetadata": {"webCommandMetadata": {"url": "/watch?v=AAA111BBB22"}}}
      }}
    ]};
    </script>
    """

    sources = youtube_sources_from_html(html, "Logitech G502", limit=2)

    assert len(sources) == 1
