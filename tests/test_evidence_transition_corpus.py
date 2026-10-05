from __future__ import annotations

from dataclasses import replace
from itertools import product

import pytest

from ladon.evidence_dimensions import (
    EvidenceDimensions,
    transition_matrix,
    validate_evidence_state,
    validate_transition,
)

ATTRIBUTES = (
    "execution_binding", "observation_state", "operation_outcome", "source_freshness",
    "environment_match", "authority_basis", "analysis_completeness",
)


def test_each_declared_axis_pair_and_projection_has_an_enforced_decision() -> None:
    matrix = transition_matrix()
    seed = EvidenceDimensions("ambient-observed", "derived", "rejected", analysis_completeness="partial")
    count = 0
    for (_, axis), attribute in zip(matrix["axes"].items(), ATTRIBUTES, strict=True):
        for projection, policy in matrix["projections"].items():
            for left, right in product(axis["states"], repeat=2):
                parent, child = replace(seed, **{attribute: left}), replace(seed, **{attribute: right})
                allowed = right in axis["allowed"][left]
                allowed = allowed and child.observation_state in policy["observationStates"]
                _assert_decision(parent, child, projection, allowed)
                count += 1
    assert count == 1029


def _assert_decision(
    parent: EvidenceDimensions, child: EvidenceDimensions, projection: str, allowed: bool,
) -> None:
    if allowed:
        validate_transition(parent, child, projection_kind=projection)
    else:
        with pytest.raises(ValueError):
            validate_transition(parent, child, projection_kind=projection)


def test_full_state_product_rejects_contradictory_evidence() -> None:
    axes = transition_matrix()["axes"]
    count = 0
    for values in product(*(axis["states"] for axis in axes.values())):
        state = EvidenceDimensions(*values)
        if _consistent(state):
            validate_evidence_state(state)
            validate_transition(state, state)
        else:
            with pytest.raises(ValueError):
                validate_evidence_state(state)
        count += 1
    assert count == 26880


def _consistent(state: EvidenceDimensions) -> bool:
    checker = state.authority_basis in {"elaborator-check", "kernel-check"}
    if state.observation_state in {"absent", "failed"} and (
        state.operation_outcome == "accepted" or checker
    ):
        return False
    if state.operation_outcome in {"not-run", "failed"} and (
        checker or state.analysis_completeness == "complete"
    ):
        return False
    if state.operation_outcome == "not-run" and state.observation_state == "live":
        return False
    return _binding_consistent(state)


def _binding_consistent(state: EvidenceDimensions) -> bool:
    if state.observation_state == "live" and state.execution_binding == "none":
        return False
    return not (state.execution_binding == "explicit-pinned" and state.environment_match == "mismatched")


@pytest.mark.parametrize("projection", list(transition_matrix()["projections"]))
def test_no_projection_promotes_execution_or_freshness(projection: str) -> None:
    weak = EvidenceDimensions("none", "absent", "not-run")
    strong = EvidenceDimensions("explicit-pinned", "live", "accepted", "fresh", "exact")
    with pytest.raises(ValueError):
        validate_transition(weak, strong, projection_kind=projection)
    stored = EvidenceDimensions("ambient-observed", "stored", "accepted", "stale", "mismatched")
    with pytest.raises(ValueError):
        validate_transition(stored, replace(stored, source_freshness="fresh"), projection_kind=projection)
    with pytest.raises(ValueError):
        validate_transition(stored, replace(stored, environment_match="exact"), projection_kind=projection)


@pytest.mark.parametrize("projection", ["sqlite-row", "dossier", "aggregate"])
def test_readers_cannot_retain_live_observation(projection: str) -> None:
    live = EvidenceDimensions("explicit-pinned", "live", "accepted", "fresh", "exact")
    with pytest.raises(ValueError, match="cannot report live"):
        validate_transition(live, live, projection_kind=projection)
