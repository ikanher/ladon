"""Version-aware Ladon report views used by atlas construction."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.coverage import (
    CoverageRegistry,
    legacy_unknown_coverage,
)
from ladon.report_adapters import coerce_report_v2, report_version
from ladon.report_v2 import supported_report_view
from ladon.report_v3 import REPORT_V3_VERSION

_ATLAS_COLLECTIONS = (
    (
        "report.findings",
        "#/sections/findings",
        ("findings",),
        "selected findings",
        "ladon_analysis",
    ),
    (
        "report.review_regions",
        "#/sections/review_regions",
        ("review_regions",),
        "selected review regions",
        "ladon_report_adapter",
    ),
    (
        "report.packet_evidence",
        "#/sections/packet_evidence",
        ("packet_evidence",),
        "selected packet evidence",
        "ladon_report_adapter",
    ),
    (
        "declaration_graph.declarations",
        "#/sections/declaration_graph/declarations",
        ("declaration_graph", "declarations"),
        "selected declarations",
        "legacy_report",
    ),
)


def is_ladon_report_payload(payload: dict[str, Any]) -> bool:
    """Return whether a JSON payload is a Ladon report, not an auxiliary cache."""

    return (
        isinstance(payload, dict)
        and isinstance(payload.get("metadata"), dict)
        and (
            isinstance(payload.get("module_dag"), dict)
            or isinstance(payload.get("phases"), dict)
        )
    )


def atlas_report_view(
    payload: dict[str, Any],
    report_path: Path,
) -> dict[str, Any]:
    """Return a v1/v2/v3 consumer view without guessing unknown versions."""

    if report_version(payload) != REPORT_V3_VERSION:
        view = supported_report_view(
            payload,
            consumer=f"atlas report reader ({report_path})",
        )
        coverage = coerce_report_v2(payload).coverage
        return _integrity_view(
            view,
            coverage=coverage,
            snapshot=None,
            analysis_fingerprint=None,
            source_fingerprint=_legacy_source_fingerprint(view),
        )
    sections = payload.get("sections")
    metadata = payload.get("metadata")
    projection = payload.get("projection")
    if not all(
        isinstance(value, dict)
        for value in (sections, metadata, projection)
    ):
        raise ValueError(f"malformed report v3 input: {report_path}")
    if projection.get("name") == "summary":
        raise ValueError(
            "atlas construction requires a Ladon report-v3 review or full "
            f"projection because summary omits graph rows: {report_path}"
        )
    coverage = _v3_coverage_registry(
        payload.get("coverage"),
        sections=sections,
        metadata=metadata,
    )
    snapshot = payload.get("snapshot")
    snapshot_view = dict(snapshot) if isinstance(snapshot, Mapping) else None
    _require_compatible_fingerprints(coverage, snapshot_view)
    view = {
        "metadata": dict(metadata),
        "warnings": list(payload.get("warnings", [])),
        "projection": dict(projection),
        **{
            str(name): inflate_declaration_evidence(value)
            for name, value in sections.items()
        },
    }
    return _integrity_view(
        view,
        coverage=coverage,
        snapshot=snapshot_view,
        analysis_fingerprint=_analysis_fingerprint(projection, coverage),
        source_fingerprint=_source_fingerprint(snapshot_view, coverage),
    )


def _integrity_view(
    view: Mapping[str, Any],
    *,
    coverage: CoverageRegistry,
    snapshot: Mapping[str, Any] | None,
    analysis_fingerprint: str | None,
    source_fingerprint: str | None,
) -> dict[str, Any]:
    """Attach normalized integrity state to one atlas consumer view."""

    return {
        **dict(view),
        "coverage": coverage.to_dict(),
        "snapshot": dict(snapshot) if snapshot is not None else None,
        "analysis_fingerprint": analysis_fingerprint,
        "source_fingerprint": source_fingerprint,
    }


def _v3_coverage_registry(
    raw: Any,
    *,
    sections: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> CoverageRegistry:
    """Parse canonical v3 coverage and fill absent atlas inputs as unknown."""

    if raw is None:
        registry = CoverageRegistry()
    elif isinstance(raw, Mapping):
        registry = CoverageRegistry.from_mapping(raw)
    else:
        raise ValueError("malformed report v3 coverage registry")
    scope = _scope_label(metadata)
    for identity, pointer, path, population, authority in _ATLAS_COLLECTIONS:
        visible = _collection_size(_nested_value(sections, path))
        existing = registry.collections.get(identity)
        if existing is not None:
            if existing.pointer != pointer:
                raise ValueError(
                    f"atlas coverage {identity!r} has unexpected pointer "
                    f"{existing.pointer!r}"
                )
            if existing.visible != visible:
                raise ValueError(
                    f"atlas coverage {identity!r} exposes "
                    f"{existing.visible} rows but its section contains "
                    f"{visible}"
                )
            continue
        registry = registry.register(
            legacy_unknown_coverage(
                identity=identity,
                pointer=pointer,
                visible=visible,
                population=population,
                scope=scope,
                authority=authority,
            )
        )
    return registry


def _analysis_fingerprint(
    projection: Mapping[str, Any],
    coverage: CoverageRegistry,
) -> str | None:
    """Return the retained report identity without fabricating one."""

    fingerprint = projection.get("analysis_fingerprint")
    if isinstance(fingerprint, str) and fingerprint:
        return fingerprint
    return _single_coverage_fingerprint(coverage, "analysis_fingerprint")


def _source_fingerprint(
    snapshot: Mapping[str, Any] | None,
    coverage: CoverageRegistry,
) -> str | None:
    """Return the retained source identity without fabricating one."""

    if snapshot is not None:
        fingerprint = snapshot.get("sourceIndexFingerprint")
        if isinstance(fingerprint, str) and fingerprint:
            return fingerprint
    return _single_coverage_fingerprint(coverage, "source_fingerprint")


def _single_coverage_fingerprint(
    coverage: CoverageRegistry,
    attribute: str,
) -> str | None:
    """Return one unambiguous collection fingerprint when available."""

    fingerprints = {
        value
        for row in coverage.collections.values()
        for value in [getattr(row, attribute)]
        if value is not None
    }
    return next(iter(fingerprints)) if len(fingerprints) == 1 else None


def _require_compatible_fingerprints(
    coverage: CoverageRegistry,
    snapshot: Mapping[str, Any] | None,
) -> None:
    """Reject collection authority that cannot belong to one report snapshot."""

    for attribute in ("analysis_fingerprint", "source_fingerprint"):
        fingerprints = _coverage_fingerprints(coverage, attribute)
        if len(fingerprints) > 1:
            raise ValueError(
                "atlas input contains incompatible "
                f"{attribute.replace('_', ' ')} values"
            )
    if snapshot is None:
        return
    snapshot_source = snapshot.get("sourceIndexFingerprint")
    coverage_sources = _coverage_fingerprints(
        coverage,
        "source_fingerprint",
    )
    if (
        isinstance(snapshot_source, str)
        and coverage_sources
        and snapshot_source not in coverage_sources
    ):
        raise ValueError(
            "atlas input snapshot and collection coverage use incompatible "
            "source fingerprints"
        )


def _coverage_fingerprints(
    coverage: CoverageRegistry,
    attribute: str,
) -> set[str]:
    """Return non-empty fingerprints carried by one coverage registry."""

    return {
        str(value)
        for row in coverage.collections.values()
        for value in (getattr(row, attribute),)
        if value is not None
    }


def _legacy_source_fingerprint(view: Mapping[str, Any]) -> str | None:
    """Retain a legacy source-index fingerprint when explicitly recorded."""

    module_dag = view.get("module_dag")
    source_index = (
        module_dag.get("source_index")
        if isinstance(module_dag, Mapping)
        else None
    )
    fingerprint = (
        source_index.get("fingerprint")
        if isinstance(source_index, Mapping)
        else None
    )
    return fingerprint if isinstance(fingerprint, str) and fingerprint else None


def _scope_label(metadata: Mapping[str, Any]) -> str:
    """Return the best bounded scope label present in one report."""

    for key in (
        "analysis_root_module",
        "analysis_root",
        "report_anchor_module",
        "report_anchor",
        "repo_root",
    ):
        value = metadata.get(key)
        if value:
            return str(value)
    return "legacy-report-unknown-scope"


def _nested_value(value: Any, path: tuple[str, ...]) -> Any:
    """Read a known section path without inventing a missing collection."""

    for key in path:
        if not isinstance(value, Mapping):
            return None
        value = value.get(key)
    return value


def _collection_size(value: Any) -> int:
    """Count visible members while leaving their population total unknown."""

    return len(value) if isinstance(value, (list, Mapping)) else 0


def inflate_declaration_evidence(value: Any) -> Any:
    """Join report-v3 declaration evidence for existing atlas consumers."""

    if isinstance(value, list):
        return [inflate_declaration_evidence(row) for row in value]
    if not isinstance(value, dict):
        return value
    evidence = value.get("_declarationEvidence")
    declarations = value.get("declarations")
    inflated = {
        key: inflate_declaration_evidence(row)
        for key, row in value.items()
        if key != "_declarationEvidence"
    }
    if not isinstance(evidence, dict) or not isinstance(declarations, list):
        return inflated
    rows: list[Any] = []
    for declaration in declarations:
        if not isinstance(declaration, dict):
            rows.append(declaration)
            continue
        rows.append(_inflate_declaration_row(declaration, evidence))
    inflated["declarations"] = rows
    return inflated


def _inflate_declaration_row(
    declaration: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Apply one report-v3 path-indexed evidence entry to its declaration."""

    row = inflate_declaration_evidence(declaration)
    reference = declaration.get("evidenceRef")
    if not isinstance(reference, str):
        return row
    evidence_key = _pointer_token_value(reference.rsplit("/", maxsplit=1)[-1])
    attached = evidence.get(evidence_key)
    if not isinstance(attached, dict):
        return row
    fields = attached.get("fields")
    if not isinstance(fields, dict):
        return row
    for pointer, field_value in sorted(fields.items()):
        _set_pointer_value(
            row,
            str(pointer),
            inflate_declaration_evidence(field_value),
        )
    return row


def _set_pointer_value(target: Any, pointer: str, value: Any) -> None:
    """Set one RFC 6901-style path already present in a compact declaration."""

    if not pointer.startswith("/") or pointer == "/":
        raise ValueError(
            f"malformed declaration evidence pointer: {pointer!r}"
        )
    tokens = [_pointer_token_value(token) for token in pointer[1:].split("/")]
    owner = target
    for token in tokens[:-1]:
        owner = owner[int(token)] if isinstance(owner, list) else owner[token]
    final = tokens[-1]
    if isinstance(owner, list):
        owner[int(final)] = value
    else:
        owner[final] = value


def _pointer_token_value(token: str) -> str:
    """Decode one JSON pointer token."""

    return token.replace("~1", "/").replace("~0", "~")
