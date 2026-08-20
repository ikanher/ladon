"""One bounded, evidence-accurate ProofIR attachment resolver."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import PurePosixPath
from typing import Any

POLICY_VERSION = "proofir-attachment-policy-v1"
MAX_CANDIDATES = 256
_METHODS = (
    "environment-fingerprint",
    "producer-declaration",
    "content-range",
    "content-name",
    "path-range",
    "module-name",
    "name-only-diagnostic",
)
POLICY_DIGEST = "sha256:" + hashlib.sha256(
    json.dumps(_METHODS, separators=(",", ":")).encode("utf-8")
).hexdigest()
RESOLVER_IDENTITY = {
    "name": "ladon-proofir-attachment-resolver",
    "version": POLICY_VERSION,
    "digest": POLICY_DIGEST,
}

_SELECTABLE_METHODS = frozenset(_METHODS[:-1])
_METHOD_RANK = {method: rank for rank, method in enumerate(_METHODS)}


def resolve_attachment(
    surface: Mapping[str, Any], declarations: list[Mapping[str, Any]]
) -> dict[str, Any]:
    """Resolve one source attachment without promoting it to theorem evidence.

    Every bounded input declaration remains visible in the returned candidate list.
    Selection is explicit and is never inferred later by SQLite or query consumers.
    """

    if len(declarations) > MAX_CANDIDATES:
        raise ValueError(f"attachment candidate bound exceeded: {MAX_CANDIDATES}")
    candidates = [_classify(surface, declaration) for declaration in declarations]
    candidates.sort(key=lambda row: (int(row["rank"]), str(row["declarationId"])))
    decision = _selection(candidates)
    return {
        "resolver": deepcopy(RESOLVER_IDENTITY),
        "selectionDecision": decision["selectionDecision"],
        "selectedCandidateId": decision["selectedCandidateId"],
        "selectedSourceRef": deepcopy(decision["selectedSourceRef"]),
        "candidates": deepcopy(candidates),
        "decisiveEvidence": deepcopy(decision["decisiveEvidence"]),
        "freshness": decision["freshness"],
        "rejectionReasons": decision["rejectionReasons"],
        "semanticAcceptance": False,
        "limitations": [
            {
                "id": "attachment-does-not-establish-theorem-truth",
                "message": "Source attachment is not semantic theorem acceptance.",
            }
        ],
    }


def resolve_source_map_anchor(
    anchor: Mapping[str, Any],
    declarations: list[Mapping[str, Any]],
    *,
    environment_ref: str,
) -> dict[str, Any]:
    """Route a native source-map anchor through the shared resolver policy."""

    surface = {
        "declarationName": anchor.get("declName"),
        "environmentRef": environment_ref,
        "declarationFingerprint": anchor.get("declarationFingerprint"),
        "declarationRef": anchor.get("declarationRef"),
        "sourcePath": anchor.get("sourcePath"),
        "contentHash": anchor.get("contentDigest"),
        "sourceRange": {"start": anchor.get("start"), "end": anchor.get("end")},
        "module": anchor.get("module"),
    }
    return resolve_attachment(surface, declarations)


def _classify(
    surface: Mapping[str, Any], declaration: Mapping[str, Any]
) -> dict[str, Any]:
    identity = _identity_conflict(surface, declaration)
    unsafe = _unsafe_reasons(surface, declaration)
    if unsafe:
        return _candidate(
            declaration, "unsafe-path-diagnostic", "none", "unknown", 90, [], unsafe
        )
    if identity:
        return _candidate(
            declaration,
            "identity-conflict-diagnostic",
            "none",
            "unknown",
            80,
            _identity_evidence(surface, declaration),
            identity,
        )
    match = _strongest_match(surface, declaration)
    if match is None:
        return _candidate(
            declaration,
            "unmatched-diagnostic",
            "none",
            "unknown",
            99,
            [],
            ["no-supported-attachment-evidence"],
        )
    method, confidence, freshness, evidence, reasons = match
    return _candidate(
        declaration,
        method,
        confidence,
        freshness,
        _METHOD_RANK[method],
        evidence,
        reasons,
    )


def _strongest_match(
    surface: Mapping[str, Any], declaration: Mapping[str, Any]
) -> tuple[str, str, str, list[dict[str, Any]], list[str]] | None:
    env_equal = _same_nonempty(surface, declaration, "environmentRef")
    fingerprint_equal = _same_nonempty(
        surface, declaration, "declarationFingerprint"
    )
    if env_equal and fingerprint_equal:
        return (
            "environment-fingerprint",
            "exact",
            _freshness(surface, declaration),
            _identity_evidence(surface, declaration),
            [],
        )
    if env_equal and _same_nonempty(surface, declaration, "declarationRef"):
        return (
            "producer-declaration",
            "exact",
            _freshness(surface, declaration),
            _evidence(surface, "environmentRef", "declarationRef"),
            [],
        )
    return _source_match(surface, declaration)


def _source_match(
    surface: Mapping[str, Any], declaration: Mapping[str, Any]
) -> tuple[str, str, str, list[dict[str, Any]], list[str]] | None:
    matchers = (
        _content_range_match,
        _content_name_match,
        _path_range_match,
        _module_name_match,
        _name_only_match,
    )
    for matcher in matchers:
        match = matcher(surface, declaration)
        if match is not None:
            return match
    return None


def _content_range_match(surface, declaration):
    if _same_nonempty(surface, declaration, "contentHash") and _same_range(
        surface.get("sourceRange"), declaration.get("sourceRange")
    ):
        return "content-range", "strong", "fresh", _evidence(
            surface, "contentHash", "sourceRange"
        ), []


def _content_name_match(surface, declaration):
    if _same_nonempty(surface, declaration, "contentHash") and _same_name(
        surface, declaration
    ):
        return "content-name", "strong", "fresh", _evidence(
            surface, "contentHash", "declarationName"
        ), []


def _path_range_match(surface, declaration):
    same_range = _same_range(surface.get("sourceRange"), declaration.get("sourceRange"))
    if _same_path(surface, declaration) and same_range and _same_name(
        surface, declaration
    ):
        reasons = [] if _freshness(surface, declaration) != "stale" else [
            "content-digest-mismatch"
        ]
        return "path-range", "bounded-fallback", _freshness(
            surface, declaration
        ), _evidence(surface, "sourcePath", "sourceRange", "declarationName"), reasons


def _module_name_match(surface, declaration):
    if _same_name(surface, declaration) and _same_nonempty(
        surface, declaration, "module"
    ):
        return "module-name", "bounded-fallback", "unknown", _evidence(
            surface, "module", "declarationName"
        ), []


def _name_only_match(surface, declaration):
    if _same_name(surface, declaration):
        return "name-only-diagnostic", "none", "unknown", _evidence(
            surface, "declarationName"
        ), ["name-only-is-not-an-attachment"]


def _selection(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    selectable = _selectable_candidates(candidates)
    if selectable:
        return _selection_from_candidates(selectable)
    decision = "unresolved" if _has_unresolved_diagnostic(candidates) else "none"
    return _unselected(decision, _diagnostic_reasons(candidates))


def _selectable_candidates(candidates):
    return [row for row in candidates if row["method"] in _SELECTABLE_METHODS]


def _selection_from_candidates(candidates):
    strongest_rank = min(int(row["rank"]) for row in candidates)
    strongest = [row for row in candidates if row["rank"] == strongest_rank]
    if len(strongest) == 1:
        return _selected(strongest[0])
    return _unselected("ambiguous", ["multiple-strongest-candidates"])


def _diagnostic_reasons(candidates):
    return sorted(
        {
            reason
            for candidate in candidates
            for reason in candidate["rejectionReasons"]
        }
    )


def _has_unresolved_diagnostic(candidates):
    methods = {"identity-conflict-diagnostic", "unsafe-path-diagnostic"}
    return any(row["method"] in methods for row in candidates)


def _selected(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "selectionDecision": "selected",
        "selectedCandidateId": candidate["declarationId"],
        "selectedSourceRef": deepcopy(candidate["sourceRef"]),
        "decisiveEvidence": deepcopy(candidate["decisiveEvidence"]),
        "freshness": candidate["freshness"],
        "rejectionReasons": list(candidate["rejectionReasons"]),
    }


def _unselected(decision: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "selectionDecision": decision,
        "selectedCandidateId": None,
        "selectedSourceRef": None,
        "decisiveEvidence": [],
        "freshness": "unknown",
        "rejectionReasons": reasons,
    }


def _candidate(
    declaration: Mapping[str, Any],
    method: str,
    confidence: str,
    freshness: str,
    rank: int,
    evidence: list[dict[str, Any]],
    reasons: list[str],
) -> dict[str, Any]:
    return {
        "declarationId": declaration.get("id") or declaration.get("declaration"),
        "sourceRef": deepcopy(declaration.get("sourceRef")),
        "method": method,
        "confidence": confidence,
        "freshness": freshness,
        "rank": rank,
        "policyVersion": POLICY_VERSION,
        "decisiveEvidence": deepcopy(evidence),
        "rejectionReasons": list(reasons),
    }


def _identity_conflict(
    surface: Mapping[str, Any], declaration: Mapping[str, Any]
) -> list[str]:
    reasons = []
    if _different_nonempty(surface, declaration, "environmentRef"):
        reasons.append("environment-mismatch")
    if _different_nonempty(surface, declaration, "declarationFingerprint"):
        reasons.append("declaration-fingerprint-mismatch")
    if _different_nonempty(surface, declaration, "declarationRef"):
        reasons.append("declaration-reference-mismatch")
    if (
        _same_nonempty(surface, declaration, "environmentRef")
        and _same_nonempty(surface, declaration, "declarationFingerprint")
        and surface.get("declarationName")
        and (declaration.get("declaration") or declaration.get("name"))
        and not _same_name(surface, declaration)
    ):
        reasons.append("declaration-name-mismatch")
    return reasons


def _unsafe_reasons(
    surface: Mapping[str, Any], declaration: Mapping[str, Any]
) -> list[str]:
    paths = (surface.get("sourcePath"), declaration.get("sourcePath"))
    return ["unsafe-source-path"] if any(_unsafe_path(path) for path in paths) else []


def _unsafe_path(value: Any) -> bool:
    if not value:
        return False
    path = PurePosixPath(str(value).replace("\\", "/"))
    return path.is_absolute() or ".." in path.parts


def _freshness(surface: Mapping[str, Any], declaration: Mapping[str, Any]) -> str:
    left, right = surface.get("contentHash"), declaration.get("contentHash")
    if not left or not right:
        return "unknown"
    return "fresh" if _hash(left) == _hash(right) else "stale"


def _same_nonempty(
    surface: Mapping[str, Any], declaration: Mapping[str, Any], field: str
) -> bool:
    left, right = surface.get(field), declaration.get(field)
    if field == "contentHash":
        left, right = _hash(left), _hash(right)
    return bool(left and right and left == right)


def _different_nonempty(
    surface: Mapping[str, Any], declaration: Mapping[str, Any], field: str
) -> bool:
    left, right = surface.get(field), declaration.get(field)
    return bool(left and right and left != right)


def _same_path(surface: Mapping[str, Any], declaration: Mapping[str, Any]) -> bool:
    left, right = surface.get("sourcePath"), declaration.get("sourcePath")
    return bool(left and right and left == right)


def _same_name(surface: Mapping[str, Any], declaration: Mapping[str, Any]) -> bool:
    wanted = str(surface.get("declarationName") or "")
    actual = str(declaration.get("declaration") or declaration.get("name") or "")
    return bool(wanted and actual and wanted == actual)


def _same_range(left: Any, right: Any) -> bool:
    return bool(left is not None and left == right)


def _hash(value: Any) -> str:
    return str(value or "").removeprefix("sha256:")


def _evidence(surface: Mapping[str, Any], *fields: str) -> list[dict[str, Any]]:
    return [{"kind": field, "value": deepcopy(surface.get(field))} for field in fields]


def _identity_evidence(
    surface: Mapping[str, Any], declaration: Mapping[str, Any]
) -> list[dict[str, Any]]:
    fields = ("environmentRef", "declarationFingerprint", "declarationRef")
    return [
        {
            "kind": field,
            "surfaceValue": deepcopy(surface.get(field)),
            "candidateValue": deepcopy(declaration.get(field)),
        }
        for field in fields
        if surface.get(field) is not None or declaration.get(field) is not None
    ]


__all__ = [
    "MAX_CANDIDATES",
    "POLICY_DIGEST",
    "POLICY_VERSION",
    "RESOLVER_IDENTITY",
    "resolve_attachment",
    "resolve_source_map_anchor",
]
