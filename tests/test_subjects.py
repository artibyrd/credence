"""Unit tests for Credence Subject Registry and Empirical Domain Expertise Engine."""

from datetime import datetime, timezone

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.subjects.expertise import (
    DomainMetrics,
    calculate_effective_weight,
    calculate_subject_expertise,
    get_node_subject_expertise,
    record_domain_evaluation,
    slash_domain_expertise,
)
from credence.subjects.registry import (
    classify_subject,
    get_subject_registry,
)


@pytest.mark.unit
def test_subject_registry_catalogs_loading():
    """Verify built-in subject catalogs are loaded with hierarchy."""
    registry = get_subject_registry()
    subjects = registry.list_subjects()

    assert len(subjects) >= 4
    subject_ids = {s.subject_id for s in subjects}

    assert "apiculture" in subject_ids
    assert "apiculture.equipment" in subject_ids
    assert "veterinary.canine" in subject_ids
    assert "scientific.clinical" in subject_ids
    assert "journalism.news" in subject_ids

    # Check hierarchy
    apiculture_equip = registry.get_subject("apiculture.equipment")
    assert apiculture_equip is not None
    assert apiculture_equip.parent_id == "apiculture"

    tree = registry.get_hierarchy_tree()
    assert len(tree) >= 4
    root_ids = {node["subject_id"] for node in tree}
    assert "apiculture" in root_ids


@pytest.mark.unit
def test_semantic_subject_classification():
    """Verify topic text classification maps to correct subject namespaces."""
    # 1. Beekeeping / Apiary article
    beekeeper_text = (
        "The new ultra-ventilated bee suit offers maximum sting resistance with a brass zipper "
        "and reinforced veil for working aggressive honeybee hives and queen inspection."
    )
    subj, conf = classify_subject(beekeeper_text)
    assert subj in ("apiculture", "apiculture.equipment")
    assert conf >= 0.50

    # 2. Canine veterinary article
    canine_text = (
        "Selecting the right harness and leash for puppy behavioral training prevents tracheal damage "
        "and improves obedience in young canines."
    )
    subj, conf = classify_subject(canine_text)
    assert "veterinary.canine" in subj
    assert conf >= 0.50

    # 3. Clinical trial / Oncology article
    clinical_text = (
        "A double-blind randomized controlled trial of 450 oncology patients evaluated the therapeutic "
        "efficacy and p-value statistical significance of the novel immunotherapy."
    )
    subj, conf = classify_subject(clinical_text, schema_types=["ScholarlyArticle"])
    assert "scientific.clinical" in subj
    assert conf >= 0.60


@pytest.mark.unit
def test_empirical_expertise_mathematical_formula():
    """Verify 4-factor empirical expertise equation without diplomas."""
    # 1. Zero evaluations -> baseline 0.05
    empty_metrics = DomainMetrics(evaluations_count=0)
    assert calculate_subject_expertise(empty_metrics) == 0.05

    # 2. Flawless 25 evaluations with high concordance and grounding
    now = datetime.now(timezone.utc)
    expert_metrics = DomainMetrics(
        evaluations_count=25,
        median_deviations_sum=0.0,  # 0 deviation -> concordance = 1.0
        grounded_quotes_count=50,
        total_quotes_count=50,  # 100% grounding -> 1.0
        slashing_count=0,
        first_evaluated_at=datetime.fromtimestamp(now.timestamp() - 35 * 86400, tz=timezone.utc),
        last_evaluated_at=now,  # 35 days -> longevity = 1.0
    )
    # Expected: 0.40(1.0) + 0.35(1.0) + 0.15(1.0) + 0.10(1.0) = 1.0
    assert calculate_subject_expertise(expert_metrics) == 1.0

    # 3. Partial experience node (5 evals)
    partial_metrics = DomainMetrics(
        evaluations_count=5,
        median_deviations_sum=10.0,
        grounded_quotes_count=8,
        total_quotes_count=10,
        slashing_count=0,
    )
    partial_score = calculate_subject_expertise(partial_metrics)
    assert 0.30 <= partial_score <= 0.70

    # 4. Slashing penalty: 1 slash cuts score by 50%
    expert_slashed_1 = DomainMetrics(
        evaluations_count=25,
        median_deviations_sum=0.0,
        grounded_quotes_count=50,
        total_quotes_count=50,
        slashing_count=1,
        first_evaluated_at=datetime.fromtimestamp(now.timestamp() - 35 * 86400, tz=timezone.utc),
        last_evaluated_at=now,
    )
    assert calculate_subject_expertise(expert_slashed_1) == pytest.approx(0.50, rel=0.05)


@pytest.mark.unit
def test_effective_authority_weight_beekeeper_vs_dogwalker():
    """Verify subject-weighted authority weight formula W_i(subject)."""
    # Beekeeper evaluating apiary equipment
    beekeeper_weight = calculate_effective_weight(
        node_pubkey="beekeeper_node",
        subject_id="apiculture.equipment",
        base_quality=0.95,
        expertise_score=0.98,
    )
    # W = 0.20 * 0.95 + 0.80 * 0.98 = 0.19 + 0.784 = 0.974
    assert beekeeper_weight == pytest.approx(0.974, rel=0.01)

    # Dog walker evaluating apiary equipment (unproven in apiculture)
    dogwalker_weight = calculate_effective_weight(
        node_pubkey="dogwalker_node",
        subject_id="apiculture.equipment",
        base_quality=0.95,
        expertise_score=0.05,
    )
    # W = 0.20 * 0.95 + 0.80 * 0.05 = 0.19 + 0.04 = 0.23
    assert dogwalker_weight == pytest.approx(0.23, rel=0.01)

    # Reversal: On canine care, dog walker has high weight
    dogwalker_canine_weight = calculate_effective_weight(
        node_pubkey="dogwalker_node",
        subject_id="veterinary.canine",
        base_quality=0.95,
        expertise_score=0.96,
    )
    assert dogwalker_canine_weight >= 0.95


@pytest.mark.asyncio
async def test_domain_metrics_database_record_and_slashing(db_session: AsyncSession):
    """Verify recording audits in SQLite and executing domain slashing."""
    pubkey = "test_beekeeper_pubkey_123"
    subject = "apiculture.equipment"

    # 1. Record first evaluation
    rec1 = await record_domain_evaluation(
        session=db_session,
        node_pubkey=pubkey,
        subject_id=subject,
        median_deviation=1.5,
        grounded_quotes=5,
        total_quotes=5,
    )
    assert rec1.evaluations_count == 1
    assert rec1.expertise_score > 0.05

    # 2. Query expertise
    exp = await get_node_subject_expertise(db_session, pubkey, subject)
    assert exp == rec1.expertise_score

    # 3. Test parent subject fallback query
    exp_child = await get_node_subject_expertise(db_session, pubkey, "apiculture.equipment.veils")
    assert exp_child == pytest.approx(rec1.expertise_score * 0.85, rel=0.05)

    # 4. Slash expertise on hallucination
    initial_exp = rec1.expertise_score
    slashed = await slash_domain_expertise(db_session, pubkey, subject)
    assert slashed is not None
    assert slashed.slashing_count == 1
    assert slashed.expertise_score < initial_exp
