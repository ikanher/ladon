"""Actual-source acceptance controls for atomic backward requirements."""

import copy
import importlib
import shutil
from pathlib import Path
from time import monotonic

import pytest

from ladon.proof_contract_formal import produce_formal_snapshot, verify_formal_snapshot
from ladon.proof_contract_obligations import BackwardTransformRequest, transform_backward_sufficient
from ladon.proof_contract_rules import PROFILE, PROFILE_DIGEST
from ladon.proof_contract_source import snapshot_identity

FIXTURE = Path(__file__).parent / "fixtures/proof_contract_source_obligations"


@pytest.fixture(scope="module")
def api():
    return importlib.import_module("ladon.proof_contract_source_obligations")


@pytest.fixture(scope="module")
def observed(tmp_path_factory, api):
    root = tmp_path_factory.mktemp("source-bound-atoms")
    for name in ("SourceAtoms.lean", "lean-toolchain"):
        shutil.copyfile(FIXTURE / name, root / name)
    snapshots = {}
    for name in ("parent", "provider", "providerD"):
        snapshot = produce_formal_snapshot(
            root, "SourceAtoms.lean", "SourceAtoms", "SourceAtoms." + name,
            timeout_seconds=30,
        )
        assert snapshot["status"] == "extracted", snapshot["residuals"]
        snapshots[name] = snapshot
    return root, snapshots


def _backward(parent, provider, split):
    contract = provider["contract"]
    context = contract["context"]
    interface = {
        "endpointId": contract["endpointId"], "operatorId": context["objectId"],
        "objectId": context["objectId"], "domainId": context["domainId"],
        "representationId": context["representationId"],
        "inputTypeId": contract["telescope"][0]["typeId"],
        "outputTypeId": contract["telescope"][0]["typeId"],
        "inputScaleId": context["scaleId"], "outputScaleId": context["scaleId"],
        "inputNormId": "norm:observed", "outputNormId": "norm:observed",
        "conclusionId": contract["conclusionId"], "evidenceRefs": ["source:fixture"],
    }
    evidence = {
        "ruleId": "compose", "ruleRef": "application:constructed-control",
        "ruleDeclaration": PROFILE["rules"]["compose"], "profileDigest": PROFILE_DIGEST,
        "attributionStatus": "unverified", "evidenceRefs": ["source:fixture"],
    }
    return BackwardTransformRequest(
        desired_contract=parent["contract"], rule_evidence=evidence,
        premise_interfaces=[dict(interface, interfaceId=i) for i in ("left", "right")],
        output_interface=dict(interface, interfaceId="output"),
        parameters={"compositeOperatorId": parent["contract"]["context"]["objectId"]},
        choices={"lossSplits": [split]},
    )


def _request(observed, *, provider="provider", parent=None, split=None):
    root, snapshots = observed
    parent = snapshots["parent"] if parent is None else parent
    supplied = snapshots[provider]
    backward = _backward(parent, supplied, [1, 2] if split is None else split)
    return {
        "repoRoot": root, "parentSnapshot": parent, "providerSnapshot": supplied,
        "parentReadingId": "reading:parent", "providerReadingId": "reading:provider",
        "desiredReadingId": "reading:desired", "backwardRequest": backward,
        "backwardResult": transform_backward_sufficient(backward),
        "branchIndex": 0, "premiseOrdinal": 0, "deadlineMonotonic": monotonic() + 120,
        "limits": {"timeout_seconds": 30, "max_output_bytes": 8 * 1024**2,
                   "max_rss_bytes": 12 * 1024**3},
    }


def _complete(request, capture, term):
    from ladon.process_supervisor import run_bounded_target_process
    from ladon.proof_slice import pinned_toolchain
    from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal

    def bounded(command, **kwargs):
        remaining = request["deadlineMonotonic"] - monotonic()
        assert remaining > 0, "the shared acceptance deadline expired"
        kwargs["timeout_seconds"] = min(remaining, kwargs["timeout_seconds"])
        return run_bounded_target_process(command, **kwargs)

    return complete_source_goal(SourceGoalCompletionRequest(
        repo_root=request["repoRoot"], capture=capture, term=term,
        toolchain=pinned_toolchain(request["repoRoot"]), **request["limits"],
    ), runner=bounded)


def _assert_closed_generated_goal(result, request):
    capture = result["capture"]
    root = request["repoRoot"]
    path = capture["source"]["path"]
    assert path.startswith(".ladon/contract-obligations/") and path.endswith("/Probe.lean")
    generated = (root / path).read_text()
    original = (root / "SourceAtoms.lean").read_text()
    assert "theorem parent" not in generated
    assert original[:original.index("theorem parent")] in generated
    assert capture["goal"]["typeStructural"].startswith("ladon-expr-dag-v1:")
    assert all(row["implementationDetail"] for row in capture["goal"]["localContext"])
    assert "SourceAtoms" not in {
        row["module"] for row in capture["environment"]["compiledInventory"]["modules"]
    }


def test_actual_generated_goal_replays_provider_and_rejects_parent_and_self(api, observed):
    request = _request(observed)
    result = api.instantiate_source_bound_premise(request)
    assert result["status"] == "candidate-goal", result
    assert "trusted" not in result
    _assert_closed_generated_goal(result, request)
    capture = result["capture"]
    positive = _complete(request, capture, (
        "by intro s x; simpa [SourceAtoms.A, SourceAtoms.B, SourceAtoms.C] "
        "using SourceAtoms.provider s x"
    ))
    assert positive["status"] == "completed", positive["diagnostic"]
    assert positive["replay"]["status"] == "accepted"
    assert positive["trust"]["accepted"] is True
    parent = _complete(request, capture, "by exact SourceAtoms.parent")
    assert parent["status"] == "rejected"
    own = next((row["userName"] for row in capture["goal"]["localContext"]
                if row["implementationDetail"]), "ladonGeneratedRequirement")
    self_reference = _complete(request, capture, "by exact " + own)
    assert self_reference["status"] == "rejected"


def test_identical_coarse_profiles_do_not_transport_C_to_D(api, observed):
    snapshots = observed[1]
    assert snapshots["provider"]["contract"] == snapshots["providerD"]["contract"]
    result = api.instantiate_source_bound_premise(_request(observed, provider="providerD"))
    assert result["status"] == "incomplete", result
    assert result.get("capture") is None


def _replace_offset(expression):
    if isinstance(expression, list):
        return [_replace_offset(item) for item in expression]
    if not isinstance(expression, dict):
        return expression
    return {key: 4 if key == "nat" and value == 3 else _replace_offset(value)
            for key, value in expression.items()}


def _forged_parent(observed):
    from ladon.proof_contract_formal import _artifacts, _replay_summary

    parent = copy.deepcopy(observed[1]["parent"])
    for key in ("typeExpr", "normalizedTypeExpr"):
        parent["observation"][key] = _replace_offset(parent["observation"][key])
    parent = _replay_summary(parent, parent["observation"], "SourceAtoms.parent")
    parent["artifacts"] = _artifacts(parent, observed[0])
    parent["snapshotId"] = snapshot_identity(parent)
    return parent


def test_self_consistent_rehashed_forgery_is_rejected_by_fresh_observation(api, observed):
    forged = _forged_parent(observed)
    assert forged["contract"]["features"]["regularity"]["offset"] == 4
    assert verify_formal_snapshot(forged, observed[0]) == forged
    result = api.instantiate_source_bound_premise(
        _request(observed, parent=forged, split=[1, 3]),
    )
    assert result["status"] == "rejected", result
    assert result.get("capture") is None


@pytest.mark.parametrize("field", ["source", "helper"])
def test_stale_source_or_helper_snapshot_cannot_generate_a_goal(api, observed, field):
    parent = copy.deepcopy(observed[1]["parent"])
    parent[field]["sha256"] = "0" * 64
    parent["snapshotId"] = snapshot_identity(parent)
    result = api.instantiate_source_bound_premise(_request(observed, parent=parent))
    assert result["status"] == "rejected", result
    assert result.get("capture") is None


def test_expired_shared_deadline_stages_nothing(api, observed):
    root = observed[0] / ".ladon/contract-obligations"
    before = set(root.rglob("*")) if root.exists() else set()
    request = _request(observed)
    request["deadlineMonotonic"] = monotonic() - 1
    result = api.instantiate_source_bound_premise(request)
    after = set(root.rglob("*")) if root.exists() else set()
    assert result["status"] == "incomplete"
    assert after == before
