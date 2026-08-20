"""Conservative lexical owner candidates for audit-command subjects."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from ladon.coverage import CollectionCoverage, CoverageCause
from ladon.source_index_models import (
    SOURCE_INDEX_DECLARATIONS_COVERAGE,
    SourceIndex,
)

MAX_AMBIGUOUS_CANDIDATES = 8
LEXICAL_CANDIDATE_NONCLAIM = (
    "Exact lexical source-index candidate only; not Lean name resolution, "
    "visibility checking, elaboration, proof correctness, or theorem truth."
)


def attach_lexical_audit_candidates(
    surfaces: Sequence[Any],
    source_index: SourceIndex | None,
) -> None:
    """Join safely parsed bare subjects to exact lexical candidate names."""

    if not _has_audit_commands(surfaces):
        return
    candidates = _candidate_index(source_index)
    fingerprint = source_index.fingerprint if source_index is not None else None
    declaration_coverage = _declaration_coverage(source_index)
    for surface_index, surface in enumerate(surfaces):
        if not isinstance(surface, dict):
            continue
        for command_index, command in enumerate(surface.get("auditCommands", [])):
            if isinstance(command, dict):
                _attach_candidate(
                    command,
                    candidates,
                    fingerprint,
                    declaration_coverage,
                    pointer=(
                        "#/sections/module_dag/audit_surfaces/"
                        f"{surface_index}/auditCommands/{command_index}/"
                        "candidateMatches"
                    ),
                )


def _has_audit_commands(surfaces: Sequence[Any]) -> bool:
    """Return whether any well-shaped surface has commands to enrich."""

    return any(
        isinstance(surface, Mapping)
        and isinstance(surface.get("auditCommands"), list)
        and bool(surface["auditCommands"])
        for surface in surfaces
    )


def _candidate_index(
    source_index: SourceIndex | None,
) -> Mapping[str, tuple[dict[str, Any], ...]]:
    """Index exact lexical FQN candidates without basename aliases."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if source_index is None:
        return {}
    for entry in source_index.entries:
        for declaration in entry.module.declaration_evidence:
            if (
                declaration.candidate_status != "lexical_candidate"
                or not declaration.candidate_name
            ):
                continue
            grouped[declaration.candidate_name].append(
                {
                    "id": declaration.identifier,
                    "canonicalRef": (
                        f"source-index:declaration:{declaration.identifier}"
                    ),
                    "candidateDeclaration": declaration.candidate_name,
                    "candidateReferencedOwner": entry.name,
                    "sourcePath": entry.path,
                    "sourceRange": declaration.source_range,
                    "privacy": declaration.privacy,
                    "locality": declaration.locality,
                    "authority": declaration.authority,
                }
            )
    return {
        name: tuple(
            sorted(
                rows,
                key=lambda row: (
                    str(row["candidateReferencedOwner"]),
                    str(row["sourcePath"]),
                    str(row["id"]),
                ),
            )
        )
        for name, rows in grouped.items()
    }


def _attach_candidate(
    command: dict[str, Any],
    candidates: Mapping[str, tuple[dict[str, Any], ...]],
    source_fingerprint: str | None,
    declaration_coverage: CollectionCoverage | None,
    *,
    pointer: str,
) -> None:
    """Attach one exact, ambiguous, or unresolved lexical join result."""

    subject = _exact_subject(command)
    matches = candidates.get(subject, ()) if subject is not None else ()
    status = _candidate_status(
        subject,
        matches,
        source_fingerprint,
        declaration_coverage,
    )
    visible = min(len(matches), MAX_AMBIGUOUS_CANDIDATES)
    command.update(
        {
            "candidateStatus": status,
            "candidateMatchCount": len(matches),
            "candidateMatches": [
                dict(row) for row in matches[:MAX_AMBIGUOUS_CANDIDATES]
            ],
            "candidateAuthority": (
                "lexical_text" if source_fingerprint is not None else None
            ),
            "candidateSourceIndexFingerprint": source_fingerprint,
            "candidateCoverage": _candidate_coverage(
                command,
                matches,
                visible=visible,
                pointer=pointer,
                upstream=declaration_coverage,
                source_fingerprint=source_fingerprint,
            ).to_dict(),
            "candidateNonclaim": LEXICAL_CANDIDATE_NONCLAIM,
        }
    )
    if status == "lexical_candidate":
        match = matches[0]
        command["candidateDeclarationId"] = match["id"]
        command["candidateReferencedDeclaration"] = match["candidateDeclaration"]
        command["candidateReferencedOwner"] = match["candidateReferencedOwner"]


def _exact_subject(command: Mapping[str, Any]) -> str | None:
    """Return only a safely parsed, untruncated bare lexical subject."""

    if command.get("status") != "lexical":
        return None
    if bool(command.get("subjectTruncated")):
        return None
    subject = str(command.get("subject", "")).strip()
    if subject.startswith("_root_."):
        subject = subject.removeprefix("_root_.")
    if not subject or any(character.isspace() for character in subject):
        return None
    return subject


def _candidate_status(
    subject: str | None,
    matches: Sequence[Any],
    source_fingerprint: str | None,
    declaration_coverage: CollectionCoverage | None,
) -> str:
    """Classify the lexical join without choosing among multiple rows."""

    if source_fingerprint is None:
        return "unavailable"
    if subject is None:
        return "unresolved"
    if len(matches) > 1:
        return "ambiguous"
    if declaration_coverage is None or declaration_coverage.completeness != "complete":
        return "unavailable"
    if not matches:
        return "unresolved"
    return "lexical_candidate"


def _declaration_coverage(
    source_index: SourceIndex | None,
) -> CollectionCoverage | None:
    """Return the canonical population controlling exact owner lookup."""

    if source_index is None:
        return None
    return source_index.coverage_registry().require(SOURCE_INDEX_DECLARATIONS_COVERAGE)


def _candidate_coverage(
    command: Mapping[str, Any],
    matches: Sequence[Any],
    *,
    visible: int,
    pointer: str,
    upstream: CollectionCoverage | None,
    source_fingerprint: str | None,
) -> CollectionCoverage:
    """Project one subject lookup without inventing an exact total."""

    identity = f"{command.get('id', 'audit')}.candidate_matches"
    causes = _candidate_coverage_causes(upstream, len(matches))
    common = {
        "identity": identity,
        "pointer": pointer,
        "visible": visible,
        "population": "exact_lexical_subject_candidate_matches",
        "scope": "source_index_inventory",
        "authority": upstream.authority if upstream is not None else "unavailable",
        "causes": causes,
        "source_fingerprint": (
            upstream.source_fingerprint if upstream is not None else source_fingerprint
        ),
    }
    if upstream is not None and upstream.completeness == "complete":
        return CollectionCoverage.exact(
            total=len(matches),
            observed_lower_bound=len(matches),
            **common,
        )
    return CollectionCoverage.unknown(
        observed_lower_bound=len(matches),
        completeness=(upstream.completeness if upstream is not None else "unavailable"),
        **common,
    )


def _candidate_coverage_causes(
    upstream: CollectionCoverage | None,
    observed: int,
) -> tuple[CoverageCause, ...]:
    """Retain upstream extraction causes and any bounded display omission."""

    causes = (
        upstream.causes
        if upstream is not None
        else (
            CoverageCause(
                kind="analysis",
                identifier="audit_ownership.source_index_unavailable",
                detail=(
                    "Lexical audit ownership has no source-index declaration "
                    "population."
                ),
            ),
        )
    )
    if observed <= MAX_AMBIGUOUS_CANDIDATES:
        return causes
    return (
        *causes,
        CoverageCause(
            kind="projection",
            identifier="audit_ownership.candidate_match_limit",
            detail=(
                "Lexical audit ownership retained a deterministic candidate "
                "match prefix."
            ),
            controlling_cap=MAX_AMBIGUOUS_CANDIDATES,
        ),
    )
