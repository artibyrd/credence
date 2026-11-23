"""Volunteer Worker Daemon for Decentralized Epistemic Mempool Evaluation.

Governed by Theme 1: Botanical Network & Lifecycle & Theme 4: Sovereign Governance.
Executes blind evaluations, Ed25519 signs audit reports, and submits quorums to the coordinator.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import sys
from typing import Any, Dict, Optional

import httpx

from credence.config import settings
from credence.identity import NodeIdentity, load_or_create_node_identity, sign_audit_report
from credence.ingestion.extractor import ExtractedContent
from credence.ingestion.hasher import compute_content_sha256, compute_simhash
from credence.ingestion.snapshot import DualCaptureResult, capture_webpage_fastpath
from credence.pipeline.adapters import (
    BaseLLMProvider,
    ClaudeProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    OpenAIProvider,
    get_llm_provider,
)
from credence.pipeline.evaluator import evaluate_snapshot
from credence.worker.leases import (
    LocalLeaseTracker,
    compute_backoff_delay,
    resolve_model_family,
    sign_claim_proof,
)

logger = logging.getLogger("credence.worker")


def init_worker_provider(
    model: str,
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
) -> BaseLLMProvider:
    """Initialize the appropriate LLM inference provider for the volunteer worker."""
    clean_model = model.strip()
    clean_lower = clean_model.lower()

    if api_base:
        return OpenAICompatibleProvider(
            base_url=api_base,
            api_key=api_key,
            model_name=clean_model,
        )

    # Vendor-specific routing
    if "gemini" in clean_lower or "gemma" in clean_lower:
        raw_name = clean_model.split("/")[-1]
        return GeminiProvider(api_key=api_key, model_name=raw_name)
    if "claude" in clean_lower:
        raw_name = clean_model.split("/")[-1]
        return ClaudeProvider(api_key=api_key, model_name=raw_name)
    if any(k in clean_lower for k in ("gpt", "openai")) or re.search(r"(?:^|[/:_-])o[134](?:$|[/:_.-])", clean_lower):
        raw_name = clean_model.split("/")[-1]
        return OpenAIProvider(api_key=api_key, model_name=raw_name)
    if "deepseek" in clean_lower or re.search(r"(?:^|[/:_-])r1(?:$|[/:_.-])", clean_lower):
        raw_name = clean_model.split("/")[-1]
        if "ollama" in clean_lower:
            return OllamaProvider(base_url=api_base, model_name=raw_name)
        resolved_key = (
            api_key
            or os.environ.get("DEEPSEEK_API_KEY")
            or settings.DEEPSEEK_API_KEY
            or os.environ.get("CREDENCE_MODEL_API_KEY")
            or settings.CREDENCE_MODEL_API_KEY
        )
        return OpenAICompatibleProvider(
            base_url="https://api.deepseek.com/v1",
            api_key=resolved_key,
            model_name=raw_name,
        )
    if "ollama" in clean_lower:
        raw_name = clean_model.split("/")[-1]
        return OllamaProvider(base_url=api_base, model_name=raw_name)

    # Fallback to general environment provider or OpenAI-compatible default
    env_provider = get_llm_provider()
    if env_provider is not None:
        return env_provider

    return OpenAICompatibleProvider(
        base_url=api_base or "http://localhost:8000/v1",
        api_key=api_key,
        model_name=clean_model,
    )


def print_worker_banner(
    ident: NodeIdentity,
    model: str,
    model_family: str,
    node_url: str,
    affinity: Optional[str],
) -> None:
    """Print clean startup banner with contributor identity and odometer."""
    print("\n" + "=" * 68)
    print(" 🐝  CREDENCE VOLUNTEER WORKER DAEMON — OPEN MEMPOOL CONSENSUS")
    print("=" * 68)
    print(f"  Worker Pubkey:   {ident.public_key_hex}")
    print(f"  Model Slug:      {model}")
    print(f"  Model Family:    {model_family}")
    print(f"  Client Affinity: {affinity or 'all (general mempool)'}")
    print(f"  Coordinator:     {node_url}")
    print("=" * 68)
    print("  Ready to process peer evaluation bounties. Press Ctrl+C to exit.\n")
    sys.stdout.flush()


async def _execute_claimed_job(
    client: httpx.AsyncClient,
    base_url: str,
    ident: NodeIdentity,
    provider: BaseLLMProvider,
    lease_tracker: LocalLeaseTracker,
    model: str,
    model_family: str,
    job_payload: Dict[str, Any],
) -> bool:
    """Evaluate a claimed mempool job, sign the report, and submit it."""
    job_id = job_payload["job_id"]
    url = job_payload["url"]
    normalized_text = job_payload.get("normalized_text", "")
    lease_id = job_payload["lease_id"]
    lease_seconds = job_payload.get("lease_seconds", 180)

    lease_tracker.track_lease(lease_id, job_id, url, lease_seconds)
    logger.info("Claimed bounty %s for URL: %s (lease: %ds)", job_id[:8], url, lease_seconds)

    try:
        if normalized_text and len(normalized_text.strip()) > 0:
            sha256 = job_payload.get("content_sha256") or compute_content_sha256(normalized_text)
            simhash = compute_simhash(normalized_text)
            extracted = ExtractedContent(
                url=url,
                clean_text=normalized_text,
                clean_markdown=normalized_text,
                title="",
                byline="",
                date=None,
                site_name="",
                word_count=len(normalized_text.split()),
                char_count=len(normalized_text),
            )
            snapshot = DualCaptureResult(
                url=url,
                content_sha256=sha256,
                simhash_64=simhash,
                raw_html=f"<html><body><p>{normalized_text}</p></body></html>",
                extracted=extracted,
            )
        else:
            snapshot = await capture_webpage_fastpath(url)

        # Sign strictly once with worker's explicit Ed25519 identity
        report = await evaluate_snapshot(snapshot=snapshot, provider=provider, sign_result=False)
        signed_report = sign_audit_report(report, ident)
    except Exception as eval_err:
        logger.error("Evaluation failed for job %s: %s", job_id, eval_err, exc_info=True)
        lease_tracker.release_lease(lease_id)
        return False

    if not lease_tracker.is_lease_valid(lease_id):
        logger.warning("Lease %s expired prior to completion. Discarding submission.", lease_id[:8])
        lease_tracker.release_lease(lease_id)
        return False

    submit_body = {
        "job_id": job_id,
        "worker_pubkey": ident.public_key_hex,
        "model_family": model_family,
        "model_slug": model,
        "tokens_donated": report.tokens_used,
        "report": signed_report.model_dump(mode="json"),
    }

    try:
        res_sub = await client.post(f"{base_url}/api/queue/submit", json=submit_body)
        lease_tracker.release_lease(lease_id)
        if res_sub.status_code == 200:
            sub_data = res_sub.json()
            status = sub_data.get("status", "accepted")
            badges = sub_data.get("badges_awarded", [])
            print(
                f"  [✓] Bounty cleared: {job_id} | "
                f"Status: {status} | Badges: {badges if badges else 'none'} | "
                f"Tokens: {report.tokens_used}"
            )
            sys.stdout.flush()
            return True
        logger.warning("Submit rejected (%d): %s", res_sub.status_code, res_sub.text[:150])
        return False
    except Exception as submit_err:
        logger.error("Submission failed for job %s: %s", job_id, submit_err)
        lease_tracker.release_lease(lease_id)
        return False


async def run_worker_daemon(
    node_url: str = "https://credence.run",
    model: str = settings.DEFAULT_WORKER_MODEL,
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    affinity: Optional[str] = None,
    concurrency: int = 1,
    continuous: bool = True,
    max_jobs: Optional[int] = None,
    key_file: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> None:
    """Run the volunteer worker daemon evaluation loop with bounded concurrency."""
    ident = load_or_create_node_identity(key_file)
    model_family = resolve_model_family(model)
    provider = init_worker_provider(model=model, api_base=api_base, api_key=api_key)
    max_slots = max(1, min(int(concurrency), 3))
    lease_tracker = LocalLeaseTracker(max_concurrency=max_slots)

    print_worker_banner(ident, model, model_family, node_url, affinity)

    completed_jobs = 0
    count_lock = asyncio.Lock()
    base_url = node_url.rstrip("/")

    close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=60.0)
        close_client = True

    async def _worker_slot() -> None:
        nonlocal completed_jobs
        consecutive_idle = 0
        consecutive_errors = 0

        while True:
            async with count_lock:
                if max_jobs is not None and completed_jobs >= max_jobs:
                    break

            if not lease_tracker.can_claim_more():
                await asyncio.sleep(0.25)
                continue

            claim_ts, claim_sig = sign_claim_proof(ident, model)
            claim_body: Dict[str, Any] = {
                "worker_pubkey": ident.public_key_hex,
                "model_family": model_family,
                "model_slug": model,
                "claim_timestamp": claim_ts,
                "claim_signature": claim_sig,
            }
            if affinity:
                claim_body["client_affinity"] = affinity

            try:
                res_claim = await client.post(f"{base_url}/api/queue/claim", json=claim_body)
            except Exception as e:
                consecutive_errors += 1
                backoff = compute_backoff_delay(consecutive_errors, base_delay=3.0, max_delay=30.0)
                logger.warning("Coordinator connection error: %s. Retrying in %.1fs.", e, backoff)
                await asyncio.sleep(backoff)
                continue

            if res_claim.status_code == 429:
                logger.info("Active lease limit reached. Waiting 10s.")
                await asyncio.sleep(10.0)
                continue
            if res_claim.status_code != 200:
                logger.warning("Claim error (%d): %s", res_claim.status_code, res_claim.text[:150])
                if not continuous:
                    break
                await asyncio.sleep(5.0)
                continue

            job_payload = res_claim.json().get("job")
            if not job_payload:
                consecutive_idle += 1
                if not continuous:
                    logger.info("No jobs pending and non-continuous mode requested. Exiting.")
                    break
                backoff = compute_backoff_delay(consecutive_idle, base_delay=2.5, max_delay=20.0)
                await asyncio.sleep(backoff)
                continue

            consecutive_idle = 0
            consecutive_errors = 0

            succeeded = await _execute_claimed_job(
                client=client,
                base_url=base_url,
                ident=ident,
                provider=provider,
                lease_tracker=lease_tracker,
                model=model,
                model_family=model_family,
                job_payload=job_payload,
            )
            if succeeded:
                async with count_lock:
                    completed_jobs += 1
            else:
                await asyncio.sleep(0.5)

            if not continuous:
                break

    try:
        await asyncio.gather(*(_worker_slot() for _ in range(max_slots)))
    finally:
        if close_client:
            await client.aclose()
        print("\n 🛑 Credence volunteer worker stopped.")
