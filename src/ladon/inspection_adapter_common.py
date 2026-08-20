"""Shared row construction for canonical inspection artifact adapters."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from ladon.coverage import CollectionCoverage, CoverageCause, CoverageRegistry
from ladon.inspection_models import (
    MAX_RELATED_ROWS,
    ArtifactIdentity,
    InspectionCompatibilityError,
    InspectionRow,
    SourceAnchor,
)
from ladon.source_index_models import (
    SourceIndexError,
    source_index_collection_mapping,
    source_index_declaration_mapping,
)

LEXICAL_DECLARATION_NONCLAIM = (
    "Lexical declaration navigation only; not a Lean-resolved identity, "
    "dependency fact, elaboration result, proof-success result, or theorem "
    "quality verdict."
)
PROOF_MECHANISM_NONCLAIM = (
    "Lexical token occurrence only; not an elaborated tactic invocation, "
    "theorem dependency, rewrite direction, simplifier use, proof-success "
    "result, or theorem-quality verdict."
)
RESOURCE_NONCLAIM = (
    "Configured lexical setting only; not measured runtime, resource "
    "consumption, proof failure, or theorem quality."
)


def artifact_fingerprint(payload: Mapping[str, Any]) -> str:
    """Hash the exact immutable JSON evidence selected by the caller."""

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def mapping_rows(raw: Any) -> list[Mapping[str, Any]]:
    """Decode one canonical list of object rows or fail closed."""

    if not isinstance(raw, list):
        return []
    if not all(isinstance(row, Mapping) for row in raw):
        raise InspectionCompatibilityError(
            "canonical inspection collection contains a non-object row"
        )
    return list(raw)


def optional_mapping(raw: Any) -> Mapping[str, Any]:
    """Return an optional object as an empty read-only view."""

    return raw if isinstance(raw, Mapping) else {}


def optional_mapping_or_none(raw: Any) -> Mapping[str, Any] | None:
    """Return an optional object without inventing availability."""

    return raw if isinstance(raw, Mapping) else None


def text(raw: Any) -> str:
    """Normalize an identity field to text."""

    return str(raw) if raw is not None else ""


def optional_text(raw: Any) -> str | None:
    """Normalize an optional identity field to text."""

    return str(raw) if raw is not None and raw != "" else None


def string_list(raw: Any) -> list[str]:
    """Return a JSON-compatible string list."""

    return [str(value) for value in raw] if isinstance(raw, list) else []


def optional_int(raw: Any) -> int | None:
    """Reject booleans while decoding an optional source integer."""

    return raw if isinstance(raw, int) and not isinstance(raw, bool) else None


def ordered_int(value: int | None) -> str:
    """Encode optional source integers for lexical stable ordering."""

    return f"{value:012d}" if value is not None else "~"


def source_order(
    source_range: Mapping[str, Any] | None,
    field: str,
) -> str:
    """Return a stable source-position component."""

    start = optional_mapping(
        source_range.get("start") if source_range is not None else None
    )
    return ordered_int(optional_int(start.get(field)))


def stable_id(prefix: str, *values: str) -> str:
    """Derive a compatibility identity only when an owner supplies none."""

    encoded = json.dumps(
        [prefix, *values],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"ladon.{prefix}.{hashlib.sha256(encoded).hexdigest()[:20]}"


def pointer_token(value: str) -> str:
    """Escape one RFC 6901 pointer token."""

    return value.replace("~", "~0").replace("/", "~1")


def module_id(module: Mapping[str, Any]) -> str:
    """Adopt the canonical population ID or the module identity."""

    evidence = optional_mapping(module.get("populationEvidence"))
    return optional_text(evidence.get("id")) or ("module:" + text(module.get("name")))


def population(row: Mapping[str, Any], fallback: str) -> str:
    """Read a selected population without upgrading absent evidence."""

    return (
        optional_text(row.get("population") or row.get("containingPopulation"))
        or fallback
    )


def candidate_family(row: Mapping[str, Any]) -> str | None:
    """Read one additive generated-family candidate link."""

    return optional_text(
        row.get("candidateFamily") or row.get("familyId") or row.get("partitionId")
    )


def noun_population(noun: str) -> str:
    """Return the declared population for each finite inspection noun."""

    return {
        "modules": "modules",
        "declarations": "declarations",
        "imports": "lexical_import_occurrences",
        "audits": "lexical_audit_commands",
        "options": "lexical_option_commands",
        "resources": "lexical_resource_settings",
        "proof-mechanisms": "lexical_proof_mechanism_occurrences",
    }[noun]


def noun_authority(noun: str) -> str:
    """Return the default backend authority for a noun."""

    return "source_index_manifest" if noun == "modules" else "lexical_text"


def noun_nonclaim(noun: str) -> str:
    """Return the authority boundary for additive lexical rows."""

    if noun == "proof-mechanisms":
        return PROOF_MECHANISM_NONCLAIM
    if noun in {"options", "resources"}:
        return RESOURCE_NONCLAIM
    return "Lexical navigation evidence only; no elaboration result is implied."


def filter_link(
    noun: str,
    field: str,
    value: str,
    relationship: str,
) -> Mapping[str, Any]:
    """Build one ordinary follow-up filter action."""

    return {
        "noun": noun,
        "relationship": relationship,
        "action": {
            "command": "ladon",
            "arguments": ["inspect", noun, "--filter", f"{field}={value}"],
        },
    }


def id_link(noun: str, identifier: str, relationship: str) -> Mapping[str, Any]:
    """Build one ordinary exact-lookup action."""

    return {
        "noun": noun,
        "id": identifier,
        "relationship": relationship,
        "action": {
            "command": "ladon",
            "arguments": ["inspect", noun, "--id", identifier],
        },
    }


def source_anchor(
    path: str | None,
    source_range: Mapping[str, Any] | None,
    *,
    unavailable_reason: str | None = None,
) -> SourceAnchor:
    """Represent exact navigation or a reason no single source owns a row."""

    if path:
        return SourceAnchor.exact(path, source_range)
    return SourceAnchor.unavailable(
        unavailable_reason or "canonical row has no repository-relative source path"
    )


def line_anchor(path: str, line: int | None) -> SourceAnchor:
    """Build an import-site anchor whose only guaranteed coordinate is line."""

    source_range = (
        {
            "start": {"line": line, "column": None, "offset": None},
            "end": {"line": line, "column": None, "offset": None},
        }
        if line is not None
        else None
    )
    return source_anchor(path, source_range)


def coverage_registry(raw: Any) -> CoverageRegistry:
    """Decode canonical report-v3 coverage."""

    if raw is None:
        return CoverageRegistry()
    if not isinstance(raw, Mapping):
        raise InspectionCompatibilityError("report coverage registry is malformed")
    try:
        return CoverageRegistry.from_mapping(raw)
    except ValueError as exc:
        raise InspectionCompatibilityError(str(exc)) from exc


def unknown_coverage(
    *,
    identity: str,
    pointer: str,
    visible: int,
    population_name: str,
    scope: str,
    authority: str,
    source_fingerprint: str | None,
    reason: str,
    completeness: str = "unavailable",
    scope_fingerprint: str | None = None,
    analysis_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Expose an unknown total without interpreting it as zero omitted."""

    return CollectionCoverage.unknown(
        identity=identity,
        pointer=pointer,
        visible=visible,
        observed_lower_bound=visible,
        completeness=completeness,
        population=population_name,
        scope=scope,
        authority=authority,
        causes=(
            CoverageCause(
                kind="compatibility",
                identifier="inspection.coverage_unavailable",
                detail=reason,
            ),
        ),
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    ).to_dict()


def make_row(
    artifact: ArtifactIdentity,
    *,
    noun: str,
    identifier: str,
    canonical_ref: str,
    population_name: str,
    scope: str,
    authority: str,
    anchor: SourceAnchor,
    coverage_ref: str,
    fields: Mapping[str, Any],
    order_key: tuple[str, ...],
    related: tuple[Mapping[str, Any], ...] = (),
    enrichments: tuple[Mapping[str, Any], ...] = (),
    nonclaims: tuple[str, ...] = (),
) -> InspectionRow:
    """Attach common artifact and authority state to one adapter row."""

    return InspectionRow(
        identifier=identifier,
        noun=noun,
        canonical_ref=canonical_ref,
        artifact_fingerprint=artifact.fingerprint,
        source_fingerprint=artifact.source_fingerprint,
        schema_version=artifact.schema,
        population=population_name,
        scope=scope,
        authority=authority,
        source_anchor=anchor,
        coverage_ref=coverage_ref,
        fields=fields,
        order_key=order_key,
        related=related[:MAX_RELATED_ROWS],
        enrichments=enrichments,
        nonclaims=nonclaims,
    )


def with_enrichment(
    row: InspectionRow,
    enrichment: Mapping[str, Any],
) -> InspectionRow:
    """Attach a distinct Lean-backed authority row to lexical navigation."""

    return InspectionRow(
        identifier=row.identifier,
        noun=row.noun,
        canonical_ref=row.canonical_ref,
        artifact_fingerprint=row.artifact_fingerprint,
        source_fingerprint=row.source_fingerprint,
        schema_version=row.schema_version,
        population=row.population,
        scope=row.scope,
        authority=row.authority,
        source_anchor=row.source_anchor,
        coverage_ref=row.coverage_ref,
        fields=row.fields,
        order_key=row.order_key,
        related=row.related,
        enrichments=(*row.enrichments, dict(enrichment)),
        nonclaims=row.nonclaims,
    )


def declaration_mapping(raw: Any) -> Mapping[str, Any]:
    """Decode current and legacy compact source-index declaration rows."""

    if isinstance(raw, Mapping):
        return raw
    try:
        return source_index_declaration_mapping(raw)
    except SourceIndexError as exc:
        raise InspectionCompatibilityError(str(exc)) from exc


def declaration_source_range(
    raw: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    """Build the written-name range retained by compact lexical rows."""

    supplied = optional_mapping_or_none(raw.get("sourceRange"))
    if supplied is not None:
        return supplied
    line = optional_int(raw.get("line"))
    if line is None:
        return None
    column = optional_int(raw.get("column"))
    start = optional_int(raw.get("startOffset"))
    end = optional_int(raw.get("endOffset"))
    return {
        "start": {"line": line, "column": column, "offset": start},
        "end": {
            "line": line,
            "column": _end_column(column, start, end),
            "offset": end,
        },
    }


def _end_column(
    column: int | None,
    start: int | None,
    end: int | None,
) -> int | None:
    if column is None or start is None or end is None:
        return None
    return column + end - start


def declaration_row(
    artifact: ArtifactIdentity,
    raw: Mapping[str, Any],
    module: Mapping[str, Any],
    *,
    canonical_ref: str,
    coverage_ref: str,
    scope: str,
) -> InspectionRow:
    """Adapt one lexical declaration without upgrading its authority."""

    name = text(raw.get("name"))
    module_name = text(module.get("name"))
    path = text(module.get("path"))
    line = optional_int(raw.get("line"))
    column = optional_int(raw.get("column"))
    identifier = optional_text(raw.get("id")) or stable_id(
        "lexical-declaration",
        module_name,
        path,
        name,
        str(raw.get("startOffset")),
    )
    source_range = declaration_source_range(raw)
    return make_row(
        artifact,
        noun="declarations",
        identifier=identifier,
        canonical_ref=canonical_ref,
        population_name=population(
            module,
            "lexical_declaration_candidates",
        ),
        scope=scope,
        authority=optional_text(raw.get("authority")) or "lexical_text",
        anchor=source_anchor(path, source_range),
        coverage_ref=coverage_ref,
        fields=_declaration_fields(raw, module, name),
        order_key=(
            module_name,
            path,
            ordered_int(line),
            ordered_int(column),
            name,
            identifier,
        ),
        related=(
            id_link("modules", module_id(module), "declaring module"),
            filter_link(
                "proof-mechanisms",
                "declaration",
                optional_text(raw.get("candidateName")) or name,
                "lexical proof mechanisms",
            ),
        ),
        nonclaims=(optional_text(raw.get("nonclaim")) or LEXICAL_DECLARATION_NONCLAIM,),
    )


def _declaration_fields(
    raw: Mapping[str, Any],
    module: Mapping[str, Any],
    name: str,
) -> dict[str, Any]:
    module_name = text(module.get("name"))
    return {
        "module": module_name,
        "name": name,
        "kind": optional_text(raw.get("kind")),
        "candidate-status": optional_text(raw.get("candidateStatus"))
        or "scope_unavailable",
        "candidate-name": optional_text(raw.get("candidateName")),
        "privacy": optional_text(raw.get("privacy")) or "unknown",
        "locality": optional_text(raw.get("locality")) or "unknown",
        "candidate-family": candidate_family(raw),
        "namespace": string_list(raw.get("namespaceStack")),
        "section": string_list(raw.get("sectionStack")),
        "modifier": string_list(raw.get("modifiers")),
        "namespace-stack": string_list(raw.get("namespaceStack")),
        "section-stack": string_list(raw.get("sectionStack")),
        "modifiers": string_list(raw.get("modifiers")),
        "scope-context-status": optional_text(
            raw.get("scopeContextStatus")
        )
        or "unavailable",
        "scope-context": _resolved_scope_context(raw, module),
    }


def _resolved_scope_context(
    raw: Mapping[str, Any],
    module: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    identifier = optional_text(raw.get("scopeContextId"))
    if identifier is None:
        supplied = optional_mapping_or_none(raw.get("scopeContext"))
        return dict(supplied) if supplied is not None else None
    contexts = module.get("scopeContextRows")
    if not isinstance(contexts, list):
        return None
    module_name = text(module.get("name"))
    path = text(module.get("path"))
    try:
        expanded = (
            source_index_collection_mapping(
                "scopeContextRows",
                value,
                module=module_name,
                path=path,
            )
            for value in contexts
        )
        return next(
            (context for context in expanded if context.get("id") == identifier),
            None,
        )
    except SourceIndexError as exc:
        raise InspectionCompatibilityError(str(exc)) from exc


def additive_row(
    artifact: ArtifactIdentity,
    noun: str,
    raw: Mapping[str, Any],
    module: Mapping[str, Any],
    *,
    canonical_ref: str,
    coverage_ref: str,
    scope: str,
) -> InspectionRow:
    """Adapt one registered additive lexical row."""

    module_name = text(raw.get("module") or module.get("name"))
    source_range = optional_mapping_or_none(raw.get("sourceRange") or raw.get("range"))
    path, no_anchor_reason = _additive_path(raw, module, source_range)
    identifier = optional_text(raw.get("id")) or stable_id(
        noun.replace("-", "_"),
        module_name,
        path,
        json.dumps(raw, sort_keys=True, separators=(",", ":")),
    )
    return make_row(
        artifact,
        noun=noun,
        identifier=identifier,
        canonical_ref=canonical_ref,
        population_name=population(raw, noun_population(noun)),
        scope=scope,
        authority=optional_text(raw.get("authority")) or "lexical_text",
        anchor=source_anchor(
            path or None,
            source_range,
            unavailable_reason=no_anchor_reason,
        ),
        coverage_ref=optional_text(raw.get("coverageRef")) or coverage_ref,
        fields=additive_fields(noun, raw, module_name),
        order_key=_additive_order(raw, module_name, path, identifier, source_range),
        related=(
            id_link("modules", f"module:{module_name}", "containing module"),
            *_member_links(noun, raw),
        ),
        enrichments=_additive_enrichments(raw),
        nonclaims=(optional_text(raw.get("nonclaim")) or noun_nonclaim(noun),),
    )


def _additive_enrichments(
    raw: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    """Keep Lean results and policy classifications as separate authorities."""

    lean = optional_mapping_or_none(
        raw.get("queryResult") or raw.get("leanEnrichment")
    )
    policy = optional_mapping_or_none(raw.get("policyMatch"))
    return tuple(row for row in (lean, policy) if row is not None)


def _additive_path(
    raw: Mapping[str, Any],
    module: Mapping[str, Any],
    source_range: Mapping[str, Any] | None,
) -> tuple[str, str | None]:
    explicit_path = optional_text(raw.get("path"))
    aggregate = bool(raw.get("aggregate") or raw.get("memberIds") or raw.get("members"))
    if aggregate and explicit_path is None and source_range is None:
        return "", "aggregate has no single owning source range"
    return explicit_path or text(module.get("path")), None


def _additive_order(
    raw: Mapping[str, Any],
    module: str,
    path: str,
    identifier: str,
    source_range: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    subject = text(
        raw.get("option")
        or raw.get("kind")
        or raw.get("mechanism")
        or raw.get("subject")
    )
    return (
        module,
        path,
        source_order(source_range, "line"),
        source_order(source_range, "column"),
        subject,
        identifier,
    )


def _member_links(
    noun: str,
    raw: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    values = raw.get("memberIds") or raw.get("members") or []
    identifiers = (
        [
            text(value.get("id") or value.get("memberId"))
            if isinstance(value, Mapping)
            else text(value)
            for value in values
        ]
        if isinstance(values, list)
        else []
    )
    return tuple(
        id_link(noun, identifier, "aggregate member")
        for identifier in identifiers[: MAX_RELATED_ROWS - 1]
        if identifier
    )


def additive_fields(
    noun: str,
    raw: Mapping[str, Any],
    module: str,
) -> dict[str, Any]:
    """Return only the finite filter vocabulary for a noun."""

    builders = {
        "audits": _audit_fields,
        "options": _option_fields,
        "resources": _resource_fields,
        "proof-mechanisms": _mechanism_fields,
    }
    return builders[noun](raw, module)


def _common_fields(raw: Mapping[str, Any], module: str) -> dict[str, Any]:
    return {
        "module": module,
        "status": optional_text(raw.get("status")),
        "scope-context": (
            dict(context)
            if (
                context := optional_mapping_or_none(raw.get("scopeContext"))
            )
            is not None
            else None
        ),
    }


def _audit_fields(raw: Mapping[str, Any], module: str) -> dict[str, Any]:
    return {
        **_common_fields(raw, module),
        "kind": optional_text(raw.get("kind")),
        "subject": optional_text(raw.get("subject")),
        "result-status": optional_text(raw.get("resultStatus")),
    }


def _option_fields(raw: Mapping[str, Any], module: str) -> dict[str, Any]:
    return {
        **_common_fields(raw, module),
        "option": optional_text(raw.get("option") or raw.get("name")),
        "option-class": optional_text(raw.get("optionClass") or raw.get("class")),
        "scope": optional_text(raw.get("lexicalScope") or raw.get("scope")),
    }


def _resource_fields(raw: Mapping[str, Any], module: str) -> dict[str, Any]:
    return {
        **_common_fields(raw, module),
        "option": optional_text(raw.get("option") or raw.get("name")),
        "scope": optional_text(raw.get("lexicalScope") or raw.get("scope")),
        "meaning": optional_text(raw.get("normalizedMeaning") or raw.get("meaning")),
        "pressure": resource_pressure(raw),
    }


def _mechanism_fields(raw: Mapping[str, Any], module: str) -> dict[str, Any]:
    return {
        **_common_fields(raw, module),
        "declaration": optional_text(
            raw.get("declaration")
            or raw.get("declarationCandidate")
            or raw.get("candidateName")
            or raw.get("declarationName")
        ),
        "mechanism": optional_text(
            raw.get("mechanism") or raw.get("token") or raw.get("name")
        ),
        "kind": optional_text(raw.get("kind")),
        "attribute": optional_text(raw.get("attribute")),
        "candidate-family": candidate_family(raw),
    }


def resource_pressure(raw: Mapping[str, Any]) -> str:
    """Use only explicit policy output or normalized unlimited settings."""

    explicit = optional_text(raw.get("pressure") or raw.get("pressureClass"))
    if explicit:
        return explicit
    meaning = optional_text(raw.get("normalizedMeaning") or raw.get("meaning"))
    return "unlimited" if meaning == "unlimited" else "navigation_only"


def single_coverage_fingerprint(
    coverage: CoverageRegistry,
    attribute: str,
) -> str | None:
    """Return one unambiguous fingerprint across registered collections."""

    values = {
        value
        for row in coverage.collections.values()
        for value in [getattr(row, attribute)]
        if value is not None
    }
    return next(iter(values)) if len(values) == 1 else None


__all__ = [
    "additive_row",
    "artifact_fingerprint",
    "candidate_family",
    "coverage_registry",
    "declaration_mapping",
    "declaration_row",
    "filter_link",
    "id_link",
    "line_anchor",
    "make_row",
    "mapping_rows",
    "module_id",
    "noun_authority",
    "noun_population",
    "optional_int",
    "optional_mapping",
    "optional_mapping_or_none",
    "optional_text",
    "ordered_int",
    "pointer_token",
    "population",
    "single_coverage_fingerprint",
    "source_anchor",
    "source_order",
    "stable_id",
    "string_list",
    "text",
    "unknown_coverage",
    "with_enrichment",
]
