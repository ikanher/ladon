from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.proof_contract_bridge import _accepted_check

bundle = Path(__file__).resolve().parents[1] / "INEQUALITY-DIRECTION-20261019"
attempt = bundle / "source-attempt-05"
repo = attempt / "repo"
checks = []
for name, code in (
    ("failed-elaboration", "typecheck-or-closure"),
    ("proof-search-failure", "typecheck-or-closure"),
):
    result = json.loads((attempt / f"{name}-checked.json").read_text(encoding="utf-8"))
    goal = next(item for item in result["goals"] if item["goalId"] == "probe")
    raw = load_goal_evidence(repo, goal["result"])
    completion = raw["completion"]
    application = completion["application"]
    assert result["status"] == "unresolved" and goal["status"] == "unresolved"
    assert raw["status"] == "unresolved" and application["status"] == "rejected"
    assert completion["diagnostic"]["code"] == code
    assert completion["trust"]["accepted"] is False and not _accepted_check(raw)
    assert result["checkerAuthority"] == "none"
    assert result["mathematicalFalsity"] == "not-established"
    ref = goal["result"]["evidenceRef"]
    checks.append({"case": name, "term": goal["term"], "status": result["status"],
                   "goalStatus": goal["status"], "applicationStatus": application["status"],
                   "diagnostic": completion["diagnostic"]["message"],
                   "trustAccepted": completion["trust"]["accepted"],
                   "rawSha256": "sha256:" + hashlib.sha256(
                       json.dumps(raw, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                   "storedEvidenceRef": ref})

expired = json.loads((attempt / "expired-planning.json").read_text(encoding="utf-8"))
assert expired["status"] == "incomplete"
assert expired["diagnostic"]["code"] == "timeout"
assert expired["checkerAuthority"] == "none"
assert expired["mathematicalFalsity"] == "not-established"
checks.append({"case": "expired-deadline", "status": expired["status"],
               "diagnostic": expired["diagnostic"]["code"],
               "checkerAuthority": expired["checkerAuthority"],
               "mathematicalFalsity": expired["mathematicalFalsity"]})

report = {"status": "PASS", "cases": checks,
          "scope": "Read-only verification of current-checkout raw checker receipts; timeout stop is incomplete and no failure is treated as semantic evidence."}
(Path(__file__).resolve().parent / "CURRENT-RUN-VERIFICATION.json").write_text(
    json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True), flush=True)
