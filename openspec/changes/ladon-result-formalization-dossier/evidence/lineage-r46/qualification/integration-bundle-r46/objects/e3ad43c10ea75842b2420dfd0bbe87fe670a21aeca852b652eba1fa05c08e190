"""Search bounded AND/OR support with explicit goal and step frames.

Earlier unknown alternatives block later selections. Memoized results retain
structural evidence only; unknown depends on remaining budget and is not cached.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ladon._proofir_derivation_core import (
    Occurrence,
    RefKey,
    _Budget,
    _Graph,
    _key,
    _ref,
    _Residual,
)

_Frame = dict[str, Any]


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

    def step(self, step: Mapping[str, Any], depth: int = 0) -> _Solved:
        """Evaluate every ordered premise occurrence of one conjunctive step."""
        return self._run(("step", step, depth))

    def _run(self, initial: tuple[str, RefKey | Mapping[str, Any], int]) -> _Solved:
        """Dispatch explicit frames; only a finished child can return to its parent."""
        stack = [_frame(*initial)]
        returned = None
        while stack:
            frame = stack[-1]
            if frame["kind"] == "goal":
                returned = self._advance_goal(frame, returned, stack)
            else:
                returned = self._advance_step(frame, returned, stack)
            if frame["stage"] == "finish":
                stack.pop()
        return returned or _Solved("unknown")

    def _advance_goal(
        self, frame: _Frame, returned: _Solved | None, stack: list[_Frame]
    ) -> _Solved | None:
        """Enter, resume, or select an OR frame without evaluating a child inline."""
        if frame["stage"] == "enter":
            returned = self._enter_goal(frame)
        elif frame["stage"] == "waiting-step":
            returned = self._accept_step(frame, _child(returned))
        if frame["stage"] == "alternatives":
            returned = self._next_alternative(frame, stack)
        if frame["stage"] == "finish":
            self.visiting.discard(frame["goal"])
            if returned is not None and returned.status != "unknown":
                self.memo[frame["goal"]] = returned
        return returned

    def _enter_goal(self, frame: _Frame) -> _Solved | None:
        """Preserve depth, available-leaf, memo, visit, and cycle check order."""
        goal = frame["goal"]
        frontier = [{"ref": _ref(goal), "depth": frame["depth"]}]
        frame["stage"] = "finish"
        if not self.budget.depth(frame["depth"], frontier):
            return _Solved("unknown")
        if goal in self.available:
            return _Solved("true")
        if goal in self.memo:
            return self.memo[goal]
        if not self.budget.take("maxVisitedRefs", frontier):
            return _Solved("unknown")
        if goal in self.visiting:
            return _Solved("invalid", residuals=(_Residual(goal),))
        self.visiting.add(goal)
        frame.update(
            stage="alternatives",
            index=0,
            failures=[],
            alternatives=self.graph.by_conclusion.get(goal, ()),
        )
        return None

    def _accept_step(self, frame: _Frame, child: _Solved) -> _Solved | None:
        """Select a true child, stop at unknown/invalid, or retain one failed branch."""
        failures = tuple(frame["failures"])
        frame["stage"] = "finish"
        step = frame["step"]
        step_key = _key(step["stepRef"])
        if child.status == "true":
            return _Solved(
                "true",
                step,
                ((frame["goal"], step_key), *child.selections),
                child.occurrences,
                failures=failures,
            )
        if child.status in {"unknown", "invalid"}:
            return _Solved(child.status, failures=failures)
        frame["failures"].append((step_key, "false", child.residuals))
        frame["index"] += 1
        frame["stage"] = "alternatives"
        return None

    def _next_alternative(self, frame: _Frame, stack: list[_Frame]) -> _Solved | None:
        """Charge one sorted alternative before scheduling its conjunctive step."""
        alternatives = frame["alternatives"]
        failures = tuple(frame["failures"])
        if frame["index"] >= len(alternatives):
            frame["stage"] = "finish"
            return _Solved(
                "false",
                residuals=tuple(row for _, _, rows in failures for row in rows),
                failures=failures,
            )
        step = alternatives[frame["index"]]
        frontier = [{"stepRef": _ref(_key(step["stepRef"]))}]
        if not self.budget.take("maxAlternatives", frontier):
            frame["stage"] = "finish"
            return _Solved("unknown", failures=failures)
        frame.update(step=step, stage="waiting-step")
        stack.append(_frame("step", step, frame["depth"]))
        return None

    def _advance_step(
        self, frame: _Frame, returned: _Solved | None, stack: list[_Frame]
    ) -> _Solved | None:
        """Charge a step or resume its ordered AND premises after a child returns."""
        if frame["stage"] == "enter":
            frontier = [{"stepRef": _ref(_key(frame["step"]["stepRef"]))}]
            if not self.budget.take("maxEvaluatedSteps", frontier):
                frame["stage"] = "finish"
                return _Solved("unknown")
            frame["stage"] = "premise"
        elif frame["stage"] == "waiting-goal":
            returned = self._accept_premise(frame, _child(returned))
        if frame["stage"] == "premise":
            returned = self._next_premise(frame, stack)
        return returned

    def _accept_premise(self, frame: _Frame, child: _Solved) -> _Solved | None:
        """Prefix the first unsupported occurrence or accumulate a true witness."""
        if child.status != "true":
            step_key = _key(frame["step"]["stepRef"])
            residual = child.residuals[:1] or (_Residual(frame["premise_key"]),)
            frame["stage"] = "finish"
            return _Solved(
                child.status,
                residuals=tuple(
                    _Residual(row.ref, ((step_key, frame["index"]), *row.route)) for row in residual
                ),
            )
        frame["selections"].extend(child.selections)
        frame["occurrences"].extend(child.occurrences)
        frame["stage"] = "premise"
        frame["index"] += 1
        return None

    def _next_premise(self, frame: _Frame, stack: list[_Frame]) -> _Solved | None:
        """Record each charged premise slot before scheduling its statement goal."""
        step = frame["step"]
        ordinal = frame["index"]
        if ordinal >= len(step["premiseRefs"]):
            frame["stage"] = "finish"
            return _Solved("true", step, tuple(frame["selections"]), tuple(frame["occurrences"]))
        step_key = _key(step["stepRef"])
        premise_key = _key(step["premiseRefs"][ordinal])
        frontier = [{"stepRef": _ref(step_key), "premiseOrdinal": ordinal}]
        if not self.budget.take("maxPremiseSlots", frontier):
            frame["stage"] = "finish"
            return _Solved("unknown")
        frame["occurrences"].append((step_key, ordinal, premise_key))
        frame.update(premise_key=premise_key, stage="waiting-goal")
        stack.append(_frame("goal", premise_key, frame["depth"] + 1))
        return None


def _frame(kind: str, value: RefKey | Mapping[str, Any], depth: int) -> dict[str, Any]:
    """Initialize one goal or step frame with independent occurrence accumulators."""
    return {
        "kind": kind,
        "goal": value if kind == "goal" else None,
        "step": value if kind == "step" else None,
        "depth": depth,
        "stage": "enter",
        "index": 0,
        "selections": [],
        "occurrences": [],
    }


def _child(returned: _Solved | None) -> _Solved:
    """Require a finished child when a waiting frame resumes."""
    if returned is None:
        raise AssertionError("missing iterative child result")
    return returned
