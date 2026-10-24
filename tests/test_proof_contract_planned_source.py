"""Source-paired RED controls: planner requirements must retain original authority."""

import copy
import importlib
import shutil
from pathlib import Path
from time import monotonic

import pytest
from support.proof_contract_planned_source import build_plan_request
from test_proof_contract_source_obligations import _complete

from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.proof_contract_obligation_planner import plan_contract_obligations

FIXTURE = Path(__file__).parent / "fixtures/proof_contract_planned_source"
IDENTITY_KEYS = (
    "stepRef",
    "witnessRef",
    "branchRef",
    "branchIndex",
    "premiseOrdinal",
    "forwardContractRef",
    "statementRef",
    "parentWitnessRef",
    "interfaceId",
)


@pytest.fixture(scope="module")
def observed_plan(tmp_path_factory):
    root = tmp_path_factory.mktemp("planned-source")
    for name in ("ThreeSteps.lean", "lean-toolchain"):
        shutil.copyfile(FIXTURE / name, root / name)
    snapshots = {}
    for name in ("firstBound", "secondBound", "thirdBound", "alternateBound", "endpoint"):
        snap = produce_formal_snapshot(
            root, "ThreeSteps.lean", "ThreeSteps", "ThreeSteps." + name, timeout_seconds=30
        )
        assert snap["status"] == "extracted", snap
        snapshots[name] = snap
    return root, snapshots


def request_for(observed, statement="second", provider="secondBound"):
    root, snapshots = observed
    plan = build_plan_request(snapshots)
    result = plan_contract_obligations(plan)
    route_index = next(
        i
        for i, r in enumerate(result["routeComparisons"])
        if r["describedRoute"] == (statement != "alternate")
    )
    route = result["routeComparisons"][route_index]
    requirement_index = next(
        i
        for i, r in enumerate(route["backwardRequirements"])
        if r["statementRef"]["localId"] == statement
    )
    row = route["backwardRequirements"][requirement_index]
    identity = {"routeId": route["routeId"]} | {k: copy.deepcopy(row[k]) for k in IDENTITY_KEYS}
    return {
        "repoRoot": root,
        "parentSnapshot": snapshots["endpoint"],
        "providerSnapshot": snapshots[provider],
        "parentReadingId": plan.desired_reading_identity["readingId"],
        "providerReadingId": "reading:provider:" + provider,
        "planRequest": plan,
        "planResult": result,
        "routeIndex": route_index,
        "requirementIndex": requirement_index,
        "selectedIdentity": identity,
        "deadlineMonotonic": monotonic() + 120,
        "limits": {
            "timeout_seconds": 30,
            "max_output_bytes": 8 * 1024**2,
            "max_rss_bytes": 12 * 1024**3,
        },
    }


@pytest.fixture
def api():
    module = importlib.import_module("ladon.proof_contract_source_obligations")
    operation = getattr(module, "instantiate_planned_source_leaf_requirement", None)
    assert callable(operation), "missing source-paired planned requirement constructor"
    return operation


def test_pair_has_three_steps_and_differing_middle_requirement(observed_plan):
    request = request_for(observed_plan)
    result = request["planResult"]
    route = result["routeComparisons"][request["routeIndex"]]
    selected = route["backwardRequirements"][request["requirementIndex"]]
    assert len(route["stepRefs"]) == 3
    assert selected["contractRecord"] != request["parentSnapshot"]["contract"]
    assert selected["contractRecord"]["features"]["regularity"]["offset"] == 0
    assert request["providerSnapshot"]["contract"]["features"]["regularity"]["offset"] == 2
    assert route["endpoint"]["status"] == "unresolved"
    assert route["earliestUnresolved"] is not None
    assert any(
        r["endpoint"]["status"] == "conditional-profile-support"
        for r in result["routeComparisons"]
        if not r["describedRoute"]
    )


def test_exact_intermediate_goal_rejects_wrong_provider_retains_alternative(api, observed_plan):
    request = request_for(observed_plan)
    result = api(request)
    assert result["status"] == "candidate-goal", result
    assert result["selectedRequirement"]["contractRecord"] != request["parentSnapshot"]["contract"]
    assert result["wholeMethodAuthority"] == "none"
    assert result["mathematicalFalsity"] == "not-established"
    failed = _complete(request, result["capture"], "by exact ThreeSteps.secondBound")
    assert failed["status"] == "rejected", failed
    alternate = request_for(observed_plan, "alternate", "alternateBound")
    good = api(alternate)
    assert good["status"] == "candidate-goal", good
    completed = _complete(alternate, good["capture"], "by exact ThreeSteps.alternateBound")
    assert completed["status"] == "completed", completed
    assert completed["replay"]["status"] == "accepted"
    assert completed["trust"]["accepted"] is True


@pytest.mark.parametrize("key", IDENTITY_KEYS + ("routeId",))
def test_altered_occurrence_stages_no_goal(api, observed_plan, key):
    request = request_for(observed_plan)
    request["selectedIdentity"][key] = "forged-identity"
    result = api(request)
    assert result["status"] == "rejected", result
    assert result.get("capture") is None


@pytest.mark.parametrize("mutation", ["result", "parent-reading", "provider", "parent", "extra"])
def test_plan_source_mismatch_stages_no_goal(api, observed_plan, mutation):
    request = request_for(observed_plan)
    if mutation == "result":
        request["planResult"]["analysisId"] = "sha256:" + "0" * 64
    elif mutation == "parent-reading":
        request["parentReadingId"] = "reading:another"
    elif mutation == "provider":
        request["providerSnapshot"] = observed_plan[1]["firstBound"]
    elif mutation == "parent":
        request["parentSnapshot"] = observed_plan[1]["thirdBound"]
    else:
        request["allowParentMismatch"] = True
    result = api(request)
    assert result["status"] == "rejected", result
    assert result.get("capture") is None


def test_route_internal_requirement_is_not_source_leaf(api, observed_plan):
    request = request_for(observed_plan, "inner")
    result = api(request)
    assert result["status"] == "rejected", result
    assert result.get("capture") is None


def test_expired_source_budget_stages_nothing(api, observed_plan):
    request = request_for(observed_plan)
    directory = request["repoRoot"] / ".ladon/contract-obligations"
    before = set(directory.rglob("*")) if directory.exists() else set()
    request["deadlineMonotonic"] = monotonic() - 1
    result = api(request)
    assert result["status"] == "incomplete", result
    assert result.get("capture") is None
    assert (set(directory.rglob("*")) if directory.exists() else set()) == before
