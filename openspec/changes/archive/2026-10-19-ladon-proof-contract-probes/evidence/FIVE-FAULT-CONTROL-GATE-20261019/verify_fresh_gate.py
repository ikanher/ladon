"""Validate fresh five-fault/five-control outputs and raw receipts."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.proof_contract_bridge import _accepted_check

ROOT = Path(__file__).resolve().parents[5]
GATE = Path(__file__).resolve().parent
RUN = GATE / "fresh-run-03"
START_RESULT = json.loads((GATE / "fresh-run-01/RESULT.json").read_text(encoding="utf-8"))
DEADLINE = float(START_RESULT["deadlineMonotonic"])
START = DEADLINE - 1800


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


CASES = [
    ("regularity-boundary", "fault", RUN / "constant-uniformity/regularity-checked-request.json",
     RUN / "constant-uniformity/regularity-checked-result.json", "checked-local-nonimplication"),
    ("regularity-boundary", "control", RUN / "constant-uniformity/regularity-control-checked-request.json",
     RUN / "constant-uniformity/regularity-control-checked-result.json", "checked-local-implication"),
    ("constant-uniformity", "fault", RUN / "constant-uniformity/uniformity-checked-request.json",
     RUN / "constant-uniformity/uniformity-checked-result.json", "checked-local-nonimplication"),
    ("constant-uniformity", "control", RUN / "constant-uniformity/uniformity-control-checked-request.json",
     RUN / "constant-uniformity/uniformity-control-checked-result.json", "checked-local-implication"),
    ("witness-dependence", "fault", RUN / "witness-dependence/discrepancy-request.json",
     RUN / "witness-dependence/discrepancy-checked.json", "checked-local-nonimplication"),
    ("witness-dependence", "control", RUN / "witness-dependence/strong-to-weak-control-02/request.json",
     RUN / "witness-dependence/strong-to-weak-control-02/checked.json", "checked-local-implication"),
    ("restricted-domain", "fault", RUN / "restricted-wrapper/restricted-domain/discrepancy-request.json",
     RUN / "restricted-wrapper/restricted-domain/discrepancy-checked.json", "checked-local-nonimplication"),
    ("restricted-domain", "control", RUN / "restricted-wrapper/restricted-domain/control-request.json",
     RUN / "restricted-wrapper/restricted-domain/control-checked.json", "checked-local-implication"),
    ("inequality-direction", "fault", RUN / "inequality-wrapper/inequality-direction/discrepancy-request.json",
     RUN / "inequality-wrapper/inequality-direction/discrepancy-checked.json", "checked-local-nonimplication"),
    ("inequality-direction", "control", RUN / "inequality-wrapper/inequality-direction/control-request.json",
     RUN / "inequality-wrapper/inequality-direction/control-checked.json", "checked-local-implication"),
]

outcomes = []
for family, role, request_path, checked_path, expected_status in CASES:
    request_bytes, checked_bytes = request_path.read_bytes(), checked_path.read_bytes()
    request, checked = json.loads(request_bytes), json.loads(checked_bytes)
    if request.get("deadlineMonotonic") != DEADLINE:
        raise AssertionError(f"{family}/{role}: not bound to the shared absolute deadline")
    if Path(request["repoRoot"]).resolve().is_relative_to(RUN.resolve()) is False:
        raise AssertionError(f"{family}/{role}: repoRoot is not a fresh campaign path")
    if "reuse-result" in request or "cachedResult" in request:
        raise AssertionError(f"{family}/{role}: checked request unexpectedly uses prior-result reuse")
    if checked.get("status") != expected_status:
        raise AssertionError(f"{family}/{role}: {checked.get('status')} != {expected_status}")
    goals = checked.get("goals")
    if not isinstance(goals, list) or len(goals) != 2:
        raise AssertionError(f"{family}/{role}: expected exactly two generated goals")
    accepted = []
    for goal in goals:
        if goal.get("status") != "checked-support" or not isinstance(goal.get("term"), str):
            raise AssertionError(f"{family}/{role}/{goal.get('goalId')}: incomplete checker goal")
        raw = load_goal_evidence(request["repoRoot"], goal["result"])
        if not _accepted_check(raw):
            raise AssertionError(f"{family}/{role}/{goal.get('goalId')}: raw receipt rejected")
        term_digest = "sha256:" + sha(goal["term"].encode())
        if raw.get("completion", {}).get("termDigest") != term_digest:
            raise AssertionError(f"{family}/{role}/{goal.get('goalId')}: term digest mismatch")
        evidence_path = Path(request["repoRoot"]) / goal["result"]["evidenceRef"]["path"]
        if not evidence_path.resolve().is_relative_to(Path(request["repoRoot"]).resolve()):
            raise AssertionError(f"{family}/{role}: receipt escaped the fresh repository")
        accepted.append({"goalId": goal["goalId"], "goalDigest": goal["goalDigest"],
                         "termDigest": term_digest, "evidenceRef": goal["result"]["evidenceRef"],
                         "receiptSha256": sha(evidence_path.read_bytes()),
                         "replay": raw["completion"]["replay"]["status"],
                         "trustAccepted": raw["completion"]["trust"]["accepted"]})
    payload = checked.get("artifact", {}).get("payload", {})
    if payload.get("checkRunRefs") != [] or any(
            goal.get("status") != "open" for goal in payload.get("result", {}).get("goals", [])):
        raise AssertionError(f"{family}/{role}: checked authority was added to the open plan")
    outcomes.append({"family": family, "role": role, "status": expected_status,
                     "requestPath": request_path.relative_to(RUN).as_posix(),
                     "requestSha256": sha(request_bytes),
                     "checkedPath": checked_path.relative_to(RUN).as_posix(),
                     "checkedSha256": sha(checked_bytes), "acceptedGoals": accepted})

unsupported = []
for family, version in [
    ("constant-uniformity", "constant-uniformity-v1"),
    ("witness-dependence", "witness-dependence-v1"),
    ("restricted-domain", "restricted-domain-v1"),
    ("inequality-direction", "inequality-direction-v1"),
]:
    path = RUN / "constant-uniformity" / f"unsupported-{family}-result.json"
    envelope = json.loads(path.read_text(encoding="utf-8"))
    template = envelope.get("artifact", {}).get("payload", {}).get("template", {})
    if envelope.get("status") != "unsupported" or template.get("version") != version:
        raise AssertionError(f"unsupported historical template changed: {family}/{version}")
    unsupported.append({"family": family, "version": version, "status": "unsupported",
                        "path": path.relative_to(RUN).as_posix(), "sha256": sha(path.read_bytes())})

assert len(outcomes) == 10
assert sum(row["role"] == "fault" for row in outcomes) == 5
assert sum(row["role"] == "control" for row in outcomes) == 5
assert sum(len(row["acceptedGoals"]) for row in outcomes) == 20
elapsed = time.monotonic() - START

result = {
    "schema": "ladon-five-fault-five-control-shared-deadline-v1",
    "status": "PASS",
    "budgetSeconds": 1800,
    "elapsedSeconds": elapsed,
    "firstAttemptElapsedSeconds": 1134.667,
    "deadlineMonotonic": DEADLINE,
    "familyCount": 5,
    "faultCount": 5,
    "controlCount": 5,
    "acceptedCheckerGoalCount": 20,
    "freshRepoPerSourceContext": True,
    "cacheReuse": "no previous result envelope or checker receipt supplied; every fresh request uses a new per-family repository root",
    "runnerScripts": [
        {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path.read_bytes())}
        for path in [GATE / "run_fresh_gate.py", GATE / "run_fresh_gate_02.py",
                     GATE / "resume_inequality.py", GATE / "run_witness_transport_control.py",
                     Path(__file__)]
    ],
    "sourceQualifiers": [
        {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path.read_bytes())}
        for path in [
            ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/CONSTANT-UNIFORMITY-20261019/qualify.py",
            ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/WITNESS-DEPENDENCE-20261019/qualify.py",
            ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/RESTRICTED-DOMAIN-20261019/source-attempt-04/qualify.py",
            ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/INEQUALITY-DIRECTION-20261019/qualify-final.py",
        ]
    ],
    "outcomes": outcomes,
    "unsupportedTemplates": unsupported,
    "retainedHarnessFailures": [
        {"path": "fresh-run-01/failure.json", "classification": "source-context mismatch before any checker call"},
        {"path": "fresh-run-02/failure.json", "classification": "wrapper looked for the result at the wrong directory after the restricted checker returned zero"},
        {"path": "fresh-run-03/failure.json", "classification": "same result-path assumption; all child outputs are preserved and independently read above"},
    ],
    "runtimeIdentityDrift": json.loads((RUN / "constant-uniformity/BASELINE-DRIFT.json").read_text()),
    "verificationBoundary": "Constructed source-bound implications/counterexamples only; no natural-language fidelity, whole-method, or Navier-Stokes paper-detection claim.",
}
result_path = RUN / "FRESH-RESULT.json"
if "--write" in sys.argv:
    if elapsed > 1800:
        raise AssertionError("the shared 30-minute campaign deadline was exceeded")
    result_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
else:
    saved = json.loads(result_path.read_text(encoding="utf-8"))
    for key in ("status", "budgetSeconds", "deadlineMonotonic", "familyCount", "faultCount",
                "controlCount", "acceptedCheckerGoalCount", "freshRepoPerSourceContext",
                "cacheReuse", "outcomes", "unsupportedTemplates", "runtimeIdentityDrift",
                "runnerScripts", "sourceQualifiers"):
        if saved.get(key) != result.get(key):
            raise AssertionError(f"saved fresh result differs from current evidence for {key}")
    if not isinstance(saved.get("elapsedSeconds"), (int, float)) or saved["elapsedSeconds"] > 1800:
        raise AssertionError("saved gate elapsed time is missing or exceeds 1800 seconds")
    result = saved
print(json.dumps({"status": result["status"], "elapsedSeconds": result["elapsedSeconds"],
                  "families": result["familyCount"], "faults": result["faultCount"],
                  "controls": result["controlCount"], "acceptedReceipts": result["acceptedCheckerGoalCount"],
                  "unsupported": len(unsupported)}, sort_keys=True))
