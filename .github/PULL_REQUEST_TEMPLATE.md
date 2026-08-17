## Summary of Changes
Provide a brief, high-level summary of what this pull request accomplishes and why.

---

## Related Issue / RFC
Fixes #(issue number) or References #(issue number)

---

## Credence Invariant Checklist
Please verify that this pull request complies with the **31 Credence Project Invariants** ([`docs/agent-invariants.md`](docs/agent-invariants.md)):

- [ ] **Hermetic Testing**: Default unit test suite passes 100% network-free in `<65s` (`just test`).
- [ ] **Universal Parity**: Changes maintain synchronized feature parity across CLI, FastMCP 2.0, Textual TUI, and Zero-Build Web if applicable.
- [ ] **Deterministic Cryptography**: Any serialized attestation uses RFC 8785 canonical JSON bytes and UTC datetimes.
- [ ] **SSRF & Red Team Hardening**: No raw network calls bypass SSRF guards, XML entity parsing enforces `safe_parse_xml`, and prompt inputs use `<untrusted_source_text>`.
- [ ] **Formatting & Typing**: Clean mypy static typing and ruff checks pass (`just format && just lint`).

---

## Local Verification Output
Paste your local `just test` and `just lint` execution summary below:

```text
(Paste verification output here)
```
