"""Stable dataclasses shared between Ladon extraction and analysis passes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LeanImport:
    """Source evidence for one Lean import command target."""

    module: str
    line: int | None = None
    text: str | None = None


@dataclass(frozen=True)
class LeanLexicalMarker:
    """Source-level lexical marker used for lightweight smell scans."""

    kind: str
    line: int
    text: str


@dataclass(frozen=True)
class LeanTextDeclaration:
    """Offset-backed declaration candidate from the bounded text scanner."""

    name: str
    kind: str
    line: int
    column: int
    start_offset: int
    end_offset: int
    authority: str = "lexical_text"
    confidence: str = "bounded_lexical_scan"
    nonclaim: str = (
        "Text evidence only; not a complete Lean parse, elaboration result, "
        "dependency fact, or theorem verdict."
    )


@dataclass(frozen=True)
class BoundedStrings:
    """One finite declaration-surface string collection.

    `total` is the pre-cap count.  An unavailable collection has no items and a
    textual reason; callers must not interpret that state as an observed empty
    set.
    """

    items: tuple[str, ...] = ()
    total: int = 0
    truncated: bool = False
    status: str = "unavailable"
    reason: str | None = "not supplied by the extraction backend"
    authority: str = "lean_environment"


@dataclass(frozen=True)
class LeanBinderSurface:
    """Bounded pretty-printed information for one leading Lean binder."""

    name: str
    binder_info: str
    type_text: str
    is_premise: bool = False


@dataclass(frozen=True)
class BoundedBinders:
    """One finite leading-binder collection."""

    items: tuple[LeanBinderSurface, ...] = ()
    total: int = 0
    truncated: bool = False
    status: str = "unavailable"
    reason: str | None = "not supplied by the extraction backend"


@dataclass(frozen=True)
class BoundedText:
    """One finite source-text surface with explicit truncation state."""

    text: str | None = None
    total_bytes: int = 0
    truncated: bool = False
    status: str = "unavailable"
    reason: str | None = "not supplied by the extraction backend"


@dataclass(frozen=True)
class LeanTrustFact:
    """One direct Lean-observed trust-footprint fact."""

    kind: str
    scope: str
    target: str | None = None
    authority: str = "lean_environment"
    nonclaim: str = (
        "Direct expression evidence only; not a transitive axiom closure, "
        "proof-correctness result, or theorem-truth verdict."
    )


@dataclass(frozen=True)
class LeanDeclarationSurface:
    """Typed, bounded statement and body-navigation surface from Lean."""

    status: str = "unavailable"
    reason: str | None = "not supplied by the extraction backend"
    rendered_type: str | None = None
    rendered_type_bytes: int = 0
    rendered_type_truncated: bool = False
    printer_options: dict[str, Any] = field(default_factory=dict)
    binders: BoundedBinders = field(default_factory=BoundedBinders)
    premises: BoundedStrings = field(default_factory=BoundedStrings)
    conclusion: str | None = None
    conclusion_truncated: bool = False
    statement_excerpt: BoundedText = field(default_factory=BoundedText)
    statement_range: dict[str, Any] | None = None
    proof_range: dict[str, Any] | None = None
    has_value: bool | None = None
    proof_form: str | None = None
    body_total_bytes: int = 0
    body_truncated: bool = False
    declared_axiom: bool | None = None
    unsafe: bool | None = None
    trust_facts: tuple[LeanTrustFact, ...] = ()
    dependency_modules: dict[str, str] = field(default_factory=dict)
    backend: str = "lean_elaborator"
    helper_version: str | None = None
    lean_version: str | None = None
    nonclaim: str = (
        "Navigation and direct Lean artifact evidence only; Ladon does not "
        "independently verify proof correctness or theorem truth."
    )


@dataclass(frozen=True)
class LeanModule:
    """Stable module-level IR shared by pure Ladon analysis passes.

    `imports` stores module names as written in Lean import headers.
    `import_sites` optionally stores source locations for those imports.
    `line_count` and `tags` are source-level triage metadata for report
    filtering; they do not change graph semantics.
    `declarations` stores only names in the clean core; declaration-level proof
    facts are a future Lean-native extraction surface.
    """

    name: str
    path: str
    imports: tuple[str, ...] = ()
    import_sites: tuple[LeanImport, ...] = ()
    line_count: int = 0
    tags: tuple[str, ...] = ()
    lexical_markers: tuple[LeanLexicalMarker, ...] = ()
    declarations: tuple[str, ...] = ()
    declaration_evidence: tuple[LeanTextDeclaration, ...] = ()


@dataclass(frozen=True)
class LeanDeclaration:
    """Stable declaration-level IR for exact-reference graph analysis.

    `references` stores raw candidate names supplied by extraction. Analysis
    only turns them into edges when a candidate exactly matches another known
    declaration name. Source evidence fields identify the file/range/hash used
    for attachment confidence; they are not Lean kernel dependency facts.

    `parser_candidates`, `type_dependencies`, and `value_dependencies` retain
    distinct evidence authorities.  `references` remains the compatibility
    spelling for parser candidates and is never silently upgraded to an
    elaborated dependency.
    """

    name: str
    module: str
    kind: str | None = None
    references: tuple[str, ...] = ()
    source_path: str | None = None
    source_range: dict[str, Any] | None = None
    selection_range: dict[str, Any] | None = None
    content_hash: str | None = None
    extraction_backend: str | None = None
    extractor_version: str | None = None
    name_resolution_method: str | None = None
    confidence: str | None = None
    parser_candidates: BoundedStrings = field(
        default_factory=lambda: BoundedStrings(authority="lean_parser")
    )
    type_dependencies: BoundedStrings = field(default_factory=BoundedStrings)
    value_dependencies: BoundedStrings = field(default_factory=BoundedStrings)
    surface: LeanDeclarationSurface = field(default_factory=LeanDeclarationSurface)
    is_imported_stub: bool = False
    compiler_generated: bool | None = None
    compiler_authority: str | None = None
    compiler_toolchain: str | None = None
    resolution: str | None = None


@dataclass(frozen=True)
class LeanAuditQuery:
    """One bounded result for an exact lexical audit-command subject."""

    identifier: str
    kind: str
    containing_owner: str
    source_path: str
    subject: str
    status: str
    reason: str
    referenced_declaration: str | None = None
    referenced_owner: str | None = None
    rendered_type: str | None = None
    rendered_type_truncated: bool = False
    axioms: BoundedStrings = field(default_factory=BoundedStrings)
    backend: str = "lean_elaborated_helper"
    authority: str = "lean_environment"
    helper_version: str | None = None
    lean_version: str | None = None
    nonclaim: str = (
        "Lean query evidence for one exact source subject only; bounded output "
        "does not independently establish proof correctness or theorem truth."
    )

    def to_dict(self) -> dict[str, Any]:
        """Return the additive report-facing query-result shape."""

        return {
            "id": self.identifier,
            "kind": self.kind,
            "containingOwner": self.containing_owner,
            "sourcePath": self.source_path,
            "subject": self.subject,
            "status": self.status,
            "reason": self.reason,
            "referencedDeclaration": self.referenced_declaration,
            "referencedOwner": self.referenced_owner,
            "renderedType": self.rendered_type,
            "renderedTypeTruncated": self.rendered_type_truncated,
            "axioms": {
                "items": list(self.axioms.items),
                "total": self.axioms.total,
                "truncated": self.axioms.truncated,
                "status": self.axioms.status,
                "reason": self.axioms.reason,
                "authority": self.axioms.authority,
            },
            "backend": self.backend,
            "authority": self.authority,
            "helperVersion": self.helper_version,
            "leanVersion": self.lean_version,
            "nonclaim": self.nonclaim,
        }


@dataclass(frozen=True)
class ExtractionBundle:
    """Backend-normalized extraction output for analysis phases."""

    modules: dict[str, LeanModule]
    declarations: dict[str, LeanDeclaration] | None = None
    counters: dict[str, int] = field(default_factory=dict)
    diagnostics: tuple[dict[str, Any], ...] = ()
    runtime: dict[str, Any] = field(default_factory=dict)
    audit_queries: dict[str, LeanAuditQuery] = field(default_factory=dict)
