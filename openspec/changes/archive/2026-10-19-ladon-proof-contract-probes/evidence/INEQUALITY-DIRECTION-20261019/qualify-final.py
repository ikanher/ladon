import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.correspondence_check import prepare_correspondence
from ladon.proof_contract_artifacts import source_contract_artifact
from ladon.proof_contract_bridge import _accepted_check
from ladon.proof_contract_bridge_supervision import run_bridge_job
from ladon.proof_contract_probes import check_application_probe, plan_application_probe
from ladon.proofir_correspondence import (
    bind_native_interpretation,
    correspondence_artifacts,
    interpretation_artifacts,
)
from ladon.proofir_v3 import validate_envelope_batch

base = Path(__file__).resolve().parent
output_name = sys.argv[1] if len(sys.argv) > 1 else "source-attempt-replay"
attempt = (base / output_name).resolve()
if attempt.parent != base:
    raise ValueError("qualification output must be a new child directory of this evidence bundle")
attempt.mkdir(exist_ok=False)
repo = (attempt / "repo").resolve()
repo.mkdir()
shutil.copyfile(Path.cwd() / ".codex/state/proof-contract-analysis/restricted-domain/lean-toolchain",
                repo / "lean-toolchain")
source = '''import Lean
import Std
namespace InequalityProbe
theorem nonnegative (_tag : Unit) : ∀ x : Nat, 0 ≤ x := by
  intro x
  exact Nat.zero_le x
theorem use : ∀ x : Nat, 0 ≤ x := nonnegative ()
end InequalityProbe
'''
(repo / "Bridge.lean").write_text(source, encoding="utf-8")
started = time.monotonic()
deadline = started + 1800
limits = {"timeout_seconds": 30, "max_rss_bytes": 12 * 1024**3,
          "max_output_bytes": 8 * 1024**2}
extraction = run_bridge_job(
    "extract-provider",
    {"repoRoot": str(repo), "sourcePath": "Bridge.lean",
     "sourceDigest": "sha256:" + hashlib.sha256(source.encode()).hexdigest(),
     "declaration": "InequalityProbe.use", "application": "InequalityProbe.nonnegative"},
    deadline_monotonic=deadline, limits=limits)
(attempt / "extraction.json").write_text(json.dumps(extraction, sort_keys=True, indent=2))
assert extraction["status"] == "completed", extraction.get("diagnostic")
actual = extraction["result"]
assert actual["complete"] and actual["localContext"] == []
assert not actual["nodes"][0]["premises"]
(attempt / "actual.json").write_text(json.dumps(actual, sort_keys=True, indent=2))

def record(index, reversed_order):
    quote = ("For every natural x, x is at most zero." if reversed_order
             else "For every natural x, zero is at most x.")
    raw = (quote + "\n").encode()
    filename = f"reading-{index}.txt"
    (repo / filename).write_bytes(raw)
    binder = {"id": "x", "name": "x", "domain": "Nat"}
    lhs = {"tag": "var", "id": "x"} if reversed_order else {"tag": "const", "name": "0"}
    rhs = {"tag": "const", "name": "0"} if reversed_order else {"tag": "var", "id": "x"}
    record = {
        "id": f"reading-{index}",
        "source": {"path": filename, "startLine": 1, "endLine": 1, "quote": quote,
                   "sha256": hashlib.sha256(raw).hexdigest()},
        "formula": {"tag": "forall", "binder": binder,
                    "body": {"tag": "le", "left": lhs, "right": rhs}},
        "symbols": {},
    }
    source_map, interpretation = interpretation_artifacts(
        record, actual["environment"], source_root=repo)
    contract = {
        "profileId": "norm-scale-v1", "endpointId": "relation:Nat.le",
        "context": {"objectId": "object:nat-order", "domainId": "domain:Nat",
                    "scaleId": "scale:none", "representationId": "representation:original"},
        "telescope": [{"binderId": "x", "typeId": "Nat", "quantifier": "forall"}],
        "assumptions": [], "conclusionId": "relation:Nat.le",
        "features": {
            "regularity": {"state": "unknown", "scaleId": "scale:none", "offset": None,
                           "reason": "not modeled by inequality-direction profile"},
            "constantDependencies": {"state": "unknown", "allowedBinderIds": None,
                                     "reason": "not modeled by inequality-direction profile"},
            "witnessDependencies": [],
        },
    }
    owner = source_contract_artifact(
        contract, contract_id=f"contract:reading-{index}",
        environment_ref=actual["environment"],
        source_map_refs=[{"artifactRef": source_map["artifactId"], "kind": "source-map",
                          "localId": source_map["payload"]["sourceMapId"]}],
        residuals=[{"code": "profile-feature-omitted",
                    "message": "Other mathematical features are outside this profile.",
                    "feature": "inequality-direction-v2"}],
    )
    correspondence = correspondence_artifacts(bind_native_interpretation(
        prepare_correspondence(record, actual, {}), [source_map, interpretation], source_root=repo))
    return [source_map, interpretation, owner, correspondence], {
        "contractRef": {"artifactRef": owner["artifactId"], "kind": "contract",
                        "localId": owner["payload"]["contractId"]},
        "correspondenceRef": {"artifactRef": correspondence["artifactId"],
                              "kind": "correspondence",
                              "localId": correspondence["payload"]["correspondenceId"]},
    }

left_rows, left = record(0, True)
right_rows, right = record(1, False)
context = {"artifacts": left_rows + right_rows}
validate_envelope_batch(context["artifacts"])
discrepancy = {
    "formal-reading": "Iff.rfl",
    "probe": "by\n  constructor\n  · intro x\n    exact Nat.zero_le x\n  · intro h\n    exact Nat.not_succ_le_zero 0 (h 1)",
}
control = {"formal-reading": "Iff.rfl",
           "probe": "by\n  intro h x\n  exact Nat.zero_le x"}
cases = [
    ("discrepancy", "right-to-left", "counterexample", discrepancy),
    ("control", "left-to-right", "implication", control),
]
summary = []
for label, direction, kind, terms in cases:
    request = {
        "repoRoot": str(repo), "context": context, "left": left, "right": right,
        "template": {"familyId": "inequality-direction", "version": "inequality-direction-v2",
                     "direction": direction, "kind": kind},
        "deadlineMonotonic": deadline, "limits": limits,
    }
    planned = plan_application_probe(request)
    (attempt / f"{label}-planned.json").write_text(json.dumps(planned, sort_keys=True, indent=2))
    assert planned["status"] == "planned", planned
    validate_envelope_batch([*context["artifacts"], planned["artifact"]])
    checked = check_application_probe(request, planned["planId"], terms)
    (attempt / f"{label}-checked.json").write_text(json.dumps(checked, sort_keys=True, indent=2))
    accepted = []
    for goal in checked["goals"]:
        compact = goal.get("result")
        assert compact, (label, goal)
        raw = load_goal_evidence(repo, compact)
        assert _accepted_check(raw), (label, goal["goalId"], goal["status"])
        accepted.append(goal["goalId"])
    assert len(accepted) == 2, (label, checked)
    assert checked["artifact"]["payload"]["checkRunRefs"] == []
    assert all(g["status"] == "open" for g in checked["artifact"]["payload"]["result"]["goals"])
    summary.append({"case": label, "acceptedGoals": accepted, "status": checked["status"],
                    "elapsedSeconds": time.monotonic() - started})
    print(label, checked["status"], accepted, flush=True)

result = {"status": "PASS", "elapsedSeconds": time.monotonic() - started,
          "budgetSeconds": 1800, "limits": limits, "summary": summary,
          "scope": "constructed source-bound Nat zero-bound discrepancy and valid left-to-right control; no prose fidelity or paper error claim"}
(attempt / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2))
print(json.dumps(result, sort_keys=True), flush=True)

if len(sys.argv) > 2 and sys.argv[2] == "negative-checks":
    negative_request = {
        "repoRoot": str(repo), "context": context, "left": left, "right": right,
        "template": {"familyId": "inequality-direction", "version": "inequality-direction-v2",
                     "direction": "right-to-left", "kind": "counterexample"},
        "deadlineMonotonic": deadline, "limits": limits,
    }
    negative_plan = plan_application_probe(negative_request)
    assert negative_plan["status"] == "planned", negative_plan.get("diagnostic")
    negative_cases = []
    for label, term in (("failed-elaboration", "by exact 17"),
                        ("proof-search-failure", "by trivial")):
        failed = check_application_probe(
            negative_request, negative_plan["planId"], {"probe": term})
        (attempt / f"{label}-checked.json").write_text(
            json.dumps(failed, sort_keys=True, indent=2))
        assert failed["status"] == "unresolved", (label, failed.get("diagnostic"))
        assert failed["checkerAuthority"] == "none"
        assert failed["mathematicalFalsity"] == "not-established"
        probe_goal = next(goal for goal in failed["goals"] if goal["goalId"] == "probe")
        assert probe_goal["status"] == "unresolved"
        raw = load_goal_evidence(repo, probe_goal["result"])
        assert not _accepted_check(raw), label
        negative_cases.append({"case": label, "status": failed["status"],
                               "probeStatus": probe_goal["status"],
                               "checkerStatus": raw.get("status"),
                               "term": term})
    expired = plan_application_probe({**negative_request, "deadlineMonotonic": 0})
    (attempt / "expired-planning.json").write_text(
        json.dumps(expired, sort_keys=True, indent=2))
    assert expired["status"] == "incomplete"
    assert expired["diagnostic"]["code"] == "timeout"
    assert expired["checkerAuthority"] == "none"
    assert expired["mathematicalFalsity"] == "not-established"
    negative_cases.append({"case": "expired-deadline", "status": expired["status"],
                           "diagnostic": expired["diagnostic"]["code"]})
    negatives = {"status": "PASS", "cases": negative_cases,
                 "elapsedSeconds": time.monotonic() - started,
                 "scope": "failed proof terms remain unresolved; timeout is incomplete, never a semantic counterexample"}
    (attempt / "NEGATIVE-CASES.json").write_text(
        json.dumps(negatives, sort_keys=True, indent=2))
    print(json.dumps(negatives, sort_keys=True), flush=True)
