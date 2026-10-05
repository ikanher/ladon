"""Validate native derivation graphs and enforce shared query envelopes and bounds.

Exact artifact-local reference pairs own all joins. Graph validation precedes
traversal; bounded omissions retain their frontier instead of claiming failure.
Query envelopes describe structural evidence and never checker acceptance.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

RefKey = tuple[str, str]
Occurrence = tuple[RefKey, int, RefKey]
Route = tuple[tuple[RefKey, int], ...]
_NONCLAIM = "Structural derivation evidence only; checker acceptance is not evaluated."
_SCC_NONCLAIM = (
    "SCC membership is structural only; theorem truth and fixed-point semantics "
    "are not established."
)
_NAVIGATION_LIMITATION = {
    "id": "navigation-not-complete-proof-slice",
    "message": "A navigation route is not a complete derivation slice.",
}
_SAFE_INTEGER_MAX = 2**53 - 1


@dataclass(frozen=True)
class DerivationQueryBounds:
    """Finite resource limits shared by native derivation queries.

    Construction rejects booleans, non-integers, unsafe integers, and values
    that cannot hold the fixed result header.
    """

    max_depth: int = 64
    max_visited_refs: int = 10_000
    max_evaluated_steps: int = 10_000
    max_premise_slots: int = 10_000
    max_alternatives: int = 1_000
    max_output_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        """Reject a bound set that cannot define a finite portable query."""
        for name, value in self.__dict__.items():
            invalid = (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 1 <= value <= _SAFE_INTEGER_MAX
            )
            if invalid:
                raise ValueError(f"derivation query bound {name} must be positive")
        if self.max_output_bytes < 1_024:
            raise ValueError("derivation query output bound is smaller than its header")

    def to_dict(self) -> dict[str, int]:
        """Return the frozen lower-camel-case wire representation."""
        return {
            _camel(name.removeprefix("max_"), prefix="max"): value
            for name, value in self.__dict__.items()
        }


def _camel(value: str, *, prefix: str = "") -> str:
    """Convert an internal snake-case bound name into its frozen wire spelling."""
    head, *tail = value.split("_")
    return prefix + head.title() + "".join(part.title() for part in tail)


def _key(row: Mapping[str, Any]) -> RefKey:
    """Extract an enclosing-artifact-owned kind/local-id identity pair."""

    return (str(row["kind"]), str(row["localId"]))


def _ref(key: RefKey) -> dict[str, str]:
    """Serialize a compact artifact-local reference in the frozen field order."""

    kind, local_id = key
    return {"kind": kind, "localId": local_id}


def _plain(value: Any) -> Any:
    """Copy immutable validator values into ordinary JSON-compatible containers."""
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _external_reference_pointer(value: Any, pointer: str) -> str | None:
    """Return the first deterministic artifactRef pointer in a payload tree."""

    if isinstance(value, Mapping):
        if "artifactRef" in value:
            return pointer + "/artifactRef"
        for key in sorted(value):
            found = _external_reference_pointer(value[key], pointer + "/" + str(key))
            if found is not None:
                return found
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found = _external_reference_pointer(item, pointer + f"/{index}")
            if found is not None:
                return found
    return None


def _diagnostic(code: str, pointer: str, message: str) -> dict[str, Any]:
    """Build one stable reference-validation diagnostic."""
    return {
        "stage": "reference-valid",
        "code": code,
        "pointer": pointer,
        "message": message,
    }


class _InvalidGraph(ValueError):
    """Internal exception carrying the validator diagnostic for a rejected graph."""

    def __init__(self, diagnostic: dict[str, Any]):
        super().__init__(diagnostic["message"])
        self.diagnostic = diagnostic


@dataclass(frozen=True)
class _Graph:
    """Validated derivation data plus deterministic incoming/outgoing indexes."""

    artifact_id: str
    environment: str
    subjects: frozenset[RefKey]
    steps: tuple[Mapping[str, Any], ...]
    by_conclusion: Mapping[RefKey, tuple[Mapping[str, Any], ...]]
    outgoing: Mapping[RefKey, tuple[tuple[RefKey, int, RefKey, Mapping[str, Any]], ...]]
    recursive_components: tuple[Mapping[str, Any], ...]
    dependencies: Mapping[RefKey, frozenset[RefKey]]

    @classmethod
    def build(cls, artifact: Any) -> _Graph:
        """Validate an envelope and index its steps, or raise ``_InvalidGraph``."""
        # Validation owns cycle/reference/schema rejection; traversal never repairs input.
        checked = _validated_artifact(artifact)
        value = checked.payload
        if value["artifactKind"] != "proofir.derivation":
            raise _InvalidGraph(
                _diagnostic(
                    "unexpected-artifact-kind",
                    "/artifactKind",
                    "query input must be proofir.derivation",
                )
            )
        external_pointer = _external_reference_pointer(value["payload"], "/payload")
        if external_pointer is not None:
            raise _InvalidGraph(
                _diagnostic(
                    "external-reference-not-local",
                    external_pointer,
                    "single-artifact derivation queries cannot resolve artifactRef",
                )
            )
        steps = tuple(sorted(value["payload"]["steps"], key=lambda row: _key(row["stepRef"])))
        grouped = _steps_by_conclusion(steps)
        outgoing = _steps_by_premise(steps)
        dependencies = _step_dependencies(steps)
        return cls(
            checked.content_id,
            str(value["environmentRef"]),
            frozenset(_key(row) for row in value["subjectRefs"]),
            steps,
            {key: tuple(rows) for key, rows in grouped.items()},
            {key: tuple(sorted(rows, key=lambda row: row[:3])) for key, rows in outgoing.items()},
            tuple(value["payload"].get("recursion", {}).get("components", ())),
            {key: frozenset(rows) for key, rows in dependencies.items()},
        )

    def local_ref(
        self, row: Any, pointer: str, kind: str = "statement"
    ) -> tuple[RefKey | None, dict[str, Any] | None]:
        """Validate one compact query reference against this artifact's registry."""
        if isinstance(row, Mapping) and "artifactRef" in row:
            return None, _diagnostic(
                "external-reference-not-local",
                pointer + "/artifactRef",
                "single-artifact derivation queries cannot resolve artifactRef",
            )
        fields = {"kind", "localId"}
        if not isinstance(row, Mapping) or set(row) != fields:
            return None, _diagnostic("invalid-reference-shape", pointer, "invalid reference")
        if not all(isinstance(row[name], str) and row[name] for name in fields):
            return None, _diagnostic("invalid-reference-shape", pointer, "empty reference field")
        key = _key(row)
        checks = (
            (key[0] != kind, "unexpected-reference-kind", pointer + "/kind"),
            (key not in self.subjects, "dangling-local-reference", pointer),
        )
        for failed, code, location in checks:
            if failed:
                return None, _diagnostic(code, location, "query reference is not valid")
        return key, None


def _steps_by_conclusion(
    steps: tuple[Mapping[str, Any], ...],
) -> dict[RefKey, list[Mapping[str, Any]]]:
    """Group OR alternatives by exact conclusion identity."""

    grouped: dict[RefKey, list[Mapping[str, Any]]] = {}
    for step in steps:
        grouped.setdefault(_key(step["conclusionRef"]), []).append(step)
    return grouped


def _steps_by_premise(
    steps: tuple[Mapping[str, Any], ...],
) -> dict[RefKey, list[tuple[RefKey, int, RefKey, Mapping[str, Any]]]]:
    """Index every ordered premise occurrence for navigation queries."""

    outgoing: dict[RefKey, list[tuple[RefKey, int, RefKey, Mapping[str, Any]]]] = {}
    for step in steps:
        conclusion, step_key = _key(step["conclusionRef"]), _key(step["stepRef"])
        for ordinal, premise in enumerate(step["premiseRefs"]):
            outgoing.setdefault(_key(premise), []).append((step_key, ordinal, conclusion, step))
    return outgoing


def _step_dependencies(
    steps: tuple[Mapping[str, Any], ...],
) -> dict[RefKey, set[RefKey]]:
    """Index conservative conclusion-to-premise SCC edges."""

    dependencies: dict[RefKey, set[RefKey]] = {}
    for step in steps:
        conclusion = _key(step["conclusionRef"])
        dependencies.setdefault(conclusion, set()).update(
            _key(premise) for premise in step["premiseRefs"]
        )
    return dependencies


def _validated_artifact(artifact: Any) -> Any:
    """Accept an already validated envelope or validate raw input exactly once."""
    if hasattr(artifact, "content_id") and hasattr(artifact, "payload"):
        return artifact
    from ladon.proofir_v3 import ProofIRV3Error, validate_envelope

    try:
        return validate_envelope(artifact)
    except ProofIRV3Error as error:
        raise _InvalidGraph(error.diagnostic.to_dict()) from error


@dataclass
class _Budget:
    """Track resource use and the exact frontier of every bounded omission.

    Counters record consumed units.  A failed take records truncation without
    consuming the unavailable unit, so callers can distinguish known work from
    omitted work.

    Depth is inclusive: depth equal to ``max_depth`` is visitable, while its
    children are not.  Visit, step, premise, and alternative counters charge
    work immediately before that work is inspected.  This makes the recorded
    frontier reproducible and avoids claiming facts about uncharged work.

    A truncation is deduplicated only when its complete serialized record is
    equal.  Repeated premise slots therefore retain distinct ordinal frontiers,
    while an identical retry does not inflate omitted counters.
    """

    limits: DerivationQueryBounds
    counts: dict[str, int] = field(
        default_factory=lambda: {
            "visitedRefs": 0,
            "evaluatedSteps": 0,
            "premiseSlots": 0,
            "alternatives": 0,
            "returnedRows": 0,
            "omittedRows": 0,
        }
    )
    truncations: list[dict[str, Any]] = field(default_factory=list)

    def depth(self, depth: int, frontier: list[dict[str, Any]]) -> bool:
        """Accept an inclusive depth or record its first excluded frontier."""
        if depth <= self.limits.max_depth:
            return True
        self.cut("maxDepth", self.limits.max_depth, frontier)
        return False

    def take(self, dimension: str, frontier: list[dict[str, Any]]) -> bool:
        """Consume one unit of a named bound, recording failure deterministically."""
        count_name, limit = {
            "maxVisitedRefs": ("visitedRefs", self.limits.max_visited_refs),
            "maxEvaluatedSteps": ("evaluatedSteps", self.limits.max_evaluated_steps),
            "maxPremiseSlots": ("premiseSlots", self.limits.max_premise_slots),
            "maxAlternatives": ("alternatives", self.limits.max_alternatives),
        }[dimension]
        if self.counts[count_name] >= limit:
            self.cut(dimension, limit, frontier)
            return False
        self.counts[count_name] += 1
        return True

    def cut(
        self,
        dimension: str,
        limit: int,
        frontier: list[dict[str, Any]],
        omitted: int = 1,
    ) -> None:
        """Record one unique truncation frontier and its known omitted count."""
        # A bound records an exact frontier; it never turns unknown into false/absent.
        row = {
            "dimension": dimension,
            "limit": limit,
            "frontierRoute": frontier,
            "omittedCount": omitted,
        }
        if row not in self.truncations:
            self.truncations.append(row)
            self.counts["omittedRows"] += omitted


@dataclass(frozen=True)
class _Residual:
    """One unsupported statement occurrence and its selected-step route."""

    ref: RefKey
    route: Route = ()


@dataclass(frozen=True)
class _Prepared:
    """Shared validated query state, including any attributable input error."""

    graph: _Graph
    target: RefKey
    available: frozenset[RefKey]
    bounds: DerivationQueryBounds
    error: dict[str, Any] | None = None


def _prepare(
    artifact: Any,
    target_ref: Any,
    available_refs: list[dict[str, str]],
    bounds: DerivationQueryBounds | None,
) -> _Prepared:
    """Validate graph, target, available leaves, and bounds for a native query.

    Validation failures are values here so every public query can emit the same
    stable invalid-result envelope rather than expose validator exceptions.
    """
    selected_bounds = bounds or DerivationQueryBounds()
    try:
        graph = _Graph.build(artifact)
    except _InvalidGraph as error:
        raw = artifact.payload if hasattr(artifact, "payload") else artifact
        raw = raw if isinstance(raw, Mapping) else {}
        environment = str(raw.get("environmentRef", ""))
        target = ("statement", _local_id(target_ref))
        empty = _Graph(
            str(raw.get("artifactId", "")),
            environment,
            frozenset(),
            (),
            {},
            {},
            (),
            {},
        )
        return _Prepared(empty, target, frozenset(), selected_bounds, error.diagnostic)
    target, error = graph.local_ref(target_ref, "/query/targetRef")
    if error:
        return _Prepared(
            graph,
            ("statement", _local_id(target_ref)),
            frozenset(),
            selected_bounds,
            error,
        )
    available: set[RefKey] = set()
    for index, row in enumerate(available_refs):
        key, error = graph.local_ref(row, f"/query/availableRefs/{index}")
        if error:
            return _Prepared(graph, target, frozenset(), selected_bounds, error)
        available.add(key)
    return _Prepared(graph, target, frozenset(available), selected_bounds)


def _local_id(row: Any) -> str:
    """Recover a displayable target id for an invalid-result envelope."""
    return str(row.get("localId", "")) if isinstance(row, Mapping) else ""


def _result(
    prepared: _Prepared,
    query_kind: str,
    budget: _Budget,
    status: str,
    payload: dict[str, Any] | None,
    *,
    complete: bool,
) -> dict[str, Any]:
    """Assemble the common query envelope and enforce its byte-size bound."""
    value = {
        "queryVersion": "1",
        "queryKind": query_kind,
        "sourceArtifactId": prepared.graph.artifact_id,
        "ownerArtifactId": prepared.graph.artifact_id,
        "environmentRef": prepared.graph.environment,
        "targetRef": _ref(prepared.target),
        "status": status,
        "checkerAcceptance": "not-evaluated",
        "complete": complete,
        "boundsApplied": prepared.bounds.to_dict(),
        "counters": budget.counts,
        "truncations": budget.truncations,
        "result": payload,
        "limitations": ([_NAVIGATION_LIMITATION] if query_kind == "navigation-path" else []),
        "nonclaims": [
            _NONCLAIM,
            *([_SCC_NONCLAIM] if query_kind == "scc-analysis" else []),
        ],
        "diagnostics": [prepared.error] if prepared.error else [],
    }
    return _fit_output(value, prepared.bounds.max_output_bytes)


def _fit_output(value: dict[str, Any], limit: int) -> dict[str, Any]:
    """Replace an oversized result with a digest-bearing truncation header.

    The digest commits to the omitted deterministic result.  Failure is raised
    only when the configured limit cannot contain even the compact header.

    The compact result retains source identity, target identity, applied bounds,
    counters, and the nonclaim.  It discards the oversized payload and ordinary
    diagnostics because retaining either could violate the same byte ceiling.
    ``omittedDigest`` is computed over canonical JSON bytes of the full result.
    """
    encoded = _json_bytes(value)
    if len(encoded) <= limit:
        return value
    compact = {
        key: value[key]
        for key in (
            "queryVersion",
            "queryKind",
            "sourceArtifactId",
            "ownerArtifactId",
            "environmentRef",
            "targetRef",
            "checkerAcceptance",
            "boundsApplied",
            "limitations",
            "nonclaims",
            "counters",
            "evidenceReceipt",
        )
        if key in value
    }
    compact.update(
        status="unknown",
        complete=False,
        truncations=[
            {
                "dimension": "maxOutputBytes",
                "limit": limit,
                "frontierRoute": [],
                "omittedCount": max(1, value["counters"]["returnedRows"]),
                "omittedDigest": "sha256:" + hashlib.sha256(encoded).hexdigest(),
            }
        ],
        result=None,
        diagnostics=[],
    )
    # Even the truncation report must fit; otherwise the configured header is impossible.
    if len(_json_bytes(compact)) > limit:
        raise ValueError("derivation query output bound is smaller than its result header")
    return compact


def _json_bytes(value: Any) -> bytes:
    """Encode query output canonically for size checks and omission digests."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _invalid(prepared: _Prepared, kind: str) -> dict[str, Any]:
    """Return the common invalid envelope without attempting graph traversal."""
    return _result(prepared, kind, _Budget(prepared.bounds), "invalid", None, complete=False)


def _residual(row: _Residual) -> dict[str, Any]:
    """Serialize a residual, adding a route only beyond its immediate premise."""
    result: dict[str, Any] = {
        "ordinal": row.route[0][1] if row.route else None,
        "ref": _ref(row.ref),
    }
    if len(row.route) > 1:
        result["route"] = _route(row.route)
    return result


def _route(route: Route) -> list[dict[str, Any]]:
    """Serialize ordered step/ordinal hops without collapsing repeated slots."""
    return [{"stepRef": _ref(step), "premiseOrdinal": ordinal} for step, ordinal in route]


def _occurrence(row: Occurrence) -> dict[str, Any]:
    """Serialize one premise slot without deduplicating its statement reference."""
    step, ordinal, premise = row
    return {"stepRef": _ref(step), "ordinal": ordinal, "ref": _ref(premise)}
