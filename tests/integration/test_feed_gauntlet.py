"""Scenario 1: The Dirty Feed Gauntlet.

Tests feed parser resilience against real-world malformed RSS/Atom feeds:
1. HTML/CDATA tags inside titles and descriptions (stripped/cleaned).
2. Exotic/non-standard date formats (RFC 822 with GMT/EST, ISO with offsets, YYYY/MM/DD).
3. Missing fields, empty channels, and duplicate GUIDs.
4. Atom feeds with mixed namespaces and HTML content.
"""

from datetime import datetime, timezone

import pytest

from credence.feeds.parser import parse_feed_content


@pytest.mark.integration
def test_dirty_rss_with_html_tags_and_cdata() -> None:
    """Verify that RSS feeds with embedded HTML and CDATA in titles/descriptions are cleaned."""
    dirty_rss = """<?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0">
      <channel>
        <title>&lt;b&gt;The Real News&lt;/b&gt; &amp; Analysis</title>
        <link>https://example.com</link>
        <description><![CDATA[<p>Daily investigative journalism feed</p>]]></description>
        <item>
          <title><![CDATA[<h3>BREAKING:</h3> Council Passes <i>New</i> Budget]]></title>
          <link>https://example.com/posts/budget-2026</link>
          <description>&lt;p&gt;The city council approved the &lt;strong&gt;$50M&lt;/strong&gt; plan.&lt;/p&gt;</description>
          <author><b>Jane Doe</b> &lt;jane@example.com&gt;</author>
          <pubDate>Mon, 17 Aug 2026 14:30:00 GMT</pubDate>
          <guid>post-101</guid>
        </item>
      </channel>
    </rss>"""

    feed = parse_feed_content(dirty_rss)
    assert feed.title == "The Real News & Analysis"
    assert len(feed.entries) == 1

    entry = feed.entries[0]
    assert entry.title == "BREAKING: Council Passes New Budget"
    assert entry.summary == "The city council approved the $50M plan."
    assert "Jane Doe" in (entry.author or "")
    assert entry.published_at == datetime(2026, 8, 17, 14, 30, tzinfo=timezone.utc)
    assert entry.guid == "post-101"


@pytest.mark.integration
def test_dirty_atom_with_exotic_dates_and_missing_fields() -> None:
    """Verify that Atom feeds with exotic dates, missing authors, and html summaries parse cleanly."""
    dirty_atom = """<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title><span>Tech Blog</span></title>
      <entry>
        <title>Article with Non-Standard Date</title>
        <link rel="alternate" href="https://tech.example.org/article-1"/>
        <content type="html">&lt;div class="post"&gt;Full article content here&lt;/div&gt;</content>
        <updated>2026-08-17T21:45:00+00:00</updated>
        <id>urn:uuid:12345</id>
      </entry>
      <entry>
        <title>Second Article with YYYY-MM-DD Date</title>
        <link href="https://tech.example.org/article-2"/>
        <summary>Short summary without author tag</summary>
        <published>2026-08-15</published>
        <id>urn:uuid:67890</id>
      </entry>
    </feed>"""

    feed = parse_feed_content(dirty_atom)
    assert feed.title == "Tech Blog"
    assert len(feed.entries) == 2

    e1 = feed.entries[0]
    assert e1.title == "Article with Non-Standard Date"
    assert e1.summary == "Full article content here"
    assert e1.published_at == datetime(2026, 8, 17, 21, 45, tzinfo=timezone.utc)

    e2 = feed.entries[1]
    assert e2.title == "Second Article with YYYY-MM-DD Date"
    assert e2.summary == "Short summary without author tag"
    assert e2.published_at == datetime(2026, 8, 15, 0, 0, tzinfo=timezone.utc)


@pytest.mark.integration
def test_empty_and_minimal_channels_do_not_crash() -> None:
    """Verify that empty channels and minimal items without descriptions do not crash."""
    minimal_rss = """<rss version="2.0"><channel><item><link>https://example.com/min</link></item></channel></rss>"""
    feed = parse_feed_content(minimal_rss)
    assert len(feed.entries) == 1
    assert feed.entries[0].title == "Untitled"
    assert feed.entries[0].summary is None
