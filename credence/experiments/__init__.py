"""Credence Bicameral Experimentation, Shadow Auditing, and Federation Suite."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from credence.experiments.env_verifier import EnvVerificationReport, verify_environments
    from credence.experiments.federation_bridge import FederationBridgeHarness
    from credence.experiments.shadow_audit import ShadowAuditReport, run_shadow_audit


def __getattr__(name: str):
    if name in ("EnvVerificationReport", "verify_environments"):
        import credence.experiments.env_verifier as ev

        return getattr(ev, name)
    if name == "FederationBridgeHarness":
        import credence.experiments.federation_bridge as fb

        return fb.FederationBridgeHarness
    if name in ("ShadowAuditReport", "run_shadow_audit"):
        import credence.experiments.shadow_audit as sa

        return getattr(sa, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "EnvVerificationReport",
    "FederationBridgeHarness",
    "ShadowAuditReport",
    "run_shadow_audit",
    "verify_environments",
]
