"""Hierarchical Subject Registry and Content Domain Classifier for Credence.

Provides dynamic loading of subject catalogs and semantic topic classification
to prevent unqualified domain evaluations and enable domain-weighted consensus.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel, Field


class SubjectDescriptor(BaseModel):
    """Represents a registered subject domain namespace."""

    subject_id: str = Field(..., description="Canonical hierarchical namespace ID (e.g. apiculture.equipment)")
    title: str = Field(..., description="Human-readable subject title")
    description: str = Field(default="", description="Subject domain description")
    parent_id: Optional[str] = Field(default=None, description="Parent subject namespace ID")
    taxonomies: List[str] = Field(default_factory=list, description="Associated taxonomy catalog IDs")
    keywords: List[str] = Field(default_factory=list, description="Semantic keyword triggers")
    schema_org_types: List[str] = Field(default_factory=list, description="Matching Schema.org entity types")


class SubjectRegistry:
    """Manages loaded subject definitions and hierarchical queries."""

    def __init__(self, catalogs_dir: Optional[Path] = None) -> None:
        self._catalogs_dir = catalogs_dir or (Path(__file__).parent / "catalogs")
        self._subjects: Dict[str, SubjectDescriptor] = {}
        self.load_catalogs()

    def load_catalogs(self) -> None:
        """Scan and load all YAML subject catalog files."""
        self._subjects.clear()
        if not self._catalogs_dir.exists():
            return

        for yaml_file in sorted(self._catalogs_dir.glob("*.yaml")):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not data or "subject_id" not in data:
                    continue

                # Register top-level subject
                top_subject = SubjectDescriptor(
                    subject_id=data["subject_id"],
                    title=data.get("title", data["subject_id"]),
                    description=data.get("description", ""),
                    parent_id=data.get("parent_id"),
                    taxonomies=data.get("taxonomies", []),
                    keywords=data.get("keywords", []),
                    schema_org_types=data.get("schema_org_types", []),
                )
                self._subjects[top_subject.subject_id] = top_subject

                # Register sub-subjects if defined
                for sub in data.get("sub_subjects", []):
                    if "subject_id" not in sub:
                        continue
                    sub_subject = SubjectDescriptor(
                        subject_id=sub["subject_id"],
                        title=sub.get("title", sub["subject_id"]),
                        description=sub.get("description", ""),
                        parent_id=top_subject.subject_id,
                        taxonomies=sub.get("taxonomies", top_subject.taxonomies),
                        keywords=sub.get("keywords", []) + top_subject.keywords,
                        schema_org_types=sub.get("schema_org_types", top_subject.schema_org_types),
                    )
                    self._subjects[sub_subject.subject_id] = sub_subject
            except Exception:  # noqa: S112
                continue

    def get_subject(self, subject_id: str) -> Optional[SubjectDescriptor]:
        """Lookup subject descriptor by ID."""
        return self._subjects.get(subject_id)

    def list_subjects(self) -> List[SubjectDescriptor]:
        """Return list of all registered subject descriptors."""
        return list(self._subjects.values())

    def get_hierarchy_tree(self) -> List[Dict[str, Any]]:
        """Return hierarchical subject tree structure."""
        roots: List[Dict[str, Any]] = []
        by_parent: Dict[Optional[str], List[SubjectDescriptor]] = {}

        for subj in self._subjects.values():
            by_parent.setdefault(subj.parent_id, []).append(subj)

        for root in by_parent.get(None, []):
            node = {
                "subject_id": root.subject_id,
                "title": root.title,
                "description": root.description,
                "children": [
                    {
                        "subject_id": child.subject_id,
                        "title": child.title,
                        "description": child.description,
                    }
                    for child in by_parent.get(root.subject_id, [])
                ],
            }
            roots.append(node)

        return roots


_GLOBAL_REGISTRY: Optional[SubjectRegistry] = None


def get_subject_registry() -> SubjectRegistry:
    """Return singleton SubjectRegistry instance."""
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = SubjectRegistry()
    return _GLOBAL_REGISTRY


def classify_subject(
    text: str,
    schema_types: Optional[List[str]] = None,
    registry: Optional[SubjectRegistry] = None,
) -> Tuple[str, float]:
    """Classify text and schema metadata into primary subject namespace and confidence.

    Returns:
        tuple of (primary_subject_id, confidence_score [0.0 to 1.0])
    """
    reg = registry or get_subject_registry()
    subjects = reg.list_subjects()
    if not subjects:
        return "journalism.news", 0.5

    normalized_text = text.lower()
    schema_set = {s.lower() for s in (schema_types or [])}

    scores: Dict[str, float] = {}

    for subj in subjects:
        score = 0.0

        # Schema.org match (strong signal)
        for stype in subj.schema_org_types:
            if stype.lower() in schema_set:
                score += 3.0

        # Keyword frequency match
        for kw in subj.keywords:
            kw_clean = kw.lower()
            if " " in kw_clean:
                # Substring phrase count
                count = normalized_text.count(kw_clean)
                score += count * 2.0
            else:
                # Regex word boundary count
                pattern = r"\b" + re.escape(kw_clean) + r"\b"
                matches = len(re.findall(pattern, normalized_text))
                score += matches * 1.0

        if score > 0:
            scores[subj.subject_id] = score

    if not scores:
        return "journalism.news", 0.5

    # Find highest scoring subject
    best_subject_id = max(scores, key=lambda k: scores[k])
    raw_max_score = scores[best_subject_id]

    # Calculate normalized confidence (0.5 to 0.99)
    confidence = min(0.99, max(0.5, 0.5 + (raw_max_score / (raw_max_score + 10.0)) * 0.49))

    return best_subject_id, round(confidence, 3)
