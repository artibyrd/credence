"""Hermetic Unit Tests for Expanded InMaricopa Corpus (N=50).

Governed by: inv-hermetic-unit-tests, inv-verbatim-grounding, inv-canonical-json-ed25519
"""

import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from credence.identity import canonical_json_bytes


@pytest.mark.unit
def test_inmaricopa_50_articles_genesis_parity():
    """Assert all 50 InMaricopa articles are present, validly signed, and well-distributed."""
    seeds_path = Path("credence/seeds/genesis_attestations.json")
    assert seeds_path.exists(), "Genesis attestations file must exist"

    data = json.loads(seeds_path.read_text(encoding="utf-8"))
    attestations = data.get("attestations", [])

    inm_attestations = [a for a in attestations if "inmaricopa.com" in a.get("url", "")]
    assert len(inm_attestations) == 50, f"Expected exactly 50 InMaricopa attestations, found {len(inm_attestations)}"

    # 1. Verify every Ed25519 signature over canonical RFC 8785 JSON bytes
    for idx, att in enumerate(inm_attestations):
        pubkey_hex = att.get("node_pubkey")
        sig_hex = att.get("node_signature")
        assert pubkey_hex, f"Attestation {idx} missing node_pubkey"
        assert sig_hex, f"Attestation {idx} missing node_signature"

        pubkey_bytes = bytes.fromhex(pubkey_hex)
        sig_bytes = bytes.fromhex(sig_hex)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pubkey_bytes)

        payload_keys = {
            "url": att["url"],
            "content_sha256": att["content_sha256"],
            "simhash_64": att.get("simhash_64", "0x00"),
            "audited_at": att.get("audited_at"),
            "suspicion_score": float(att["suspicion_score"]),
            "suspicion_density": float(att.get("suspicion_density", 0.0)),
            "confidence_score": float(att.get("confidence_score", 0.95)),
            "classification": att.get("classification", "CLEAN"),
            "is_satire": bool(att.get("is_satire", False)),
            "content_type": att.get("content_type", "NEWS_ARTICLE"),
            "satire_notes": att.get("satire_notes"),
            "violations": att.get("violations", []),
            "taxonomies_used": att.get("taxonomies_used", {}),
            "evaluation_method": att.get("evaluation_method", "mesh_genesis"),
            "quota_preserved": bool(att.get("quota_preserved", False)),
        }
        canonical_bytes = canonical_json_bytes(payload_keys)
        public_key.verify(sig_bytes, canonical_bytes)

    # 2. Verify score distribution (proving no cherry-picking)
    scores = [float(a["suspicion_score"]) for a in inm_attestations]
    clean_scores = [s for s in scores if s <= 15.0]
    blotter_scores = [s for s in scores if 25.0 <= s < 50.0]
    advertorial_scores = [s for s in scores if s >= 50.0]

    assert len(clean_scores) >= 35, f"Expected at least 35 clean articles, got {len(clean_scores)}"
    assert len(blotter_scores) >= 5, f"Expected at least 5 police blotters, got {len(blotter_scores)}"
    assert len(advertorial_scores) >= 4, f"Expected at least 4 advertorial/COI articles, got {len(advertorial_scores)}"

    # 3. Verify specific case studies
    coi_art = next(a for a in inm_attestations if "copper-sky-land-sale" in a["url"])
    assert float(coi_art["suspicion_score"]) == 78.4
    assert any(v["rule_id"] == "SPJ-3.1" for v in coi_art["violations"])

    tattoo_art = next(a for a in inm_attestations if "tattoo-removal" in a["url"])
    assert float(tattoo_art["suspicion_score"]) == 82.0
    assert any(v["rule_id"] == "DEC-1.4" for v in tattoo_art["violations"])

    heat_art = next(a for a in inm_attestations if "heat-related-causes" in a["url"])
    assert float(heat_art["suspicion_score"]) <= 5.0
    assert len(heat_art["violations"]) == 0
