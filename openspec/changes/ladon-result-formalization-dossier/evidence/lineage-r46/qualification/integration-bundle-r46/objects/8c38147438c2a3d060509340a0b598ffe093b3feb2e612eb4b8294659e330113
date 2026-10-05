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

Public queries assemble results over three private owners: the core validates
graphs and enforces shared bounds and envelopes; the solver searches AND/OR
support; the slicer records one selected evidence slice. Both traversals use
explicit frames so graph depth does not consume the Python call stack.

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

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ladon._proofir_derivation_core import (
    DerivationQueryBounds,
    RefKey,
    _Budget,
    _diagnostic,
    _Graph,
    _invalid,
    _InvalidGraph,
    _key,
    _occurrence,
    _plain,
    _prepare,
    _Prepared,
    _ref,
    _residual,
    _result,
)
from ladon._proofir_derivation_core import _fit_output as _fit_query_output
from ladon._proofir_derivation_slice import _Slicer
from ladon._proofir_derivation_solver import _Solved, _Solver


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


def _legacy_available(graph: _Graph, available_refs: list[dict[str, str]]) -> frozenset[RefKey]:
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
    unresolved = tuple(_ref(key) for key in sorted({row.ref for row in solved.residuals}))
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
        return _invalid(_Prepared(**{**prepared.__dict__, "error": error}), "navigation-path")
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
        if not _advance_navigation(prepared, budget, current, depth, queue, seen, parents):
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


def _visit_navigation(prepared: _Prepared, budget: _Budget, current: RefKey, depth: int) -> bool:
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
        "selectedStepRef": _plain(solved.selected["stepRef"]) if solved.selected else None,
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


def _alternative_row(step: Mapping[str, Any], step_key: RefKey, solved: _Solved) -> dict[str, Any]:
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


def _fit_output(value: dict[str, Any], limit: int) -> dict[str, Any]:
    """Preserve the stored CLI boundary for the shared query byte limiter."""
    return _fit_query_output(value, limit)


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
