"""Route-local profile comparison helpers."""

from ladon.proof_contracts import _permission_sets, compare_contracts

from ._proof_contract_obligation_planner_validation import _refkey


def _unresolved_explanation(index):
    return {"comparisonIndex": index, "ordering": "route-dependency-order",
            "scope": "this-explored-route"}


def _earliest_unresolved(comparisons, steps):
    order = {_refkey(step): index for index, step in enumerate(steps)}
    candidates = [(order[_refkey(row["stepRef"])], index)
                  for index, row in enumerate(comparisons)
                  if row["status"] in {"candidate-contract-mismatch", "unresolved-bridge"}]
    return _unresolved_explanation(min(candidates)[1]) if candidates else None


def _route_endpoint(path, desired, goal_ref, frontier, comparisons):
    final_ref = path[-1][0]
    goal_rows = frontier.get((goal_ref["kind"], goal_ref["localId"]), [])
    direct = any(
        final_ref in row.get("routeWitnessRefs", [])
        and compare_contracts(row["contractRecord"], desired)["relation"]
        in {"dominates", "equivalent"}
        for row in goal_rows
    )
    support = direct
    return (
        {"status": "conditional-profile-support", "supportKind": "profile-dominance"}
        if support
        else {"status": "unresolved"}
    )


def _route_priority(root_key, priorities):
    return priorities.get(
        root_key,
        {
            "sourceLocation": None,
            "sourceId": "fallback:" + root_key[1],
            "line": None,
            "column": None,
            "heuristicPriority": 0,
        },
    )


def _local_requirement_comparisons(requirements, frontier, budget=None):
    comparisons, residuals = [], []
    for requirement in requirements:
        statement = requirement.get("statementRef")
        if not statement:
            continue
        witness_ref = requirement.get("parentWitnessRef")
        candidate_row = _candidate_row(statement, witness_ref, frontier)
        if candidate_row is None:
            continue
        candidate = candidate_row["contractRecord"]
        target = requirement["contractRecord"]
        if not _comparison_fits(candidate, target, budget):
            break
        comparison = compare_contracts(candidate, target)
        dimensions = _mismatch_dimensions(candidate, target, comparison["relation"])
        if candidate["assumptions"] != target["assumptions"]:
            residuals.append({"code": "assumption-supply", "statementRef": statement})
        if _has_unknown(candidate):
            residuals.append({"code": "unknown-contract-feature", "statementRef": statement})
        row = {
            "statementRef": statement,
            "stepRef": requirement["stepRef"],
            "witnessRef": requirement["witnessRef"],
            "parentWitnessRef": witness_ref,
            "branchRef": requirement["branchRef"],
            "contractRecord": candidate,
            "requiredContractRecord": target,
            "comparison": comparison,
            "mismatchDimensions": dimensions,
            "status": _comparison_status(comparison),
        }
        if budget is not None and not budget.reserve(row, copies=2, overhead=8):
            break
        comparisons.append(row)
    return comparisons, residuals


def _mismatch_dimensions(candidate, desired, relation=None):
    relation = relation or compare_contracts(candidate, desired)["relation"]
    if relation in {"dominates", "equivalent", "unknown"}:
        return []
    left, right = candidate["features"], desired["features"]
    dimensions = []
    regularity, target = left["regularity"], right["regularity"]
    if (
        regularity["state"] == target["state"] == "known"
        and regularity["offset"] > target["offset"]
    ):
        dimensions.append("regularity")
    dimensions.extend(_permission_mismatches(candidate, desired))
    return dimensions


def _permission_mismatches(candidate, desired):
    left, right = _permission_sets(candidate), _permission_sets(desired)
    dimensions = []
    if not left[0] <= right[0]:
        dimensions.append("constantDependencies")
    if any(not own <= required for own, required in zip(left[1:], right[1:])):
        dimensions.append("witnessDependencies")
    return dimensions


def _has_unknown(candidate):
    features = [
        candidate["features"]["regularity"],
        candidate["features"]["constantDependencies"],
        *candidate["features"]["witnessDependencies"],
    ]
    return any(feature.get("state") == "unknown" for feature in features)


def _comparison_status(comparison):
    relation = comparison["relation"]
    if relation in {"dominates", "equivalent"}:
        return "profile-related"
    return "unresolved-bridge" if relation == "unknown" else "candidate-contract-mismatch"


def _comparison_fits(candidate, target, budget):
    return budget is None or budget.admits([candidate, target])


def _candidate_row(statement, witness_ref, frontier):
    rows = frontier.get((statement["kind"], statement["localId"]), [])
    return next((row for row in rows if witness_ref in row.get("routeWitnessRefs", [])), None)


def _final_goal_comparison(path, desired, goal_ref, replay, budget):
    witness_ref, witness = path[-1]
    candidate = replay["records"].get(witness_ref)
    if candidate is None or not _comparison_fits(candidate, desired, budget):
        return []
    comparison = compare_contracts(candidate, desired)
    row = {
        "statementRef": goal_ref,
        "stepRef": witness["stepRef"],
        "witnessRef": witness_ref,
        "contractRecord": candidate,
        "requiredContractRecord": desired,
        "comparison": comparison,
        "mismatchDimensions": _mismatch_dimensions(candidate, desired, comparison["relation"]),
        "status": _comparison_status(comparison),
    }
    return [row] if budget.reserve(row, copies=2, overhead=8) else []
