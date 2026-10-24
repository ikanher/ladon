"""Validation of rational branch check receipts and their native runs."""

from __future__ import annotations

from ladon._proof_contract_rational_common import (
    _DIGEST,
    _digest,
    _require_digest,
    _text_digest,
    _validate_checker,
    _validate_spans,
)
from ladon.proof_contract_payloads import closed

_ALLOWED_AXIOMS = {"Classical.choice", "Quot.sound", "propext"}


def _validate_checked_receipt(receipt, payload, environment_ref):
    keys = {
        "schema",
        "planId",
        "branchId",
        "originalFindingId",
        "branchKind",
        "sourceSpanIdentities",
        "baseGoalSha256",
        "derivedGoalSha256",
        "assignment",
        "goalDigests",
        "checkerIdentity",
        "proofCheckerIdentity",
        "workspaceIdentity",
        "compiledInventoryDigest",
        "compiledInventoryDigestsByGoal",
        "termDigests",
        "checkRunRefs",
        "checkerAuthority",
        "sourceFormulaFidelity",
        "originalClaimRefuted",
        "cacheTrust",
    }
    closed(receipt, keys, "rational branch checked receipt")
    _validate_receipt_authority(receipt, payload, environment_ref)
    _validate_proof_checker(receipt["proofCheckerIdentity"])
    for key in ("baseGoalSha256", "derivedGoalSha256", "compiledInventoryDigest"):
        _require_digest(receipt[key], key)
    _validate_spans(receipt["sourceSpanIdentities"])
    _validate_checker(receipt["checkerIdentity"])
    _require_digest(receipt["planId"], "plan identity")
    _require_digest(receipt["compiledInventoryDigest"], "compiled inventory identity")
    _validate_receipt_collections(receipt, payload)
    goal_ids = list(receipt["termDigests"])
    _validate_receipt_goal_digests(receipt, goal_ids)
    _validate_receipt_replay_identities(receipt, goal_ids)


def _validate_receipt_authority(receipt, payload, environment_ref):
    if (
        receipt["schema"] != "ladon-rational-branch-check-receipt-v1"
        or receipt["branchId"] != payload["branchId"]
        or receipt["workspaceIdentity"] != environment_ref
        or receipt["checkerAuthority"] != "exact-generated-goals-only"
        or receipt["sourceFormulaFidelity"] != "unverified"
        or receipt["originalClaimRefuted"] is not False
    ):
        raise ValueError("rational branch checked receipt authority or identity is invalid")


def _validate_receipt_collections(receipt, payload):
    if (
        type(receipt["assignment"]) is not dict
        or type(receipt["goalDigests"]) is not list
        or not receipt["goalDigests"]
        or type(receipt["termDigests"]) is not dict
        or type(receipt["compiledInventoryDigestsByGoal"]) is not dict
        or receipt["checkRunRefs"] != payload["checkRunRefs"]
    ):
        raise ValueError("rational branch receipt collections are malformed")


def _validate_receipt_goal_digests(receipt, goal_ids):
    if (
        len(goal_ids) != len(receipt["goalDigests"])
        or not all(type(value) is str and value for value in goal_ids)
        or len(goal_ids) != len(set(goal_ids))
        or not all(
            type(value) is str and _DIGEST.fullmatch(value) for value in receipt["goalDigests"]
        )
    ):
        raise ValueError("rational branch goal digests are malformed")


def _validate_receipt_replay_identities(receipt, goal_ids):
    if (
        set(receipt["termDigests"]) != set(goal_ids)
        or set(receipt["compiledInventoryDigestsByGoal"]) != set(goal_ids)
        or any(not _DIGEST.fullmatch(value) for value in receipt["termDigests"].values())
        or any(
            value != receipt["compiledInventoryDigest"]
            for value in receipt["compiledInventoryDigestsByGoal"].values()
        )
    ):
        raise ValueError("rational branch per-goal replay identities are inconsistent")


def _validate_check_run(artifacts, plan_artifact, plan, receipt, ref):
    run = _load_check_run(artifacts, ref)
    inputs = run["payload"].get("inputs", {})
    _validate_check_run_inputs(inputs, plan_artifact, plan)
    extension = _accepted_extension(run)
    completion, capture, binding = _check_run_evidence(extension)
    goal_id, goal = _checked_goal(plan, binding)
    _validate_goal_binding(binding, plan, goal, goal_id)
    term_digest = binding.get("termDigest")
    _validate_replay_evidence(receipt, completion, capture, goal_id, term_digest)
    checker_identity = binding.get("proofCheckerIdentity")
    _validate_check_run_checker(run, extension, checker_identity)
    _validate_check_run_subject(inputs, plan, goal_id, term_digest)
    _validate_check_run_completion(run, completion)
    return goal_id, checker_identity


def _load_check_run(artifacts, ref):
    run = artifacts.get(ref["artifactRef"])
    if (
        not isinstance(run, dict)
        or run.get("artifactKind") != "proofir.check-run"
        or run.get("payload", {}).get("checkRunId") != ref["localId"]
    ):
        raise ValueError("rational branch check-run reference is not the exact run")
    return run


def _validate_check_run_inputs(inputs, plan_artifact, plan):
    if (
        plan_artifact["artifactId"] not in inputs.get("artifactRefs", [])
        or inputs.get("environmentRef") != plan["workspaceIdentity"]
    ):
        raise ValueError("rational branch check-run does not depend on the exact plan environment")


def _accepted_extension(run):
    extension = run.get("extensions", {}).get("ladon.rational-branch-receipt/v1")
    if not isinstance(extension, dict) or extension.get("status") != "accepted":
        raise ValueError("rational branch check-run lacks its accepted rational binding")
    return extension


def _check_run_evidence(extension):
    completion = extension.get("completion")
    capture = extension.get("capture")
    if not isinstance(completion, dict) or not isinstance(capture, dict):
        raise TypeError("rational branch check-run replay receipt is malformed")
    binding = extension.get("rationalBranchBinding")
    if not isinstance(binding, dict):
        raise TypeError("rational branch check-run binding is missing")
    return completion, capture, binding


def _checked_goal(plan, binding):
    goal_id = binding.get("goalId")
    try:
        goal_index = plan["generatedGoalIdentities"].index(goal_id)
        goal = plan["goals"][goal_index]
    except ValueError as error:
        raise ValueError("rational branch check-run names a missing generated goal") from error
    return goal_id, goal


def _validate_goal_binding(binding, plan, goal, goal_id):
    expected = {
        "planId": plan["planId"],
        "branchId": plan["branchId"],
        "branchKind": plan["branchKind"],
        "sourceSpanIdentities": plan["sourceSpanIdentities"],
        "baseGoalSha256": plan["baseGoalSha256"],
        "derivedGoalSha256": plan["derivedGoalSha256"],
        "assignment": plan["assignment"],
        "goalDigest": _text_digest(goal["leanProposition"]),
        "generatedProposition": goal["leanProposition"],
        "checkerIdentity": plan["checkerIdentity"],
        "workspaceIdentity": plan["workspaceIdentity"],
    }
    for key, expected_value in expected.items():
        if binding.get(key) != expected_value:
            raise ValueError("rational branch check-run binding differs from its regenerated goal")


def _validate_replay_evidence(receipt, completion, capture, goal_id, term_digest):
    if (
        term_digest != receipt["termDigests"].get(goal_id)
        or completion.get("termDigest") != term_digest
        or capture.get("compiledInventoryDigest")
        != receipt["compiledInventoryDigestsByGoal"].get(goal_id)
    ):
        raise ValueError("rational branch check-run replay evidence differs from its receipt")


def _validate_check_run_checker(run, extension, checker_identity):
    _validate_proof_checker(checker_identity)
    checker = run["payload"].get("checker", {})
    if (
        run["payload"].get("operation") != "rational-branch-generated-goal-completion-and-replay"
        or checker.get("name") != checker_identity["name"]
        or checker.get("version") != checker_identity["version"]
        or checker.get("implementationDigest") != checker_identity["helperDigest"]
        or checker.get("executableDigest") != extension.get("leanExecutableDigest")
    ):
        raise ValueError("rational branch check-run checker identity is inconsistent")


def _validate_check_run_subject(inputs, plan, goal_id, term_digest):
    token = _digest({"planId": plan["planId"], "goalId": goal_id, "termDigest": term_digest})[7:]
    expected_subject = {"kind": "statement", "localId": "rational-goal:" + token}
    if expected_subject not in inputs.get("subjectRefs", []):
        raise ValueError("rational branch check-run subject does not match its checked goal")


def _validate_check_run_completion(run, completion):
    if (
        completion.get("status") != "completed"
        or completion.get("replayStatus") != "accepted"
        or completion.get("trustCoverage") != "complete"
        or completion.get("trustPolicy") != "lean-standard-no-placeholders-v1"
        or completion.get("trustAccepted") is not True
        or not isinstance(completion.get("observedAxioms"), list)
        or any(axiom not in _ALLOWED_AXIOMS for axiom in completion.get("observedAxioms", []))
        or run["payload"].get("results", [{}])[0].get("result") != "accepted"
    ):
        raise ValueError("rational branch check-run lacks completed replay and trusted acceptance")


def _validate_proof_checker(identity):
    closed(
        identity,
        {"name", "version", "helperDigest", "completionPolicy"},
        "rational branch proof checker identity",
    )
    if (
        identity["name"] != "ladon-rational-branch-source-completion"
        or identity["version"] != "1"
        or identity["completionPolicy"] != "independent-replay-no-placeholders-v1"
    ):
        raise ValueError("unsupported rational branch proof checker")
    _require_digest(identity["helperDigest"], "proof checker helper")
