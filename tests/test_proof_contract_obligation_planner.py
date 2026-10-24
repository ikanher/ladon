"""Task 2.1 public-contract red cases; graph evidence is conditional only."""
from __future__ import annotations

from copy import deepcopy

from support.proof_contract_obligation_planner import (
    composition_case,
    multi_frontier_case,
    provider_scope_mismatch_case,
    repeated_and_case,
    request_kwargs,
    route_a_route_b,
    run_forward,
    split_context_and_case,
    substitution_mismatch_case,
    unknown_feature_case,
    unsupported_and_missing_case,
)
from support.proofir_v3_native import ref


def _ref_key(value):
    return (value["kind"], value["localId"])


def _plan(case, **overrides):
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )
    values = request_kwargs(case, **overrides)
    return plan_contract_obligations(ContractObligationPlanRequest(**values))


def test_native_route_fixture_has_local_route_a_mismatch_and_route_b_endpoint_support():
    case = route_a_route_b()
    forward = run_forward(case)
    goal = next(row["contracts"] for row in forward["frontiers"]
                if row["statementRef"] == ref("statement", "goal"))
    assert [(row["contractRecord"]["features"]["regularity"]["offset"],
             row["contractRecord"]["features"]["constantDependencies"]["allowedBinderIds"])
            for row in goal] == [(2, [])]
    assert forward["prunings"]  # route A is pruned at goal, but its full witness closure remains
    assert forward["authority"] == "conditional-profile"
    assert forward["mathematicalFalsity"] == "not-established"


def _assert_local_mismatch(local):
    assert local and local[0]["status"] in {"candidate-contract-mismatch", "unresolved-bridge"}
    assert {"regularity", "constantDependencies"} <= set(local[0]["mismatchDimensions"])


def _assert_route_a_findings(case, result):
    described = next(row for row in result["routeComparisons"] if row["describedRoute"] is True)
    assert described["stepRefs"] == case["routeASteps"]
    local = [row for row in described["comparisons"]
             if row["statementRef"] == ref("statement", "route-a-mid1")]
    _assert_local_mismatch(local)
    removed_refs = {row["removedWitness"]["witnessRef"] for row in result["prunings"]}
    described_refs = set(described["forwardRouteWitnessRefs"])
    assert removed_refs & described_refs
    assert {_ref_key(value) for value in result["coverage"]["exploredStepRefs"]} == {
        _ref_key(row["stepRef"]) for row in case["steps"]
    }


def _assert_route_b_conditional_support(result):
    alternative = next(row for row in result["routeComparisons"]
                       if row["endpoint"].get("status") == "conditional-profile-support")
    assert alternative["endpoint"]["supportKind"] == "profile-dominance"
    assert all(row["status"] != "checked-support" for row in result["routeComparisons"])
    assert result["authority"] == "conditional-profile"
    assert result["checkerAuthority"] == "none"
    assert result["mathematicalFalsity"] == "not-established"
    assert result["coverage"]["unvisitedApplications"] == []


def test_described_route_a_discrepancy_survives_route_b_support_and_frontier_pruning():
    case = route_a_route_b()
    result = _plan(case)
    _assert_route_a_findings(case, result)
    _assert_route_b_conditional_support(result)


def _priority_rows(case):
    return [
        {"rootStepRef": step, "sourceLocation": {"path": "src/proof.lean", "line": line,
         "column": 1}, "sourceId": "src:proof:" + step["localId"],
         "line": line, "column": 1, "heuristicPriority": 0}
        for step, line in zip(case["routeBSteps"] + case["routeASteps"], [1, 2, 3, 4])
    ]


def _assert_duplicate_priorities_rejected(case):
    duplicate = deepcopy(case["routePriorities"])
    duplicate.append(deepcopy(duplicate[0]))
    try:
        _plan(case, route_priorities=duplicate)
    except (TypeError, ValueError):
        return
    raise AssertionError("duplicate priority roots must be rejected")


def test_priority_metadata_rejects_foreign_wrong_kind_and_malformed_entries():
    case = route_a_route_b()
    valid = _priority_rows(case)
    malformed = [
        [dict(valid[0], rootStepRef=ref("derivation-step", "foreign")), *valid[1:]],
        [dict(valid[0], rootStepRef=ref("statement", "goal")), *valid[1:]],
        [dict(valid[0], line=-1), *valid[1:]],
        [dict(valid[0], heuristicPriority="high"), *valid[1:]],
    ]
    for rows in malformed:
        try:
            _plan(case, route_priorities=rows)
        except (TypeError, ValueError):
            continue
        raise AssertionError("malformed or foreign priority metadata must be rejected")


def _assert_priority_reorders_without_changing_findings(case, first):
    baseline = [_ref_key(row["stepRefs"][0]) for row in first["routeComparisons"]]
    case["routePriorities"] = _priority_rows(case)
    reordered = _plan(case)
    changed = [_ref_key(row["stepRefs"][0]) for row in reordered["routeComparisons"]]
    assert changed != baseline
    original = {row["routeId"]: (row["comparisons"], row["endpoint"])
                for row in first["routeComparisons"]}
    updated = {row["routeId"]: (row["comparisons"], row["endpoint"])
               for row in reordered["routeComparisons"]}
    assert updated == original
    assert reordered["priorityPolicy"] == ["source-location", "route-identity", "explicit-heuristic"]
    assert reordered["requestDigest"] != first["requestDigest"]
    assert reordered["minimalityClaim"] == "none"
    _assert_duplicate_priorities_rejected(case)


def test_planner_is_deterministic_and_uses_explicit_stable_route_priority():
    case = route_a_route_b()
    first = _plan(case)
    assert first == _plan(case)
    _assert_priority_reorders_without_changing_findings(case, first)


def test_repeated_ordered_and_premises_keep_both_occurrences_and_branch_identity():
    case = repeated_and_case()
    forward = run_forward(case)
    goal = next(row["contracts"] for row in forward["frontiers"]
                if row["statementRef"] == ref("statement", "goal"))
    occurrences = goal[0]["routeWitness"]["premiseOccurrences"]
    assert [row["ordinal"] for row in occurrences] == [0, 1]
    assert occurrences[0]["contractRef"] == occurrences[1]["contractRef"]
    result = _plan(case)
    route = result["routeComparisons"][0]
    requirements = route["backwardRequirements"]
    assert [row["premiseOrdinal"] for row in requirements] == [0, 1]
    assert requirements[0]["forwardContractRef"] == requirements[1]["forwardContractRef"]
    assert len(requirements) == 2


def test_distinct_branch_contexts_cannot_be_joined_to_claim_support():
    case = split_context_and_case()
    forward = run_forward(case)
    assert not any(row["contracts"] for row in forward["frontiers"]
                   if row["statementRef"] == ref("statement", "goal"))
    assert any(row["code"] == "incompatible-local-context" for row in forward["residuals"])
    result = _plan(case)
    assert result["status"] in {"partial", "unsupported"}
    assert result["routeComparisons"] == [] or all(
        row["endpoint"]["status"] != "conditional-profile-support"
        for row in result["routeComparisons"]
    )
    assert any(row["code"] == "incompatible-local-context" for row in result["residuals"])


def test_distinct_substitution_contexts_cannot_be_joined():
    case = substitution_mismatch_case()
    forward = run_forward(case)
    assert any(row["code"] == "incompatible-substitution" for row in forward["residuals"])
    result = _plan(case)
    assert result["endpoint"]["status"] != "conditional-profile-support"
    assert any(row["code"] == "incompatible-substitution" for row in result["residuals"])


def test_unsupported_rule_unknown_feature_and_missing_provider_remain_residuals():
    case = unsupported_and_missing_case()
    result = _plan(case, backward_choices=[])
    assert any(row["code"] == "unsupported-rule" for row in result["residuals"])
    assert not any(row.get("generatedFromUnsupportedRule") for row in result["backwardRequirements"])
    assert any(row["code"] == "missing-source-contract" for row in result["residuals"])
    assert result["endpoint"]["status"] != "conditional-profile-support"

    unknown = unknown_feature_case()
    unknown_result = _plan(unknown)
    assert any(row["code"] == "unknown-contract-feature" for row in unknown_result["residuals"])
    assert unknown_result["endpoint"]["status"] != "conditional-profile-support"


def test_desired_reading_and_original_record_are_bound_without_scope_rewriting():
    case = route_a_route_b()
    desired = deepcopy(case["desired"])
    desired["assumptions"] = [{"predicateId": "desired:original-assumption"}]
    first = _plan(case, desired=desired, reading_id="reading:paper-v1")
    second = _plan(case, desired=desired, reading_id="reading:paper-v2")
    assert first["desired"]["readingIdentity"]["readingId"] == "reading:paper-v1"
    assert second["desired"]["readingIdentity"]["readingId"] == "reading:paper-v2"
    assert first["desired"]["contractRecord"] == desired
    assert first["requestDigest"] != second["requestDigest"]
    assert first["analysisId"] != second["analysisId"]
    assert any(row["code"] in {"assumption-supply", "scope-transport-unresolved"}
               for row in first["residuals"])
    assert all(row.get("contractRecord", {}).get("assumptions") == desired["assumptions"]
               for row in first.get("backwardRequirements", []))


def test_unvisited_branches_are_accounted_under_shared_parent_bounds():
    case = route_a_route_b()
    result = _plan(case, bounds={"maxEvaluatedSteps": 1})
    assert result["status"] == "partial"
    pending = result["coverage"].get("pendingBranches") or result["coverage"]["unvisitedApplications"]
    assert pending
    assert all("reason" in row and ("stepRef" in row or "applicationRef" in row)
               for row in pending)
    assert result["mathematicalFalsity"] == "not-established"
    expired = _plan(case, bounds={"deadlineUtc": "2000-01-01T00:00:00Z"})
    assert expired["status"] == "partial"
    assert expired["coverage"].get("pendingBranches") or expired["coverage"].get("unvisitedApplications")
    assert expired["endpoint"]["status"] != "conditional-profile-support"


def _assert_budget_accounting(work, bound):
    assert work["totalSteps"] == work["forwardSteps"] + work["plannerSteps"]
    assert work["totalSteps"] <= bound.get("maxEvaluatedSteps", 8192)
    assert work["totalCombinations"] == work["forwardCombinations"] + work["plannerCombinations"]
    assert work["totalCombinations"] <= bound.get("maxTotalCombinations", 16384)


def _assert_shared_budget_partial(case, bound):
    raw = run_forward(case, bounds=bound)
    assert raw["status"] == "partial"
    assert raw["coverage"]["pending"] or raw["residuals"]
    result = _plan(case, bounds=bound)
    assert result["status"] == "partial"
    _assert_budget_accounting(result["coverage"]["workBudget"], bound)
    assert result["coverage"].get("pendingBranches") or result["coverage"].get("unvisitedApplications")
    assert result["mathematicalFalsity"] == "not-established"
    assert result["endpoint"]["status"] != "checked-support"
    assert result["analysisInputs"]["bounds"].get("deadlineUtc") == bound.get("deadlineUtc")


def test_all_parent_caps_and_one_deadline_preserve_prior_comparisons_and_pending_branches():
    cases = [
        (route_a_route_b(), {"maxDepth": 1}),
        (route_a_route_b(), {"maxEvaluatedSteps": 2}),
        (route_a_route_b(), {"maxGraphReferences": 1}),
        (multi_frontier_case(), {"maxFrontierContractsPerStatement": 1}),
        (multi_frontier_case(), {"maxCombinationsPerStep": 1}),
        (multi_frontier_case(), {"maxTotalCombinations": 1}),
        (route_a_route_b(), {"maxOutputBytes": 4096}),
        (route_a_route_b(), {"deadlineUtc": "2000-01-01T00:00:00Z"}),
    ]
    for case, bound in cases:
        _assert_shared_budget_partial(case, bound)


def test_mismatched_provider_scope_is_transport_residual_not_strengthened_assumption():
    case = provider_scope_mismatch_case()
    forward = run_forward(case)
    assert any(row["code"] == "incompatible-identity-interface" for row in forward["residuals"])
    result = _plan(case)
    assert result["desired"]["contractRecord"]["context"] == case["desired"]["context"]
    assert any(row["code"] in {"domain-representation-transport", "unsupported-identity-interface",
                               "incompatible-identity-interface"}
               for row in result["residuals"])
    assert result["authority"] == "conditional-profile"


def test_route_selection_rejects_foreign_wrong_kind_and_disconnected_steps():
    case = route_a_route_b()
    foreign = ref("derivation-step", "not-in-derivation")
    for selected in ([foreign], [ref("statement", "goal")],
                     [case["routeASteps"][0], case["routeASteps"][2]]):
        try:
            _plan(case, described_route_step_refs=selected)
        except (TypeError, ValueError):
            continue
        raise AssertionError("malformed described route must be rejected, not corrected")


def test_composition_choices_are_consumed_without_changing_desired_record():
    case = composition_case()
    before = deepcopy(case["desired"])
    choices = [{"stepRef": case["routeASteps"][0], "choices": {"lossSplits": [[1, 2]]}}]
    result = _plan(case, backward_choices=choices)
    assert result["desired"]["contractRecord"] == before
    requirements = result["routeComparisons"][0]["backwardRequirements"]
    assert [row["premiseOrdinal"] for row in requirements] == [0, 1]
    assert [row["contractRecord"]["features"]["regularity"]["offset"]
            for row in requirements] == [1, 2]

    bad_case = composition_case(wrong_middle=True)
    bad_choices = [{"stepRef": bad_case["routeASteps"][0],
                    "choices": {"lossSplits": [[1, 2]]}}]
    residual = _plan(bad_case, backward_choices=bad_choices)
    assert any(row["code"] in {"incompatible-compose-interface", "unsupported-rule"}
               for row in residual["residuals"])


def _assert_small_output_cap(case):
    try:
        bounded = _plan(case, bounds={"maxOutputBytes": 512})
    except ValueError as error:
        assert any(word in str(error) for word in ("bound", "maxOutputBytes", "metadata"))
        assert len(str(error)) <= 512
    else:
        assert bounded["status"] in {"partial", "truncated"}
        assert bounded["authority"] == "conditional-profile"
        assert bounded["mathematicalFalsity"] == "not-established"


def test_aggregate_input_and_output_caps_reuse_existing_preflight_and_partial_semantics():
    case = route_a_route_b()
    oversized = deepcopy(case["desired"])
    oversized["assumptions"] = [{"predicateId": "x" * (8 * 1024 * 1024)}]
    try:
        _plan(case, desired=oversized)
    except ValueError as exc:
        assert "aggregate input" in str(exc)
    else:
        raise AssertionError("oversized aggregate input must stop before copying/traversal")

    _assert_small_output_cap(case)


def test_cycle_control_preserves_existing_unsupported_cycle_semantics():
    from test_proof_contract_propagation import _cyclic_derivation

    case = route_a_route_b()
    case["graph"] = _cyclic_derivation()
    case["goalRef"] = ref("statement", "A")
    case["routeASteps"] = [ref("derivation-step", "step:cycle-a")]
    case["steps"] = [{"stepRef": case["routeASteps"][0]}]
    result = _plan(case, bindings=[], interfaces=[], scopes=[], artifacts=[],
                   backward_choices=[], route_priorities=[])
    assert result["status"] == "unsupported-cycle"
    assert result["mathematicalFalsity"] == "not-established"
    assert result["authority"] != "checked-support"
