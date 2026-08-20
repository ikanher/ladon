"""Normalization for bounded Lean-elaborated declaration surfaces.

The Lean helper owns elaboration facts.  This module only validates, bounds,
sorts, and joins those facts into Ladon's typed IR.  Missing helper fields are
represented as unavailable, never as observed empty data.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

from ladon.ir import (
    BoundedBinders,
    BoundedStrings,
    BoundedText,
    LeanBinderSurface,
    LeanDeclaration,
    LeanDeclarationSurface,
    LeanTrustFact,
)

MAX_BINDERS = 32
MAX_DEPENDENCIES = 64
MAX_PREMISES = 32
MAX_STATEMENT_BYTES = 1024
MAX_TYPE_BYTES = 4096
SURFACE_NONCLAIM = (
    "Navigation and direct Lean artifact evidence only; Ladon does not "
    "independently verify proof correctness or theorem truth."
)


def declarations_from_elaborated_payload(
    module: str,
    source_path: str,
    payload: Mapping[str, Any],
    *,
    parser_declarations: Mapping[str, LeanDeclaration] | None = None,
    source_content_hash: str | None = None,
    restrict_to_parser_inventory: bool = False,
) -> dict[str, LeanDeclaration]:
    """Normalize one elaborated-helper payload and add imported target stubs."""

    parser_rows = parser_declarations or {}
    helper_rows = selected_helper_rows(
        mapping_rows(payload.get("declarations")),
        parser_rows,
        restrict_to_parser_inventory=restrict_to_parser_inventory,
    )
    declarations = normalized_helper_declarations(
        module,
        source_path,
        helper_rows,
        parser_rows,
        payload,
        source_content_hash,
    )
    return with_imported_stubs(declarations)


def selected_helper_rows(
    rows: Sequence[Mapping[str, Any]],
    parser_rows: Mapping[str, LeanDeclaration],
    *,
    restrict_to_parser_inventory: bool,
) -> list[Mapping[str, Any]]:
    """Keep parser-owned rows plus source-anchored compiler auxiliaries."""

    if not restrict_to_parser_inventory or not parser_rows:
        return list(rows)
    return [
        row
        for row in rows
        if helper_row_is_selected(row, parser_rows)
    ]


def helper_row_is_selected(
    row: Mapping[str, Any],
    parser_rows: Mapping[str, LeanDeclaration],
) -> bool:
    """Return whether a restricted elaborated row has retained evidence."""

    if declaration_name(row) in parser_rows:
        return True
    return (
        row.get("compilerGenerated") is True
        and normalized_range(row.get("sourceRange")) is not None
    )


def normalized_helper_declarations(
    module: str,
    source_path: str,
    rows: Sequence[Mapping[str, Any]],
    parser_rows: Mapping[str, LeanDeclaration],
    payload: Mapping[str, Any],
    source_content_hash: str | None,
) -> dict[str, LeanDeclaration]:
    """Normalize named helper rows without changing their input order policy."""

    declarations: dict[str, LeanDeclaration] = {}
    for row in rows:
        name = declaration_name(row)
        if name is None:
            continue
        declarations[name] = normalized_declaration(
            module,
            source_path,
            row,
            parser_rows.get(name),
            payload,
            source_content_hash,
        )
    return declarations


def normalized_declaration(
    module: str,
    source_path: str,
    row: Mapping[str, Any],
    parser_row: LeanDeclaration | None,
    payload: Mapping[str, Any],
    source_content_hash: str | None,
) -> LeanDeclaration:
    """Build one declaration row while preserving parser-only evidence."""

    surface = surface_from_helper_row(row, payload)
    parser_candidates = parser_candidate_collection(parser_row)
    type_dependencies = bounded_strings(
        row.get("typeConstants"),
        cap=MAX_DEPENDENCIES,
        authority="lean_environment",
    )
    value_dependencies = bounded_strings(
        row.get("valueConstants"),
        cap=MAX_DEPENDENCIES,
        authority="lean_environment",
    )
    compiler_generated, compiler_authority, compiler_toolchain = (
        compiler_generation_evidence(row, payload)
    )
    name = declaration_name(row)
    assert name is not None
    return LeanDeclaration(
        name=name,
        module=module,
        kind=declaration_kind(row, parser_row),
        references=parser_references(parser_row),
        source_path=source_path,
        source_range=declaration_range(
            row,
            "sourceRange",
            parser_row,
            "source_range",
        ),
        selection_range=declaration_range(
            row,
            "selectionRange",
            parser_row,
            "selection_range",
        ),
        content_hash=declaration_content_hash(row, source_content_hash),
        extraction_backend="lean_elaborated_helper",
        extractor_version=helper_version(payload),
        name_resolution_method="lean_environment",
        confidence="lean_environment",
        parser_candidates=parser_candidates,
        type_dependencies=type_dependencies,
        value_dependencies=value_dependencies,
        surface=surface,
        compiler_generated=compiler_generated,
        compiler_authority=compiler_authority,
        compiler_toolchain=compiler_toolchain,
    )


def declaration_kind(
    row: Mapping[str, Any],
    parser_row: LeanDeclaration | None,
) -> str | None:
    """Prefer the Lean helper kind and retain a parser fallback."""

    helper_kind = string_or_none(row.get("kind"))
    return helper_kind or getattr(parser_row, "kind", None)


def parser_references(
    parser_row: LeanDeclaration | None,
) -> tuple[str, ...]:
    """Retain parser reference candidates when a parser row exists."""

    return parser_row.references if parser_row is not None else ()


def declaration_range(
    row: Mapping[str, Any],
    helper_key: str,
    parser_row: LeanDeclaration | None,
    parser_attribute: str,
) -> dict[str, int] | None:
    """Prefer a normalized Lean range and retain the parser range fallback."""

    helper_range = normalized_range(row.get(helper_key))
    return helper_range or getattr(parser_row, parser_attribute, None)


def declaration_content_hash(
    row: Mapping[str, Any],
    source_content_hash: str | None,
) -> str | None:
    """Prefer the caller-validated source hash over helper metadata."""

    return source_content_hash or string_or_none(row.get("sourceHash"))


def compiler_generation_evidence(
    row: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> tuple[bool | None, str | None, str | None]:
    """Preserve Lean-owned compiler-generation identity and toolchain."""

    generated = bool_or_none(row.get("compilerGenerated"))
    if row.get("compilerGenerated") is not True:
        return generated, None, None
    return (
        generated,
        "lean_environment",
        string_or_none(payload.get("leanVersion")),
    )


def surface_from_helper_row(
    row: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> LeanDeclarationSurface:
    """Normalize optional surface fields from one helper declaration."""

    raw = row.get("declarationSurface")
    if not isinstance(raw, Mapping):
        raw = row
    status = normalized_status(raw.get("status"))
    reason = normalized_reason(status, raw.get("reason"))
    rendered_type_raw = string_or_none(raw.get("renderedType"))
    rendered_type = bounded_text_value(rendered_type_raw, MAX_TYPE_BYTES)
    binders = bounded_binders(raw.get("binders"))
    premises = bounded_strings(
        raw.get("premises"),
        cap=MAX_PREMISES,
        authority="lean_environment",
    )
    trust_facts = normalized_trust_facts(raw.get("trustFacts"))
    conclusion_raw = string_or_none(raw.get("conclusion"))
    return LeanDeclarationSurface(
        status=status,
        reason=reason,
        rendered_type=rendered_type,
        rendered_type_bytes=integer_at_least(
            raw.get("renderedTypeBytes"),
            utf8_size(rendered_type_raw),
        ),
        rendered_type_truncated=(
            bool(raw.get("renderedTypeTruncated"))
            or utf8_size(rendered_type_raw) > utf8_size(rendered_type)
        ),
        printer_options=string_mapping(raw.get("printerOptions")),
        binders=binders,
        premises=premises,
        conclusion=bounded_text_value(conclusion_raw, MAX_TYPE_BYTES),
        conclusion_truncated=(
            bool(raw.get("conclusionTruncated"))
            or utf8_size(conclusion_raw) > MAX_TYPE_BYTES
        ),
        statement_excerpt=bounded_source_text(raw.get("statementExcerpt")),
        statement_range=normalized_range(raw.get("statementRange")),
        proof_range=normalized_range(raw.get("proofRange")),
        has_value=bool_or_none(raw.get("hasValue")),
        proof_form=string_or_none(raw.get("proofForm")),
        body_total_bytes=integer_at_least(raw.get("bodyTotalBytes"), 0),
        body_truncated=bool(raw.get("bodyTruncated")),
        declared_axiom=bool_or_none(raw.get("declaredAxiom")),
        unsafe=bool_or_none(raw.get("unsafe")),
        trust_facts=trust_facts,
        dependency_modules=dependency_modules(raw.get("dependencyModules")),
        helper_version=helper_version(payload),
        lean_version=string_or_none(payload.get("leanVersion")),
        nonclaim=string_or_none(raw.get("nonclaim")) or SURFACE_NONCLAIM,
    )


def parser_candidate_collection(
    parser_row: LeanDeclaration | None,
) -> BoundedStrings:
    """Return explicit parser authority without upgrading it to Lean authority."""

    if parser_row is None:
        return BoundedStrings(
            authority="lean_parser",
            reason="parser helper row unavailable",
        )
    if parser_row.parser_candidates.status != "unavailable":
        return parser_row.parser_candidates
    return bounded_strings(
        {"items": list(parser_row.references), "total": len(parser_row.references)},
        cap=MAX_DEPENDENCIES,
        authority="lean_parser",
    )


def bounded_strings(
    raw: Any,
    *,
    cap: int,
    authority: str,
) -> BoundedStrings:
    """Normalize one sorted, deduplicated, finite string collection."""

    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        raw = {"items": raw}
    if not isinstance(raw, Mapping):
        return BoundedStrings(authority=authority)
    items = sorted(
        {
            text
            for item in sequence_value(raw.get("items"))
            for text in [string_or_none(item)]
            if text
        }
    )
    total = integer_at_least(raw.get("total"), len(items))
    visible = tuple(items[:cap])
    truncated = bool(raw.get("truncated")) or total > len(visible)
    status = normalized_collection_status(raw.get("status"), raw)
    return BoundedStrings(
        items=visible,
        total=total,
        truncated=truncated,
        status=status,
        reason=normalized_reason(status, raw.get("reason")),
        authority=authority,
    )


def bounded_binders(raw: Any) -> BoundedBinders:
    """Normalize leading binder rows and their cap state."""

    if not isinstance(raw, Mapping):
        return BoundedBinders()
    items = tuple(
        binder
        for item in sequence_value(raw.get("items"))[:MAX_BINDERS]
        for binder in [normalized_binder(item)]
        if binder is not None
    )
    total = integer_at_least(raw.get("total"), len(items))
    status = normalized_collection_status(raw.get("status"), raw)
    return BoundedBinders(
        items=items,
        total=total,
        truncated=bool(raw.get("truncated")) or total > len(items),
        status=status,
        reason=normalized_reason(status, raw.get("reason")),
    )


def normalized_binder(raw: Any) -> LeanBinderSurface | None:
    """Normalize one helper binder row."""

    if not isinstance(raw, Mapping):
        return None
    type_text = string_or_none(raw.get("type") or raw.get("typeText"))
    if type_text is None:
        return None
    return LeanBinderSurface(
        name=string_or_none(raw.get("name")) or "_",
        binder_info=string_or_none(raw.get("binderInfo")) or "default",
        type_text=bounded_text_value(type_text, MAX_TYPE_BYTES) or "",
        is_premise=bool(raw.get("isPremise")),
    )


def bounded_source_text(raw: Any) -> BoundedText:
    """Normalize one bounded source excerpt."""

    if isinstance(raw, str):
        raw = {"text": raw}
    if not isinstance(raw, Mapping):
        return BoundedText()
    original = string_or_none(raw.get("text")) or ""
    encoded = original.encode("utf-8")
    total = integer_at_least(raw.get("totalBytes"), len(encoded))
    text = encoded[:MAX_STATEMENT_BYTES].decode("utf-8", errors="ignore")
    status = normalized_collection_status(raw.get("status"), raw)
    return BoundedText(
        text=text,
        total_bytes=total,
        truncated=bool(raw.get("truncated")) or total > len(text.encode("utf-8")),
        status=status,
        reason=normalized_reason(status, raw.get("reason")),
    )


def normalized_trust_facts(raw: Any) -> tuple[LeanTrustFact, ...]:
    """Return stable direct trust rows and reject unsupported scopes."""

    rows = {
        (
            str(item["kind"]),
            str(item["scope"]),
            string_or_none(item.get("target")),
        )
        for item in mapping_rows(raw)
        if item.get("kind")
        and item.get("scope") in {"declaration", "type", "value"}
    }
    return tuple(
        LeanTrustFact(kind=kind, scope=scope, target=target)
        for kind, scope, target in sorted(
            rows,
            key=lambda item: (item[0], item[1], item[2] or ""),
        )
    )


def with_imported_stubs(
    declarations: Mapping[str, LeanDeclaration],
) -> dict[str, LeanDeclaration]:
    """Add one deterministic stub per Lean-resolved target outside inventory."""

    combined = dict(declarations)
    for declaration in sorted(declarations.values(), key=lambda item: item.name):
        dependencies = (
            *declaration.type_dependencies.items,
            *declaration.value_dependencies.items,
        )
        for target in sorted(set(dependencies)):
            if target in combined or target == declaration.name:
                continue
            target_module = declaration.surface.dependency_modules.get(
                target,
                imported_module_fallback(target),
            )
            combined[target] = LeanDeclaration(
                name=target,
                module=target_module,
                extraction_backend="lean_environment",
                name_resolution_method="environment_constant",
                confidence="lean_resolved_import",
                is_imported_stub=True,
                resolution="resolved_imported_constant",
            )
    return dict(sorted(combined.items()))


def join_declaration_inventories(
    *inventories: Mapping[str, LeanDeclaration],
) -> dict[str, LeanDeclaration]:
    """Join inventories by fully qualified name, preferring complete rows."""

    joined: dict[str, LeanDeclaration] = {}
    for inventory in inventories:
        for name, declaration in sorted(inventory.items()):
            current = joined.get(name)
            if current is None or current.is_imported_stub:
                joined[name] = declaration
            elif not declaration.is_imported_stub:
                joined[name] = merge_declaration_rows(current, declaration)
    return dict(sorted(joined.items()))


def declaration_surface_json(surface: LeanDeclarationSurface) -> dict[str, Any]:
    """Return the stable report-v2 declaration-surface shape."""

    return {
        "status": surface.status,
        "reason": surface.reason,
        "renderedType": surface.rendered_type,
        "renderedTypeBytes": surface.rendered_type_bytes,
        "renderedTypeTruncated": surface.rendered_type_truncated,
        "printerOptions": dict(sorted(surface.printer_options.items())),
        "binders": bounded_binders_json(surface.binders),
        "premises": bounded_strings_json(surface.premises),
        "conclusion": surface.conclusion,
        "conclusionTruncated": surface.conclusion_truncated,
        "statementExcerpt": bounded_text_json(surface.statement_excerpt),
        "statementRange": surface.statement_range,
        "proofRange": surface.proof_range,
        "hasValue": surface.has_value,
        "proofForm": surface.proof_form,
        "bodyTotalBytes": surface.body_total_bytes,
        "bodyTruncated": surface.body_truncated,
        "declaredAxiom": surface.declared_axiom,
        "unsafe": surface.unsafe,
        "trustFacts": [
            {
                "kind": row.kind,
                "scope": row.scope,
                "target": row.target,
                "authority": row.authority,
                "nonclaim": row.nonclaim,
            }
            for row in surface.trust_facts
        ],
        "backend": surface.backend,
        "helperVersion": surface.helper_version,
        "leanVersion": surface.lean_version,
        "nonclaim": surface.nonclaim,
    }


def bounded_strings_json(rows: BoundedStrings) -> dict[str, Any]:
    """Return one explicit bounded collection shape."""

    return {
        "items": list(rows.items),
        "total": rows.total,
        "truncated": rows.truncated,
        "status": rows.status,
        "reason": rows.reason,
        "authority": rows.authority,
    }


def bounded_binders_json(rows: BoundedBinders) -> dict[str, Any]:
    """Return one explicit bounded binder collection shape."""

    return {
        "items": [
            {
                "name": row.name,
                "binderInfo": row.binder_info,
                "type": row.type_text,
                "isPremise": row.is_premise,
            }
            for row in rows.items
        ],
        "total": rows.total,
        "truncated": rows.truncated,
        "status": rows.status,
        "reason": rows.reason,
    }


def bounded_text_json(row: BoundedText) -> dict[str, Any]:
    """Return one explicit bounded source-text shape."""

    return {
        "text": row.text,
        "totalBytes": row.total_bytes,
        "truncated": row.truncated,
        "status": row.status,
        "reason": row.reason,
    }


def merge_declaration_rows(
    current: LeanDeclaration,
    incoming: LeanDeclaration,
) -> LeanDeclaration:
    """Merge two full rows without collapsing their evidence authorities."""

    preferred = incoming if incoming.surface.status != "unavailable" else current
    other = current if preferred is incoming else incoming
    return replace(
        preferred,
        references=preferred.references or other.references,
        parser_candidates=prefer_available(
            preferred.parser_candidates,
            other.parser_candidates,
        ),
        type_dependencies=prefer_available(
            preferred.type_dependencies,
            other.type_dependencies,
        ),
        value_dependencies=prefer_available(
            preferred.value_dependencies,
            other.value_dependencies,
        ),
    )


def prefer_available(
    first: BoundedStrings,
    second: BoundedStrings,
) -> BoundedStrings:
    """Prefer an observed collection over an unavailable compatibility row."""

    return second if first.status == "unavailable" else first


def declaration_name(row: Mapping[str, Any]) -> str | None:
    """Return the helper's fully qualified declaration name."""

    return string_or_none(
        row.get("fullyQualifiedName")
        or row.get("declarationFullName")
        or row.get("name")
    )


def helper_version(payload: Mapping[str, Any]) -> str | None:
    """Return a helper version from single or batched protocol payloads."""

    return string_or_none(payload.get("helperVersion") or payload.get("version"))


def dependency_modules(raw: Any) -> dict[str, str]:
    """Normalize dependency name-to-module provenance rows."""

    return {
        str(row["name"]): str(row["module"])
        for row in mapping_rows(raw)
        if row.get("name") and row.get("module")
    }


def imported_module_fallback(name: str) -> str:
    """Return a conservative unresolved module label for a named constant."""

    prefix, separator, _ = name.rpartition(".")
    return prefix if separator else "<imported>"


def normalized_range(raw: Any) -> dict[str, int] | None:
    """Normalize helper ranges in nested or report-facing shape."""

    if not isinstance(raw, Mapping):
        return None
    direct_keys = ("startLine", "startColumn", "endLine", "endColumn")
    if all(key in raw for key in direct_keys):
        values = tuple(positive_int(raw.get(key)) for key in direct_keys)
    else:
        start = raw.get("start")
        finish = raw.get("finish")
        if not isinstance(start, Mapping) or not isinstance(finish, Mapping):
            return None
        values = (
            positive_int(start.get("line")),
            positive_int(start.get("column")),
            positive_int(finish.get("line")),
            positive_int(finish.get("column")),
        )
    if any(value is None for value in values):
        return None
    return dict(zip(direct_keys, values, strict=True))


def normalized_status(raw: Any) -> str:
    """Return a report-phase-compatible surface state."""

    value = string_or_none(raw)
    return value if value in {"complete", "partial", "unavailable"} else "unavailable"


def normalized_collection_status(raw: Any, row: Mapping[str, Any]) -> str:
    """Infer complete only when a collection object was actually supplied."""

    value = string_or_none(raw)
    if value in {"complete", "partial", "unavailable"}:
        return value
    return "complete" if "items" in row else "unavailable"


def normalized_reason(status: str, raw: Any) -> str | None:
    """Require an honest reason for unavailable or partial surfaces."""

    if status == "complete":
        return None
    return string_or_none(raw) or "surface was not completely supplied by Lean"


def bounded_text_value(raw: Any, cap: int) -> str | None:
    """Return a UTF-8-safe finite string."""

    value = string_or_none(raw)
    if value is None:
        return None
    return value.encode("utf-8")[:cap].decode("utf-8", errors="ignore")


def string_mapping(raw: Any) -> dict[str, str]:
    """Return a deterministic string-only mapping."""

    if not isinstance(raw, Mapping):
        return {}
    return {
        str(key): str(value)
        for key, value in sorted(raw.items(), key=lambda item: str(item[0]))
    }


def mapping_rows(raw: Any) -> list[Mapping[str, Any]]:
    """Return dictionary rows from an arbitrary JSON value."""

    return [
        row
        for row in sequence_value(raw)
        if isinstance(row, Mapping)
    ]


def sequence_value(raw: Any) -> list[Any]:
    """Return JSON-array-like input without accepting strings as sequences."""

    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        return list(raw)
    return []


def string_or_none(raw: Any) -> str | None:
    """Return a non-empty string or none."""

    if raw is None:
        return None
    value = str(raw)
    return value if value else None


def bool_or_none(raw: Any) -> bool | None:
    """Keep unavailable booleans distinct from false observations."""

    return raw if isinstance(raw, bool) else None


def positive_int(raw: Any) -> int | None:
    """Return one positive integer."""

    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def integer_at_least(raw: Any, minimum: int) -> int:
    """Return a non-negative count no smaller than observed visible rows."""

    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = minimum
    return max(minimum, value, 0)


def utf8_size(raw: str | None) -> int:
    """Return the UTF-8 byte count of optional text."""

    return len(raw.encode("utf-8")) if raw is not None else 0
