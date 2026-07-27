"""Report-owned review-region synthesis over canonical producer registrations."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ladon.coverage import (
    CollectionCoverage,
    CoverageCause,
    InspectionAction,
)
from ladon.finding_evidence import resolve_local_json_pointer

IMPORT_PRESSURE_THRESHOLD = 5
IMPORT_PRESSURE_FINDINGS = {"root_import_closure_hotspot", "composite_import_pressure"}
REGISTERED_REGION_SIGNAL_LIMIT = 8
REGISTERED_SIGNAL_EVIDENCE_LIMIT = 12

_ARCHITECTURE_KINDS = frozenset(
    {
        "composite_import_pressure",
        "facade_fanout_pressure",
        "proof_family_import_pressure",
        "root_scope_pressure",
        "structurally_joined_architecture",
    }
)
_REGION_METADATA = {
    "architecture": (
        "architecture_integrity_region",
        "Structurally joined architecture review region",
    ),
    "declaration_collision": (
        "declaration_collision_region",
        "Declaration-collision review region",
    ),
    "generated_family": (
        "generated_family_candidate_region",
        "Generated-family candidate review region",
    ),
    "audit": (
        "audit_surface_region",
        "Lexical audit-surface review region",
    ),
    "option_resource": (
        "option_resource_region",
        "Actionable option/resource review region",
    ),
}
_TOP_LEVEL_COVERAGE_KEYS = (
    "declaration_coreachable_coverage",
    "generated_family_candidate_coverage",
    "audit_command_coverage",
    "resource_review_coverage",
    "architecture_joined_coverage",
)
_NESTED_COVERAGE_OWNERS = (
    "declaration_integrity",
    "generated_family_candidates",
    "architecture",
)
_CANONICAL_REF_OWNERS = (
    "declaration_integrity",
    "audit_surfaces",
)


@dataclass(frozen=True)
class _RegisteredProducer:
    """One validated producer row ready for bounded report integration."""

    identity: str
    kind: str
    evidence_refs: tuple[str, ...]
    coverage: CollectionCoverage
    authority: str
    nonclaims: tuple[str, ...]
    inspection_action: Mapping[str, Any]
    inspection_noun: str
    family: str


@dataclass(frozen=True)
class _ProducerFields:
    """Validated scalar and sequence fields from one registration."""

    family: str
    evidence_refs: tuple[str, ...]
    coverage_ref: str
    authority: str
    nonclaims: tuple[str, ...]


def summarize_review_regions(
    module_dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
    findings: list[dict[str, Any]],
    packet_evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Group related report signals into navigable review regions."""

    legacy_regions = [
        import_pressure_region(module_dag, findings),
        proof_family_region(declaration_graph, findings),
        packet_evidence_region(packet_evidence),
    ]
    regions = [region for region in legacy_regions if region is not None]
    regions.extend(
        registered_review_regions(
            module_dag,
            declaration_graph,
            findings,
            start_index=len(regions),
        )
    )
    return regions


def registered_review_regions(
    module_dag: Mapping[str, Any],
    declaration_graph: Mapping[str, Any] | None,
    findings: Sequence[Mapping[str, Any]],
    *,
    start_index: int = 0,
) -> list[dict[str, Any]]:
    """Integrate valid producer rows without reopening producer contracts.

    A malformed, dangling, or coverage-inconsistent producer group is omitted
    in full.  This prevents a surviving row from making the group look
    complete after another row failed validation.
    """

    report = _canonical_report_view(module_dag, declaration_graph, findings)
    coverage = _coverage_index(module_dag, report)
    canonical_refs = _canonical_identity_refs(module_dag)
    producers = _validated_producers(
        module_dag,
        report=report,
        coverage=coverage,
        canonical_refs=canonical_refs,
    )
    groups = _producer_groups(producers)
    regions: list[dict[str, Any]] = []
    for group in groups:
        index = start_index + len(regions)
        integrated = _registered_region(group, index=index)
        if integrated is not None:
            regions.append(integrated)
    return regions


def import_pressure_region(
    module_dag: dict[str, Any],
    findings: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return an import-pressure region when closure/finding signals exist."""

    closures = module_dag.get("root_direct_import_closures", [])[:3]
    signals = [
        closure_signal(row)
        for row in closures
    ]
    pressure_findings = finding_signals(findings, IMPORT_PRESSURE_FINDINGS)
    signals.extend(pressure_findings)
    if is_import_pressure_region(closures, pressure_findings):
        return region("import_pressure_region", "Import-pressure review region", signals)
    return region("import_context_region", "Import-context review region", signals)


def is_import_pressure_region(
    closures: list[dict[str, Any]],
    pressure_findings: list[dict[str, Any]],
) -> bool:
    """Return whether an import region should be labeled as pressure."""

    return bool(pressure_findings) or any(
        int(row.get("reachable_module_count", 0)) >= IMPORT_PRESSURE_THRESHOLD
        for row in closures
    )


def proof_family_region(
    declaration_graph: dict[str, Any] | None,
    findings: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return a proof-family region when repeated-family signals exist."""

    if declaration_graph is None:
        return None
    signals = [
        {"kind": "declaration_family", "subject": row["suffix"], "count": row["count"]}
        for row in declaration_graph.get("declaration_name_families", [])[:5]
    ]
    signals.extend(
        {
            "kind": "proof_similarity",
            "subject": row["suffix"],
            "score": row.get("similarity_score"),
        }
        for row in declaration_graph.get("proof_family_similarity_candidates", [])[:5]
    )
    signals.extend(finding_signals(findings, {"declaration_family_hotspot", "proof_family_import_pressure"}))
    return region("proof_family_region", "Proof-family review region", signals)


def packet_evidence_region(packet_evidence: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return a packet-evidence region when packet rows exist."""

    signals = [
        {
            "kind": "packet_evidence",
            "subject": row["packet_dir"],
            "status": row.get("status"),
            "profile_status": row.get("profile_status"),
        }
        for row in packet_evidence
    ]
    return region("packet_evidence_region", "Packet-evidence review region", signals)


def closure_signal(row: dict[str, Any]) -> dict[str, Any]:
    """Convert one direct import closure row into a region signal."""

    return {
        "kind": "root_import_closure",
        "subject": f"{row['root']} -> {row['direct_import']}",
        "count": row["reachable_module_count"],
    }


def finding_signals(findings: list[dict[str, Any]], kinds: set[str]) -> list[dict[str, Any]]:
    """Convert selected findings into compact region signals."""

    return [
        {"kind": finding["kind"], "subject": finding.get("subject", "")}
        for finding in findings
        if finding.get("kind") in kinds
    ]


def region(kind: str, title: str, signals: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Build one region row or return none for empty regions."""

    if not signals:
        return None
    return {
        "kind": kind,
        "title": title,
        "signal_count": len(signals),
        "signals": signals,
    }


def _canonical_report_view(
    module_dag: Mapping[str, Any],
    declaration_graph: Mapping[str, Any] | None,
    findings: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the report-local pointer root available during synthesis."""

    return {
        "sections": {
            "module_dag": module_dag,
            "declaration_graph": (
                declaration_graph if declaration_graph is not None else {}
            ),
            "findings": findings,
        }
    }


def _coverage_index(
    module_dag: Mapping[str, Any],
    report: Mapping[str, Any],
) -> dict[str, CollectionCoverage]:
    """Collect finite producer coverage without walking unrelated evidence."""

    rows: dict[str, CollectionCoverage] = {}
    conflicts: set[str] = set()
    for raw in _producer_coverage_rows(module_dag):
        coverage = _decode_coverage(raw, report)
        if coverage is None:
            continue
        existing = rows.get(coverage.identity)
        if existing is not None and existing != coverage:
            conflicts.add(coverage.identity)
            continue
        rows[coverage.identity] = coverage
    for identity in conflicts:
        rows.pop(identity, None)
    return rows


def _producer_coverage_rows(
    module_dag: Mapping[str, Any],
) -> Iterable[Mapping[str, Any]]:
    """Yield only coverage envelopes at registered producer ownership seams."""

    for key in _TOP_LEVEL_COVERAGE_KEYS:
        raw = module_dag.get(key)
        if isinstance(raw, Mapping):
            yield raw
    for owner_key in _NESTED_COVERAGE_OWNERS:
        owner = module_dag.get(owner_key)
        if not isinstance(owner, Mapping):
            continue
        raw = owner.get("coverage")
        if not isinstance(raw, Mapping):
            continue
        if "id" in raw:
            yield raw
            continue
        for row in raw.values():
            if isinstance(row, Mapping):
                yield row


def _decode_coverage(
    raw: Mapping[str, Any],
    report: Mapping[str, Any],
) -> CollectionCoverage | None:
    """Decode one complete coverage shape and reject dangling ownership."""

    required = {
        "id",
        "pointer",
        "visible",
        "observedLowerBound",
        "totalKnown",
        "total",
        "omitted",
        "completeness",
        "population",
        "scope",
        "authority",
        "causes",
    }
    if not required.issubset(raw):
        return None
    try:
        coverage = CollectionCoverage.from_mapping(raw)
        resolve_local_json_pointer(report, coverage.pointer)
    except (IndexError, KeyError, TypeError, ValueError):
        return None
    return coverage


def _nested_mappings(value: Any) -> Iterable[Mapping[str, Any]]:
    """Yield nested mappings without interpreting strings as collections."""

    if isinstance(value, Mapping):
        yield value
        for child in value.values():
            yield from _nested_mappings(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            yield from _nested_mappings(child)


def _canonical_identity_refs(module_dag: Mapping[str, Any]) -> set[str]:
    """Return serialized source-index identities available to inspection."""

    return {
        value
        for owner_key in _CANONICAL_REF_OWNERS
        for row in _nested_mappings(module_dag.get(owner_key))
        for value in (row.get("canonicalRef"),)
        if isinstance(value, str) and value
    }


def _validated_producers(
    module_dag: Mapping[str, Any],
    *,
    report: Mapping[str, Any],
    coverage: Mapping[str, CollectionCoverage],
    canonical_refs: set[str],
) -> tuple[_RegisteredProducer, ...]:
    """Decode every explicit registry, suppressing conflicting identities."""

    selected: dict[str, _RegisteredProducer] = {}
    conflicts: set[str] = set()
    for registry in _producer_registries(module_dag):
        raw_producers = registry.get("producers")
        if not isinstance(raw_producers, Mapping):
            continue
        for identity, raw in sorted(
            raw_producers.items(),
            key=lambda item: str(item[0]),
        ):
            producer = _validated_producer(
                identity,
                raw,
                report=report,
                coverage=coverage,
                canonical_refs=canonical_refs,
            )
            if producer is None:
                conflicts.add(str(identity))
                continue
            existing = selected.get(producer.identity)
            if existing is not None and existing != producer:
                conflicts.add(producer.identity)
                continue
            selected[producer.identity] = producer
    return tuple(
        selected[identity]
        for identity in sorted(selected)
        if identity not in conflicts
    )


def _producer_registries(
    module_dag: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    """Return the finite, explicitly owned registries known to this owner."""

    candidates = (
        _nested_mapping(
            module_dag,
            "declaration_integrity",
            "producerRegistrations",
        ),
        _nested_mapping(
            module_dag,
            "generated_family_candidates",
            "producerRegistry",
        ),
        _nested_mapping(
            module_dag,
            "architecture",
            "producerRegistrations",
        ),
        _mapping_value(
            module_dag.get("architectureProducerRegistrations")
        ),
        _mapping_value(
            module_dag.get("architecture_producer_registrations")
        ),
        _mapping_value(module_dag.get("auditProducerRegistrations")),
        _mapping_value(module_dag.get("resourceProducerRegistrations")),
        _mapping_value(module_dag.get("producerRegistrations")),
    )
    selected: list[Mapping[str, Any]] = []
    seen: set[int] = set()
    for candidate in candidates:
        if candidate is not None and id(candidate) not in seen:
            seen.add(id(candidate))
            selected.append(candidate)
    return tuple(selected)


def _nested_mapping(
    owner: Mapping[str, Any],
    outer_key: str,
    inner_key: str,
) -> Mapping[str, Any] | None:
    outer = owner.get(outer_key)
    if not isinstance(outer, Mapping):
        return None
    return _mapping_value(outer.get(inner_key))


def _mapping_value(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _validated_producer(
    registry_identity: Any,
    raw: Any,
    *,
    report: Mapping[str, Any],
    coverage: Mapping[str, CollectionCoverage],
    canonical_refs: set[str],
) -> _RegisteredProducer | None:
    """Return one fully validated producer or fail closed."""

    identity = _nonempty_text(registry_identity)
    if identity is None:
        return None
    if not isinstance(raw, Mapping) or raw.get("id") != identity:
        return None
    fields = _producer_fields(raw)
    if fields is None:
        return None
    action = _inspection_action(raw.get("inspectionAction"))
    if action is None:
        return None
    coverage_row = coverage.get(fields.coverage_ref)
    if coverage_row is None:
        return None
    if not _evidence_resolves(
        fields.evidence_refs,
        report=report,
        canonical_refs=canonical_refs,
    ):
        return None
    action_row, noun = action
    return _RegisteredProducer(
        identity=identity,
        kind=str(raw["kind"]),
        evidence_refs=fields.evidence_refs,
        coverage=coverage_row,
        authority=fields.authority,
        nonclaims=fields.nonclaims,
        inspection_action=action_row,
        inspection_noun=noun,
        family=fields.family,
    )


def _producer_fields(raw: Mapping[str, Any]) -> _ProducerFields | None:
    family = _producer_family(raw.get("kind"))
    if family is None:
        return None
    evidence_refs = _nonempty_strings(raw.get("evidenceRefs"))
    if evidence_refs is None:
        return None
    nonclaims = _nonempty_strings(raw.get("nonclaims"))
    if nonclaims is None:
        return None
    coverage_ref = _nonempty_text(raw.get("coverageRef"))
    authority = _nonempty_text(raw.get("authority"))
    if coverage_ref is None or authority is None:
        return None
    return _ProducerFields(
        family=family,
        evidence_refs=evidence_refs,
        coverage_ref=coverage_ref,
        authority=authority,
        nonclaims=nonclaims,
    )


def _producer_family(kind: Any) -> str | None:
    if kind == "co_reachable_declaration_collision_candidate":
        return "declaration_collision"
    if kind == "generated_family_candidate":
        return "generated_family"
    if kind == "audit_command_navigation":
        return "audit"
    if kind in {
        "normalized_unlimited_resource_setting",
        "policy_backed_finite_resource_setting",
    }:
        return "option_resource"
    if isinstance(kind, str) and (
        kind in _ARCHITECTURE_KINDS
        or kind.startswith("structurally_joined_")
    ):
        return "architecture"
    return None


def _nonempty_strings(value: Any) -> tuple[str, ...] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    rows = tuple(value)
    if not rows or any(not isinstance(row, str) or not row for row in rows):
        return None
    return rows


def _nonempty_text(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value


def _inspection_action(
    value: Any,
) -> tuple[Mapping[str, Any], str] | None:
    if not isinstance(value, Mapping) or value.get("command") != "ladon":
        return None
    arguments = _inspection_arguments(value.get("arguments"))
    if arguments is None:
        return None
    return dict(value), arguments[1]


def _inspection_arguments(value: Any) -> tuple[str, ...] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    arguments = tuple(value)
    if len(arguments) < 2 or arguments[0] != "inspect":
        return None
    if _nonempty_text(arguments[1]) is None:
        return None
    if any(not isinstance(item, str) for item in arguments):
        return None
    return arguments


def _evidence_resolves(
    evidence_refs: Sequence[str],
    *,
    report: Mapping[str, Any],
    canonical_refs: set[str],
) -> bool:
    return all(
        _evidence_ref_resolves(
            reference,
            report=report,
            canonical_refs=canonical_refs,
        )
        for reference in evidence_refs
    )


def _evidence_ref_resolves(
    reference: str,
    *,
    report: Mapping[str, Any],
    canonical_refs: set[str],
) -> bool:
    if reference.startswith("#/sections/"):
        try:
            resolve_local_json_pointer(report, reference)
        except (IndexError, KeyError, TypeError, ValueError):
            return False
        return True
    return reference in canonical_refs and reference.startswith(
        ("source-index:declaration:", "source-index:module:")
    )


def _producer_groups(
    producers: Sequence[_RegisteredProducer],
) -> tuple[tuple[_RegisteredProducer, ...], ...]:
    """Group rows by region family and source coverage deterministically."""

    groups: dict[tuple[str, str], list[_RegisteredProducer]] = {}
    for producer in producers:
        key = (producer.family, producer.coverage.identity)
        groups.setdefault(key, []).append(producer)
    return tuple(
        tuple(sorted(rows, key=lambda row: row.identity))
        for _, rows in sorted(groups.items())
    )


def _registered_region(
    producers: Sequence[_RegisteredProducer],
    *,
    index: int,
) -> dict[str, Any] | None:
    """Build one bounded region when its whole producer group is coherent."""

    if not producers or not _coherent_producer_group(producers):
        return None
    source_coverage = producers[0].coverage
    selected = tuple(producers[:REGISTERED_REGION_SIGNAL_LIMIT])
    signal_coverage = _region_signal_coverage(
        source_coverage,
        visible=len(selected),
        region_index=index,
        capped=len(selected) < len(producers),
        family=producers[0].family,
    )
    kind, title = _REGION_METADATA[producers[0].family]
    authorities = sorted({producer.authority for producer in producers})
    nouns = {producer.inspection_noun for producer in producers}
    noun = next(iter(nouns))
    return {
        "id": _region_identity(
            producers[0].family,
            source_coverage.identity,
        ),
        "kind": kind,
        "title": title,
        "signal_count": len(selected),
        "signals": [_registered_signal(row) for row in selected],
        "coverageRef": signal_coverage.identity,
        "coverage": signal_coverage.to_dict(),
        "upstreamCoverageRefs": [source_coverage.identity],
        "authority": (
            authorities[0]
            if len(authorities) == 1
            else "multiple_registered_producer_authorities"
        ),
        "authorities": authorities,
        "nonclaims": sorted(
            {
                nonclaim
                for producer in producers
                for nonclaim in producer.nonclaims
            }
        ),
        "inspectionAction": InspectionAction(noun=noun).to_dict(),
    }


def _coherent_producer_group(
    producers: Sequence[_RegisteredProducer],
) -> bool:
    coverage = producers[0].coverage
    nouns = {producer.inspection_noun for producer in producers}
    if len(nouns) != 1:
        return False
    if any(producer.coverage != coverage for producer in producers):
        return False
    return coverage.visible == len(producers)


def _registered_signal(
    producer: _RegisteredProducer,
) -> dict[str, Any]:
    evidence_refs = list(
        producer.evidence_refs[:REGISTERED_SIGNAL_EVIDENCE_LIMIT]
    )
    return {
        "id": producer.identity,
        "kind": producer.kind,
        "subject": producer.identity,
        "evidenceRefCount": len(producer.evidence_refs),
        "evidenceRefs": evidence_refs,
        "omittedEvidenceRefCount": (
            len(producer.evidence_refs) - len(evidence_refs)
        ),
        "coverageRef": producer.coverage.identity,
        "authority": producer.authority,
        "nonclaims": list(producer.nonclaims),
        "inspectionAction": dict(producer.inspection_action),
    }


def _region_signal_coverage(
    source: CollectionCoverage,
    *,
    visible: int,
    region_index: int,
    capped: bool,
    family: str,
) -> CollectionCoverage:
    identity = _region_coverage_identity(family, source.identity)
    pointer = f"#/sections/review_regions/{region_index}/signals"
    causes = source.causes
    if capped:
        causes = (
            *causes,
            CoverageCause(
                kind="projection",
                identifier=f"{identity}.signal_limit",
                detail=(
                    "review-region synthesis retained a deterministic "
                    "producer-registration prefix"
                ),
                controlling_cap=REGISTERED_REGION_SIGNAL_LIMIT,
            ),
        )
    if source.total_known:
        if source.total is None:
            raise AssertionError("validated known coverage lost its total")
        return CollectionCoverage.exact(
            identity=identity,
            pointer=pointer,
            visible=visible,
            total=source.total,
            observed_lower_bound=source.observed_lower_bound,
            population=source.population,
            scope=source.scope,
            authority=source.authority,
            causes=causes,
            source_fingerprint=source.source_fingerprint,
            scope_fingerprint=source.scope_fingerprint,
            analysis_fingerprint=source.analysis_fingerprint,
        )
    return CollectionCoverage.unknown(
        identity=identity,
        pointer=pointer,
        visible=visible,
        observed_lower_bound=source.observed_lower_bound,
        completeness=source.completeness,
        population=source.population,
        scope=source.scope,
        authority=source.authority,
        causes=causes,
        source_fingerprint=source.source_fingerprint,
        scope_fingerprint=source.scope_fingerprint,
        analysis_fingerprint=source.analysis_fingerprint,
    )


def _region_identity(family: str, coverage_ref: str) -> str:
    digest = hashlib.sha256(
        f"{family}\0{coverage_ref}".encode()
    ).hexdigest()[:12]
    return f"review-region:{family}:{digest}"


def _region_coverage_identity(family: str, coverage_ref: str) -> str:
    digest = hashlib.sha256(
        f"{family}\0{coverage_ref}".encode()
    ).hexdigest()[:12]
    return f"report.review_regions.{family}.{digest}.signals"
