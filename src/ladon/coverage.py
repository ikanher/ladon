"""Public coverage contract.

The implementation is split by responsibility, while this module remains the
stable import surface for analyzers, report adapters, and callers.
"""

from ladon.coverage_base import (
    COVERAGE_CAUSE_KINDS,
    COVERAGE_COMPLETENESS,
    COVERAGE_SCHEMA,
    CollectionCoverage,
    CoverageCause,
    CoverageError,
    CoverageRegistry,
    legacy_unknown_coverage,
)
from ladon.coverage_derivation import (
    DERIVED_CLAIM_KINDS,
    DERIVED_COVERAGE_STATUSES,
    DerivedCoverage,
    derive_coverage,
    mark_coverage_unstable,
    require_compatible_fingerprints,
)
from ladon.coverage_producers import (
    EvidenceStratumRegistration,
    InspectionAction,
    ProducerRegistration,
    ProducerRegistry,
)

__all__ = [
    "COVERAGE_CAUSE_KINDS",
    "COVERAGE_COMPLETENESS",
    "COVERAGE_SCHEMA",
    "DERIVED_CLAIM_KINDS",
    "DERIVED_COVERAGE_STATUSES",
    "CollectionCoverage",
    "CoverageCause",
    "CoverageError",
    "CoverageRegistry",
    "DerivedCoverage",
    "EvidenceStratumRegistration",
    "InspectionAction",
    "ProducerRegistration",
    "ProducerRegistry",
    "derive_coverage",
    "legacy_unknown_coverage",
    "mark_coverage_unstable",
    "require_compatible_fingerprints",
]
