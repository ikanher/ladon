"""Fresh, conservative comparison and identity propagation for Real bounds.

These operations compare the admitted predicate interpretation only.  They do
not certify the source theorem body or a prose norm bridge.
"""

import json
import math
import time
from copy import deepcopy

from ladon.proof_contract_source import snapshot_identity
from ladon.real_bound_native_check import check_real_bound_relation
from ladon.real_bound_native_production import replay_real_bound

SCHEMA = "ladon-real-bound-analysis-v1"
MAX_ANALYSIS_INPUT_BYTES = 32 * 1024**2
MAX_ANALYSIS_PRODUCTIONS = 128
MAX_ANALYSIS_SECONDS = 600


def compare_real_bounds(left, right, root, *, timeout_seconds=600):
    """Replay both inputs, then compare their complete typed predicate contexts.

    Context equality is a diagnostic only: the exact relation proposition still
    needs its own Lean check before this can become a resolved comparison.
    """
    return _comparison_run(left, right, root, timeout_seconds=timeout_seconds)[0]


def _comparison_run(left, right, root, *, timeout_seconds=600):
    _bound_inputs([left, right])
    deadline = _deadline(timeout_seconds)
    left_fresh = _fresh(left, root, _remaining(deadline))
    right_fresh = _fresh(right, root, _remaining(deadline))
    result = _compare_fresh(left_fresh, right_fresh)
    checked = _check_fresh_relation(result, left_fresh, right_fresh, root, _remaining(deadline))
    return checked, [left_fresh, right_fresh]


def propagate_real_bound_identity(productions, root, *, timeout_seconds=600):
    """Diagnose candidate identity edges, leaving them open without Lean proof.

    This intentionally does not accept a derivation graph or rule name list.
    Each edge names an explicit pair of source-owned Real productions. Fresh
    context replay is necessary but insufficient; every rule application stays
    unresolved until its exact relation proposition receives a Lean check.
    """
    if (not isinstance(productions, (list, tuple))
            or not 2 <= len(productions) <= MAX_ANALYSIS_PRODUCTIONS):
        raise ValueError("identity propagation requires 2 to 128 productions")
    _bound_inputs(productions)
    deadline = _deadline(timeout_seconds)
    fresh_left = _fresh(productions[0], root, _remaining(deadline))
    candidates = []
    contract_refs = [_contract_ref(fresh_left)]
    for production in productions[1:]:
        fresh_right = _fresh(production, root, _remaining(deadline))
        contract_refs.append(_contract_ref(fresh_right))
        edge = _compare_fresh(fresh_left, fresh_right)
        checked = _check_fresh_relation(edge, fresh_left, fresh_right, root,
                                        _remaining(deadline))
        accepted = checked["status"] == "resolved"
        candidates.append({
            "rule": "identity-v1" if accepted else None,
            "ruleCandidate": "identity-v1",
            "contextMatch": edge["contextMatch"],
            "status": "resolved" if accepted else "unresolved",
            "relation": checked.get("relation"),
            "ruleApplication": ({
                "inputContractRef": _contract_ref(fresh_left),
                "outputContractRef": _contract_ref(fresh_right),
                "goalDigest": checked["relationCheckEvidence"]["goalDigest"],
                "checkerIdentity": checked["relationCheckEvidence"]["checkerIdentity"],
            } if accepted else None),
            "relationCheckRun": checked.get("relationCheckRun"),
            "residual": None if accepted else {
                "code": checked.get("residuals", [{"code": "real-rule-application-not-checked"}])[0]["code"]
            },
            "comparisonDiagnostic": edge,
        })
        fresh_left = fresh_right
    complete = all(row["status"] == "resolved" for row in candidates)
    result = {
        "schema": SCHEMA,
        "stage": "propagation",
        "status": "resolved" if complete else "unresolved",
        "complete": complete,
        "contractRefs": contract_refs,
        "candidateEdges": candidates,
        "residuals": [] if complete else [row["residual"] for row in candidates
                                         if row["status"] != "resolved"],
        "authority": ("fresh-source-predicate-scalar-and-relation-checks" if complete
                      else "fresh-source-predicate-and-scalar-checks"),
        "sourceTheoremProof": "not-checked",
        "paperNormBridge": "unresolved",
        "mathematicalFalsity": "not-established",
        "limitations": ["only-definitional-identity-relations-are-currently-proved",
                        "source-theorem-proof-not-checked", "paper-norm-bridge-unresolved",
                        "not-persisted-as-a-native-analysis"],
    }
    result["analysisId"] = snapshot_identity(result)
    return result


def _compare_fresh(left_fresh, right_fresh):
    left_context = _context(left_fresh)
    right_context = _context(right_fresh)
    same = left_context == right_context
    result = {
        "schema": SCHEMA,
        "stage": "comparison",
        "status": "unresolved",
        "relation": None,
        "contextMatch": same,
        "contractRefs": [_contract_ref(left_fresh), _contract_ref(right_fresh)],
        "contextDigest": snapshot_identity(left_context) if same else None,
        "freshCheckEvidence": _fresh_check_evidence(left_fresh) + _fresh_check_evidence(right_fresh),
        "residuals": [{"code": "real-relation-proposition-not-checked"}
                      if same else {"code": "real-bound-context-mismatch"}],
        "authority": "fresh-source-predicate-and-scalar-checks",
        "sourceTheoremProof": "not-checked",
        "paperNormBridge": "unresolved",
        "mathematicalFalsity": "not-established",
        "limitations": ["relation-proposition-not-checked", "source-theorem-proof-not-checked",
                        "paper-norm-bridge-unresolved", "not-persisted-as-a-native-analysis"],
    }
    result["analysisId"] = snapshot_identity(result)
    return result


def _check_fresh_relation(result, left_fresh, right_fresh, root, timeout_seconds):
    if not result["contextMatch"]:
        return result
    left_plan = left_fresh["request"]["plan"]
    right_plan = right_fresh["request"]["plan"]
    run = check_real_bound_relation(root, left_plan, right_plan,
                                    timeout_seconds=timeout_seconds)
    receipt = run.get("processReceipt") if isinstance(run, dict) else None
    process_ok = (isinstance(receipt, dict) and receipt.get("returnCode") == 0
                  and not any(receipt.get(field, False) for field in
                              ("timedOut", "memoryLimited", "outputLimited")))
    checked = run.get("result") if run.get("status") == "completed" else None
    evidence = checked.get("check") if isinstance(checked, dict) else None
    goal = checked.get("goal") if isinstance(checked, dict) else None
    if (process_ok and isinstance(checked, dict) and checked.get("status") == "checked"
            and isinstance(evidence, dict) and isinstance(goal, dict)
            and checked.get("leftPlanId") == left_plan["planId"]
            and checked.get("rightPlanId") == right_plan["planId"]):
        result.update({
            "status": "resolved",
            "relation": "equivalent",
            "residuals": [],
            "authority": "fresh-source-predicate-scalar-and-relation-checks",
            "relationCheckEvidence": {
                "goalDigest": goal["sha256"],
                "checkerIdentity": checked["checkerIdentity"],
                "leftPlanId": checked["leftPlanId"],
                "rightPlanId": checked["rightPlanId"],
                "processReceipt": run.get("processReceipt"),
            },
            "relationCheckRun": run,
            "limitations": [limitation for limitation in result["limitations"]
                            if limitation != "relation-proposition-not-checked"],
        })
    else:
        residual = (checked.get("residual") if isinstance(checked, dict) else None)
        result["residuals"] = [{"code": residual or "real-relation-lean-check-unaccepted"}]
        result["relationCheckRun"] = run
    result["analysisId"] = snapshot_identity(result)
    return result


def _fresh(production, root, timeout_seconds):
    fresh = replay_real_bound(production, root, timeout_seconds=timeout_seconds)
    if fresh.get("status") != "admitted" or fresh.get("authority") != "fresh-lean-check":
        raise ValueError("Real comparison requires fresh admitted source checks")
    artifacts = fresh.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("fresh Real admission is missing its native contract owner")
    record = artifacts[-1].get("payload", {}).get("record")
    if not isinstance(record, dict):
        raise TypeError("fresh Real admission is missing its exact typed record")
    refs = _check_refs(fresh)
    if len(refs) != 2:
        raise ValueError("fresh Real admission is missing predicate or scalar check evidence")
    check = fresh.get("check", {})
    inner = check.get("result") or {}
    if check.get("status") != "completed" or inner.get("status") != "checked":
        raise ValueError("Real comparison requires completed fresh Lean checks")
    expected_goals = {row["id"] for row in fresh["request"]["plan"]["goals"]}
    observed_goals = {row.get("goal", {}).get("id") for row in inner.get("checks", [])}
    if observed_goals != expected_goals or len(inner.get("checks", [])) != len(expected_goals):
        raise ValueError("fresh Real replay does not cover every exact admission goal")
    return fresh


def _bound_inputs(productions):
    try:
        encoded = json.dumps(productions, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode()
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError("Real analysis inputs must be finite JSON-compatible values") from error
    if len(encoded) > MAX_ANALYSIS_INPUT_BYTES:
        raise ValueError("Real analysis inputs exceed the aggregate 32 MiB limit")


def _deadline(timeout_seconds):
    if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
            or not 0 < timeout_seconds <= MAX_ANALYSIS_SECONDS):
        raise ValueError("Real analysis deadline must be positive and at most 600 seconds")
    return time.monotonic() + timeout_seconds


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("shared Real analysis deadline expired")
    return remaining


def _context(production):
    contract = production["artifacts"][-1]
    payload = contract["payload"]
    record = payload["record"]
    owners = {(row["kind"], row["localId"]): row for row in contract["subjectRefs"]}

    def expr(ref):
        owner = owners.get((ref["kind"], ref["localId"]))
        if owner is None:
            raise ValueError("Real context expression is not owned by its exact contract")
        fingerprint = owner.get("fingerprint")
        if not isinstance(fingerprint, dict):
            raise TypeError("Real context expression is missing its typed fingerprint")
        return deepcopy(fingerprint)

    application = record["application"]
    binder_ids = [row["binderId"] for row in record["telescope"]]

    def binder_index(binder_id):
        try:
            return binder_ids.index(binder_id)
        except ValueError as error:
            raise ValueError("Real context binder is outside its exact telescope") from error

    return {
        "profileId": record["profileId"],
        "endpointId": record["endpointId"],
        "telescope": [
            {"quantifier": row["quantifier"], "binderInfo": row["binderInfo"],
             "type": expr(row["typeRef"])}
            for row in record["telescope"]
        ],
        "roles": {role: binder_index(binder) for role, binder in record["roles"].items()},
        "application": {
            "predicate": expr(application["predicateRef"]),
            "operator": expr(application["operatorRef"]),
            **{side: {key: expr(ref) for key, ref in application[side].items()}
               for side in ("input", "output")},
        },
        "constant": {
            "binder": binder_index(record["constant"]["binderId"]),
            "permittedBinders": [binder_index(item)
                                 for item in record["constant"]["permittedBinderIds"]],
        },
        "loss": record["loss"],
        "guards": {
            "constantNonnegative": expr(record["guards"]["constantNonnegativeRef"]),
            "boundNonnegative": binder_index(record["guards"]["boundNonnegativeBinderId"]),
        },
        "interpretation": deepcopy(record["interpretation"]),
    }


def _contract_ref(production):
    artifact = production["artifacts"][-1]
    payload = artifact["payload"]
    return {"artifactRef": artifact["artifactId"], "kind": "contract",
            "localId": payload["contractId"]}


def _check_refs(production):
    contract = production.get("artifacts", [])[-1]
    return deepcopy(contract.get("payload", {}).get("checkRunRefs", []))


def _fresh_check_evidence(production):
    check = production["check"]
    inner = check["result"]
    return [
        {"planId": production["request"]["plan"]["planId"],
         "contractRef": _contract_ref(production),
         "goalId": row["goal"]["id"],
         "checkerIdentity": inner["checkerIdentity"],
         "evidenceDigest": snapshot_identity({"checkerIdentity": inner["checkerIdentity"],
                                                "run": check, "check": row["evidence"]})}
        for row in inner["checks"]
    ]
