"""Run bounded, prover-neutral queries over ProofIR derivation hypergraphs.

The module treats a derivation step as an AND node: every premise occurrence
must be supported for the step to support its conclusion.  Steps with the same
conclusion are OR alternatives.  Repeated premises remain distinct occurrences
because their ordinals are part of the evidence structure.

Inputs cross one strict validation boundary before traversal. References are
compact ``(kind, local-id)`` pairs owned by the enclosing artifact; a local
identifier alone never establishes identity. Native single-artifact queries
reject malformed, external, dangling, and cyclic input instead of repairing or
silently omitting it.

Every traversal is bounded.  Exhausting a bound yields an explicit frontier and
an unknown or truncated result, never a fabricated negative answer.  Stable sort
keys make results independent of input step order.

All results describe structural evidence only.  This module does not execute a
checker and cannot establish theorem truth or checker acceptance.

The native query lifecycle is deliberately uniform:

1. Validate the envelope and require ``proofir.derivation``.
2. Build indexes from exact references and stable step ordering.
3. Validate the target and every caller-supplied available reference.
4. Traverse while charging the shared finite resource dimensions.
5. Serialize a common result envelope and enforce its byte-size ceiling.

The common envelope separates several concepts that callers must not conflate:

``status``
    The query-specific structural outcome.  Satisfaction uses true, false, or
    unknown; navigation and slicing use their own documented structural states.
``complete``
    Whether bounded execution omitted work.  It does not mean that a slice is
    closed, that a theorem is true, or that any external checker accepted it.
``checkerAcceptance``
    Always ``not-evaluated`` because checker execution is outside this module.
``truncations``
    Exact frontier records for work hidden by a resource limit.  They preserve
    the distinction between negative evidence and missing computation.
``nonclaims``
    A stable reminder of the structural-only authority boundary.

Native reference validation is intentionally stricter than graph reachability.
Every query reference is a compact local pair with nonempty strings, the expected
kind, and a declared subject. An ``artifactRef`` needs a batch resolver and is
therefore invalid for this single-artifact graph view.

The four native operations expose different views over the same semantics:

``navigation_path``
    Finds one shortest premise-to-conclusion route.  Because a route follows one
    premise slot at a time, sibling slots are emitted as explicit requirements.
``complete_derivation_slice``
    Selects one step per reachable conclusion and expands every premise slot of
    each selected step.  Unselected OR alternatives remain observable metadata.
``structural_satisfaction``
    Searches for one closed witness under caller-provided available leaves and
    reports residual occurrences when every visible alternative fails.
``analyze_alternatives``
    Evaluates immediate alternatives independently, retaining each conjunctive
    premise set rather than unioning premises across alternatives.

Acyclic artifacts reject cycles; recursive artifacts validate exact declared SCC
membership.  Recursive SCC analysis remains structural metadata only.  It does
not establish fixed-point semantics, theorem truth, or checker acceptance, and
ordinary satisfaction deliberately reports a recursive cycle as invalid.
"""

from __future__ import annotations

import hashlib
import json
from collections import deque
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

# Exact artifact-local reference pairs are the only semantic join keys used here.
# Step arrays carry no priority, so alternatives are always sorted by exact step key.
# Premise arrays are different: their source order and repeated slots are preserved.


@dataclass(frozen=True)
class DerivationEvaluation:
    """A structural graph result, never a checker-acceptance observation.

    ``checker_accepted`` remains false by construction.  The field survives for
    compatibility and must not be inferred from structural satisfaction.
    """

    structurally_satisfied: bool
    selected_step_ref: dict[str, str] | None = None
    unresolved_refs: tuple[dict[str, str], ...] = ()
    checker_accepted: bool = False

    @property
    def satisfied(self) -> bool:
        """Compatibility spelling for structural satisfaction only."""

        return self.structurally_satisfied


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
        steps = tuple(
            sorted(value["payload"]["steps"], key=lambda row: _key(row["stepRef"]))
        )
        grouped = _steps_by_conclusion(steps)
        outgoing = _steps_by_premise(steps)
        dependencies = _step_dependencies(steps)
        return cls(
            checked.content_id,
            str(value["environmentRef"]),
            frozenset(_key(row) for row in value["subjectRefs"]),
            steps,
            {key: tuple(rows) for key, rows in grouped.items()},
            {
                key: tuple(sorted(rows, key=lambda row: row[:3]))
                for key, rows in outgoing.items()
            },
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
            return None, _diagnostic(
                "invalid-reference-shape", pointer, "invalid reference"
            )
        if not all(isinstance(row[name], str) and row[name] for name in fields):
            return None, _diagnostic(
                "invalid-reference-shape", pointer, "empty reference field"
            )
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
            outgoing.setdefault(_key(premise), []).append(
                (step_key, ordinal, conclusion, step)
            )
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
class _Solved:
    """Tri-state solver result with selected evidence or scoped residuals."""

    status: str
    selected: Mapping[str, Any] | None = None
    selections: tuple[tuple[RefKey, RefKey], ...] = ()
    occurrences: tuple[Occurrence, ...] = ()
    residuals: tuple[_Residual, ...] = ()
    failures: tuple[tuple[RefKey, str, tuple[_Residual, ...]], ...] = ()


class _Solver:
    """Memoized bounded least-support search over the indexed AND/OR graph.

    ``unknown`` is contagious across OR selection because a bounded earlier
    alternative might succeed.  ``invalid`` is reserved for a cycle encountered
    despite envelope validation and is never interpreted as ordinary failure.

    A goal has structural status ``true`` when it is an available leaf or at
    least one concluding step has status ``true``.  A step is true only when
    every ordered premise occurrence is true.  A goal is false only when every
    visible alternative is false; a goal with no alternatives is a residual
    false leaf.

    Memoization stores final true, false, and invalid results, but never unknown.
    Unknown depends on remaining budget and cannot safely be reused as a graph
    property.  Available leaves are checked before the memo so caller evidence
    remains the strongest local support condition.

    OR evaluation follows exact step-key order.  Encountering unknown stops the
    scan: choosing a later true step would conceal the possibility that omitted
    work supports the earlier alternative.  The same rule makes selection stable
    when bounds change.

    Step evaluation short-circuits at the first non-true premise but records the
    premise's full route prefix.  This is logically sound for conjunctive status
    and deliberately does not claim to enumerate every failing conjunct.
    """

    def __init__(self, graph: _Graph, available: frozenset[RefKey], budget: _Budget):
        self.graph, self.available, self.budget = graph, available, budget
        self.memo: dict[RefKey, _Solved] = {}
        self.visiting: set[RefKey] = set()

    def solve(self, goal: RefKey, depth: int = 0) -> _Solved:
        """Solve one statement goal under the available-leaf assumption."""
        return self._run(("goal", goal, depth))

    def _run(self, initial: tuple[str, RefKey | Mapping[str, Any], int]) -> _Solved:
        """Evaluate goals and steps with an explicit call stack.

        The old implementation used Python calls for every premise edge.  This
        frame machine keeps the same short-circuiting and budget events while
        making graph depth independent of the interpreter recursion limit.
        """
        stack: list[dict[str, Any]] = []
        kind, value, depth = initial
        stack.append(
            {
                "kind": kind,
                "goal": value if kind == "goal" else None,
                "step": value if kind == "step" else None,
                "depth": depth,
                "stage": "enter",
                "index": 0,
                "selections": [],
                "occurrences": [],
            }
        )
        returned: _Solved | None = None
        while stack:
            frame = stack[-1]
            if frame["kind"] == "goal":
                goal = frame["goal"]
                if frame["stage"] == "enter":
                    frontier = [{"ref": _ref(goal), "depth": frame["depth"]}]
                    if not self.budget.depth(frame["depth"], frontier):
                        returned = _Solved("unknown")
                    elif goal in self.available:
                        returned = _Solved("true")
                    elif goal in self.memo:
                        returned = self.memo[goal]
                    elif not self.budget.take("maxVisitedRefs", frontier):
                        returned = _Solved("unknown")
                    elif goal in self.visiting:
                        returned = _Solved("invalid", residuals=(_Residual(goal),))
                    else:
                        self.visiting.add(goal)
                        frame.update(
                            stage="alternatives", alternatives=self.graph.by_conclusion.get(goal, ()),
                            index=0, failures=[]
                        )
                        continue
                elif frame["stage"] == "waiting-step":
                    child = returned
                    returned = None
                    if child is None:
                        raise AssertionError("missing iterative child result")
                    if child.status == "true":
                        step = frame["step"]
                        returned = _Solved(
                            "true", step,
                            ((goal, _key(step["stepRef"])), *child.selections),
                            child.occurrences,
                            failures=tuple(frame["failures"]),
                        )
                        frame["stage"] = "finish"
                    elif child.status in {"unknown", "invalid"}:
                        returned = _Solved(child.status, failures=tuple(frame["failures"]))
                        frame["stage"] = "finish"
                    else:
                        step_key = _key(frame["step"]["stepRef"])
                        frame["failures"].append((step_key, "false", child.residuals))
                        frame["index"] += 1
                        frame["stage"] = "alternatives"
                        continue
                if frame["stage"] == "enter":
                    # Immediate leaves, memo hits, and budget failures return
                    # without creating an alternatives frame.
                    frame["stage"] = "finish"
                if frame["stage"] == "alternatives":
                    alternatives = frame["alternatives"]
                    if frame["index"] >= len(alternatives):
                        returned = _Solved(
                            "false",
                            residuals=tuple(row for _, _, rows in frame["failures"] for row in rows),
                            failures=tuple(frame["failures"]),
                        )
                        frame["stage"] = "finish"
                    else:
                        step = alternatives[frame["index"]]
                        step_key = _key(step["stepRef"])
                        if not self.budget.take("maxAlternatives", [{"stepRef": _ref(step_key)}]):
                            returned = _Solved("unknown", failures=tuple(frame["failures"]))
                            frame["stage"] = "finish"
                        else:
                            frame["step"] = step
                            frame["stage"] = "waiting-step"
                            stack.append({"kind": "step", "step": step, "goal": None,
                                          "depth": frame["depth"], "stage": "enter",
                                          "index": 0, "selections": [], "occurrences": []})
                            continue
                if frame["stage"] == "finish":
                    if goal in self.visiting:
                        self.visiting.remove(goal)
                    if returned is not None and returned.status != "unknown":
                        self.memo[goal] = returned
            else:
                step = frame["step"]
                step_key = _key(step["stepRef"])
                if frame["stage"] == "enter":
                    if not self.budget.take("maxEvaluatedSteps", [{"stepRef": _ref(step_key)}]):
                        returned = _Solved("unknown")
                        frame["stage"] = "finish"
                    else:
                        frame["stage"] = "premise"
                elif frame["stage"] == "waiting-goal":
                    child = returned
                    returned = None
                    premise_key = frame["premise_key"]
                    ordinal = frame["index"]
                    if child is None:
                        raise AssertionError("missing iterative premise result")
                    if child.status != "true":
                        residual = child.residuals[:1] or (_Residual(premise_key),)
                        returned = _Solved(
                            child.status,
                            residuals=tuple(
                                _Residual(row.ref, ((step_key, ordinal), *row.route))
                                for row in residual
                            ),
                        )
                        frame["stage"] = "finish"
                    else:
                        frame["selections"].extend(child.selections)
                        frame["occurrences"].extend(child.occurrences)
                        frame["stage"] = "premise"
                        frame["index"] += 1
                if frame["stage"] == "premise":
                    premises = step["premiseRefs"]
                    if frame["index"] >= len(premises):
                        returned = _Solved(
                            "true", step, tuple(frame["selections"]), tuple(frame["occurrences"])
                        )
                        frame["stage"] = "finish"
                    else:
                        ordinal = frame["index"]
                        premise_key = _key(premises[ordinal])
                        frontier = [{"stepRef": _ref(step_key), "premiseOrdinal": ordinal}]
                        if not self.budget.take("maxPremiseSlots", frontier):
                            returned = _Solved("unknown")
                            frame["stage"] = "finish"
                        else:
                            frame["occurrences"].append((step_key, ordinal, premise_key))
                            frame["premise_key"] = premise_key
                            frame["stage"] = "waiting-goal"
                            stack.append({"kind": "goal", "goal": premise_key, "step": None,
                                          "depth": frame["depth"] + 1, "stage": "enter"})
                            continue
            if frame["stage"] == "waiting-step":
                # The child step returned into the goal frame on this iteration.
                child = returned
                returned = None
                if child is None:
                    raise AssertionError("missing iterative step result")
                goal = frame["goal"]
                if child.status == "true":
                    returned = _Solved(
                        "true", frame["step"],
                        ((goal, _key(frame["step"]["stepRef"])), *child.selections),
                        child.occurrences, failures=tuple(frame["failures"]),
                    )
                    frame["stage"] = "finish"
                elif child.status in {"unknown", "invalid"}:
                    returned = _Solved(child.status, failures=tuple(frame["failures"]))
                    frame["stage"] = "finish"
                else:
                    frame["failures"].append((_key(frame["step"]["stepRef"]), "false", child.residuals))
                    frame["index"] += 1
                    frame["stage"] = "alternatives"
            if frame["stage"] == "finish":
                stack.pop()
        return returned or _Solved("unknown")

    def _alternatives(self, goal: RefKey, depth: int) -> _Solved:
        """Evaluate sorted OR alternatives without selecting past unknown work."""
        # OR selection is conservative: an earlier unknown blocks every later choice.
        alternatives = self.graph.by_conclusion.get(goal, ())
        if not alternatives:
            return _Solved("false", residuals=(_Residual(goal),))
        failures: list[tuple[RefKey, str, tuple[_Residual, ...]]] = []
        for step in alternatives:
            step_key = _key(step["stepRef"])
            if not self.budget.take("maxAlternatives", [{"stepRef": _ref(step_key)}]):
                return _Solved("unknown", failures=tuple(failures))
            solved = self.step(step, depth)
            if solved.status in {"unknown", "invalid"}:
                return _Solved(solved.status, failures=tuple(failures))
            if solved.status == "true":
                return _Solved(
                    "true",
                    step,
                    ((goal, step_key), *solved.selections),
                    solved.occurrences,
                    failures=tuple(failures),
                )
            failures.append((step_key, "false", solved.residuals))
        return _Solved(
            "false",
            residuals=tuple(row for _, _, rows in failures for row in rows),
            failures=tuple(failures),
        )

    def step(self, step: Mapping[str, Any], depth: int = 0) -> _Solved:
        """Evaluate every ordered premise occurrence of one conjunctive step."""
        return self._run(("step", step, depth))


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
        "limitations": (
            [_NAVIGATION_LIMITATION] if query_kind == "navigation-path" else []
        ),
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
        )
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
        raise ValueError(
            "derivation query output bound is smaller than its result header"
        )
    return compact


def _json_bytes(value: Any) -> bytes:
    """Encode query output canonically for size checks and omission digests."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _invalid(prepared: _Prepared, kind: str) -> dict[str, Any]:
    """Return the common invalid envelope without attempting graph traversal."""
    return _result(
        prepared, kind, _Budget(prepared.bounds), "invalid", None, complete=False
    )


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
    return [
        {"stepRef": _ref(step), "premiseOrdinal": ordinal} for step, ordinal in route
    ]


def evaluate_derivation(
    artifact: Any,
    target_ref: dict[str, str],
    *,
    available_refs: list[dict[str, str]] = (),
) -> DerivationEvaluation:
    """Evaluate structural alternatives while preserving the legacy return type.

    Malformed artifacts and targets become unsatisfied legacy results.  Foreign
    available references retain historical ignore semantics rather than the
    strict invalid-result behavior of native queries.
    """

    try:
        graph = _Graph.build(artifact)
    except _InvalidGraph as error:
        if error.diagnostic["code"] == "external-reference-not-local":
            raise ValueError(error.diagnostic["message"]) from error
        return DerivationEvaluation(False, unresolved_refs=(dict(target_ref),))
    for row in available_refs:
        if isinstance(row, Mapping) and "artifactRef" in row:
            raise ValueError(
                "single-artifact derivation queries cannot resolve external artifactRef"
            )
    target, error = graph.local_ref(target_ref, "/query/targetRef")
    if error:
        return DerivationEvaluation(False, unresolved_refs=(dict(target_ref),))
    available = _legacy_available(graph, available_refs)
    bounds = DerivationQueryBounds()
    solved = _Solver(graph, available, _Budget(bounds)).solve(target)
    return _legacy_evaluation(solved)


def _legacy_available(
    graph: _Graph, available_refs: list[dict[str, str]]
) -> frozenset[RefKey]:
    """Filter legacy available refs, preserving its ignore-invalid behavior."""
    fields = {"kind", "localId"}
    result: set[RefKey] = set()
    for row in available_refs:
        if not isinstance(row, Mapping) or set(row) != fields:
            continue
        key = _key(row)
        if key in graph.subjects:
            result.add(key)
    return frozenset(result)


def _legacy_evaluation(solved: _Solved) -> DerivationEvaluation:
    """Project a solver state into the smaller historical evaluation type."""
    selected = _plain(solved.selected["stepRef"]) if solved.selected else None
    unresolved = tuple(
        _ref(key) for key in sorted({row.ref for row in solved.residuals})
    )
    return DerivationEvaluation(solved.status == "true", selected, unresolved)


def navigation_path(
    artifact: Any,
    start_ref: dict[str, str],
    target_ref: dict[str, str],
    *,
    bounds: DerivationQueryBounds | None = None,
) -> dict[str, Any]:
    """Return one shortest linear route with omitted AND siblings made explicit.

    Breadth-first traversal follows premise-to-conclusion edges.  The returned
    route is navigational evidence only: sibling requirements state why a path
    through one premise is not by itself a complete derivation.

    Multiple shortest routes are resolved by deterministic outgoing-edge order.
    Reaching the target ends expansion without charging unrelated queued work.
    A bounded frontier returns unknown, whereas an exhausted unbounded search
    returns not-found.
    """

    prepared = _prepare(artifact, target_ref, [], bounds)
    if prepared.error:
        return _invalid(prepared, "navigation-path")
    start, error = prepared.graph.local_ref(start_ref, "/query/startRef")
    if error:
        return _invalid(
            _Prepared(**{**prepared.__dict__, "error": error}), "navigation-path"
        )
    budget, parents = _Budget(prepared.bounds), {}
    seen = _search_navigation(prepared, start, budget, parents)
    found = prepared.target in seen
    payload = (
        _navigation_payload(prepared, start, parents)
        if found
        else {"startRef": _ref(start), "path": [], "requirements": []}
    )
    budget.counts["returnedRows"] = len(payload["path"]) + len(payload["requirements"])
    status = "found" if found else "unknown" if budget.truncations else "not-found"
    return _result(
        prepared,
        "navigation-path",
        budget,
        status,
        payload,
        complete=not budget.truncations,
    )


def _search_navigation(
    prepared: _Prepared,
    start: RefKey,
    budget: _Budget,
    parents: dict[RefKey, tuple[RefKey, RefKey, int, Mapping[str, Any]]],
) -> set[RefKey]:
    """Search breadth-first until the target, exhaustion, or a resource frontier."""
    queue, seen = deque([(start, 0)]), {start}
    while queue and prepared.target not in seen:
        current, depth = queue.popleft()
        if not _visit_navigation(prepared, budget, current, depth):
            break
        if not _advance_navigation(
            prepared, budget, current, depth, queue, seen, parents
        ):
            break
    return seen


def _advance_navigation(
    prepared: _Prepared,
    budget: _Budget,
    current: RefKey,
    depth: int,
    queue: deque[tuple[RefKey, int]],
    seen: set[RefKey],
    parents: dict[RefKey, tuple[RefKey, RefKey, int, Mapping[str, Any]]],
) -> bool:
    """Queue unseen conclusions for every deterministically ordered outgoing edge."""
    for edge in prepared.graph.outgoing.get(current, ()):
        if not _take_navigation_edge(prepared, budget, edge, depth):
            return False
        step, ordinal, conclusion, row = edge
        if conclusion in seen:
            continue
        parents[conclusion] = (current, step, ordinal, row)
        seen.add(conclusion)
        queue.append((conclusion, depth + 1))
        if conclusion == prepared.target:
            break
    return True


def _visit_navigation(
    prepared: _Prepared, budget: _Budget, current: RefKey, depth: int
) -> bool:
    """Charge the depth and statement-visit budgets for one dequeued node."""
    frontier = [{"ref": _ref(current), "depth": depth}]
    return budget.depth(depth, frontier) and budget.take("maxVisitedRefs", frontier)


def _take_navigation_edge(
    prepared: _Prepared,
    budget: _Budget,
    edge: tuple[RefKey, int, RefKey, Mapping[str, Any]],
    depth: int,
) -> bool:
    """Charge step, premise-slot, and next-depth bounds for one hyperedge slot."""
    step, ordinal, conclusion, _ = edge
    frontier = [{"stepRef": _ref(step), "premiseOrdinal": ordinal}]
    return (
        budget.take("maxEvaluatedSteps", frontier)
        and budget.take("maxPremiseSlots", frontier)
        and budget.depth(depth + 1, [{"ref": _ref(conclusion), "depth": depth + 1}])
    )


def _navigation_payload(
    prepared: _Prepared,
    start: RefKey,
    parents: Mapping[RefKey, tuple[RefKey, RefKey, int, Mapping[str, Any]]],
) -> dict[str, Any]:
    """Reconstruct a route and expose every untraversed sibling premise slot."""
    chain, cursor = [], prepared.target
    while cursor != start:
        previous, step, ordinal, row = parents[cursor]
        chain.append((previous, step, ordinal, row))
        cursor = previous
    chain.reverse()
    path = [
        {
            "statementRef": _ref(statement),
            "viaStepRef": _ref(step),
            "viaPremiseOrdinal": ordinal,
        }
        for statement, step, ordinal, _ in chain
    ]
    path.append(
        {
            "statementRef": _ref(prepared.target),
            "viaStepRef": None,
            "viaPremiseOrdinal": None,
        }
    )
    requirements = [
        {
            "stepRef": _ref(step),
            "chosenPremiseOrdinal": chosen,
            "siblingPremiseOccurrences": [
                {"ordinal": ordinal, "ref": _ref(_key(premise))}
                for ordinal, premise in enumerate(row["premiseRefs"])
                if ordinal != chosen
            ],
        }
        for _, step, chosen, row in chain
    ]
    return {"startRef": _ref(start), "path": path, "requirements": requirements}


@dataclass
class _Slicer:
    """Build one bounded OR-selected, AND-complete evidence slice.

    Explicit selections are keyed by conclusion local id only after the target
    artifact has fixed their environment and kind.  Missing selections use the
    lexicographically first exact step key; all unselected alternatives remain
    visible in the result.

    Shared subgoals expand once, but premise occurrences are recorded before the
    recursive call.  Consequently two selected steps that require the same fact
    retain two evidence slots even though the shared subgraph is serialized once.

    Available statements are leaves regardless of whether the graph also has a
    concluding step for them.  Unsupported leaves become route-scoped residuals.
    Neither case is treated as a validator error.

    Alternative capacity is reserved for the complete set before selection.
    Choosing from a partially visible OR set would make a deterministic-looking
    slice conceal an omitted lexicographically earlier or explicitly requested
    step.  The slicer therefore truncates before making that choice.

    The accumulator separates selections, unique step bodies, premise slots,
    available leaves, residual occurrences, and unselected alternatives.  That
    separation lets consumers inspect evidence without reconstructing semantics
    from a flattened edge set.
    """

    prepared: _Prepared
    selection: Mapping[str, Mapping[str, Any]]
    budget: _Budget = field(init=False)
    selections: dict[RefKey, RefKey] = field(default_factory=dict)
    steps: dict[RefKey, Mapping[str, Any]] = field(default_factory=dict)
    occurrences: list[Occurrence] = field(default_factory=list)
    available: set[RefKey] = field(default_factory=set)
    residuals: list[_Residual] = field(default_factory=list)
    unselected: dict[RefKey, tuple[RefKey, ...]] = field(default_factory=dict)
    expanded: set[RefKey] = field(default_factory=set)
    error: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self.budget = _Budget(self.prepared.bounds)

    def run(self) -> None:
        """Expand the prepared target into this mutable slice accumulator."""
        self._expand_iterative(self.prepared.target)

    def _expand_iterative(self, target: RefKey) -> None:
        """Expand slice goals with explicit frames instead of Python recursion."""
        pending: list[tuple[RefKey, int, Route]] = [(target, 0, ())]
        while pending and not self.error and not self.budget.truncations:
            goal, depth, route = pending.pop()
            frontier = _slice_frontier(goal, depth, route)
            if not self.budget.depth(depth, frontier):
                continue
            if self._record_leaf_or_seen(goal):
                continue
            if not self.budget.take("maxVisitedRefs", frontier):
                continue
            alternatives = self.prepared.graph.by_conclusion.get(goal, ())
            if not alternatives:
                self.residuals.append(_Residual(goal, route))
                self.expanded.add(goal)
                continue
            if not self._take_alternatives(alternatives, frontier):
                continue
            step = self._choose(goal, alternatives)
            if self.error or not step:
                continue
            step_key = _key(step["stepRef"])
            if not self.budget.take("maxEvaluatedSteps", [{"stepRef": _ref(step_key)}]):
                continue
            self.selections[goal], self.steps[step_key] = step_key, step
            omitted = tuple(_key(row["stepRef"]) for row in alternatives if row is not step)
            if omitted:
                self.unselected[goal] = omitted
            self.expanded.add(goal)
            children: list[tuple[RefKey, int, Route]] = []
            for ordinal, premise in enumerate(step["premiseRefs"]):
                premise_key = _key(premise)
                premise_frontier = [{"stepRef": _ref(step_key), "premiseOrdinal": ordinal}]
                if not self.budget.take("maxPremiseSlots", premise_frontier):
                    break
                self.occurrences.append((step_key, ordinal, premise_key))
                children.append((premise_key, depth + 1, (*route, (step_key, ordinal))))
            pending.extend(reversed(children))

    def expand(self, goal: RefKey, depth: int, route: Route) -> None:
        """Expand one goal while retaining route-scoped residual occurrences."""
        if self.error or self.budget.truncations:
            return
        frontier = _slice_frontier(goal, depth, route)
        if not self.budget.depth(depth, frontier):
            return
        if self._record_leaf_or_seen(goal):
            return
        if not self.budget.take("maxVisitedRefs", frontier):
            return
        alternatives = self.prepared.graph.by_conclusion.get(goal, ())
        if not alternatives:
            self.residuals.append(_Residual(goal, route))
            self.expanded.add(goal)
            return
        if not self._take_alternatives(alternatives, frontier):
            return
        step = self._choose(goal, alternatives)
        if self.error or not step:
            return
        self._expand_step(goal, step, alternatives, depth, route)

    def _record_leaf_or_seen(self, goal: RefKey) -> bool:
        """Record available leaves and prevent repeated expansion of shared goals."""
        if goal in self.prepared.available:
            self.available.add(goal)
            return True
        return goal in self.expanded

    def _take_alternatives(
        self,
        alternatives: tuple[Mapping[str, Any], ...],
        frontier: list[dict[str, Any]],
    ) -> bool:
        """Reserve the complete alternative set or truncate before choosing."""
        remaining = (
            self.prepared.bounds.max_alternatives - self.budget.counts["alternatives"]
        )
        if len(alternatives) <= remaining:
            self.budget.counts["alternatives"] += len(alternatives)
            return True
        self.budget.cut(
            "maxAlternatives",
            self.prepared.bounds.max_alternatives,
            frontier,
            max(1, len(alternatives) - max(0, remaining)),
        )
        return False

    def _choose(
        self, goal: RefKey, alternatives: tuple[Mapping[str, Any], ...]
    ) -> Mapping[str, Any] | None:
        """Resolve an explicit alternative or choose the stable default."""
        requested = self.selection.get(goal[1])
        if requested is None:
            return alternatives[0]
        key, self.error = self.prepared.graph.local_ref(
            requested, f"/query/selection/{goal[1]}", "derivation-step"
        )
        selected = next(
            (row for row in alternatives if _key(row["stepRef"]) == key), None
        )
        if not self.error and selected is None:
            self.error = _diagnostic(
                "invalid-alternative-selection",
                f"/query/selection/{goal[1]}",
                "selected step does not conclude the statement",
            )
        return selected

    def _expand_step(
        self,
        goal: RefKey,
        step: Mapping[str, Any],
        alternatives: tuple[Mapping[str, Any], ...],
        depth: int,
        route: Route,
    ) -> None:
        """Record a chosen step and recursively expand every premise occurrence."""
        step_key = _key(step["stepRef"])
        if not self.budget.take("maxEvaluatedSteps", [{"stepRef": _ref(step_key)}]):
            return
        self.selections[goal], self.steps[step_key] = step_key, step
        omitted = tuple(_key(row["stepRef"]) for row in alternatives if row is not step)
        if omitted:
            self.unselected[goal] = omitted
        self.expanded.add(goal)
        for ordinal, premise in enumerate(step["premiseRefs"]):
            premise_key = _key(premise)
            frontier = [{"stepRef": _ref(step_key), "premiseOrdinal": ordinal}]
            if not self.budget.take("maxPremiseSlots", frontier):
                return
            self.occurrences.append((step_key, ordinal, premise_key))
            self.expand(premise_key, depth + 1, (*route, (step_key, ordinal)))

    def payload(self) -> dict[str, Any]:
        """Serialize accumulated evidence in exact-key deterministic order."""
        selections = [
            {"conclusionRef": _ref(goal), "stepRef": _ref(step)}
            for goal, step in sorted(self.selections.items())
        ]
        occurrences = [
            _occurrence(row)
            for row in sorted(self.occurrences, key=lambda row: row[:2])
        ]
        unselected = [
            {"conclusionRef": _ref(goal), "stepRefs": [_ref(step) for step in steps]}
            for goal, steps in sorted(self.unselected.items())
        ]
        residuals = [
            {"route": _route(row.route), "ref": _ref(row.ref)} for row in self.residuals
        ]
        self.budget.counts["returnedRows"] = sum(
            map(len, (selections, occurrences, unselected, residuals))
        )
        return {
            "selectionPolicy": "explicit-or-lexicographic-first",
            "selections": selections,
            "steps": [_plain(self.steps[key]) for key in sorted(self.steps)],
            "premiseOccurrences": occurrences,
            "availableLeaves": [_ref(key) for key in sorted(self.available)],
            "residualOccurrences": residuals,
            "unselectedAlternatives": unselected,
            "structurallyClosed": not self.residuals and not self.budget.truncations,
        }


def _slice_frontier(goal: RefKey, depth: int, route: Route) -> list[dict[str, Any]]:
    """Describe the exact recursive slice location hidden by a depth bound."""
    return [{"ref": _ref(goal), "depth": depth, "route": _route(route)}]


def _occurrence(row: Occurrence) -> dict[str, Any]:
    """Serialize one premise slot without deduplicating its statement reference."""
    step, ordinal, premise = row
    return {"stepRef": _ref(step), "ordinal": ordinal, "ref": _ref(premise)}


def complete_derivation_slice(
    artifact: Any,
    target_ref: dict[str, str],
    *,
    available_refs: list[dict[str, str]] = (),
    selection: Mapping[str, Mapping[str, Any]] | None = None,
    bounds: DerivationQueryBounds | None = None,
) -> dict[str, Any]:
    """Return one OR-selected slice containing every selected AND premise slot.

    A complete result may remain structurally open when a selected branch reaches
    a statement that is neither available nor concluded by a step.  Resource
    exhaustion instead returns an explicitly truncated, incomplete result.
    """

    prepared = _prepare(artifact, target_ref, available_refs, bounds)
    if prepared.error:
        return _invalid(prepared, "complete-derivation-slice")
    slicer = _Slicer(prepared, selection or {})
    slicer.run()
    if slicer.error:
        return _invalid(
            _Prepared(**{**prepared.__dict__, "error": slicer.error}),
            "complete-derivation-slice",
        )
    status = "truncated" if slicer.budget.truncations else "complete"
    return _result(
        prepared,
        "complete-derivation-slice",
        slicer.budget,
        status,
        slicer.payload(),
        complete=not slicer.budget.truncations,
    )


def structural_satisfaction(
    artifact: Any,
    target_ref: dict[str, str],
    *,
    available_refs: list[dict[str, str]] = (),
    bounds: DerivationQueryBounds | None = None,
) -> dict[str, Any]:
    """Decide bounded structural AND/OR satisfaction without checker authority.

    ``true`` carries one conjunctively complete witness, ``false`` carries
    residual occurrences for exhausted alternatives, and ``unknown`` carries
    truncation frontiers.  None of these states reports checker execution.
    """

    prepared = _prepare(artifact, target_ref, available_refs, bounds)
    if prepared.error:
        return _invalid(prepared, "structural-satisfaction")
    recursive_members = {
        _key(member)
        for component in prepared.graph.recursive_components
        for member in component["statementRefs"]
    }
    if prepared.target in recursive_members:
        invalid = _Prepared(
            **{
                **prepared.__dict__,
                "error": _diagnostic(
                    "recursive-satisfaction-unsupported",
                    "/query/targetRef",
                    "fixed-point satisfaction is not defined for recursive SCC members",
                ),
            }
        )
        return _invalid(invalid, "structural-satisfaction")
    budget = _Budget(prepared.bounds)
    solved = _Solver(prepared.graph, prepared.available, budget).solve(prepared.target)
    if solved.status == "invalid":
        invalid = _Prepared(
            **{
                **prepared.__dict__,
                "error": _diagnostic(
                    "derivation-cycle",
                    "/payload/steps",
                    "cycle encountered during query",
                ),
            }
        )
        return _invalid(invalid, "structural-satisfaction")
    payload = _satisfaction_payload(solved)
    budget.counts["returnedRows"] = sum(
        len(payload[key])
        for key in (
            "witnessSelections",
            "witnessPremiseOccurrences",
            "alternativeFailures",
        )
    )
    return _result(
        prepared,
        "structural-satisfaction",
        budget,
        solved.status,
        payload,
        complete=solved.status != "unknown",
    )


def _satisfaction_payload(solved: _Solved) -> dict[str, Any]:
    """Serialize solver evidence while keeping failed alternatives disjoint."""
    return {
        "selectedStepRef": _plain(solved.selected["stepRef"])
        if solved.selected
        else None,
        "witnessSelections": [
            {"conclusionRef": _ref(goal), "stepRef": _ref(step)}
            for goal, step in sorted(set(solved.selections))
        ],
        "witnessPremiseOccurrences": [_occurrence(row) for row in solved.occurrences],
        "witnessResidualOccurrences": [_residual(row) for row in solved.residuals]
        if solved.status == "false"
        else [],
        "alternativeFailures": [
            {
                "stepRef": _ref(step),
                "status": status,
                "residualOccurrences": [_residual(row) for row in rows],
            }
            for step, status, rows in solved.failures
        ],
        "selectionFinal": solved.status != "unknown",
    }


def analyze_alternatives(
    artifact: Any,
    target_ref: dict[str, str],
    *,
    available_refs: list[dict[str, str]] = (),
    bounds: DerivationQueryBounds | None = None,
) -> dict[str, Any]:
    """Enumerate bounded immediate OR alternatives without merging premise sets.

    Each row preserves that step's own ordered premise occurrences and residuals.
    Selection is final only when no earlier alternative is unknown and no bound
    hid an alternative.
    """

    prepared = _prepare(artifact, target_ref, available_refs, bounds)
    if prepared.error:
        return _invalid(prepared, "alternative-analysis")
    budget = _Budget(prepared.bounds)
    solver = _Solver(prepared.graph, prepared.available, budget)
    alternatives = prepared.graph.by_conclusion.get(prepared.target, ())
    returned = alternatives[: prepared.bounds.max_alternatives]
    _record_alternative_cap(prepared, budget, alternatives, returned)
    rows, selected, blocked = _analyze_rows(prepared, budget, solver, returned)
    payload = {
        "targetAvailable": prepared.target in prepared.available,
        "rows": rows,
        "selectedStepRef": selected,
        "selectionFinal": not blocked and not budget.truncations,
    }
    budget.counts["returnedRows"] = len(rows)
    status = "truncated" if budget.truncations else "complete"
    return _result(
        prepared,
        "alternative-analysis",
        budget,
        status,
        payload,
        complete=not budget.truncations,
    )


def analyze_sccs(
    artifact: Any,
    *,
    bounds: DerivationQueryBounds | None = None,
) -> dict[str, Any]:
    """Project declared SCCs through the isolated bounded query implementation."""

    from ladon.proofir_derivation_scc import analyze_sccs as implementation

    return implementation(artifact, bounds=bounds)


def _record_alternative_cap(
    prepared: _Prepared,
    budget: _Budget,
    alternatives: tuple[Mapping[str, Any], ...],
    returned: tuple[Mapping[str, Any], ...],
) -> None:
    """Record immediate alternatives omitted by the top-level enumeration cap."""
    omitted = len(alternatives) - len(returned)
    if omitted:
        budget.cut(
            "maxAlternatives",
            prepared.bounds.max_alternatives,
            [{"targetRef": _ref(prepared.target)}],
            omitted,
        )


def _analyze_rows(
    prepared: _Prepared,
    budget: _Budget,
    solver: _Solver,
    alternatives: tuple[Mapping[str, Any], ...],
) -> tuple[list[dict[str, Any]], dict[str, str] | None, bool]:
    """Evaluate returned alternatives and conservatively identify a selection."""
    rows: list[dict[str, Any]] = []
    selected: dict[str, str] | None = None
    blocked = False
    for step in alternatives:
        budget.counts["alternatives"] += 1
        solved = solver.step(step)
        step_key = _key(step["stepRef"])
        rows.append(_alternative_row(step, step_key, solved))
        blocked = blocked or solved.status == "unknown"
        if _selectable_alternative(prepared, solved, selected, blocked):
            selected = _ref(step_key)
    return rows, selected, blocked


def _alternative_row(
    step: Mapping[str, Any], step_key: RefKey, solved: _Solved
) -> dict[str, Any]:
    """Serialize one alternative with its own premises and residuals."""
    premises = [
        {"ordinal": ordinal, "ref": _ref(_key(premise))}
        for ordinal, premise in enumerate(step["premiseRefs"])
    ]
    return {
        "stepRef": _ref(step_key),
        "premiseOccurrences": premises,
        "structuralStatus": solved.status,
        "residualOccurrences": [_residual(row) for row in solved.residuals],
    }


def _selectable_alternative(
    prepared: _Prepared,
    solved: _Solved,
    selected: dict[str, str] | None,
    blocked: bool,
) -> bool:
    """Select a supported row only when no earlier unknown can supersede it."""
    return (
        solved.status == "true"
        and selected is None
        and not blocked
        and prepared.target not in prepared.available
    )


__all__ = [
    "DerivationEvaluation",
    "DerivationQueryBounds",
    "analyze_alternatives",
    "analyze_sccs",
    "complete_derivation_slice",
    "evaluate_derivation",
    "navigation_path",
    "structural_satisfaction",
]
