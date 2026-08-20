"""Unit tests for Syndicated Feed Parsing and HTTP Conditional Caching."""

import pytest

from credence.feeds.parser import (
    parse_feed_content,
)

SAMPLE_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Global Wire News</title>
    <link>https://globalwire.org</link>
    <description>Top breaking world news</description>
    <item>
      <title>Autonomous Mesh Epistemics Launch Worldwide</title>
      <link>https://globalwire.org/2026/08/epistemic-mesh-launch</link>
      <description>Decentralized nodes coordinate trust verification across 4 canonical domains.</description>
      <author>Jane Doe</author>
      <pubDate>Mon, 17 Aug 2026 12:00:00 GMT</pubDate>
      <guid>https://globalwire.org/2026/08/epistemic-mesh-launch</guid>
    </item>
    <item>
      <title>Apiculture Researchers Unveil Ultra-Sting Bee Suit</title>
      <link>https://globalwire.org/2026/08/apiculture-bee-suit</link>
      <description>Triple-layer brass mesh veil resists aggressive honeybee hive inspections.</description>
      <pubDate>Mon, 17 Aug 2026 10:30:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

SAMPLE_ATOM_XML = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Independent Science Review</title>
  <link href="https://sciencereview.org/feed" rel="self"/>
  <updated>2026-08-17T12:00:00Z</updated>
  <entry>
    <title>Randomized Trial of Immunotherapy in Oncology</title>
    <link href="https://sciencereview.org/articles/oncology-rct-2026" rel="alternate"/>
    <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
    <published>2026-08-17T11:00:00Z</published>
    <summary>Phase 3 double-blind randomized clinical trial of 500 patients.</summary>
    <author><name>Dr. Emily Stone</name></author>
  </entry>
</feed>
"""

SAMPLE_JSON_FEED = """{
  "version": "https://jsonfeed.org/version/1.1",
  "title": "Tech Dispatch",
  "home_page_url": "https://techdispatch.io",
  "items": [
    {
      "id": "https://techdispatch.io/posts/mesh-gossip-scaling",
      "url": "https://techdispatch.io/posts/mesh-gossip-scaling",
      "title": "Scaling Watts-Strogatz Gossip to 13 Nodes",
      "content_text": "How epidemic routing achieves sub-5s consensus.",
      "date_published": "2026-08-17T09:00:00Z"
    }
  ]
}"""


@pytest.mark.unit
def test_parse_rss_feed():
    """Verify RSS 2.0 parsing extracts items, dates, and links."""
    parsed = parse_feed_content(SAMPLE_RSS_XML)

    assert parsed.feed_format == "rss"
    assert parsed.title == "Global Wire News"
    assert len(parsed.entries) == 2

    e1 = parsed.entries[0]
    assert e1.title == "Autonomous Mesh Epistemics Launch Worldwide"
    assert e1.url == "https://globalwire.org/2026/08/epistemic-mesh-launch"
    assert e1.author == "Jane Doe"
    assert e1.published_at is not None
    assert e1.published_at.year == 2026


@pytest.mark.unit
def test_parse_atom_feed():
    """Verify Atom 1.0 XML parsing extracts entries and links."""
    parsed = parse_feed_content(SAMPLE_ATOM_XML)

    assert parsed.feed_format == "atom"
    assert parsed.title == "Independent Science Review"
    assert len(parsed.entries) == 1

    e1 = parsed.entries[0]
    assert e1.title == "Randomized Trial of Immunotherapy in Oncology"
    assert e1.url == "https://sciencereview.org/articles/oncology-rct-2026"
    assert e1.author == "Dr. Emily Stone"
    assert e1.published_at is not None


@pytest.mark.unit
def test_parse_json_feed():
    """Verify JSON Feed 1.1 parsing extracts items."""
    parsed = parse_feed_content(SAMPLE_JSON_FEED)

    assert parsed.feed_format == "json"
    assert parsed.title == "Tech Dispatch"
    assert len(parsed.entries) == 1

    e1 = parsed.entries[0]
    assert e1.title == "Scaling Watts-Strogatz Gossip to 13 Nodes"
    assert e1.url == "https://techdispatch.io/posts/mesh-gossip-scaling"
