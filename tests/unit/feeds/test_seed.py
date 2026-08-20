"""Hermetic Unit Tests for RFC 8785 Signed Bootstrap Seed Manifest Protocol."""

from datetime import datetime, timedelta, timezone

from credence.identity import generate_node_keypair, load_or_create_node_identity
from credence.mesh.seed import (
    BootstrapSeedFile,
    SeedNodeEntry,
    extract_signable_seed_payload,
    generate_seed_file,
    verify_seed_file,
)


def test_generate_and_verify_seed_file(tmp_path):
    """Verify that a generated seed file produces valid signatures and passes verification."""
    key_path = tmp_path / "root_test.key"
    identity = load_or_create_node_identity(key_path=key_path)

    nodes = [
        SeedNodeEntry(
            node_pubkey="a" * 64,
            node_alias="seed-us-central1",
            ws_url="wss://seed1.credence.nexus:8765",
            quality_score=0.98,
            uptime_pct=99.99,
            region="us-central1",
            supported_catalogs={"spj_ethics": "hash1", "iep_fallacies": "hash2"},
        ),
        SeedNodeEntry(
            node_pubkey="b" * 64,
            node_alias="seed-europe-west1",
            ws_url="wss://seed2.credence.nexus:8765",
            quality_score=0.94,
            uptime_pct=99.85,
            region="europe-west1",
        ),
    ]

    seed_file = generate_seed_file(
        nodes=nodes,
        identity=identity,
        valid_hours=48,
        canonical_domain="https://seeds.credence.nexus/peers.json",
    )

    assert seed_file.root_pubkey == identity.public_key_hex
    assert seed_file.root_signature is not None
    assert len(seed_file.seed_nodes) == 2
    assert seed_file.canonical_domain == "https://seeds.credence.nexus/peers.json"

    # Verification should succeed with matching root key
    assert verify_seed_file(seed_file) is True
    assert verify_seed_file(seed_file, trusted_root_pubkey=identity.public_key_hex) is True


def test_tampered_seed_file_rejection(tmp_path):
    """Verify that any modification to seed entries invalidates the cryptographic signature."""
    identity = load_or_create_node_identity(key_path=tmp_path / "root.key")

    nodes = [
        SeedNodeEntry(
            node_pubkey="a" * 64,
            node_alias="legitimate-seed",
            ws_url="wss://legit.credence.nexus:8765",
            quality_score=0.95,
            uptime_pct=99.9,
        )
    ]

    seed_file = generate_seed_file(nodes=nodes, identity=identity)
    assert verify_seed_file(seed_file) is True

    # 1. Tamper with ws_url
    tampered_file = BootstrapSeedFile.model_validate(seed_file.model_dump())
    tampered_file.seed_nodes[0].ws_url = "wss://malicious-redirect.attacker.com:8765"
    assert verify_seed_file(tampered_file) is False

    # 2. Tamper with quality_score
    tampered_score = BootstrapSeedFile.model_validate(seed_file.model_dump())
    tampered_score.seed_nodes[0].quality_score = 1.00
    assert verify_seed_file(tampered_score) is False


def test_expired_seed_file_rejection(tmp_path):
    """Verify that an expired seed file is rejected even if signature is valid."""
    identity = load_or_create_node_identity(key_path=tmp_path / "root.key")
    past_time = datetime.now(timezone.utc) - timedelta(days=7)

    nodes = [
        SeedNodeEntry(
            node_pubkey="a" * 64,
            node_alias="expired-seed",
            ws_url="wss://seed.credence.nexus:8765",
            quality_score=0.90,
            uptime_pct=99.0,
        )
    ]

    expired_file = generate_seed_file(nodes=nodes, identity=identity, valid_hours=24, now=past_time)

    # Checking at current time should fail due to expiration
    assert verify_seed_file(expired_file) is False
    # Checking at past timestamp should pass signature validation
    assert verify_seed_file(expired_file, current_time=past_time + timedelta(hours=1)) is True


def test_mismatched_root_pubkey_rejection(tmp_path):
    """Verify that verification fails when trusted_root_pubkey does not match."""
    identity1 = load_or_create_node_identity(key_path=tmp_path / "root1.key")
    key2 = generate_node_keypair()
    from cryptography.hazmat.primitives import serialization

    pub2_hex = (
        key2.public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        .hex()
    )

    seed_file = generate_seed_file(nodes=[], identity=identity1)
    assert verify_seed_file(seed_file, trusted_root_pubkey=identity1.public_key_hex) is True
    assert verify_seed_file(seed_file, trusted_root_pubkey=pub2_hex) is False


def test_extract_signable_payload():
    """Verify that signature fields are excluded from signable payload."""
    seed_file = BootstrapSeedFile(
        protocol="credence-mesh/1.0",
        canonical_domain="https://seeds.credence.nexus/peers.json",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        root_pubkey="pubkey_hex_value",
        root_signature="sig_hex_value",
    )
    payload = extract_signable_seed_payload(seed_file)
    assert "root_pubkey" not in payload
    assert "root_signature" not in payload
    assert payload["canonical_domain"] == "https://seeds.credence.nexus/peers.json"
