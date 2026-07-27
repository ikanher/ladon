"""Compact v3 codec for additive lexical source-index navigation rows.

The source-index model owns module populations and manifests.  This module
owns only the repetitive wire conversion for scope contexts, generic options,
resource settings, and proof-mechanism occurrences.  Compact arrays keep large
indexes bounded; public mapping expansion gives inspection adapters stable
field names without creating a second inventory.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from typing import Any

from ladon.analysis.audit_surface import (
    AuditCommand,
    AuditDiagnostic,
    SourcePosition,
    SourceRange,
)
from ladon.ir import (
    LeanCommandSkeleton,
    LeanLexicalContextCommand,
    LeanLexicalScopeContext,
    LeanModule,
    LeanOptionOccurrence,
    LeanProofMechanismOccurrence,
    LeanResourceSetting,
)
from ladon.source_index_errors import SourceIndexError


def module_navigation_payload(module: LeanModule) -> dict[str, Any]:
    """Encode every additive navigation collection under canonical keys."""

    return {
        "scopeContextCommands": [
            _encode_context_command(row) for row in module.scope_context_commands
        ],
        "scopeContextRows": [
            _encode_scope_context(row) for row in module.scope_contexts
        ],
        "optionRows": [_encode_option(row) for row in module.option_rows],
        "resourceSettings": [_encode_resource(row) for row in module.resource_settings],
        "proofMechanisms": [_encode_mechanism(row) for row in module.proof_mechanisms],
        "auditCommands": [_encode_audit_command(row) for row in module.audit_commands],
        "auditCommandsComplete": module.audit_commands_complete,
        "commandSkeletons": [
            _encode_command_skeleton(row) for row in module.command_skeletons
        ],
        "commandSkeletonsComplete": module.command_skeletons_complete,
    }


def _encode_context_command(row: LeanLexicalContextCommand) -> list[Any]:
    return [
        row.identifier,
        row.kind,
        row.value,
        row.line,
        row.column,
        row.start_offset,
        row.end_offset,
        row.status,
        row.reason,
        row.authority,
        row.nonclaim,
        row.value_total_characters,
        row.value_truncated,
    ]


def _encode_scope_context(row: LeanLexicalScopeContext) -> list[Any]:
    return [
        row.identifier,
        row.status,
        row.reason,
        list(row.namespace_stack),
        list(row.section_stack),
        list(row.variables),
        list(row.omissions),
        list(row.local_notations),
        list(row.local_instances),
        list(row.opened_scopes),
        list(row.exports),
        list(row.source_refs),
        row.omitted_count,
        row.authority,
        row.nonclaim,
    ]


def _encode_option(row: LeanOptionOccurrence) -> list[Any]:
    return [
        row.identifier,
        row.option,
        row.option_class,
        row.raw_value,
        row.raw_value_total_characters,
        row.raw_value_truncated,
        row.lexical_scope,
        row.line,
        row.column,
        row.start_offset,
        row.end_offset,
        row.status,
        row.reason,
        row.declaration_id,
        row.declaration_candidate,
        row.scope_context_id,
        row.authority,
        row.nonclaim,
    ]


def _encode_resource(row: LeanResourceSetting) -> list[Any]:
    return [
        row.identifier,
        row.option_row_id,
        row.option,
        row.raw_value,
        row.numeric_value,
        row.normalized_meaning,
        row.lexical_scope,
        row.line,
        row.column,
        row.start_offset,
        row.end_offset,
        row.status,
        row.reason,
        row.declaration_id,
        row.declaration_candidate,
        row.scope_context_id,
        row.authority,
        row.nonclaim,
    ]


def _encode_mechanism(row: LeanProofMechanismOccurrence) -> list[Any]:
    return [
        row.identifier,
        row.mechanism,
        row.kind,
        row.line,
        row.column,
        row.start_offset,
        row.end_offset,
        row.declaration_id,
        row.declaration_candidate,
        row.attribute,
        row.scope_context_id,
        row.status,
        row.authority,
        row.nonclaim,
    ]


def _encode_audit_command(row: AuditCommand) -> list[Any]:
    source_range = row.source_range
    return [
        row.identifier,
        row.kind,
        [
            source_range.start.line,
            source_range.start.column,
            source_range.start.offset,
            source_range.end.line,
            source_range.end.column,
            source_range.end.offset,
        ],
        row.subject,
        row.subject_total_characters,
        row.subject_truncated,
        row.status,
        [[item.code, item.message] for item in row.diagnostics],
        row.backend,
        row.authority,
        row.referenced_declaration,
        row.referenced_owner,
        row.result_status,
        row.result_authority,
        row.result_reason,
        row.nonclaim,
    ]


def _encode_command_skeleton(row: LeanCommandSkeleton) -> list[Any]:
    return [
        row.identifier,
        row.value,
        row.token_count,
        row.normalization_version,
        row.status,
        row.authority,
        row.nonclaim,
    ]


def decode_context_commands(
    raw: Any,
    *,
    module: str,
    path: str,
) -> tuple[LeanLexicalContextCommand, ...]:
    """Decode one optional context-command collection."""

    return _decode_rows(
        raw,
        lambda row: _decode_context_command(row, module, path),
    )


def decode_scope_contexts(
    raw: Any,
    *,
    module: str,
    path: str,
) -> tuple[LeanLexicalScopeContext, ...]:
    """Decode one optional interned-context collection."""

    return _decode_rows(
        raw,
        lambda row: _decode_scope_context(row, module, path),
    )


def decode_options(
    raw: Any,
    *,
    module: str,
    path: str,
) -> tuple[LeanOptionOccurrence, ...]:
    """Decode one optional generic-option collection."""

    return _decode_rows(raw, lambda row: _decode_option(row, module, path))


def decode_resources(
    raw: Any,
    *,
    module: str,
    path: str,
) -> tuple[LeanResourceSetting, ...]:
    """Decode one optional normalized-resource collection."""

    return _decode_rows(raw, lambda row: _decode_resource(row, module, path))


def decode_mechanisms(
    raw: Any,
    *,
    module: str,
    path: str,
) -> tuple[LeanProofMechanismOccurrence, ...]:
    """Decode one optional proof-mechanism collection."""

    return _decode_rows(raw, lambda row: _decode_mechanism(row, module, path))


def decode_audit_commands(
    raw: Any,
    *,
    module: str,
    path: str,
) -> tuple[AuditCommand, ...]:
    """Decode one optional canonical lexical audit-command collection."""

    return _decode_rows(raw, lambda row: _decode_audit_command(row, module, path))


def decode_command_skeletons(
    raw: Any,
    *,
    module: str,
    path: str,
) -> tuple[LeanCommandSkeleton, ...]:
    """Decode one optional versioned command-skeleton collection."""

    return _decode_rows(
        raw,
        lambda row: _decode_command_skeleton(row, module, path),
    )


def _decode_rows(raw: Any, decoder: Callable[[Any], Any]) -> tuple[Any, ...]:
    if not isinstance(raw, list):
        raise SourceIndexError("source-index navigation collection is malformed")
    return tuple(decoder(row) for row in raw)


def _decode_context_command(
    raw: Any,
    module: str,
    path: str,
) -> LeanLexicalContextCommand:
    if isinstance(raw, Mapping):
        line, column, start, end = _coordinates(raw)
        return LeanLexicalContextCommand(
            _identifier(raw, "scope-command", module, path, start),
            str(raw.get("kind", "unavailable")),
            str(raw.get("module", module)),
            str(raw.get("path", path)),
            str(raw.get("value", "")),
            line,
            column,
            start,
            end,
            str(raw.get("status", "unavailable")),
            _optional_string(raw.get("reason")),
            str(raw.get("authority", "lexical_text")),
            str(raw.get("nonclaim", _default(LeanLexicalContextCommand))),
            _nat(
                raw.get("valueTotalCharacters", len(str(raw.get("value", "")))),
                "scope-command value total",
            ),
            bool(raw.get("valueTruncated", False)),
        )
    row = _compact_sizes(raw, {11, 13}, "scope-context command")
    total = (
        _nat(row[11], "scope-command value total")
        if len(row) == 13
        else len(_string(row[2], "scope-command value"))
    )
    truncated = (
        _boolean(row[12], "scope-command value truncation") if len(row) == 13 else False
    )
    return LeanLexicalContextCommand(
        _string(row[0], "scope-command id"),
        _string(row[1], "scope-command kind"),
        module,
        path,
        _string(row[2], "scope-command value"),
        _nat(row[3], "scope-command line"),
        _nat(row[4], "scope-command column"),
        _nat(row[5], "scope-command start"),
        _nat(row[6], "scope-command end"),
        _string(row[7], "scope-command status"),
        _optional_string(row[8]),
        _string(row[9], "scope-command authority"),
        _string(row[10], "scope-command nonclaim"),
        total,
        truncated,
    )


def _decode_scope_context(
    raw: Any,
    module: str,
    path: str,
) -> LeanLexicalScopeContext:
    if isinstance(raw, Mapping):
        return LeanLexicalScopeContext(
            identifier=_identifier(raw, "scope-context", module, path, 0),
            module=str(raw.get("module", module)),
            path=str(raw.get("path", path)),
            status=str(raw.get("status", "unavailable")),
            reason=_optional_string(raw.get("reason")),
            namespace_stack=_mapping_strings(raw, "namespaceStack"),
            section_stack=_mapping_strings(raw, "sectionStack"),
            variables=_mapping_strings(raw, "variables"),
            omissions=_mapping_strings(raw, "omissions"),
            local_notations=_mapping_strings(raw, "localNotations"),
            local_instances=_mapping_strings(raw, "localInstances"),
            opened_scopes=_mapping_strings(raw, "openedScopes"),
            exports=_mapping_strings(raw, "exports"),
            source_refs=_mapping_strings(raw, "sourceRefs"),
            omitted_count=_nat(
                raw.get("omittedCount", 0),
                "scope-context omitted count",
            ),
            authority=str(raw.get("authority", "lexical_text")),
            nonclaim=str(raw.get("nonclaim", _default(LeanLexicalScopeContext))),
        )
    row = _compact(raw, 15, "scope-context row")
    return LeanLexicalScopeContext(
        _string(row[0], "scope-context id"),
        module,
        path,
        _string(row[1], "scope-context status"),
        _optional_string(row[2]),
        *(
            _strings(row[index], f"scope-context field {index}")
            for index in range(3, 12)
        ),
        _nat(row[12], "scope-context omitted count"),
        _string(row[13], "scope-context authority"),
        _string(row[14], "scope-context nonclaim"),
    )


def _decode_option(
    raw: Any,
    module: str,
    path: str,
) -> LeanOptionOccurrence:
    if isinstance(raw, Mapping):
        line, column, start, end = _coordinates(raw)
        value = str(raw.get("rawValue", ""))
        return LeanOptionOccurrence(
            _identifier(raw, "option", module, path, start),
            str(raw.get("module", module)),
            str(raw.get("path", path)),
            str(raw.get("option", raw.get("name", "unavailable"))),
            str(raw.get("optionClass", raw.get("class", "unavailable"))),
            value,
            _nat(
                raw.get("rawValueTotalCharacters", len(value)),
                "option raw-value total",
            ),
            bool(raw.get("rawValueTruncated", False)),
            str(raw.get("lexicalScope", raw.get("scope", "unavailable"))),
            line,
            column,
            start,
            end,
            str(raw.get("status", "unavailable")),
            _optional_string(raw.get("reason")),
            _optional_string(raw.get("declarationId")),
            _optional_string(raw.get("declarationCandidate")),
            _optional_string(raw.get("scopeContextId")),
            str(raw.get("authority", "lexical_text")),
            str(raw.get("nonclaim", _default(LeanOptionOccurrence))),
        )
    row = _compact(raw, 18, "option row")
    return LeanOptionOccurrence(
        _string(row[0], "option id"),
        module,
        path,
        _string(row[1], "option name"),
        _string(row[2], "option class"),
        _string(row[3], "option raw value"),
        _nat(row[4], "option raw-value total"),
        _boolean(row[5], "option raw-value truncation"),
        _string(row[6], "option lexical scope"),
        _nat(row[7], "option line"),
        _nat(row[8], "option column"),
        _nat(row[9], "option start"),
        _nat(row[10], "option end"),
        _string(row[11], "option status"),
        _optional_string(row[12]),
        _optional_string(row[13]),
        _optional_string(row[14]),
        _optional_string(row[15]),
        _string(row[16], "option authority"),
        _string(row[17], "option nonclaim"),
    )


def _decode_resource(
    raw: Any,
    module: str,
    path: str,
) -> LeanResourceSetting:
    if isinstance(raw, Mapping):
        line, column, start, end = _coordinates(raw)
        return LeanResourceSetting(
            _identifier(raw, "resource", module, path, start),
            str(raw.get("optionRowId", "source-option-row-unavailable")),
            str(raw.get("module", module)),
            str(raw.get("path", path)),
            str(raw.get("option", raw.get("name", "unavailable"))),
            str(raw.get("rawValue", "")),
            _optional_nat(raw.get("numericValue"), "resource numeric value"),
            _optional_string(raw.get("normalizedMeaning", raw.get("meaning"))),
            str(raw.get("lexicalScope", raw.get("scope", "unavailable"))),
            line,
            column,
            start,
            end,
            str(raw.get("status", "unavailable")),
            _optional_string(raw.get("reason")),
            _optional_string(raw.get("declarationId")),
            _optional_string(raw.get("declarationCandidate")),
            _optional_string(raw.get("scopeContextId")),
            str(raw.get("authority", "lexical_text")),
            str(raw.get("nonclaim", _default(LeanResourceSetting))),
        )
    row = _compact(raw, 18, "resource setting")
    return LeanResourceSetting(
        _string(row[0], "resource id"),
        _string(row[1], "resource option-row id"),
        module,
        path,
        _string(row[2], "resource option"),
        _string(row[3], "resource raw value"),
        _optional_nat(row[4], "resource numeric value"),
        _optional_string(row[5]),
        _string(row[6], "resource lexical scope"),
        _nat(row[7], "resource line"),
        _nat(row[8], "resource column"),
        _nat(row[9], "resource start"),
        _nat(row[10], "resource end"),
        _string(row[11], "resource status"),
        _optional_string(row[12]),
        _optional_string(row[13]),
        _optional_string(row[14]),
        _optional_string(row[15]),
        _string(row[16], "resource authority"),
        _string(row[17], "resource nonclaim"),
    )


def _decode_mechanism(
    raw: Any,
    module: str,
    path: str,
) -> LeanProofMechanismOccurrence:
    if isinstance(raw, Mapping):
        return _mapping_mechanism(raw, module, path)
    row = _compact(raw, 14, "proof-mechanism row")
    return LeanProofMechanismOccurrence(
        _string(row[0], "mechanism id"),
        module,
        path,
        _string(row[1], "mechanism name"),
        _string(row[2], "mechanism kind"),
        _nat(row[3], "mechanism line"),
        _nat(row[4], "mechanism column"),
        _nat(row[5], "mechanism start"),
        _nat(row[6], "mechanism end"),
        _string(row[7], "mechanism declaration id"),
        _string(row[8], "mechanism declaration candidate"),
        _optional_string(row[9]),
        _optional_string(row[10]),
        _string(row[11], "mechanism status"),
        _string(row[12], "mechanism authority"),
        _string(row[13], "mechanism nonclaim"),
    )


def _decode_command_skeleton(
    raw: Any,
    module: str,
    path: str,
) -> LeanCommandSkeleton:
    if isinstance(raw, Mapping):
        return LeanCommandSkeleton(
            _identifier(raw, "command-skeleton", module, path, 0),
            str(raw.get("module", module)),
            str(raw.get("path", path)),
            _string(raw.get("value"), "command-skeleton value"),
            _nat(raw.get("tokenCount"), "command-skeleton token count"),
            _string(
                raw.get("normalizationVersion"),
                "command-skeleton normalization version",
            ),
            str(raw.get("status", "unavailable")),
            str(raw.get("authority", "lexical_text")),
            str(raw.get("nonclaim", _default(LeanCommandSkeleton))),
        )
    row = _compact(raw, 7, "command skeleton")
    return LeanCommandSkeleton(
        _string(row[0], "command-skeleton id"),
        module,
        path,
        _string(row[1], "command-skeleton value"),
        _nat(row[2], "command-skeleton token count"),
        _string(row[3], "command-skeleton normalization version"),
        _string(row[4], "command-skeleton status"),
        _string(row[5], "command-skeleton authority"),
        _string(row[6], "command-skeleton nonclaim"),
    )


def _decode_audit_command(
    raw: Any,
    module: str,
    path: str,
) -> AuditCommand:
    if isinstance(raw, Mapping):
        return _mapping_audit_command(raw, module, path)
    row = _compact(raw, 16, "audit command")
    source_range = _compact(row[2], 6, "audit command source range")
    return AuditCommand(
        identifier=_string(row[0], "audit-command id"),
        kind=_string(row[1], "audit-command kind"),
        module=module,
        path=path,
        source_range=_audit_source_range(source_range),
        subject=_string(row[3], "audit-command subject"),
        subject_total_characters=_nat(
            row[4],
            "audit-command subject total",
        ),
        subject_truncated=_boolean(
            row[5],
            "audit-command subject truncation",
        ),
        status=_string(row[6], "audit-command status"),
        diagnostics=_audit_diagnostics(row[7]),
        backend=_string(row[8], "audit-command backend"),
        authority=_string(row[9], "audit-command authority"),
        referenced_declaration=_optional_string(row[10]),
        referenced_owner=_optional_string(row[11]),
        result_status=_string(row[12], "audit-command result status"),
        result_authority=_optional_string(row[13]),
        result_reason=_string(row[14], "audit-command result reason"),
        nonclaim=_string(row[15], "audit-command nonclaim"),
    )


def _mapping_audit_command(
    raw: Mapping[str, Any],
    module: str,
    path: str,
) -> AuditCommand:
    source_range = raw.get("sourceRange")
    if not isinstance(source_range, Mapping):
        raise SourceIndexError("source-index audit-command range is malformed")
    return AuditCommand(
        identifier=_required_identifier(raw, "audit-command id"),
        kind=_string(raw.get("kind"), "audit-command kind"),
        module=_owned_text(raw.get("module"), module, "audit-command module"),
        path=_owned_text(raw.get("path"), path, "audit-command path"),
        source_range=_mapping_audit_source_range(source_range),
        subject=_string(raw.get("subject", ""), "audit-command subject"),
        subject_total_characters=_nat(
            raw.get(
                "subjectTotalCharacters",
                len(str(raw.get("subject", ""))),
            ),
            "audit-command subject total",
        ),
        subject_truncated=_mapping_boolean(
            raw,
            "subjectTruncated",
            default=False,
        ),
        status=str(raw.get("status", "unavailable")),
        diagnostics=_audit_diagnostics(raw.get("diagnostics", [])),
        backend=str(raw.get("backend", "text")),
        authority=str(raw.get("authority", "lexical_text")),
        referenced_declaration=_optional_string(
            raw.get("referencedDeclaration"),
        ),
        referenced_owner=_optional_string(raw.get("referencedOwner")),
        result_status=str(raw.get("resultStatus", "unavailable")),
        result_authority=_optional_string(raw.get("resultAuthority")),
        result_reason=str(
            raw.get(
                "resultReason",
                "Lean enrichment was not requested by lexical extraction",
            )
        ),
        nonclaim=str(
            raw.get(
                "nonclaim",
                "Lexical audit intent only; no elaboration result is implied.",
            )
        ),
    )


def _audit_source_range(raw: list[Any]) -> SourceRange:
    source_range = SourceRange(
        SourcePosition(
            _positive(raw[0], "audit-command start line"),
            _positive(raw[1], "audit-command start column"),
            _nat(raw[2], "audit-command start offset"),
        ),
        SourcePosition(
            _positive(raw[3], "audit-command end line"),
            _positive(raw[4], "audit-command end column"),
            _nat(raw[5], "audit-command end offset"),
        ),
    )
    if source_range.end.offset < source_range.start.offset:
        raise SourceIndexError("source-index audit-command range is reversed")
    return source_range


def _mapping_audit_source_range(raw: Mapping[str, Any]) -> SourceRange:
    start = raw.get("start")
    end = raw.get("end")
    if not isinstance(start, Mapping) or not isinstance(end, Mapping):
        raise SourceIndexError("source-index audit-command range is malformed")
    return _audit_source_range(
        [
            start.get("line"),
            start.get("column"),
            start.get("offset"),
            end.get("line"),
            end.get("column"),
            end.get("offset"),
        ]
    )


def _audit_diagnostics(raw: Any) -> tuple[AuditDiagnostic, ...]:
    if not isinstance(raw, list):
        raise SourceIndexError("source-index audit diagnostics are malformed")
    return tuple(_audit_diagnostic(row) for row in raw)


def _audit_diagnostic(raw: Any) -> AuditDiagnostic:
    if isinstance(raw, Mapping):
        return AuditDiagnostic(
            _string(raw.get("code"), "audit diagnostic code"),
            _string(raw.get("message"), "audit diagnostic message"),
        )
    row = _compact(raw, 2, "audit diagnostic")
    return AuditDiagnostic(
        _string(row[0], "audit diagnostic code"),
        _string(row[1], "audit diagnostic message"),
    )


def _mapping_mechanism(
    raw: Mapping[str, Any],
    module: str,
    path: str,
) -> LeanProofMechanismOccurrence:
    line, column, start, end = _coordinates(raw)
    mechanism = str(
        raw.get("mechanism", raw.get("token", raw.get("name", "unavailable")))
    )
    candidate = str(
        raw.get(
            "declarationCandidate",
            raw.get("candidateName", raw.get("declaration", "unavailable")),
        )
    )
    return LeanProofMechanismOccurrence(
        _identifier(raw, "proof-mechanism", module, path, start),
        str(raw.get("module", module)),
        str(raw.get("path", path)),
        mechanism,
        str(raw.get("kind", "unavailable")),
        line,
        column,
        start,
        end,
        str(raw.get("declarationId", "declaration-unavailable")),
        candidate,
        _optional_string(raw.get("attribute")),
        _optional_string(raw.get("scopeContextId")),
        str(raw.get("status", "unavailable")),
        str(raw.get("authority", "lexical_text")),
        str(raw.get("nonclaim", _default(LeanProofMechanismOccurrence))),
    )


def source_index_collection_mapping(
    collection: str,
    raw: Any,
    *,
    module: str,
    path: str,
) -> dict[str, Any]:
    """Expand one compact row into stable inspection field names."""

    if isinstance(raw, Mapping):
        return dict(raw)
    decoders: dict[str, Callable[[], Any]] = {
        "scopeContextCommands": lambda: _decode_context_command(raw, module, path),
        "scopeContextRows": lambda: _decode_scope_context(raw, module, path),
        "optionRows": lambda: _decode_option(raw, module, path),
        "resourceSettings": lambda: _decode_resource(raw, module, path),
        "proofMechanisms": lambda: _decode_mechanism(raw, module, path),
        "auditCommands": lambda: _decode_audit_command(raw, module, path),
        "commandSkeletons": lambda: _decode_command_skeleton(raw, module, path),
    }
    mappings: dict[str, Callable[[Any], dict[str, Any]]] = {
        "scopeContextCommands": _context_command_mapping,
        "scopeContextRows": _scope_context_mapping,
        "optionRows": _option_mapping,
        "resourceSettings": _resource_mapping,
        "proofMechanisms": _mechanism_mapping,
        "auditCommands": lambda row: row.to_dict(),
        "commandSkeletons": _command_skeleton_mapping,
    }
    if collection not in decoders:
        raise SourceIndexError(f"unsupported source-index collection {collection!r}")
    return mappings[collection](decoders[collection]())


def source_index_option_mapping(
    row: LeanOptionOccurrence,
) -> dict[str, Any]:
    """Return the canonical inspection mapping for one typed option row."""

    return _option_mapping(row)


def source_index_proof_mechanism_mapping(
    row: LeanProofMechanismOccurrence,
) -> dict[str, Any]:
    """Return the canonical inspection mapping for one typed mechanism row."""

    return _mechanism_mapping(row)


def _context_command_mapping(
    row: LeanLexicalContextCommand,
) -> dict[str, Any]:
    return {
        "id": row.identifier,
        "kind": row.kind,
        "module": row.module,
        "path": row.path,
        "value": row.value,
        "sourceRange": row.source_range,
        "status": row.status,
        "reason": row.reason,
        "authority": row.authority,
        "nonclaim": row.nonclaim,
        "valueTotalCharacters": row.value_total_characters,
        "valueTruncated": row.value_truncated,
    }


def _scope_context_mapping(row: LeanLexicalScopeContext) -> dict[str, Any]:
    return {
        "id": row.identifier,
        "module": row.module,
        "path": row.path,
        "status": row.status,
        "reason": row.reason,
        "namespaceStack": list(row.namespace_stack),
        "sectionStack": list(row.section_stack),
        "variables": list(row.variables),
        "omissions": list(row.omissions),
        "localNotations": list(row.local_notations),
        "localInstances": list(row.local_instances),
        "openedScopes": list(row.opened_scopes),
        "exports": list(row.exports),
        "sourceRefs": list(row.source_refs),
        "omittedCount": row.omitted_count,
        "authority": row.authority,
        "nonclaim": row.nonclaim,
    }


def _option_mapping(row: LeanOptionOccurrence) -> dict[str, Any]:
    return {
        "id": row.identifier,
        "module": row.module,
        "path": row.path,
        "sourceRange": row.source_range,
        "option": row.option,
        "optionClass": row.option_class,
        "rawValue": row.raw_value,
        "rawValueTotalCharacters": row.raw_value_total_characters,
        "rawValueTruncated": row.raw_value_truncated,
        "lexicalScope": row.lexical_scope,
        "status": row.status,
        "reason": row.reason,
        "declarationId": row.declaration_id,
        "declarationCandidate": row.declaration_candidate,
        "scopeContextId": row.scope_context_id,
        "authority": row.authority,
        "nonclaim": row.nonclaim,
    }


def _resource_mapping(row: LeanResourceSetting) -> dict[str, Any]:
    return {
        "id": row.identifier,
        "optionRowId": row.option_row_id,
        "module": row.module,
        "path": row.path,
        "sourceRange": row.source_range,
        "option": row.option,
        "rawValue": row.raw_value,
        "numericValue": row.numeric_value,
        "normalizedMeaning": row.normalized_meaning,
        "lexicalScope": row.lexical_scope,
        "status": row.status,
        "reason": row.reason,
        "declarationId": row.declaration_id,
        "declarationCandidate": row.declaration_candidate,
        "scopeContextId": row.scope_context_id,
        "authority": row.authority,
        "nonclaim": row.nonclaim,
    }


def _mechanism_mapping(
    row: LeanProofMechanismOccurrence,
) -> dict[str, Any]:
    return {
        "id": row.identifier,
        "module": row.module,
        "path": row.path,
        "sourceRange": row.source_range,
        "mechanism": row.mechanism,
        "kind": row.kind,
        "attribute": row.attribute,
        "declarationId": row.declaration_id,
        "declarationCandidate": row.declaration_candidate,
        "scopeContextId": row.scope_context_id,
        "status": row.status,
        "authority": row.authority,
        "nonclaim": row.nonclaim,
    }


def _command_skeleton_mapping(
    row: LeanCommandSkeleton,
) -> dict[str, Any]:
    return {
        "id": row.identifier,
        "module": row.module,
        "path": row.path,
        "value": row.value,
        "tokenCount": row.token_count,
        "normalizationVersion": row.normalization_version,
        "status": row.status,
        "authority": row.authority,
        "nonclaim": row.nonclaim,
    }


def _compact(raw: Any, size: int, label: str) -> list[Any]:
    if not isinstance(raw, list) or len(raw) != size:
        raise SourceIndexError(f"compact source-index {label} is malformed")
    return raw


def _compact_sizes(
    raw: Any,
    sizes: set[int],
    label: str,
) -> list[Any]:
    if not isinstance(raw, list) or len(raw) not in sizes:
        raise SourceIndexError(f"compact source-index {label} is malformed")
    return raw


def _string(raw: Any, label: str) -> str:
    if not isinstance(raw, str):
        raise SourceIndexError(f"source-index {label} is malformed")
    return raw


def _required_identifier(raw: Mapping[str, Any], label: str) -> str:
    value = _string(raw.get("id"), label)
    if not value:
        raise SourceIndexError(f"source-index {label} is empty")
    return value


def _owned_text(raw: Any, expected: str, label: str) -> str:
    value = expected if raw is None else _string(raw, label)
    if value != expected:
        raise SourceIndexError(f"source-index {label} does not match its owner")
    return value


def _optional_string(raw: Any) -> str | None:
    if raw is None:
        return None
    return _string(raw, "optional string")


def _nat(raw: Any, label: str) -> int:
    if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0:
        raise SourceIndexError(f"source-index {label} is malformed")
    return raw


def _positive(raw: Any, label: str) -> int:
    value = _nat(raw, label)
    if value < 1:
        raise SourceIndexError(f"source-index {label} is malformed")
    return value


def _optional_nat(raw: Any, label: str) -> int | None:
    return None if raw is None else _nat(raw, label)


def _boolean(raw: Any, label: str) -> bool:
    if not isinstance(raw, bool):
        raise SourceIndexError(f"source-index {label} is malformed")
    return raw


def _mapping_boolean(
    row: Mapping[str, Any],
    key: str,
    *,
    default: bool,
) -> bool:
    return _boolean(row.get(key, default), f"audit-command {key}")


def _strings(raw: Any, label: str) -> tuple[str, ...]:
    if not isinstance(raw, list) or not all(isinstance(row, str) for row in raw):
        raise SourceIndexError(f"source-index {label} is malformed")
    return tuple(raw)


def _mapping_strings(
    row: Mapping[str, Any],
    key: str,
) -> tuple[str, ...]:
    return _strings(row.get(key, []), key)


def _coordinates(row: Mapping[str, Any]) -> tuple[int, int, int, int]:
    source_range = row.get("sourceRange", row.get("range"))
    range_row = source_range if isinstance(source_range, Mapping) else {}
    start_row = range_row.get("start")
    end_row = range_row.get("end")
    start = start_row if isinstance(start_row, Mapping) else {}
    end = end_row if isinstance(end_row, Mapping) else {}
    start_offset = row.get("startOffset", start.get("offset", 0))
    return (
        _nat(row.get("line", start.get("line", 0)), "lexical row line"),
        _nat(row.get("column", start.get("column", 0)), "lexical row column"),
        _nat(start_offset, "lexical row start"),
        _nat(
            row.get("endOffset", end.get("offset", start_offset)),
            "lexical row end",
        ),
    )


def _identifier(
    row: Mapping[str, Any],
    kind: str,
    module: str,
    path: str,
    start: int,
) -> str:
    direct = row.get("id")
    if isinstance(direct, str) and direct:
        return direct
    encoded = json.dumps(
        {
            "kind": kind,
            "module": module,
            "path": path,
            "startOffset": start,
            "row": dict(row),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:20]
    return f"ladon.lexical_{kind.replace('-', '_')}.legacy.{digest}"


def _default(model: type[Any]) -> str:
    return str(model.__dataclass_fields__["nonclaim"].default)


__all__ = [
    "decode_audit_commands",
    "decode_command_skeletons",
    "decode_context_commands",
    "decode_mechanisms",
    "decode_options",
    "decode_resources",
    "decode_scope_contexts",
    "module_navigation_payload",
    "source_index_collection_mapping",
    "source_index_option_mapping",
    "source_index_proof_mechanism_mapping",
]
