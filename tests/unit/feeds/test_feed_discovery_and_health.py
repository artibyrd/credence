"""Hermetic Unit Tests for Feed Autodiscovery, Topic Entropy & Dynamic Health Governance."""

from datetime import datetime, timezone

from credence.feeds.discovery import (
    extract_feeds_from_html,
)
from credence.feeds.health import (
    compute_feed_quality_score,
    compute_topic_entropy,
)
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding


def test_html_feed_autodiscovery_rss_and_atom():
    """Verify HTML parser extracts RSS 2.0, Atom, and JSON feed <link> tags accurately."""
    mock_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Independent Journalism Watch</title>
        <link rel="alternate" type="application/rss+xml" title="Main RSS Feed" href="/rss.xml" />
        <link rel="alternate" type="application/atom+xml" title="Atom 1.0 Feed" href="https://example.org/atom.xml" />
        <link rel="alternate" type="application/feed+json" title="JSON Feed" href="/feed.json" />
        <link rel="stylesheet" href="/style.css" />
    </head>
    <body>
        <h1>Welcome</h1>
    </body>
    </html>
    """
    candidates = extract_feeds_from_html(mock_html, "https://example.org/news")
    assert len(candidates) == 3

    rss_cand = next(c for c in candidates if c.feed_type == "rss")
    assert rss_cand.feed_url == "https://example.org/rss.xml"
    assert rss_cand.title == "Main RSS Feed"

    atom_cand = next(c for c in candidates if c.feed_type == "atom")
    assert atom_cand.feed_url == "https://example.org/atom.xml"
    assert atom_cand.title == "Atom 1.0 Feed"

    json_cand = next(c for c in candidates if c.feed_type == "json_feed")
    assert json_cand.feed_url == "https://example.org/feed.json"


def test_topic_entropy_diverse_vs_commercial_astroturfing():
    """Verify Topic Entropy (H_topic) detects commercial takeover / astroturfing (The 'Pizza Hut Test')."""
    # Case A: Healthy Diverse Journalistic Coverage
    diverse_articles = [
        "Federal regulators approved new safety standards for autonomous heavy freight trucks following a two-year pilot.",
        "Astronomers identified an unexpected spectroscopic signature in exoplanet atmospheric transmission data.",
        "Municipal water district votes to allocate funding for reverse osmosis filtration upgrade in East Bay.",
        "Supreme Court hears oral arguments in landmark digital privacy case concerning cross-border server seizures.",
        "Labor department releases quarterly employment figures showing slight moderation in wage growth.",
    ]
    h_diverse = compute_topic_entropy(diverse_articles)
    assert h_diverse >= 0.70, f"Diverse journalistic coverage should have high topic entropy, got {h_diverse}"

    # Case B: The 'Pizza Hut Problem' - Sudden single-topic commercial clustering
    astroturfed_articles = [
        "Try the new stuffed crust pizza deal today at discount pizza hut location with coupon code save big on pepperoni pizza.",
        "Best pizza delivery deals for friday night order your favorite hot cheese pizza with breadsticks and pizza soda combo.",
        "Delicious pan pizza recipe copycat review how to make the ultimate cheesy pizza with special pizza sauce.",
        "Top ten pizza toppings ranked why pepperoni pizza and sausage pizza remain the king of delivery pizza meals.",
        "Special lunch buffet return pizza lovers rejoice with unlimited slices of deep dish pizza and personal pizza pies.",
    ]
    h_astroturfed = compute_topic_entropy(astroturfed_articles)
    assert h_astroturfed < 0.65, (
        f"Single-topic promotional clustering should produce lower entropy, got {h_astroturfed}"
    )
    assert h_diverse > h_astroturfed, (
        "Diverse editorial coverage must have higher entropy than commercial repetitive text"
    )


def test_feed_quality_score_composite_math():
    """Verify the 4-factor F_j composite metric and status classification thresholds."""
    now = datetime.now(timezone.utc)

    # Clean, grounded reports
    clean_report = AuditReport(
        url="https://example.org/a1",
        content_sha256="sha256:clean1",
        simhash_64="0x1111",
        suspicion_score=5.0,
        suspicion_density=0.0,
        classification="CLEAN",
        is_satire=False,
        violations=[],
        taxonomies_used={},
    )
    metrics_clean = compute_feed_quality_score([clean_report], published_dates=[now], now=now)
    assert metrics_clean.composite_score_fj >= 0.70
    assert metrics_clean.status == "ACTIVE"

    # Highly deceptive / compromised outlet
    deceptive_report = AuditReport(
        url="https://example.org/d1",
        content_sha256="sha256:deceptive1",
        simhash_64="0x2222",
        suspicion_score=85.0,
        suspicion_density=12.5,
        classification="DECEPTIVE",
        is_satire=False,
        violations=[
            SpecialistViolationFinding(
                rule_id="SPJ-1.1",
                rule_uri="ethics:accuracy/unverified_allegation@v1",
                domain="JOURNALISTIC_ETHICS",
                cluster_id="accuracy",
                severity=5,
                confidence=0.95,
                quote_or_element="Unverified defamatory conspiracy",
                reasoning="Fabricated claims without evidence",
                is_grounded=False,
            )
        ],
        taxonomies_used={},
    )
    metrics_deceptive = compute_feed_quality_score([deceptive_report], published_dates=[now], now=now)
    assert metrics_deceptive.composite_score_fj < 0.50
    assert metrics_deceptive.status in ("PROBATION", "QUARANTINE")


def test_feed_quality_score_with_article_texts():
    """Verify compute_feed_quality_score incorporates supplied article_texts for topic entropy."""
    now = datetime.now(timezone.utc)
    report = AuditReport(
        url="https://example.org/news/1",
        content_sha256="sha256:art1",
        simhash_64="0x3333",
        suspicion_score=10.0,
        suspicion_density=0.0,
        classification="CLEAN",
        is_satire=False,
        violations=[],
        taxonomies_used={},
    )
    texts = [
        "Major breakthroughs in quantum computing architecture reported by university researchers.",
        "Renewable energy storage capacity expands across rural cooperative grids this quarter.",
    ]
    metrics = compute_feed_quality_score([report], published_dates=[now], now=now, article_texts=texts)
    assert metrics.topic_entropy > 0.0
    assert metrics.composite_score_fj > 0.60
