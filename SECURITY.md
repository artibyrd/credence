# Security Policy

The **Credence** maintainers take the security and integrity of the epistemic evaluation engine and P2P trust network seriously.

---

## 1. Supported Versions

We provide security updates and patches for the following versions:

| Version | Supported |
| :--- | :--- |
| `1.0.x` | ✅ Active Security Support |
| `< 1.0.0` | ❌ End of Life |

---

## 2. Reporting a Vulnerability

If you discover a security vulnerability or protocol exploit within Credence, please **do not open a public GitHub issue**. Instead, follow responsible disclosure procedures:

1. **Email Security Team**: Send a confidential report to `security@credence.network` (or use GitHub Private Vulnerability Reporting).
2. **Include Reproduction Details**:
   - Detailed description of the vulnerability.
   - Proof of Concept (PoC) script or minimal reproducible example.
   - Impact assessment (e.g. SSRF, prompt injection bypass, Sybil cartel farming, denial of service).
3. **Response Timeline**:
   - **Initial Acknowledgement**: Within 24 hours.
   - **Triage & Reproduction**: Within 72 hours.
   - **Patch Release & Advisory**: Within 14 days (or coordinated disclosure timeline).

---

## 3. Threat Model & In-Scope Defenses

Credence includes dedicated protocol defenses against adversarial exploitation:

- **Server-Side Request Forgery (SSRF) Defense**: Ingestion engines reject cloud metadata (`169.254.169.254`, `metadata.google.internal`), loopback addresses (`127.0.0.1`, `localhost`), non-standard octal/hex IPs, and RFC 1918 private subnets.
- **XML Entity & Billion Laughs Defense**: All syndicated feed and sitemap parsers enforce `safe_parse_xml()`, instantly rejecting `<!DOCTYPE` and `<!ENTITY` declarations before traversal.
- **Prompt Injection Defense**: Evaluated prose text is containerized within `<untrusted_source_text>` XML boundaries accompanied by explicit security directives instructing models that evaluated text cannot override instructions or cancel rule checks.
- **Rate Limiting & DoS Protection**: FastMCP tool servers (`ServerRateLimiter`) and P2P WebSocket relays enforce token-bucket rate limits to prevent token budget exhaustion and SQLite write lock contention.
- **Cryptographic Tamper-Proofing**: Ed25519 signatures and RFC 8785 canonical JSON bytes prevent payload modification or signature relay tampering.
