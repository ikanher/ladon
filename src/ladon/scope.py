"""Public analysis-scope planning contract.

The implementation is split into private population-resolution and planning
modules.  This module remains the stable import owner for callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from ladon.changed_set import (
    CHANGED_SET_MANIFEST_SCHEMA as _CHANGED_SET_SCHEMA,
    ChangedSetManifestSource,
)


SCOPE_PLAN_SCHEMA = "ladon-scope-plan-v1"
SCOPE_FINGERPRINT_VERSION = "ladon-scope-fingerprint-v2"
CHANGED_SET_MANIFEST_SCHEMA = _CHANGED_SET_SCHEMA
SUPPORTED_SCOPE_KINDS = frozenset(
    {
        "owner",
        "closure",
        "namespace",
        "multi-root",
        "changed-set",
        "inventory",
    }
)
SCOPE_ALIASES = {
    "import-closure": "closure",
    "import_closure": "closure",
    "multi_root": "multi-root",
    "changed_set": "changed-set",
    "full-inventory": "inventory",
    "full_inventory": "inventory",
}


class ScopePlanningError(ValueError):
    """Raised for malformed scope requests rather than repository findings."""


@dataclass(frozen=True)
class ScopeDiagnostic:
    """One stable scope-resolution or truncation diagnostic."""

    identifier: str
    severity: str
    message: str
    subject: str | None = None

    def to_payload(self) -> dict[str, Any]:
        """Return a stable JSON-compatible diagnostic."""

        payload: dict[str, Any] = {
            "id": self.identifier,
            "severity": self.severity,
            "message": self.message,
        }
        if self.subject is not None:
            payload["subject"] = self.subject
        return payload


@dataclass(frozen=True)
class ScopeRequest:
    """Caller-supplied inputs for one deterministic scope plan."""

    kind: str
    roots: tuple[str, ...] = ()
    changed_paths: tuple[str, ...] = ()
    changed_manifest: ChangedSetManifestSource | None = None
    max_modules: int | None = None
    max_context_modules: int | None = None
    lean_batch_size: int = 8
    navigation_roots: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScopePlan:
    """Resolved primary/context populations without executing analysis."""

    requested_scope: str
    scope_kind: str
    requested_roots: tuple[str, ...]
    resolved_roots: tuple[str, ...]
    primary_modules: tuple[str, ...]
    context_modules: tuple[str, ...]
    external_boundaries: tuple[str, ...]
    root_attribution: Mapping[str, tuple[str, ...]]
    diagnostics: tuple[ScopeDiagnostic, ...]
    inventory_module_count: int
    omitted_primary_count: int
    omitted_context_count: int
    truncated: bool
    helper_batch_size: int
    helper_batch_estimate: int
    source_index_fingerprint: str
    fingerprint: str
    inventory_boundary: tuple[Mapping[str, Any], ...]
    changed_authority: Mapping[str, Any] | None = None
    schema: str = SCOPE_PLAN_SCHEMA
    requested_selection_roots: tuple[str, ...] = ()
    resolved_selection_roots: tuple[str, ...] = ()
    requested_navigation_roots: tuple[str, ...] = ()
    resolved_navigation_roots: tuple[str, ...] = ()
    report_anchor: str | None = None

    @property
    def navigation_status(self) -> str:
        """Return whether an inventory navigation request resolved."""

        if self.scope_kind != "inventory":
            return "not_applicable"
        if not self.requested_navigation_roots:
            return "not_requested"
        if self.resolved_navigation_roots:
            return "resolved"
        return "unresolved"

    @property
    def selected_modules(self) -> tuple[str, ...]:
        """Return the deduplicated effective helper population."""

        return tuple(sorted({*self.primary_modules, *self.context_modules}))

    @property
    def completeness(self) -> str:
        """Classify whether the requested population is usable and complete."""

        if any(row.severity == "error" for row in self.diagnostics):
            return "invalid"
        return "truncated" if self.truncated else "complete"

    def to_payload(self) -> dict[str, Any]:
        """Return the machine-readable, schema-versioned preview."""

        return {
            "schema": self.schema,
            "scopeFingerprintVersion": SCOPE_FINGERPRINT_VERSION,
            "fingerprint": self.fingerprint,
            "sourceIndexFingerprint": self.source_index_fingerprint,
            "requestedScope": self.requested_scope,
            "effectiveScope": self.scope_kind,
            "requestedRoots": list(self.requested_roots),
            "resolvedRoots": list(self.resolved_roots),
            "selectionRoots": {
                "requested": list(self.requested_selection_roots),
                "resolved": list(self.resolved_selection_roots),
            },
            "navigationRoots": {
                "requested": list(self.requested_navigation_roots),
                "resolved": list(self.resolved_navigation_roots),
                "role": (
                    "auxiliary_inventory_view"
                    if self.scope_kind == "inventory"
                    else "not_applicable"
                ),
                "status": self.navigation_status,
            },
            "reportAnchor": self.report_anchor,
            "primaryPopulation": {
                "modules": list(self.primary_modules),
                "selectedCount": len(self.primary_modules),
                "omittedCount": self.omitted_primary_count,
            },
            "contextPopulation": {
                "modules": list(self.context_modules),
                "selectedCount": len(self.context_modules),
                "omittedCount": self.omitted_context_count,
                "authority": "local_import_context",
            },
            "externalBoundaries": list(self.external_boundaries),
            "rootAttribution": {
                module: list(roots)
                for module, roots in sorted(
                    self.root_attribution.items()
                )
            },
            "inventoryBoundary": {
                "moduleCount": self.inventory_module_count,
                "omittedCount": (
                    self.inventory_module_count - len(self.selected_modules)
                ),
                "sourceRoots": [
                    dict(row) for row in self.inventory_boundary
                ],
            },
            "truncated": self.truncated,
            "completeness": self.completeness,
            "leanHelperPlan": {
                "batchSize": self.helper_batch_size,
                "selectedModules": len(self.selected_modules),
                "expectedBatches": self.helper_batch_estimate,
            },
            "changedAuthority": (
                dict(self.changed_authority)
                if self.changed_authority is not None
                else None
            ),
            "diagnostics": [
                row.to_payload() for row in self.diagnostics
            ],
            "nonclaim": (
                "Scope planning is review routing, not a claim that a "
                "selected module is the mathematically correct proof root."
            ),
        }


@dataclass
class _Population:
    primary: set[str] = field(default_factory=set)
    attribution: dict[str, set[str]] = field(default_factory=dict)
    resolved_roots: set[str] = field(default_factory=set)
    diagnostics: list[ScopeDiagnostic] = field(default_factory=list)
    changed_authority: Mapping[str, Any] | None = None
    include_direct_context: bool = False


@dataclass(frozen=True)
class _EffectivePopulation:
    primary: tuple[str, ...]
    context: tuple[str, ...]
    external: tuple[str, ...]
    attribution: Mapping[str, tuple[str, ...]]
    diagnostics: tuple[ScopeDiagnostic, ...]
    omitted_primary: int
    omitted_context: int
    helper_batches: int


# Imported after the contract types exist so the private implementation can
# type against this stable public owner without a second public model family.
from ladon._scope_planning import plan_analysis_scope, plan_scope  # noqa: E402


__all__ = [
    "CHANGED_SET_MANIFEST_SCHEMA",
    "SCOPE_ALIASES",
    "SCOPE_FINGERPRINT_VERSION",
    "SCOPE_PLAN_SCHEMA",
    "SUPPORTED_SCOPE_KINDS",
    "ScopeDiagnostic",
    "ScopePlan",
    "ScopePlanningError",
    "ScopeRequest",
    "plan_analysis_scope",
    "plan_scope",
]
