"""Coverage derivation for bounded report-v3 projections."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from typing import Any, Mapping

from ladon.coverage import (
    CollectionCoverage,
    CoverageCause,
    CoverageError,
    CoverageRegistry,
)
from ladon.analysis.audit_registrations import (
    AUDIT_COMMAND_COVERAGE,
    RESOURCE_DIRECTIVE_COVERAGE,
)
from ladon.pipeline_inspection_navigation import TEXT_DECLARATIONS_COVERAGE


_MISSING = object()


def bind_analysis_fingerprint(
    registry: CoverageRegistry,
    analysis_fingerprint: str,
) -> CoverageRegistry:
    """Bind every report coverage row to its enclosing analysis identity."""

    bound = CoverageRegistry()
    for row in registry.collections.values():
        bound = bound.register(replace(row, analysis_fingerprint=analysis_fingerprint))
    return bound


def rebind_review_region_coverage(
    registry: CoverageRegistry,
    sections: Mapping[str, Any],
) -> CoverageRegistry:
    """Point each region-owned signal collection at its projected region.

    Review stratification may reorder the region list.  Region coverage is
    identified by ``coverageRef``, so array positions must be rebound after
    that selection instead of retaining canonical pre-projection indices.
    """

    pointers = _review_region_coverage_pointers(sections)
    missing = sorted(set(pointers) - set(registry.collections))
    if missing:
        raise CoverageError(
            "projected review regions reference missing coverage: " + ", ".join(missing)
        )
    rebound = CoverageRegistry()
    for identity, row in registry.collections.items():
        pointer = pointers.get(identity)
        rebound = rebound.register(
            replace(row, pointer=pointer) if pointer is not None else row
        )
    return rebound


def project_coverage(
    registry: CoverageRegistry,
    *,
    sections: Mapping[str, Any],
    projection: str,
    item_limit: int | None,
) -> CoverageRegistry:
    """Derive projected visibility while retaining every upstream omission."""

    if projection == "full":
        return registry
    projected = CoverageRegistry()
    for identity, source in registry.collections.items():
        projected_size = _projected_collection_size(
            sections,
            source.pointer,
            identity=source.identity,
        )
        visible = min(
            source.visible,
            source.visible if projected_size is None else projected_size,
        )
        row = source
        if visible < source.visible:
            row = source.projected(
                identity=identity,
                pointer=source.pointer,
                visible=visible,
                cause=CoverageCause(
                    kind="projection",
                    identifier=f"projection.{projection}_collection_limit",
                    detail=(
                        f"{projection} projection exposes {visible} of "
                        f"{source.visible} canonical visible members"
                    ),
                    controlling_cap=item_limit,
                ),
            )
        projected = projected.register(row)
    return projected


def synchronize_review_region_coverage(
    sections: Mapping[str, Any],
    registry: CoverageRegistry,
) -> dict[str, Any]:
    """Copy projected signal coverage back into each owning region."""

    regions = sections.get("review_regions")
    if not isinstance(regions, list):
        return dict(sections)
    synchronized: list[Any] = []
    for index, region in enumerate(regions):
        if not isinstance(region, Mapping):
            synchronized.append(region)
            continue
        identity = region.get("coverageRef")
        if not isinstance(identity, str) or not identity:
            synchronized.append(dict(region))
            continue
        coverage = registry.collections.get(identity)
        if coverage is None:
            raise CoverageError(
                f"projected review region {index} references missing "
                f"coverage {identity}"
            )
        expected = f"#/sections/review_regions/{index}/signals"
        if coverage.pointer != expected:
            raise CoverageError(
                f"{identity} coverage does not own projected review region {index}"
            )
        signals = region.get("signals")
        synchronized.append(
            {
                **region,
                "signal_count": len(signals) if isinstance(signals, list) else 0,
                "coverage": coverage.to_dict(),
            }
        )
    return {**sections, "review_regions": synchronized}


def register_projection_strata(
    registry: CoverageRegistry,
    strata: list[Mapping[str, Any]],
    *,
    projection: str,
    item_limit: int | None,
) -> CoverageRegistry:
    """Register exact per-stratum visibility for bounded record collections."""

    result = registry
    unstable_owner = next(
        (
            row
            for row in registry.collections.values()
            if row.completeness == "unstable"
        ),
        None,
    )
    for stratum in strata:
        row = _projection_stratum_coverage(
            stratum,
            owner=_coverage_owner(result, str(stratum["pointer"])),
            unstable_owner=unstable_owner,
            projection=projection,
            item_limit=item_limit,
        )
        result = result.register(row)
    return result


def _review_region_coverage_pointers(
    sections: Mapping[str, Any],
) -> dict[str, str]:
    """Index projected region signal collections by stable coverage identity."""

    regions = sections.get("review_regions")
    if not isinstance(regions, list):
        return {}
    pointers: dict[str, str] = {}
    for index, region in enumerate(regions):
        if not isinstance(region, Mapping):
            continue
        identity = region.get("coverageRef")
        if not isinstance(identity, str) or not identity:
            continue
        if identity in pointers:
            raise CoverageError(
                f"projected review regions reuse coverage identity {identity}"
            )
        pointers[identity] = f"#/sections/review_regions/{index}/signals"
    return pointers


def _projection_stratum_coverage(
    stratum: Mapping[str, Any],
    *,
    owner: CollectionCoverage | None,
    unstable_owner: CollectionCoverage | None,
    projection: str,
    item_limit: int | None,
) -> CollectionCoverage:
    """Derive one stratum row from its canonical collection owner."""

    pointer = str(stratum["pointer"])
    total = int(stratum["total"])
    visible = int(stratum["visible"])
    descriptor = stratum["descriptor"]
    inherited = owner or unstable_owner
    common = {
        "identity": _stratum_identity(pointer, descriptor),
        "pointer": pointer,
        "visible": visible,
        "population": _stratum_population(descriptor),
        "scope": _inherited_value(inherited, "scope", "report_projection"),
        "authority": _inherited_value(
            owner,
            "authority",
            "report_projection_stratification",
        ),
        "causes": (
            *(inherited.causes if inherited is not None else ()),
            *_stratum_projection_causes(
                projection,
                visible,
                total,
                item_limit,
            ),
        ),
        "source_fingerprint": _optional_inherited(
            inherited,
            "source_fingerprint",
        ),
        "scope_fingerprint": _optional_inherited(
            inherited,
            "scope_fingerprint",
        ),
        "analysis_fingerprint": _optional_inherited(
            inherited,
            "analysis_fingerprint",
        ),
    }
    if inherited is not None and not inherited.total_known:
        row = CollectionCoverage.unknown(
            **common,
            observed_lower_bound=total,
            completeness=inherited.completeness,
        )
    else:
        row = CollectionCoverage.exact(**common, total=total)
    if unstable_owner is None:
        return row
    return replace(row, completeness="unstable")


def _stratum_projection_causes(
    projection: str,
    visible: int,
    total: int,
    item_limit: int | None,
) -> tuple[CoverageCause, ...]:
    """Describe a projection cut only when the stratum omitted members."""

    if visible >= total:
        return ()
    return (
        CoverageCause(
            kind="projection",
            identifier=f"projection.{projection}_stratum_limit",
            detail=(
                f"{projection} projection exposes {visible} of "
                f"{total} members in this evidence stratum"
            ),
            controlling_cap=item_limit,
        ),
    )


def _inherited_value(
    owner: CollectionCoverage | None,
    attribute: str,
    fallback: str,
) -> str:
    """Return one required inherited field with a report-owned fallback."""

    if owner is None:
        return fallback
    return str(getattr(owner, attribute))


def _optional_inherited(
    owner: CollectionCoverage | None,
    attribute: str,
) -> str | None:
    """Return one optional inherited fingerprint."""

    if owner is None:
        return None
    value = getattr(owner, attribute)
    return str(value) if value is not None else None


def coverage_linked_omissions(
    omissions: list[dict[str, Any]],
    coverage: CoverageRegistry,
) -> list[dict[str, Any]]:
    """Attach the most specific registered collection to each projection cut."""

    linked: list[dict[str, Any]] = []
    for omission in omissions:
        pointer = str(omission["pointer"])
        candidates = [
            row
            for row in coverage.collections.values()
            if _pointers_overlap(pointer, row.pointer)
        ]
        owner = max(candidates, key=lambda row: len(row.pointer), default=None)
        linked.append(
            {
                **omission,
                "coverageRef": owner.identity if owner is not None else None,
            }
        )
    return linked


def _projected_collection_size(
    sections: Mapping[str, Any],
    pointer: str,
    *,
    identity: str,
) -> int | None:
    """Count projected members, or return ``None`` for another owner."""

    if not pointer.startswith("#/sections/"):
        return None
    value = _resolve_section_pointer(sections, pointer)
    if value is _MISSING or _is_summary_descriptor(value):
        return 0
    nested_key = {
        AUDIT_COMMAND_COVERAGE: "auditCommands",
        RESOURCE_DIRECTIVE_COVERAGE: "resourceDirectives",
        TEXT_DECLARATIONS_COVERAGE: "textDeclarations",
    }.get(identity)
    if nested_key is not None:
        return _nested_collection_size(value, nested_key)
    return len(value) if isinstance(value, (list, Mapping)) else 0


def _nested_collection_size(value: Any, key: str) -> int:
    """Count child rows owned by a report grouping collection."""

    if isinstance(value, Mapping):
        parents = value.values()
    elif isinstance(value, list):
        parents = value
    else:
        return 0
    return sum(
        len(rows)
        for parent in parents
        if isinstance(parent, Mapping) and isinstance((rows := parent.get(key)), list)
    )


def _resolve_section_pointer(
    sections: Mapping[str, Any],
    pointer: str,
) -> Any:
    """Resolve a collection pointer against projected section owners."""

    prefix = "#/sections/"
    if not pointer.startswith(prefix):
        return _MISSING
    value: Any = sections
    for token in pointer.removeprefix(prefix).split("/"):
        value = _pointer_child(value, _unescape_pointer_token(token))
        if value is _MISSING:
            return _MISSING
    return value


def _pointer_child(value: Any, key: str) -> Any:
    """Return one object member or array item during pointer resolution."""

    if isinstance(value, Mapping):
        return value.get(key, _MISSING)
    if isinstance(value, list) and key.isdigit():
        index = int(key)
        return value[index] if index < len(value) else _MISSING
    return _MISSING


def _unescape_pointer_token(token: str) -> str:
    """Decode one RFC 6901 token."""

    return token.replace("~1", "/").replace("~0", "~")


def _is_summary_descriptor(value: Any) -> bool:
    """Return whether summary projection replaced members with an aggregate."""

    return (
        isinstance(value, Mapping)
        and value.get("kind") in {"array", "object"}
        and isinstance(value.get("count"), int)
    )


def _pointers_overlap(left: str, right: str) -> bool:
    """Return whether either pointer owns the other's population."""

    return left == right or left.startswith(f"{right}/") or right.startswith(f"{left}/")


def _coverage_owner(
    registry: CoverageRegistry,
    pointer: str,
) -> CollectionCoverage | None:
    """Return the most specific canonical owner of one projected pointer."""

    candidates = [
        row
        for row in registry.collections.values()
        if _pointers_overlap(pointer, row.pointer)
        and not row.identity.startswith("report.projection.stratum.")
    ]
    return max(candidates, key=lambda row: len(row.pointer), default=None)


def _stratum_identity(
    pointer: str,
    descriptor: Any,
) -> str:
    """Return a compact stable identity for one pointer-bound stratum."""

    encoded = json.dumps(
        [pointer, descriptor],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:20]
    return f"report.projection.stratum.{digest}"


def _stratum_population(descriptor: Any) -> str:
    """Render a bounded machine-readable stratum population label."""

    if not isinstance(descriptor, Mapping):
        return "report_evidence_stratum"
    values = [
        f"{key}={descriptor.get(key, 'unspecified')}"
        for key in (
            "evidenceKind",
            "severity",
            "status",
            "population",
            "role",
        )
    ]
    return "report_evidence_stratum:" + ",".join(values)


__all__ = [
    "bind_analysis_fingerprint",
    "coverage_linked_omissions",
    "project_coverage",
    "rebind_review_region_coverage",
    "register_projection_strata",
    "synchronize_review_region_coverage",
]
