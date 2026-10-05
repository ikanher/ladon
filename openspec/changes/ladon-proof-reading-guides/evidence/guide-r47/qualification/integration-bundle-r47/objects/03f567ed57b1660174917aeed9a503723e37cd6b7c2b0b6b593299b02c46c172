"""Accumulate a bounded selected derivation slice without recursive calls.

One OR alternative is selected per conclusion; every selected AND premise slot
is recorded before shared subgoals are expanded. Exhaustion leaves an explicit
frontier and cannot establish a closed slice or checker acceptance.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ladon._proofir_derivation_core import (
    Occurrence,
    RefKey,
    Route,
    _Budget,
    _diagnostic,
    _key,
    _occurrence,
    _plain,
    _Prepared,
    _ref,
    _Residual,
    _route,
)


@dataclass
class _Slicer:
    """Build one bounded OR-selected, AND-complete evidence slice.

    Explicit selections are keyed by conclusion local id only after the target
    artifact has fixed their environment and kind.  Missing selections use the
    lexicographically first exact step key; all unselected alternatives remain
    visible in the result.

    Shared subgoals expand once, but premise occurrences are recorded before
    scheduling their child frames. Two selected steps that require the same fact
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
            pending.extend(reversed(self._expand_goal(goal, depth, route)))

    def _expand_goal(
        self, goal: RefKey, depth: int, route: Route
    ) -> list[tuple[RefKey, int, Route]]:
        """Charge a goal, record a leaf, or schedule the chosen step's children."""
        frontier = _slice_frontier(goal, depth, route)
        if not self.budget.depth(depth, frontier) or self._record_leaf_or_seen(goal):
            return []
        if not self.budget.take("maxVisitedRefs", frontier):
            return []
        alternatives = self.prepared.graph.by_conclusion.get(goal, ())
        if not alternatives:
            self.residuals.append(_Residual(goal, route))
            self.expanded.add(goal)
            return []
        if not self._take_alternatives(alternatives, frontier):
            return []
        step = self._choose(goal, alternatives)
        if self.error or not step:
            return []
        step_key = _key(step["stepRef"])
        if not self.budget.take("maxEvaluatedSteps", [{"stepRef": _ref(step_key)}]):
            return []
        self._record_step(goal, step, alternatives)
        return self._children(step, depth, route)

    def _record_step(
        self, goal: RefKey, step: Mapping[str, Any], alternatives: tuple[Mapping[str, Any], ...]
    ) -> None:
        """Retain the selected body and metadata for every unselected alternative."""
        step_key = _key(step["stepRef"])
        self.selections[goal], self.steps[step_key] = step_key, step
        omitted = tuple(_key(row["stepRef"]) for row in alternatives if row is not step)
        if omitted:
            self.unselected[goal] = omitted
        self.expanded.add(goal)

    def _children(
        self, step: Mapping[str, Any], depth: int, route: Route
    ) -> list[tuple[RefKey, int, Route]]:
        """Charge slots in source order before depth-first expansion begins."""
        step_key = _key(step["stepRef"])
        children: list[tuple[RefKey, int, Route]] = []
        for ordinal, premise in enumerate(step["premiseRefs"]):
            premise_key = _key(premise)
            frontier = [{"stepRef": _ref(step_key), "premiseOrdinal": ordinal}]
            if not self.budget.take("maxPremiseSlots", frontier):
                break
            self.occurrences.append((step_key, ordinal, premise_key))
            children.append((premise_key, depth + 1, (*route, (step_key, ordinal))))
        return children

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
        remaining = self.prepared.bounds.max_alternatives - self.budget.counts["alternatives"]
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
        selected = next((row for row in alternatives if _key(row["stepRef"]) == key), None)
        if not self.error and selected is None:
            self.error = _diagnostic(
                "invalid-alternative-selection",
                f"/query/selection/{goal[1]}",
                "selected step does not conclude the statement",
            )
        return selected

    def payload(self) -> dict[str, Any]:
        """Serialize accumulated evidence in exact-key deterministic order."""
        selections = [
            {"conclusionRef": _ref(goal), "stepRef": _ref(step)}
            for goal, step in sorted(self.selections.items())
        ]
        occurrences = [
            _occurrence(row) for row in sorted(self.occurrences, key=lambda row: row[:2])
        ]
        unselected = [
            {"conclusionRef": _ref(goal), "stepRefs": [_ref(step) for step in steps]}
            for goal, steps in sorted(self.unselected.items())
        ]
        residuals = [{"route": _route(row.route), "ref": _ref(row.ref)} for row in self.residuals]
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
    """Describe the exact slice occurrence hidden by a depth bound."""
    return [{"ref": _ref(goal), "depth": depth, "route": _route(route)}]
