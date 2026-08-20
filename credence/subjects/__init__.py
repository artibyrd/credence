"""Credence Subject Registry and Empirical Domain Expertise Engine."""

from credence.subjects.expertise import (
    DomainMetrics,
    compute_effective_weight,
    compute_subject_expertise,
    record_domain_evaluation,
    slash_domain_expertise,
)
from credence.subjects.registry import (
    SubjectDescriptor,
    SubjectRegistry,
    classify_subject,
    get_subject_registry,
)

__all__ = [
    "SubjectDescriptor",
    "SubjectRegistry",
    "get_subject_registry",
    "classify_subject",
    "DomainMetrics",
    "compute_subject_expertise",
    "compute_effective_weight",
    "record_domain_evaluation",
    "slash_domain_expertise",
]
