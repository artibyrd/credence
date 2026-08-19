---
title: Election & Civic Information Integrity Blueprint
description: Auditing polling methodology disclosures, voter registration deadlines,
  and candidate quote contexts for democratic institutions.
since_version: v1.11.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Election & Civic Information Integrity Blueprint

Democratic elections depend on accurate, verified civic information. Disinformation campaigns regularly target polling locations, ballot deadlines, candidate quotes, and voting rules to suppress turnout or undermine trust.

This blueprint describes configuring Credence for **election integrity and newsroom civic verification**.

---

## 1. Civic Integrity Focus Areas

1. **Procedural Voting Information**: Auditing dates, polling locations, voter ID requirements, and ballot drop-box rules against official state election databases.
2. **Polling Methodology Transparency**: Checking whether reported political polls disclose sample size ($N$), margin of error ($\pm \%zo$), field dates, and weighting methodology.
3. **Candidate Quote Context & Deepfake Attribution**: Verifying that inflammatory audio or video quotes are grounded in unaltered primary transcripts.

---

## 2. Civic Taxonomy Rules (`election_integrity.yaml`)

```yaml
version: "1.0.0"
domain: "ELECTION_INTEGRITY"
name: "Civic Information & Election Verification Catalog"

clusters:
  - id: "PROCEDURES"
    name: "Voting Rules & Deadlines"
    rules:
      - rule_id: "false_deadline"
        severity: 5
        description: "Misrepresenting official voter registration or mail-in ballot return deadlines."
        grounding_criteria:
          - "Must cite the specific inaccurate date or deadline."

  - id: "POLLING"
    name: "Polling Methodology Disclosures"
    rules:
      - rule_id: "undisclosed_sample"
        severity: 3
        description: "Promoting sensational polling leads without stating sample size, margin of error, or methodology."
```

---

## 3. Newsroom Pre-Publication Automated Checks

Integrate Credence into newsroom CMS workflows (WordPress, Ghost, or custom editorial tools):

```bash
# Automated pre-publication review
credence audit --file ./drafts/election-night-poll-analysis.md \
  --taxonomy election_integrity \
  --profile BALANCED
```
