"""Reconcile five source-bound discrepancy/control pairs from real check runs.

This bounded gate revalidates stored native results and immutable checker
receipts. It does not launch new proof searches or replace historical attempts.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.proof_contract_bridge import _accepted_check

ROOT = Path(__file__).resolve().parents[5]
OUTPUT = Path(__file__).resolve().parent
STARTED = time.monotonic()
DEADLINE = STARTED + 1800
RUNS = ROOT / ".codex/state/proof-contract-analysis"
EVIDENCE = ROOT / "openspec/changes/ladon-proof-contract-probes/evidence"

CASES = [
    ("regularity-boundary", "fault", RUNS / "constant-probes/qualification-01/regularity-checked-result.json",
     RUNS / "constant-probes/qualification-01/regularity-repo", "checked-local-nonimplication"),
    ("regularity-boundary", "control", RUNS / "constant-probes/qualification-01/regularity-control-checked-result.json",
     RUNS / "constant-probes/qualification-01/regularity-repo", "checked-local-implication"),
    ("constant-uniformity", "fault", RUNS / "constant-probes/qualification-01/uniformity-checked-result.json",
     RUNS / "constant-probes/qualification-01/uniformity-repo", "checked-local-nonimplication"),
    ("constant-uniformity", "control", RUNS / "constant-probes/qualification-01/uniformity-control-checked-result.json",
     RUNS / "constant-probes/qualification-01/uniformity-repo", "checked-local-implication"),
    ("witness-dependence", "fault", RUNS / "witness-feasibility/attempt-07/discrepancy-checked.json",
     RUNS / "witness-feasibility/attempt-04/repo", "checked-local-nonimplication"),
    ("witness-dependence", "control", RUNS / "witness-feasibility/attempt-07/strong-to-weak-control-checked.json",
     RUNS / "witness-feasibility/attempt-04/repo", "checked-local-implication"),
    ("restricted-domain", "fault", RUNS / "restricted-domain/attempt-04/discrepancy-checked.json",
     RUNS / "restricted-domain/attempt-04/repo", "checked-local-nonimplication"),
    ("restricted-domain", "control", RUNS / "restricted-domain/attempt-04/control-checked.json",
     RUNS / "restricted-domain/attempt-04/repo", "checked-local-implication"),
    ("inequality-direction", "fault", EVIDENCE / "INEQUALITY-DIRECTION-20261019/source-attempt-05/discrepancy-checked.json",
     EVIDENCE / "INEQUALITY-DIRECTION-20261019/source-attempt-05/repo", "checked-local-nonimplication"),
    ("inequality-direction", "control", EVIDENCE / "INEQUALITY-DIRECTION-20261019/source-attempt-05/control-checked.json",
     EVIDENCE / "INEQUALITY-DIRECTION-20261019/source-attempt-05/repo", "checked-local-implication"),
]
UNSUPPORTED = [
    ("constant-uniformity", "constant-uniformity-v1",
     RUNS / "constant-probes/qualification-01/unsupported-constant-uniformity-result.json"),
    ("witness-dependence", "witness-dependence-v1",
     RUNS / "constant-probes/qualification-01/unsupported-witness-dependence-result.json"),
    ("restricted-domain", "restricted-domain-v1",
     RUNS / "constant-probes/qualification-01/unsupported-restricted-domain-result.json"),
    ("inequality-direction", "inequality-direction-v1",
     RUNS / "constant-probes/qualification-01/unsupported-inequality-direction-result.json"),
]


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def verify_case(family: str, role: str, result_path: Path, repo_path: Path, expected: str):
    if time.monotonic() >= DEADLINE:
        raise TimeoutError("five-fault/five-control gate exceeded 30 minutes")
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes)
    if result.get("status") != expected:
        raise AssertionError(f"{family}/{role}: {result.get('status')} != {expected}")
    goals = result.get("goals")
    if not isinstance(goals, list) or len(goals) != 2:
        raise AssertionError(f"{family}/{role}: expected exactly two generated goals")
    accepted = []
    for goal in goals:
        if goal.get("status") != "checked-support" or not isinstance(goal.get("term"), str):
            raise AssertionError(f"{family}/{role}/{goal.get('goalId')}: not a completed check")
        raw = load_goal_evidence(repo_path, goal["result"])
        if not _accepted_check(raw):
            raise AssertionError(f"{family}/{role}/{goal.get('goalId')}: checker receipt rejected")
        if raw["completion"].get("termDigest") != digest(goal["term"].encode()):
            raise AssertionError(f"{family}/{role}/{goal.get('goalId')}: term digest mismatch")
        accepted.append({
            "goalId": goal["goalId"],
            "goalDigest": goal["goalDigest"],
            "termDigest": digest(goal["term"].encode()),
            "evidenceRef": goal["result"]["evidenceRef"],
            "acceptedReplay": raw["completion"]["replay"]["status"],
            "acceptedTrust": raw["completion"]["trust"]["accepted"],
        })
    artifact = result.get("artifact", {})
    payload = artifact.get("payload", {})
    if payload.get("checkRunRefs") != []:
        raise AssertionError(f"{family}/{role}: planning artifact unexpectedly carries check authority")
    if any(goal.get("status") != "open" for goal in payload.get("result", {}).get("goals", [])):
        raise AssertionError(f"{family}/{role}: planned goals were not kept open")
    return {
        "family": family,
        "role": role,
        "status": expected,
        "resultPath": result_path.relative_to(ROOT).as_posix(),
        "resultSha256": digest(result_bytes),
        "checkerGoals": accepted,
    }


outcomes = [verify_case(*case) for case in CASES]
unsupported = []
for family, version, path in UNSUPPORTED:
    data = path.read_bytes()
    result = json.loads(data)
    artifact = result.get("artifact", {})
    template = artifact.get("payload", {}).get("template", {})
    if result.get("status") != "unsupported" or template.get("version") != version:
        raise AssertionError(f"{family}/{version}: saved unsupported attempt changed")
    unsupported.append({
        "family": family,
        "templateVersion": version,
        "status": result["status"],
        "resultPath": path.relative_to(ROOT).as_posix(),
        "resultSha256": digest(data),
        "residualCodes": [row.get("code") for row in result.get("residuals", [])
                            if isinstance(row, dict)],
    })
families = sorted({row[0] for row in CASES})
assert len(outcomes) == 10 and len(families) == 5
assert sum(row["role"] == "fault" for row in outcomes) == 5
assert sum(row["role"] == "control" for row in outcomes) == 5
assert all(len(row["checkerGoals"]) == 2 for row in outcomes)
elapsed = time.monotonic() - STARTED
assert elapsed < 1800

result = {
    "schema": "ladon-five-fault-five-control-gate-v1",
    "status": "PASS",
    "budgetSeconds": 1800,
    "elapsedSeconds": elapsed,
    "evidenceMode": "revalidated previously executed real checker results and content-addressed raw receipts; no fresh proof search launched",
    "sourceQualificationRuns": [
        {"families": ["regularity-boundary", "constant-uniformity"],
         "elapsedSeconds": 454.025,
         "report": "../CONSTANT-UNIFORMITY-20261019/REPORT.md"},
        {"families": ["witness-dependence"], "elapsedSeconds": 165.004,
         "report": "../WITNESS-DEPENDENCE-20261019/REPORT.md"},
        {"families": ["restricted-domain"], "elapsedSeconds": 168.594,
         "report": "../RESTRICTED-DOMAIN-20261019/REPORT.md"},
        {"families": ["inequality-direction"], "elapsedSeconds": 169.111,
         "report": "../INEQUALITY-DIRECTION-20261019/REPORT.md"},
    ],
    "aggregateSourceQualificationSeconds": 956.734,
    "familyCount": 5,
    "faultCount": 5,
    "controlCount": 5,
    "acceptedCheckerGoalCount": sum(len(row["checkerGoals"]) for row in outcomes),
    "attemptRetention": "The original result envelopes and all prior failed, unsupported, and incomplete attempts remain at their referenced source-attempt paths; this gate writes separate summaries and does not overwrite them.",
    "unsupportedScope": [
        "Four saved historical v1 results remain explicitly unsupported; their paths and hashes are retained below.",
        "Alternate AST shapes, domains, relation objects, binder orders, and metadata outside each family’s narrow v2 matcher remain explicitly unsupported.",
        "This gate does not expand any matcher or infer natural-language fidelity."
    ],
    "outcomes": outcomes,
    "unsupportedTemplates": unsupported,
}
(OUTPUT / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({key: result[key] for key in (
    "status", "elapsedSeconds", "familyCount", "faultCount", "controlCount",
    "acceptedCheckerGoalCount", "evidenceMode"
)}, sort_keys=True))
