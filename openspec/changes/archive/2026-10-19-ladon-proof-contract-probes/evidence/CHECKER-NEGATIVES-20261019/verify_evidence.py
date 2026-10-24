from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.proof_contract_bridge import _accepted_check

root = Path(__file__).resolve().parent
source = (Path(__file__).resolve().parents[1]
          / "REGULARITY-APPLICATION-20261019")
original = json.loads((source / "failed-elaboration.json").read_text(encoding="utf-8"))
assert original["status"] == "unresolved"
assert original["diagnostic"]["code"] == "unresolved-proof"
formal = next(goal for goal in original["goals"] if goal["goalId"] == "formal-reading")
probe = next(goal for goal in original["goals"] if goal["goalId"] == "probe")
assert formal["status"] == "checked-support"
assert probe["status"] == "unresolved" and probe["term"] == "by trivial"
request = json.loads((source / "request.json").read_text(encoding="utf-8"))
raw = load_goal_evidence(request["repoRoot"], probe["result"])
assert raw["status"] == "unresolved"
assert raw["completion"]["status"] == "rejected"
assert not _accepted_check(raw)
raw_bytes = json.dumps(raw, sort_keys=True, ensure_ascii=False, indent=2).encode() + b"\n"
(root / "failed-proof-search.raw.json").write_bytes(raw_bytes)

timeout = json.loads((source / "expired.json").read_text(encoding="utf-8"))
assert timeout["status"] == "incomplete"
assert timeout["diagnostic"]["code"] == "timeout"
assert timeout["checkerAuthority"] == "none"
assert timeout["mathematicalFalsity"] == "not-established"
(root / "expired-deadline.json").write_text(
    json.dumps(timeout, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

verification = {
    "status": "PASS",
    "sourceEvidence": "../REGULARITY-APPLICATION-20261019",
    "failedProofSearch": {
        "submittedTerm": probe["term"],
        "applicationProbeStatus": original["status"],
        "formalReadingStatus": formal["status"],
        "probeGoalStatus": probe["status"],
        "rawCheckerStatus": raw["status"],
        "rawCompletionStatus": raw["completion"]["status"],
        "accepted": _accepted_check(raw),
        "rawSha256": "sha256:" + hashlib.sha256(raw_bytes).hexdigest(),
    },
    "expiredDeadline": {
        "status": timeout["status"],
        "diagnostic": timeout["diagnostic"]["code"],
        "checkerAuthority": timeout["checkerAuthority"],
        "mathematicalFalsity": timeout["mathematicalFalsity"],
    },
    "scope": "Receipt verification only; no Lean work or source mutation performed.",
}
(root / "VERIFICATION.json").write_text(
    json.dumps(verification, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(verification, sort_keys=True), flush=True)
