"""Unit tests for Subject-Weighted Consensus and Empirical Domain Dominance."""

from datetime import datetime, timezone

import pytest

from credence.mesh.consensus import BayesianConsensusAggregator
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding


def _make_mock_attestation(
    node_pubkey: str,
    suspicion_score: float,
    classification: str,
    confidence: float = 0.95,
    is_grounded: bool = True,
) -> AuditReport:
    """Helper to construct synthetic signed AuditReport."""
    findings = (
        [
            SpecialistViolationFinding(
                rule_id="SPJ-1.1",
                rule_uri="journalistic-ethics:seek-truth/SPJ-1.1@v1.0.0",
                domain="JOURNALISTIC_ETHICS",
                cluster_id="accuracy",
                severity=3,
                confidence=0.9,
                quote_or_element="verbatim excerpt",
                reasoning="reasoning",
                is_grounded=is_grounded,
            )
        ]
        if suspicion_score > 0
        else []
    )

    return AuditReport(
        url="https://apiculture-daily.org/protective-suits-test",
        content_sha256="hash_apiculture_test_123",
        simhash_64="aabbccdd11223344",
        suspicion_score=suspicion_score,
        suspicion_density=4.0 if suspicion_score > 0 else 0.0,
        confidence_score=confidence,
        classification=classification,
        is_satire=False,
        content_type="NEWS_ARTICLE",
        violations=findings,
        node_pubkey=node_pubkey,
        node_signature="sig_" + node_pubkey,
        audited_at=datetime.now(timezone.utc),
    )


@pytest.mark.unit
def test_subject_consensus_beekeeper_vs_dogwalker():
    """Verify 2 beekeepers heavily dominate 4 dog walkers on apiary suit evaluation."""
    aggregator = BayesianConsensusAggregator()

    # 2 Expert Beekeeper Nodes: find real safety flaws in bee suit (S = 82.0)
    att_bee1 = _make_mock_attestation("beekeeper_1", 82.0, "DECEPTIVE")
    att_bee2 = _make_mock_attestation("beekeeper_2", 80.0, "DECEPTIVE")

    # 4 Generalist / Dog Walker Nodes: superficially rate it clean (S = 5.0)
    att_dog1 = _make_mock_attestation("dogwalker_1", 5.0, "CLEAN")
    att_dog2 = _make_mock_attestation("dogwalker_2", 6.0, "CLEAN")
    att_dog3 = _make_mock_attestation("dogwalker_3", 4.0, "CLEAN")
    att_dog4 = _make_mock_attestation("dogwalker_4", 5.0, "CLEAN")

    attestations = [att_bee1, att_bee2, att_dog1, att_dog2, att_dog3, att_dog4]

    # Reputations all high (0.95)
    reps = {p.node_pubkey: 0.95 for p in attestations}

    # Domain Expertise in apiculture.equipment:
    # Beekeepers have 0.98 expertise; dog walkers have baseline 0.05
    expertise_map = {
        "beekeeper_1": 0.98,
        "beekeeper_2": 0.96,
        "dogwalker_1": 0.05,
        "dogwalker_2": 0.05,
        "dogwalker_3": 0.05,
        "dogwalker_4": 0.05,
    }

    verdict = aggregator.compute_consensus(
        attestations=attestations,
        node_reputations=reps,
        subject_id="apiculture.equipment",
        subject_expertise_map=expertise_map,
    )

    assert verdict is not None
    assert verdict.subject_id == "apiculture.equipment"

    # Expert score (80-82) should dominate despite being outnumbered 2 to 4!
    assert verdict.consensus_score >= 70.0
    assert verdict.classification == "DECEPTIVE"

    # Beekeeper weights should be ~0.97 while dog walkers are ~0.23
    for pw in verdict.peer_weights:
        if "beekeeper" in pw.node_pubkey:
            assert pw.effective_weight >= 0.90
            assert pw.domain_expertise >= 0.95
        else:
            assert pw.effective_weight <= 0.25
            assert pw.domain_expertise == 0.05


@pytest.mark.unit
def test_subject_consensus_canine_reversal():
    """Verify dog walkers dominate beekeepers on a canine leash review."""
    aggregator = BayesianConsensusAggregator()

    # 2 Beekeepers rate leash as clean (S = 5.0)
    att_bee1 = _make_mock_attestation("beekeeper_1", 5.0, "CLEAN")
    att_bee2 = _make_mock_attestation("beekeeper_2", 6.0, "CLEAN")

    # 4 Dog Walkers detect trachea hazard (S = 75.0)
    att_dog1 = _make_mock_attestation("dogwalker_1", 75.0, "DECEPTIVE")
    att_dog2 = _make_mock_attestation("dogwalker_2", 78.0, "DECEPTIVE")
    att_dog3 = _make_mock_attestation("dogwalker_3", 72.0, "DECEPTIVE")
    att_dog4 = _make_mock_attestation("dogwalker_4", 76.0, "DECEPTIVE")

    attestations = [att_bee1, att_bee2, att_dog1, att_dog2, att_dog3, att_dog4]
    reps = {p.node_pubkey: 0.95 for p in attestations}

    # On veterinary.canine, dog walkers have 0.98 expertise; beekeepers have 0.05
    expertise_map = {
        "beekeeper_1": 0.05,
        "beekeeper_2": 0.05,
        "dogwalker_1": 0.98,
        "dogwalker_2": 0.96,
        "dogwalker_3": 0.95,
        "dogwalker_4": 0.97,
    }

    verdict = aggregator.compute_consensus(
        attestations=attestations,
        node_reputations=reps,
        subject_id="veterinary.canine",
        subject_expertise_map=expertise_map,
    )

    assert verdict is not None
    assert verdict.consensus_score >= 70.0
    assert verdict.classification == "DECEPTIVE"


@pytest.mark.unit
def test_divergence_acceleration_dampening_edge_cases():
    """Verify acceleration dampening handles short windows, exact boundaries, slow drips, negatives, and non-finite inputs."""
    from credence.subjects.expertise import compute_divergence_acceleration_dampening

    # Lengths < 6 always return full 1.0 protection
    assert compute_divergence_acceleration_dampening([]) == 1.0
    assert compute_divergence_acceleration_dampening([0.0, 0.0, 0.0, 80.0, 80.0]) == 1.0

    # Exact boundary: acceleration == 5.0 -> 1.0
    assert compute_divergence_acceleration_dampening([0.0, 0.0, 0.0, 5.0, 5.0, 5.0]) == 1.0

    # Exact midpoint: acceleration == 15.0 -> 0.5
    assert compute_divergence_acceleration_dampening([0.0, 0.0, 0.0, 15.0, 15.0, 15.0]) == 0.5

    # Exact boundary: acceleration == 25.0 -> 0.0
    assert compute_divergence_acceleration_dampening([0.0, 0.0, 0.0, 25.0, 25.0, 25.0]) == 0.0

    # Negative inputs treated as absolute deviations (cannot hide divergence behind negative signs)
    assert compute_divergence_acceleration_dampening([0.0, 0.0, 0.0, -30.0, -30.0, -30.0]) == 0.0

    # Non-finite values fail closed to 0.0 (even when len < 6)
    assert compute_divergence_acceleration_dampening([float("nan"), 10.0, 10.0]) == 0.0
    assert compute_divergence_acceleration_dampening([float("inf")]) == 0.0
    assert compute_divergence_acceleration_dampening([0.0, 0.0, 0.0, float("nan"), 10.0, 10.0]) == 0.0
    assert compute_divergence_acceleration_dampening([0.0, 0.0, 0.0, float("inf"), 10.0, 10.0]) == 0.0

    # Slow-drip linear ramp from 0 to 38 across 20 rounds (older_avg=9, recent_avg=29, accel=20 -> 0.25)
    slow_drip = [float(i * 2) for i in range(20)]
    assert compute_divergence_acceleration_dampening(slow_drip) == 0.25


@pytest.mark.unit
def test_galileo_long_con_attack_detected():
    """Node builds >=0.85 expertise over 30 concordant evals then pivots to 10 divergent grounded evals."""
    from credence.subjects.expertise import (
        DomainMetrics,
        compute_divergence_acceleration_dampening,
        compute_subject_expertise,
    )

    now = datetime.now(timezone.utc)
    first_eval = datetime.fromtimestamp(now.timestamp() - 40 * 86400, tz=timezone.utc)

    # Phase 1: 30 concordant evaluations -> expertise >= 0.85
    concordant_metrics = DomainMetrics(
        evaluations_count=30,
        median_deviations_sum=0.0,
        grounded_quotes_count=60,
        total_quotes_count=60,
        unique_domains_count=6,
        slashing_count=0,
        first_evaluated_at=first_eval,
        last_evaluated_at=now,
        recent_deviations=[0.0] * 20,
    )
    pre_pivot_expertise = compute_subject_expertise(concordant_metrics)
    assert pre_pivot_expertise >= 0.85

    # Phase 2: Pivot to 10 divergent grounded evaluations (score deviation 60.0 each)
    pivoted_recent = [0.0] * 10 + [60.0] * 10
    dampening = compute_divergence_acceleration_dampening(pivoted_recent)
    assert dampening < 0.5

    pivoted_metrics = DomainMetrics(
        evaluations_count=40,
        median_deviations_sum=600.0,
        grounded_quotes_count=80,
        total_quotes_count=80,
        unique_domains_count=6,
        slashing_count=0,
        first_evaluated_at=first_eval,
        last_evaluated_at=now,
        recent_deviations=pivoted_recent,
    )
    post_pivot_expertise = compute_subject_expertise(pivoted_metrics)
    # Without the L52-54 floor, concordance collapses to 0.0 -> E_i = 0.35 + 0.15 + 0.10 = 0.60 < 0.70
    assert post_pivot_expertise < 0.70

    # Mesh consensus must withdraw Galileo immunity and trim the pivoting node as an outlier
    aggregator = BayesianConsensusAggregator(outlier_delta_threshold=25.0)
    honest_1 = _make_mock_attestation("honest_1", 0.0, "CLEAN")
    honest_2 = _make_mock_attestation("honest_2", 2.0, "CLEAN")
    attacker = _make_mock_attestation("attacker", 80.0, "DECEPTIVE", is_grounded=True)

    verdict = aggregator.compute_consensus(
        attestations=[honest_1, honest_2, attacker],
        node_reputations={"honest_1": 0.90, "honest_2": 0.90, "attacker": 0.95},
        subject_id="journalism.news",
        subject_expertise_map={"honest_1": 0.85, "honest_2": 0.85, "attacker": post_pivot_expertise},
        peer_recent_deviations={"attacker": pivoted_recent},
    )
    assert verdict is not None
    assert "attacker" in verdict.outlier_nodes
    assert "attacker" in verdict.galileo_escalated_nodes
    assert verdict.galileo_override is False
    assert verdict.consensus_score <= 15.0
    assert verdict.classification == "CLEAN"


@pytest.mark.unit
def test_galileo_stable_expert_retains_protection():
    """Consistent divergent domain expert (beekeeper) retains dampening == 1.0, floor, and outlier immunity."""
    from credence.subjects.expertise import (
        DomainMetrics,
        compute_divergence_acceleration_dampening,
        compute_subject_expertise,
    )

    now = datetime.now(timezone.utc)
    first_eval = datetime.fromtimestamp(now.timestamp() - 40 * 86400, tz=timezone.utc)
    stable_divergent_history = [70.0] * 20

    dampening = compute_divergence_acceleration_dampening(stable_divergent_history)
    assert dampening == 1.0

    beekeeper_metrics = DomainMetrics(
        evaluations_count=20,
        median_deviations_sum=1400.0,
        grounded_quotes_count=40,
        total_quotes_count=40,
        unique_domains_count=5,
        slashing_count=0,
        first_evaluated_at=first_eval,
        last_evaluated_at=now,
        recent_deviations=stable_divergent_history,
    )
    beekeeper_expertise = compute_subject_expertise(beekeeper_metrics)
    # L52-54 floor preserved: concordance >= 0.70 -> E_i >= 0.40(0.70)+0.35(1.0)+0.15(0.8)+0.10(1.0) = 0.85
    assert beekeeper_expertise >= 0.80

    aggregator = BayesianConsensusAggregator(outlier_delta_threshold=25.0)
    swarm = [_make_mock_attestation(f"dogwalker_{i}", 4.0, "CLEAN") for i in range(6)]
    beekeeper = _make_mock_attestation("beekeeper", 82.0, "DECEPTIVE", is_grounded=True)

    reps = {p.node_pubkey: 0.90 for p in swarm + [beekeeper]}
    exp_map = {p.node_pubkey: 0.05 for p in swarm}
    exp_map["beekeeper"] = beekeeper_expertise

    verdict = aggregator.compute_consensus(
        attestations=swarm + [beekeeper],
        node_reputations=reps,
        subject_id="apiculture.equipment",
        subject_expertise_map=exp_map,
        peer_recent_deviations={"beekeeper": stable_divergent_history},
    )
    assert verdict is not None
    assert "beekeeper" not in verdict.outlier_nodes
    assert verdict.galileo_escalated_nodes == []
    assert verdict.galileo_override is True
    assert verdict.consensus_score >= 70.0
    assert verdict.classification == "DECEPTIVE"


@pytest.mark.asyncio
async def test_galileo_escalation_triggers_slash(db_session, monkeypatch):
    """3 consecutive 0.0 dampening evaluations automatically invoke slash_domain_expertise (-50%)."""
    import json

    from credence.subjects import expertise as expertise_mod
    from credence.subjects.expertise import DomainMetrics, compute_subject_expertise, record_domain_evaluation

    slash_calls: list[tuple[str, str]] = []
    real_slash = expertise_mod.slash_domain_expertise

    async def tracked_slash(session, node_pubkey: str, subject_id: str):
        slash_calls.append((node_pubkey, subject_id))
        return await real_slash(session, node_pubkey, subject_id)

    monkeypatch.setattr(expertise_mod, "slash_domain_expertise", tracked_slash)

    pubkey = "long_con_node_pubkey"
    subject = "journalism.news"

    # Build 25 concordant evaluations (0.0 deviation) with 5 distinct domains
    for i in range(25):
        await record_domain_evaluation(
            session=db_session,
            node_pubkey=pubkey,
            subject_id=subject,
            median_deviation=0.0,
            grounded_quotes=2,
            total_quotes=2,
            origin_fqdn=f"site{i % 5}.example.org",
            unique_domains=5,
        )

    # Pivot sharply to 60.0 deviation until hitting 2 consecutive zero-dampening evals, then trigger the 3rd
    pre_slash_score = None
    post_slash_record = None
    for _ in range(10):
        rec = await record_domain_evaluation(
            session=db_session,
            node_pubkey=pubkey,
            subject_id=subject,
            median_deviation=60.0,
            grounded_quotes=2,
            total_quotes=2,
        )
        if rec.consecutive_zero_dampening == 2 and rec.slashing_count == 0:
            pre_slash_score = rec.expertise_score
        elif rec.slashing_count == 1:
            post_slash_record = rec
            break

    assert pre_slash_score is not None
    assert post_slash_record is not None
    assert slash_calls == [(pubkey, subject)]
    assert post_slash_record.slashing_count == 1
    assert post_slash_record.consecutive_zero_dampening == 0

    unslashed_post_score = compute_subject_expertise(
        DomainMetrics(
            evaluations_count=post_slash_record.evaluations_count,
            median_deviations_sum=post_slash_record.median_deviations_sum,
            grounded_quotes_count=post_slash_record.grounded_quotes_count,
            total_quotes_count=post_slash_record.total_quotes_count,
            unique_domains_count=post_slash_record.unique_domains_count,
            slashing_count=0,
            first_evaluated_at=post_slash_record.first_evaluated_at,
            last_evaluated_at=post_slash_record.last_evaluated_at,
            recent_deviations=json.loads(post_slash_record.recent_deviations_json),
        )
    )
    assert post_slash_record.expertise_score == pytest.approx(unslashed_post_score * 0.5, abs=0.001)
    assert post_slash_record.expertise_score < pre_slash_score * 0.55


@pytest.mark.unit
def test_rolling_window_concordance_detects_drift():
    """100 concordant evals + 20 divergent evals collapses recent_concordance while lifetime stays high."""
    from credence.subjects.expertise import DomainMetrics, compute_subject_expertise

    now = datetime.now(timezone.utc)
    first_eval = datetime.fromtimestamp(now.timestamp() - 40 * 86400, tz=timezone.utc)

    # Use grounding_ratio = 0.80 (< 0.85) so the Galileo floor is inactive and raw_concordance drives E_i directly
    # Lifetime avg deviation = (100*0 + 20*30) / 120 = 5.0 -> lifetime_concordance = 0.80
    # Recent avg deviation = 30.0 -> recent_concordance = 0.0 -> min(0.80, 0.0) = 0.0
    drifted_metrics = DomainMetrics(
        evaluations_count=120,
        median_deviations_sum=600.0,
        grounded_quotes_count=96,
        total_quotes_count=120,
        unique_domains_count=5,
        slashing_count=0,
        first_evaluated_at=first_eval,
        last_evaluated_at=now,
        recent_deviations=[30.0] * 20,
    )
    drifted_score = compute_subject_expertise(drifted_metrics)
    # Expected if raw_concordance == 0.0: 0.40(0.0) + 0.35(0.80) + 0.15(1.0) + 0.10(1.0) = 0.53
    # (Whereas lifetime concordance 0.80 would give 0.40(0.80) + 0.53 = 0.85)
    assert drifted_score == pytest.approx(0.53, abs=0.01)


@pytest.mark.unit
def test_galileo_anchor_activates_for_low_non_zero_silent_swarm():
    """Galileo anchor activates when swarm scores <= 15.0 (CLEAN) and sets galileo_override=True."""
    aggregator = BayesianConsensusAggregator(outlier_delta_threshold=25.0)
    swarm = [_make_mock_attestation(f"gen_{i}", 5.0, "CLEAN") for i in range(6)]
    specialist = _make_mock_attestation("specialist", 75.0, "DECEPTIVE", is_grounded=True)

    reps = {p.node_pubkey: 0.90 for p in swarm + [specialist]}
    exp_map = {p.node_pubkey: 0.05 for p in swarm}
    exp_map["specialist"] = 0.95

    verdict = aggregator.compute_consensus(
        attestations=swarm + [specialist],
        node_reputations=reps,
        subject_id="apiculture.equipment",
        subject_expertise_map=exp_map,
    )
    assert verdict is not None
    assert verdict.galileo_override is True
    assert verdict.consensus_score == 75.0
    assert verdict.classification == "DECEPTIVE"


@pytest.mark.unit
def test_compute_consensus_backward_compatibility():
    """Calling compute_consensus without peer_recent_deviations preserves legacy signature and defaults."""
    aggregator = BayesianConsensusAggregator()
    r1 = _make_mock_attestation("node_1", 20.0, "LOW_SUSPICION")
    r2 = _make_mock_attestation("node_2", 25.0, "LOW_SUSPICION")

    verdict = aggregator.compute_consensus([r1, r2], node_reputations={"node_1": 0.8, "node_2": 0.8})
    assert verdict is not None
    assert verdict.galileo_override is False
    assert verdict.galileo_escalated_nodes == []
    assert all(pw.galileo_dampening == 1.0 and pw.galileo_escalation is False for pw in verdict.peer_weights)


@pytest.mark.asyncio
async def test_additive_sqlite_migration_domainmetric_and_workerrecord(tmp_path):
    """init_db() safely and idempotently adds Plan 2 columns to pre-existing SQLite tables."""
    from sqlalchemy.ext.asyncio import create_async_engine

    from credence.db import init_db

    db_file = tmp_path / "legacy_galileo.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}", future=True)

    # Create legacy schema missing the new Plan 2 columns
    async with engine.begin() as conn:
        await conn.exec_driver_sql(
            """
            CREATE TABLE domainmetric (
                id INTEGER PRIMARY KEY,
                node_pubkey VARCHAR NOT NULL,
                subject_id VARCHAR NOT NULL,
                evaluations_count INTEGER DEFAULT 0,
                median_deviations_sum REAL DEFAULT 0.0,
                grounded_quotes_count INTEGER DEFAULT 0,
                total_quotes_count INTEGER DEFAULT 0,
                unique_domains_count INTEGER DEFAULT 1,
                slashing_count INTEGER DEFAULT 0,
                expertise_score REAL DEFAULT 0.05,
                first_evaluated_at DATETIME NOT NULL,
                last_evaluated_at DATETIME NOT NULL
            );
            """
        )
        await conn.exec_driver_sql(
            """
            INSERT INTO domainmetric (
                node_pubkey, subject_id, evaluations_count, first_evaluated_at, last_evaluated_at
            ) VALUES ('pk_1', 'apiculture', 5, '2026-01-01 00:00:00', '2026-01-02 00:00:00');
            """
        )
        await conn.exec_driver_sql(
            """
            CREATE TABLE workerrecord (
                id INTEGER PRIMARY KEY,
                worker_pubkey VARCHAR NOT NULL UNIQUE,
                worker_alias VARCHAR DEFAULT 'volunteer-worker',
                model_family VARCHAR DEFAULT 'general',
                model_slug VARCHAR DEFAULT 'google/gemini-3.8-flash',
                total_completed INTEGER DEFAULT 0,
                tokens_donated INTEGER DEFAULT 0,
                bounties_cleared INTEGER DEFAULT 0,
                consensus_anchors_count INTEGER DEFAULT 0,
                grounded_violations_count INTEGER DEFAULT 0,
                quality_score REAL DEFAULT 0.50,
                first_seen DATETIME NOT NULL,
                last_seen DATETIME NOT NULL,
                badges_unlocked_json VARCHAR DEFAULT '[]'
            );
            """
        )
        await conn.exec_driver_sql(
            """
            INSERT INTO workerrecord (
                worker_pubkey, first_seen, last_seen
            ) VALUES ('wrk_1', '2026-01-01 00:00:00', '2026-01-02 00:00:00');
            """
        )

    # Run init_db twice to verify idempotency and existing row preservation
    await init_db(engine)
    await init_db(engine)

    async with engine.connect() as conn:
        dm_cols = [row[1] for row in (await conn.exec_driver_sql("PRAGMA table_info(domainmetric);")).fetchall()]
        assert "recent_deviations_json" in dm_cols
        assert "consecutive_zero_dampening" in dm_cols

        dm_row = (
            await conn.exec_driver_sql(
                "SELECT recent_deviations_json, consecutive_zero_dampening FROM domainmetric WHERE node_pubkey='pk_1';"
            )
        ).fetchone()
        assert dm_row == ("[]", 0)

        wrk_cols = [row[1] for row in (await conn.exec_driver_sql("PRAGMA table_info(workerrecord);")).fetchall()]
        assert "recent_deviations_json" in wrk_cols
        assert "consensus_evaluations_count" in wrk_cols
        assert "median_deviations_sum" in wrk_cols
        assert "divergence_slashes_count" in wrk_cols
        assert "consecutive_zero_dampening" in wrk_cols

        wrk_row = (
            await conn.exec_driver_sql(
                "SELECT recent_deviations_json, consensus_evaluations_count, median_deviations_sum, "
                "divergence_slashes_count, consecutive_zero_dampening "
                "FROM workerrecord WHERE worker_pubkey='wrk_1';"
            )
        ).fetchone()
        assert wrk_row == ("[]", 0, 0.0, 0, 0)

    await engine.dispose()


@pytest.mark.unit
def test_zero_reputation_worker_cannot_hijack_galileo_with_full_confidence():
    """Zero-reputation (Q_w=0.50) worker with confidence=1.0 cannot trigger Galileo immunity or anchor."""
    aggregator = BayesianConsensusAggregator(outlier_delta_threshold=25.0)
    honest_1 = _make_mock_attestation("honest_1", 0.0, "CLEAN", confidence=0.90)
    honest_2 = _make_mock_attestation("honest_2", 0.0, "CLEAN", confidence=0.90)
    attacker = _make_mock_attestation("attacker", 95.0, "DECEPTIVE", confidence=1.0, is_grounded=True)

    verdict = aggregator.compute_consensus(
        attestations=[honest_1, honest_2, attacker],
        node_reputations={"honest_1": 0.50, "honest_2": 0.50, "attacker": 0.50},
    )
    assert verdict is not None
    assert "attacker" in verdict.outlier_nodes
    assert verdict.galileo_override is False
    assert verdict.consensus_score == 0.0
    assert verdict.classification == "CLEAN"

    # Established worker (Q_w=0.75, confidence=0.90) legitimately retains Galileo anchor without subject_id
    legit_verdict = aggregator.compute_consensus(
        attestations=[honest_1, honest_2, attacker],
        node_reputations={"honest_1": 0.50, "honest_2": 0.50, "attacker": 0.75},
    )
    assert legit_verdict is not None
    assert "attacker" not in legit_verdict.outlier_nodes
    assert legit_verdict.galileo_override is True
    assert legit_verdict.consensus_score == 95.0


@pytest.mark.unit
def test_pivoting_heavy_authority_cannot_capture_initial_median():
    """Pivoting authority (dampening <= 0.5) has weight scaled before median so it cannot trim honest peers."""
    aggregator = BayesianConsensusAggregator(outlier_delta_threshold=25.0)
    honest = [_make_mock_attestation(f"gen_{i}", 0.0, "CLEAN", confidence=0.95) for i in range(3)]
    attacker = _make_mock_attestation("attacker", 80.0, "DECEPTIVE", confidence=0.95, is_grounded=True)

    # Attacker pre-dampening weight (0.817) > sum of 3 honest generalists (0.209 * 3 = 0.627)
    verdict = aggregator.compute_consensus(
        attestations=honest + [attacker],
        node_reputations={"gen_0": 0.90, "gen_1": 0.90, "gen_2": 0.90, "attacker": 0.90},
        subject_id="journalism.news",
        subject_expertise_map={"gen_0": 0.05, "gen_1": 0.05, "gen_2": 0.05, "attacker": 0.85},
        peer_recent_deviations={"attacker": [0.0] * 10 + [80.0] * 10},
    )
    assert verdict is not None
    assert "attacker" in verdict.outlier_nodes
    assert all(f"gen_{i}" not in verdict.outlier_nodes for i in range(3))
    assert "attacker" in verdict.galileo_escalated_nodes
    assert verdict.galileo_override is False
    assert verdict.consensus_score == 0.0
    assert verdict.classification == "CLEAN"

    # Boundary check: exact dampening == 0.50 against 2 honest generalists still cannot hijack median
    boundary_verdict = aggregator.compute_consensus(
        attestations=honest[:2] + [attacker],
        node_reputations={"gen_0": 0.90, "gen_1": 0.90, "attacker": 0.95},
        subject_id="journalism.news",
        subject_expertise_map={"gen_0": 0.05, "gen_1": 0.05, "attacker": 0.95},
        peer_recent_deviations={"attacker": [0.0] * 10 + [15.0] * 10},
    )
    assert boundary_verdict is not None
    assert "attacker" in boundary_verdict.outlier_nodes
    assert boundary_verdict.galileo_override is False
    assert boundary_verdict.consensus_score == 0.0


@pytest.mark.asyncio
async def test_post_migration_cold_start_pivot_detected_and_slashed(db_session):
    """Legacy v1->v2 migrated concordant node pivoting immediately to 80.0 is caught and slashed."""
    from credence.models import DomainMetric
    from credence.subjects.expertise import record_domain_evaluation

    now = datetime.now(timezone.utc)
    first_eval = datetime.fromtimestamp(now.timestamp() - 40 * 86400, tz=timezone.utc)

    # Simulate legacy migrated row: 30 concordant evaluations, empty recent_deviations_json
    legacy = DomainMetric(
        node_pubkey="migrated_con_node",
        subject_id="journalism.news",
        evaluations_count=30,
        median_deviations_sum=0.0,
        grounded_quotes_count=60,
        total_quotes_count=60,
        unique_domains_count=5,
        slashing_count=0,
        expertise_score=1.0,
        recent_deviations_json="[]",
        consecutive_zero_dampening=0,
        first_evaluated_at=first_eval,
        last_evaluated_at=now,
    )
    db_session.add(legacy)
    await db_session.commit()

    latest = None
    for _ in range(10):
        latest = await record_domain_evaluation(
            session=db_session,
            node_pubkey="migrated_con_node",
            subject_id="journalism.news",
            median_deviation=80.0,
            grounded_quotes=2,
            total_quotes=2,
        )

    assert latest is not None
    assert latest.slashing_count >= 1
    assert latest.expertise_score < 0.70


@pytest.mark.asyncio
async def test_slow_drip_and_alternating_pivots_caught_by_baseline(db_session):
    """Slow-drip +0.5/eval and [0, 80] alternation after concordant history are caught while stable experts stay 1.0."""
    from credence.subjects.expertise import (
        DomainMetrics,
        compute_divergence_acceleration_dampening,
        compute_subject_expertise,
        record_domain_evaluation,
    )

    now = datetime.now(timezone.utc)
    first_eval = datetime.fromtimestamp(now.timestamp() - 40 * 86400, tz=timezone.utc)

    # 1. Stable high-deviation expert (40 evals at 70.0) retains dampening == 1.0
    stable_metrics = DomainMetrics(
        evaluations_count=40,
        median_deviations_sum=2800.0,
        grounded_quotes_count=80,
        total_quotes_count=80,
        unique_domains_count=5,
        slashing_count=0,
        first_evaluated_at=first_eval,
        last_evaluated_at=now,
        recent_deviations=[70.0] * 20,
    )
    assert compute_subject_expertise(stable_metrics) >= 0.85
    assert compute_divergence_acceleration_dampening([70.0] * 20, baseline_deviation=70.0) == 1.0

    # 2. Slow-drip (+0.5/eval) after 30 concordant evals drops below 0.70 and eventually triggers slash
    drip_node = "slow_drip_attacker"
    for _ in range(30):
        await record_domain_evaluation(
            session=db_session,
            node_pubkey=drip_node,
            subject_id="journalism.news",
            median_deviation=0.0,
            grounded_quotes=2,
            total_quotes=2,
            unique_domains=5,
        )
    drip_rec = None
    for step in range(1, 75):
        drip_rec = await record_domain_evaluation(
            session=db_session,
            node_pubkey=drip_node,
            subject_id="journalism.news",
            median_deviation=step * 0.5,
            grounded_quotes=2,
            total_quotes=2,
        )
    assert drip_rec is not None
    assert drip_rec.slashing_count >= 1
    assert drip_rec.expertise_score < 0.70

    # 3. Alternating [0, 80] oscillation after 30 concordant evals triggers slash
    alt_node = "alternating_attacker"
    for _ in range(30):
        await record_domain_evaluation(
            session=db_session,
            node_pubkey=alt_node,
            subject_id="journalism.news",
            median_deviation=0.0,
            grounded_quotes=2,
            total_quotes=2,
            unique_domains=5,
        )
    alt_rec = None
    for step in range(20):
        alt_rec = await record_domain_evaluation(
            session=db_session,
            node_pubkey=alt_node,
            subject_id="journalism.news",
            median_deviation=80.0 if step % 2 == 0 else 0.0,
            grounded_quotes=2,
            total_quotes=2,
        )
    assert alt_rec is not None
    assert alt_rec.slashing_count >= 1
    assert alt_rec.expertise_score < 0.70
