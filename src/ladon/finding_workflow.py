"""Scope-aware finding evidence and deterministic report inspection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from ladon.finding_evidence import (
    DanglingFindingEvidenceError,
    aggregate_value_evidence,
    canonical_row_evidence,
    finding_evidence_refs,
    source_evidence_ref,
    validate_finding_evidence,
)


__all__ = [
    "DanglingFindingEvidenceError",
    "aggregate_value_evidence",
    "canonical_row_evidence",
    "validate_finding_evidence",
]


FINDING_VIEW_SCHEMA = "ladon-finding-view-v1"
FILTER_FIELDS = frozenset(
    {
        "authority",
        "confidence",
        "id",
        "kind",
        "path",
        "population",
        "priority",
        "scope",
        "severity",
    }
)


class FindingNotFoundError(LookupError):
    """An exact well-formed finding identifier is absent from a report."""


def enrich_findings(
    rows: Iterable[Mapping[str, Any]],
    *,
    analysis_root_module: str,
    inventory_root: str,
    module_dag: Mapping[str, Any],
    scope: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Attach scope, evidence, ranking, and next-command facts to findings."""

    scope_row = normalized_scope(
        scope,
        analysis_root_module=analysis_root_module,
        inventory_root=inventory_root,
    )
    module_metadata = (
        module_dag.get("module_metadata", {})
        if isinstance(module_dag, Mapping)
        else {}
    )
    return [
        enrich_finding(
            row,
            scope=scope_row,
            module_metadata=module_metadata
            if isinstance(module_metadata, Mapping)
            else {},
        )
        for row in rows
    ]


def enrich_finding(
    source: Mapping[str, Any],
    *,
    scope: Mapping[str, Any],
    module_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Return one canonical finding with resolvable or unavailable evidence."""

    row = dict(source)
    stable_key = str(row.get("stable_key") or semantic_finding_key(row))
    row["stable_key"] = stable_key
    row["scope"] = dict(scope)
    row["id"] = scoped_finding_id(stable_key, str(scope["fingerprint"]))
    row.setdefault("authority", "ladon_derived_heuristic")
    row["evidenceRefs"] = finding_evidence_refs(row, module_metadata)
    row.setdefault("confidence", finding_confidence(row))
    row.setdefault("priority", finding_priority(row))
    row["ownerRelevance"] = owner_relevance(
        row,
        root=str(scope.get("analysisRootModule", "")),
        module_metadata=module_metadata,
    )
    row["nextCommand"] = suggested_next_command(row, module_metadata)
    return row


def normalized_scope(
    scope: Mapping[str, Any] | Any | None,
    *,
    analysis_root_module: str,
    inventory_root: str,
) -> dict[str, Any]:
    """Return a stable explicit scope even for legacy inventory analysis."""

    if scope is not None:
        source = scope_payload(scope)
        row = {
            "kind": first_mapping_string(
                source,
                ("effectiveScope", "requestedScope", "kind"),
                default="inventory",
            ),
            "analysisRootModule": analysis_root_module,
            "inventoryRoot": inventory_root,
            "analysisScopeRef": "#/sections/module_dag/analysis_scope",
        }
        roots = source.get("resolvedRoots")
        if isinstance(roots, list):
            row["resolvedRoots"] = [str(root) for root in roots]
        if source.get("fingerprint"):
            row["fingerprint"] = str(source["fingerprint"])
    else:
        row = {
            "kind": "inventory",
            "analysisRootModule": analysis_root_module,
            "inventoryRoot": inventory_root,
        }
    if not row.get("fingerprint"):
        row["fingerprint"] = scope_fingerprint(row)
    return row


def scope_payload(scope: Mapping[str, Any] | Any) -> dict[str, Any]:
    """Adapt a scope mapping or typed scope plan without retaining its bulk."""

    exporter = getattr(scope, "to_payload", None)
    payload = exporter() if callable(exporter) else scope
    return dict(payload) if isinstance(payload, Mapping) else {}


def first_mapping_string(
    row: Mapping[str, Any],
    keys: Sequence[str],
    *,
    default: str,
) -> str:
    """Return the first non-empty string-like mapping value."""

    for key in keys:
        value = row.get(key)
        if value:
            return str(value)
    return default


def scope_fingerprint(scope: Mapping[str, Any]) -> str:
    """Hash normalized scope fields without presentation wording."""

    encoded = json.dumps(
        dict(scope),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def semantic_finding_key(row: Mapping[str, Any]) -> str:
    """Return identity fields that survive message and ordering changes."""

    return ":".join(
        (
            str(row.get("kind", "finding")),
            str(row.get("subject", "")),
            str(row.get("metric", "")),
            str(row.get("promotion_population", "")),
        )
    )


def scoped_finding_id(stable_key: str, scope_digest: str) -> str:
    """Return one compact ID for semantic evidence in one explicit scope."""

    digest = hashlib.sha256(
        f"{stable_key}\0{scope_digest}".encode("utf-8")
    ).hexdigest()[:20]
    return f"ladon.finding.{digest}"


def finding_confidence(row: Mapping[str, Any]) -> str:
    """Return existing confidence or a conservative derived label."""

    value = row.get("confidence") or row.get("confidenceLabel")
    return str(value) if value else "derived"


def finding_priority(row: Mapping[str, Any]) -> int:
    """Keep priority distinct from severity and confidence."""

    value = row.get("priority")
    if isinstance(value, int):
        return value
    severity = str(row.get("severity", "info"))
    return {"error": 300, "warning": 200, "info": 100}.get(severity, 0)


def owner_relevance(
    row: Mapping[str, Any],
    *,
    root: str,
    module_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Return inspectable ranking factors without mutating finding semantics."""

    subject = str(row.get("subject", ""))
    direct = int(subject == root or subject.startswith(f"{root}."))
    source = int(source_evidence_ref(row, module_metadata) is not None)
    score = direct * 100 + source * 10
    return {
        "score": score,
        "directOwnerSubject": bool(direct),
        "sourceLocatable": bool(source),
    }


def suggested_next_command(
    row: Mapping[str, Any],
    module_metadata: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Suggest an ordinary owner preview only for a known module subject."""

    subject = str(row.get("subject", ""))
    if subject not in module_metadata:
        return None
    return {
        "program": "ladon",
        "arguments": ["preview", "--root", subject, "--scope", "owner"],
        "advisory": True,
    }


def inspect_findings(
    payload: Mapping[str, Any],
    *,
    identifier: str | None = None,
    filters: Sequence[tuple[str, str]] = (),
) -> dict[str, Any]:
    """List, filter, or exactly select canonical report findings."""

    raw = payload.get("findings", [])
    rows = [
        dict(row)
        for row in raw
        if isinstance(raw, list) and isinstance(row, Mapping)
    ]
    validate_finding_evidence(payload, rows)
    selected = [row for row in rows if finding_matches_filters(row, filters)]
    if identifier is not None:
        selected = [row for row in selected if row.get("id") == identifier]
        if not selected:
            raise FindingNotFoundError(f"finding identifier not found: {identifier}")
    selected.sort(key=finding_order_key)
    return {
        "schema": FINDING_VIEW_SCHEMA,
        "selected": len(selected),
        "omitted": len(rows) - len(selected),
        "findings": selected,
    }


def finding_matches_filters(
    row: Mapping[str, Any],
    filters: Sequence[tuple[str, str]],
) -> bool:
    """Apply exact documented finding filters."""

    return all(finding_field(row, field) == value for field, value in filters)


def finding_field(row: Mapping[str, Any], field: str) -> str:
    """Return one normalized supported filter value."""

    reader = {
        "path": finding_path,
        "population": finding_population,
        "priority": lambda value: str(finding_priority(value)),
        "scope": finding_scope,
    }.get(field)
    if reader is not None:
        return reader(row)
    return str(row.get(field, ""))


def finding_population(row: Mapping[str, Any]) -> str:
    """Return the direct or promotion population selected by the producer."""

    return str(row.get("population") or row.get("promotion_population") or "")


def finding_scope(row: Mapping[str, Any]) -> str:
    """Return the normalized finding scope kind."""

    scope = row.get("scope", {})
    return str(scope.get("kind", "")) if isinstance(scope, Mapping) else ""


def finding_path(row: Mapping[str, Any]) -> str:
    """Return the first repository path in typed source evidence."""

    references = row.get("evidenceRefs", [])
    if not isinstance(references, list):
        return ""
    source = next(
        (
            reference
            for reference in references
            if isinstance(reference, Mapping)
            and reference.get("type") == "source"
        ),
        None,
    )
    return str(source.get("path", "")) if source is not None else ""


def finding_order_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    """Sort owner-relevant rows deterministically with stable tie-breakers."""

    relevance = row.get("ownerRelevance", {})
    score = int(relevance.get("score", 0)) if isinstance(relevance, Mapping) else 0
    return (
        -score,
        -finding_priority(row),
        str(row.get("kind", "")),
        str(row.get("subject", "")),
        str(row.get("id", "")),
    )


def parse_finding_filter(value: str) -> tuple[str, str]:
    """Parse one exact `field=value` filter for argparse."""

    field, separator, selected = value.partition("=")
    if separator != "=" or field not in FILTER_FIELDS or not selected:
        raise ValueError(
            f"invalid finding filter {value!r}; expected one of "
            + ", ".join(f"{name}=<value>" for name in sorted(FILTER_FIELDS))
        )
    return field, selected


def load_finding_report(path: Path) -> dict[str, Any]:
    """Load one explicit report without invoking analysis."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"input is not a supported Ladon finding report: {path}")
    findings = payload.get("findings")
    if isinstance(findings, list):
        return payload
    metadata = payload.get("metadata")
    sections = payload.get("sections")
    if (
        isinstance(metadata, Mapping)
        and metadata.get("report_version") == "ladon-report-v3"
        and isinstance(sections, Mapping)
        and isinstance(sections.get("findings"), list)
    ):
        normalized = dict(payload)
        normalized["findings"] = sections["findings"]
        return normalized
    raise ValueError(f"input is not a supported Ladon finding report: {path}")
