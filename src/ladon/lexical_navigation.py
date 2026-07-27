"""Canonical lexical navigation rows over one offset-preserving source mask.

The caller supplies the single comment/string mask already used for imports
and declarations.  This pass never reopens a file, remasks source, invokes
Lean, or upgrades lexical context into an elaboration claim.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Sequence

from ladon.ir import (
    LeanCommandSkeleton,
    LeanLexicalContextCommand,
    LeanLexicalScopeContext,
    LeanOptionOccurrence,
    LeanProofMechanismOccurrence,
    LeanResourceSetting,
    LeanTextDeclaration,
)
from ladon.lexical_command_skeleton import scan_command_skeleton
from ladon.lexical_occurrences import (
    ATTRIBUTE_TOKENS,
    LEXICAL_NAVIGATION_VERSION,
    MAX_LEXICAL_VALUE_CHARACTERS,
    RESOURCE_OPTIONS,
    TACTIC_TOKENS,
    bounded_lexical_text,
    mechanism_order,
    option_matches,
    option_occurrence,
    option_order,
    proof_mechanisms,
    resource_order,
    resource_setting,
)


LEXICAL_CONTEXT_VERSION = "ladon-lexical-scope-context-v1"
MAX_CONTEXT_ITEMS = 32
MAX_CONTEXT_REFERENCES = 96
_LEAN_NAME = r"[A-Za-z_][A-Za-z0-9_']*"
_LEAN_QUALIFIED_NAME = rf"{_LEAN_NAME}(?:\.{_LEAN_NAME})*"
_SCOPE_COMMAND_RE = re.compile(
    r"(?m)^[ \t]*(?P<kind>namespace|section|end|mutual)\b"
    r"(?P<body>[^\n]*)"
)
_CONTEXT_COMMAND_RE = re.compile(
    r"(?m)^[ \t]*(?:"
    r"(?P<variable>variables?)"
    r"|(?P<omit>omit)"
    r"|(?P<local_notation>local[ \t]+notation)"
    r"|(?P<local_instance>local[ \t]+instance)"
    r"|(?P<open_scoped>open[ \t]+scoped)"
    r"|(?P<export>export)"
    r")\b(?P<body>[^\n]*)"
)
_IN_TOKEN_RE = re.compile(r"(?:^|\s)in(?:\s|$)")
_SCOPE_NAME_RE = re.compile(_LEAN_QUALIFIED_NAME)
_NAVIGATION_COMMAND_HINT_RE = re.compile(
    r"\b(?:namespace|section|end|mutual|variables?|omit|local|open|export|set_option)\b"
)


@dataclass(frozen=True)
class LexicalNavigationSurface:
    """All additive lexical rows produced from one immutable source string."""

    declarations: tuple[LeanTextDeclaration, ...]
    context_commands: tuple[LeanLexicalContextCommand, ...]
    scope_contexts: tuple[LeanLexicalScopeContext, ...]
    option_rows: tuple[LeanOptionOccurrence, ...]
    resource_settings: tuple[LeanResourceSetting, ...]
    proof_mechanisms: tuple[LeanProofMechanismOccurrence, ...]
    command_skeletons: tuple[LeanCommandSkeleton, ...]


@dataclass
class _ScopeFrame:
    """One bounded lexical frame and its active context commands."""

    kind: str
    name: str | None
    start_offset: int
    source_refs: list[str] = field(default_factory=list)
    items: dict[str, list[str]] = field(default_factory=dict)
    omitted_count: int = 0
    safe: bool = True


@dataclass
class _NavigationState:
    """Mutable state local to one immutable lexical scan."""

    module: str
    path: str
    frames: list[_ScopeFrame]
    commands: dict[str, LeanLexicalContextCommand] = field(default_factory=dict)
    contexts: dict[str, LeanLexicalScopeContext] = field(default_factory=dict)
    pending_omissions: list[str] = field(default_factory=list)
    unresolved_reason: str | None = None
    revision: int = 0
    context_cache: dict[
        tuple[int, tuple[str, ...], tuple[str, ...], tuple[str, ...], str | None],
        LeanLexicalScopeContext,
    ] = field(default_factory=dict)

    @property
    def safe(self) -> bool:
        """Return whether every active lexical frame is understood."""

        return self.unresolved_reason is None and all(
            frame.safe for frame in self.frames
        )


@dataclass(frozen=True)
class _Event:
    start: int
    priority: int
    kind: str
    value: Any


def scan_lexical_navigation(
    text: str,
    masked: str,
    declarations: Sequence[LeanTextDeclaration],
    *,
    module: str,
    path: str,
    command_masked: str | None = None,
) -> LexicalNavigationSurface:
    """Return typed navigation rows over an existing source mask."""

    state = _NavigationState(module, path, [_ScopeFrame("module", None, 0)])
    declaration_rows: list[LeanTextDeclaration] = []
    option_rows: list[LeanOptionOccurrence] = []
    for event in _navigation_events(masked, declarations):
        if event.kind == "declaration":
            declaration_rows.append(_attach_context(state, event.value))
        elif event.kind == "option":
            option_rows.append(
                _option_event(
                    state,
                    text,
                    masked,
                    event.value,
                    declarations,
                )
            )
        elif event.kind == "scope":
            _apply_scope_event(state, text, masked, event.value)
        else:
            _apply_context_event(state, text, masked, event.value)
    declaration_rows = _finalize_declarations(state, declaration_rows)
    option_rows = _finalize_options(state, option_rows)
    resources = tuple(
        setting
        for option in option_rows
        for setting in [resource_setting(option)]
        if setting is not None
    )
    mechanisms = proof_mechanisms(
        masked,
        declaration_rows,
        module=module,
        path=path,
    )
    skeletons = scan_command_skeleton(
        masked if command_masked is None else command_masked,
        module=module,
        path=path,
    )
    return LexicalNavigationSurface(
        declarations=tuple(declaration_rows),
        context_commands=tuple(sorted(state.commands.values(), key=_command_order)),
        scope_contexts=tuple(
            sorted(state.contexts.values(), key=lambda row: row.identifier)
        ),
        option_rows=tuple(sorted(option_rows, key=option_order)),
        resource_settings=tuple(sorted(resources, key=resource_order)),
        proof_mechanisms=tuple(sorted(mechanisms, key=mechanism_order)),
        command_skeletons=skeletons,
    )


def _navigation_events(
    masked: str,
    declarations: Sequence[LeanTextDeclaration],
) -> list[_Event]:
    events = [
        _Event(_declaration_start(row), 0, "declaration", row) for row in declarations
    ]
    if _NAVIGATION_COMMAND_HINT_RE.search(masked) is None:
        return events
    events.extend(
        _Event(match.start(), 1, "context", match)
        for match in _CONTEXT_COMMAND_RE.finditer(masked)
    )
    events.extend(
        _Event(match.start(), 1, "scope", match)
        for match in _SCOPE_COMMAND_RE.finditer(masked)
    )
    events.extend(
        _Event(match.start(), 1, "option", match) for match in option_matches(masked)
    )
    return sorted(events, key=lambda row: (row.start, row.priority, row.kind))


def _declaration_start(row: LeanTextDeclaration) -> int:
    return (
        row.block_start_offset
        if row.block_start_offset is not None
        else row.start_offset
    )


def _attach_context(
    state: _NavigationState,
    declaration: LeanTextDeclaration,
) -> LeanTextDeclaration:
    context = _intern_context(
        state,
        namespace_stack=declaration.namespace_stack,
        section_stack=declaration.section_stack,
        extra_refs=tuple(state.pending_omissions),
        forced_reason=(
            "declaration scope is unresolved"
            if declaration.candidate_status != "lexical_candidate"
            else None
        ),
    )
    state.pending_omissions.clear()
    return replace(
        declaration,
        scope_context_id=context.identifier,
        scope_context_status=context.status,
    )


def _option_event(
    state: _NavigationState,
    text: str,
    masked: str,
    match: re.Match[str],
    declarations: Sequence[LeanTextDeclaration],
) -> LeanOptionOccurrence:
    context = _intern_context(
        state,
        namespace_stack=_namespace_stack(state.frames),
        section_stack=_section_stack(state.frames),
    )
    return option_occurrence(
        text,
        masked,
        match,
        declarations,
        module=state.module,
        path=state.path,
        scope_context_id=context.identifier,
    )


def _apply_scope_event(
    state: _NavigationState,
    text: str,
    masked: str,
    match: re.Match[str],
) -> None:
    state.revision += 1
    kind = match.group("kind")
    body, total, truncated = _bounded_command_body(text, masked, match)
    command = _command(
        state,
        masked,
        match,
        kind,
        body,
        "parsed",
        None,
        total,
        truncated,
    )
    state.commands[command.identifier] = command
    if kind == "end":
        _close_frame(state, body)
    elif kind == "mutual":
        _open_mutual(state, body, match.start(), command.identifier)
    else:
        _open_named_frame(
            state,
            kind,
            body,
            match.start(),
            command.identifier,
            truncated=truncated,
        )


def _open_named_frame(
    state: _NavigationState,
    kind: str,
    body: str,
    start: int,
    source_ref: str,
    *,
    truncated: bool,
) -> None:
    valid = not truncated and _valid_scope_body(kind, body)
    if not valid:
        state.unresolved_reason = f"unsupported {kind} scope syntax"
    state.frames.append(
        _ScopeFrame(
            kind,
            body or None,
            start,
            source_refs=[source_ref],
            safe=valid,
        )
    )


def _valid_scope_body(kind: str, body: str) -> bool:
    if kind == "namespace":
        return bool(_SCOPE_NAME_RE.fullmatch(body))
    return not body or bool(_SCOPE_NAME_RE.fullmatch(body))


def _open_mutual(
    state: _NavigationState,
    body: str,
    start: int,
    source_ref: str,
) -> None:
    if body:
        state.unresolved_reason = "unsupported mutual scope syntax"
    state.frames.append(
        _ScopeFrame(
            "mutual",
            None,
            start,
            source_refs=[source_ref],
            safe=False,
        )
    )


def _close_frame(state: _NavigationState, body: str) -> None:
    if len(state.frames) == 1:
        state.unresolved_reason = "unmatched end command"
        return
    frame = state.frames[-1]
    if body and body != frame.name:
        state.unresolved_reason = "mismatched end command"
        return
    state.frames.pop()


def _apply_context_event(
    state: _NavigationState,
    text: str,
    masked: str,
    match: re.Match[str],
) -> None:
    state.revision += 1
    kind = _context_kind(match)
    body, total, truncated, has_omit_scope = _context_body(
        kind,
        text,
        masked,
        match,
    )
    status, reason = _context_status(kind, body, has_omit_scope)
    command = _command(
        state,
        masked,
        match,
        kind,
        body,
        status,
        reason,
        total,
        truncated,
    )
    state.commands[command.identifier] = command
    state.frames[-1].omitted_count += int(truncated)
    if status != "parsed":
        state.frames[-1].safe = False
    elif kind == "omit":
        state.pending_omissions.append(command.identifier)
    else:
        _activate_command(state.frames[-1], kind, command.identifier)


def _context_kind(match: re.Match[str]) -> str:
    return next(
        kind
        for kind in (
            "variable",
            "omit",
            "local_notation",
            "local_instance",
            "open_scoped",
            "export",
        )
        if match.group(kind) is not None
    )


def _context_body(
    kind: str,
    text: str,
    masked: str,
    match: re.Match[str],
) -> tuple[str, int, bool, bool]:
    if kind != "omit":
        value, total, truncated = _bounded_command_body(text, masked, match)
        return value, total, truncated, False
    start = match.start("body")
    end = match.end("body")
    scope = _IN_TOKEN_RE.search(masked[start:end])
    if scope is None:
        value, total, truncated = _bounded_command_body(text, masked, match)
        return value, total, truncated, False
    visible_end = _visible_end(masked, start, start + scope.start())
    value, total, truncated = bounded_lexical_text(text[start:visible_end].strip())
    return value, total, truncated, True


def _context_status(
    kind: str,
    body: str,
    has_omit_scope: bool,
) -> tuple[str, str | None]:
    if not body:
        return "unresolved", f"{kind} command has no bounded lexical body"
    if kind == "omit" and not has_omit_scope:
        return "unresolved", "omit command has no safely recognized in scope"
    return "parsed", None


def _activate_command(frame: _ScopeFrame, kind: str, identifier: str) -> None:
    values = frame.items.setdefault(kind, [])
    if len(values) < MAX_CONTEXT_ITEMS:
        values.append(identifier)
    else:
        frame.omitted_count += 1


def _command(
    state: _NavigationState,
    masked: str,
    match: re.Match[str],
    kind: str,
    value: str,
    status: str,
    reason: str | None,
    value_total: int,
    value_truncated: bool,
) -> LeanLexicalContextCommand:
    start = match.start()
    end = _visible_end(masked, start, match.end())
    line, column = _position(masked, start)
    identifier = _stable_id(
        "scope-command",
        {
            "version": LEXICAL_NAVIGATION_VERSION,
            "module": state.module,
            "path": state.path,
            "kind": kind,
            "startOffset": start,
            "value": value,
        },
    )
    return LeanLexicalContextCommand(
        identifier=identifier,
        kind=kind,
        module=state.module,
        path=state.path,
        value=value,
        line=line,
        column=column,
        start_offset=start,
        end_offset=end,
        status=status,
        reason=reason,
        value_total_characters=value_total,
        value_truncated=value_truncated,
    )


def _intern_context(
    state: _NavigationState,
    *,
    namespace_stack: tuple[str, ...],
    section_stack: tuple[str, ...],
    extra_refs: tuple[str, ...] = (),
    forced_reason: str | None = None,
) -> LeanLexicalScopeContext:
    cache_key = (
        state.revision,
        namespace_stack,
        section_stack,
        extra_refs,
        forced_reason,
    )
    cached = state.context_cache.get(cache_key)
    if cached is not None:
        return cached
    active = _active_refs(state.frames, extra_refs)
    values = _active_values(state.commands, active)
    source_refs = _context_source_refs(state.frames, active)
    omitted = sum(frame.omitted_count for frame in state.frames)
    reason = forced_reason or state.unresolved_reason
    status = "unresolved" if reason or not state.safe else "complete"
    fields = _context_fields(
        namespace_stack,
        section_stack,
        values,
        source_refs,
        omitted,
    )
    identifier = _stable_id(
        "scope-context",
        {
            "version": LEXICAL_CONTEXT_VERSION,
            "module": state.module,
            "path": state.path,
            "status": status,
            "reason": reason,
            **fields,
        },
    )
    context = _scope_context(
        identifier,
        state,
        status,
        reason,
        fields,
    )
    state.contexts.setdefault(identifier, context)
    resolved = state.contexts[identifier]
    state.context_cache[cache_key] = resolved
    return resolved


def _active_refs(
    frames: Sequence[_ScopeFrame],
    extra_refs: tuple[str, ...],
) -> dict[str, tuple[str, ...]]:
    active: dict[str, list[str]] = {}
    for frame in frames:
        for kind, identifiers in frame.items.items():
            selected = active.setdefault(kind, [])
            selected.extend(identifiers[: MAX_CONTEXT_ITEMS - len(selected)])
    selected_omissions = active.setdefault("omit", [])
    selected_omissions.extend(extra_refs[: MAX_CONTEXT_ITEMS - len(selected_omissions)])
    return {kind: tuple(values) for kind, values in active.items()}


def _active_values(
    commands: Mapping[str, LeanLexicalContextCommand],
    active: Mapping[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    return {
        kind: tuple(commands[identifier].value for identifier in identifiers)
        for kind, identifiers in active.items()
    }


def _context_source_refs(
    frames: Sequence[_ScopeFrame],
    active: Mapping[str, tuple[str, ...]],
) -> tuple[str, ...]:
    candidates = [
        *(identifier for frame in frames for identifier in frame.source_refs),
        *(identifier for identifiers in active.values() for identifier in identifiers),
    ]
    selected: list[str] = []
    for identifier in candidates:
        if identifier not in selected:
            selected.append(identifier)
        if len(selected) == MAX_CONTEXT_REFERENCES:
            break
    return tuple(selected)


def _context_fields(
    namespaces: tuple[str, ...],
    sections: tuple[str, ...],
    values: Mapping[str, tuple[str, ...]],
    source_refs: tuple[str, ...],
    omitted: int,
) -> dict[str, Any]:
    return {
        "namespaceStack": namespaces,
        "sectionStack": sections,
        "variables": values.get("variable", ()),
        "omissions": values.get("omit", ()),
        "localNotations": values.get("local_notation", ()),
        "localInstances": values.get("local_instance", ()),
        "openedScopes": values.get("open_scoped", ()),
        "exports": values.get("export", ()),
        "sourceRefs": source_refs,
        "omittedCount": omitted,
    }


def _scope_context(
    identifier: str,
    state: _NavigationState,
    status: str,
    reason: str | None,
    fields: Mapping[str, Any],
) -> LeanLexicalScopeContext:
    return LeanLexicalScopeContext(
        identifier=identifier,
        module=state.module,
        path=state.path,
        status=status,
        reason=reason,
        namespace_stack=tuple(fields["namespaceStack"]),
        section_stack=tuple(fields["sectionStack"]),
        variables=tuple(fields["variables"]),
        omissions=tuple(fields["omissions"]),
        local_notations=tuple(fields["localNotations"]),
        local_instances=tuple(fields["localInstances"]),
        opened_scopes=tuple(fields["openedScopes"]),
        exports=tuple(fields["exports"]),
        source_refs=tuple(fields["sourceRefs"]),
        omitted_count=int(fields["omittedCount"]),
    )


def _finalize_declarations(
    state: _NavigationState,
    declarations: list[LeanTextDeclaration],
) -> list[LeanTextDeclaration]:
    start = _unbalanced_start(state.frames)
    if start is None:
        return declarations
    return [
        _unresolve_declaration(state, row) if row.start_offset >= start else row
        for row in declarations
    ]


def _unresolve_declaration(
    state: _NavigationState,
    declaration: LeanTextDeclaration,
) -> LeanTextDeclaration:
    context = _unresolved_context(
        state,
        state.contexts.get(declaration.scope_context_id or ""),
    )
    return replace(
        declaration,
        scope_context_id=context.identifier,
        scope_context_status="unresolved",
    )


def _finalize_options(
    state: _NavigationState,
    options: list[LeanOptionOccurrence],
) -> list[LeanOptionOccurrence]:
    start = _unbalanced_start(state.frames)
    if start is None:
        return options
    return [
        _unresolve_option(state, row) if row.start_offset >= start else row
        for row in options
    ]


def _unresolve_option(
    state: _NavigationState,
    option: LeanOptionOccurrence,
) -> LeanOptionOccurrence:
    context = _unresolved_context(
        state,
        state.contexts.get(option.scope_context_id or ""),
    )
    return replace(option, scope_context_id=context.identifier)


def _unresolved_context(
    state: _NavigationState,
    current: LeanLexicalScopeContext | None,
) -> LeanLexicalScopeContext:
    reason = "lexical scope remains unclosed at end of source"
    if current is None:
        return _intern_context(
            state,
            namespace_stack=(),
            section_stack=(),
            forced_reason=reason,
        )
    identifier = _stable_id(
        "scope-context",
        {
            "version": LEXICAL_CONTEXT_VERSION,
            "base": current.identifier,
            "status": "unresolved",
            "reason": reason,
        },
    )
    context = replace(
        current,
        identifier=identifier,
        status="unresolved",
        reason=reason,
    )
    state.contexts.setdefault(identifier, context)
    return state.contexts[identifier]


def _unbalanced_start(frames: Sequence[_ScopeFrame]) -> int | None:
    offsets = [frame.start_offset for frame in frames if frame.kind != "module"]
    return min(offsets) if offsets else None


def _namespace_stack(frames: Sequence[_ScopeFrame]) -> tuple[str, ...]:
    return tuple(
        segment
        for frame in frames
        if frame.kind == "namespace" and frame.name
        for segment in frame.name.split(".")
    )


def _section_stack(frames: Sequence[_ScopeFrame]) -> tuple[str, ...]:
    return tuple(
        frame.name or "<anonymous>" for frame in frames if frame.kind == "section"
    )


def _bounded_command_body(
    text: str,
    masked: str,
    match: re.Match[str],
) -> tuple[str, int, bool]:
    start = match.start("body")
    end = _visible_end(masked, start, match.end("body"))
    return bounded_lexical_text(text[start:end].strip())


def _visible_end(masked: str, start: int, end: int) -> int:
    cursor = end
    while cursor > start and masked[cursor - 1].isspace():
        cursor -= 1
    return cursor


def _position(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset) + 1
    return line, offset - line_start + 1


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:20]
    return f"ladon.lexical_{prefix.replace('-', '_')}.{digest}"


def _command_order(
    row: LeanLexicalContextCommand,
) -> tuple[int, int, str]:
    return row.start_offset, row.end_offset, row.identifier


__all__ = [
    "ATTRIBUTE_TOKENS",
    "LEXICAL_CONTEXT_VERSION",
    "LEXICAL_NAVIGATION_VERSION",
    "LexicalNavigationSurface",
    "MAX_CONTEXT_ITEMS",
    "MAX_CONTEXT_REFERENCES",
    "MAX_LEXICAL_VALUE_CHARACTERS",
    "RESOURCE_OPTIONS",
    "TACTIC_TOKENS",
    "scan_lexical_navigation",
]
