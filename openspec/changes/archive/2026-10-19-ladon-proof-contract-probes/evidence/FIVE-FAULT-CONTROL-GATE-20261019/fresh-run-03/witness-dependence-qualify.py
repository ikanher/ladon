"""Root-only bounded source qualification for witness-dependence-v2."""
import hashlib
import json
import os
import shutil
import time
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.correspondence_check import prepare_correspondence
from ladon.proof_contract_bridge import _accepted_check
from ladon.proof_contract_bridge_supervision import run_bridge_job
from ladon.proof_contract_probe_artifacts import application_probe_artifact
from ladon.proof_contract_probes import check_application_probe, plan_application_probe
from ladon.proof_contract_source import produce_prose_contract
from ladon.proofir_correspondence import bind_native_interpretation, correspondence_artifacts
from ladon.proofir_v3 import validate_envelope_batch

base = Path(".codex/state/proof-contract-analysis/witness-feasibility")
prior = json.loads((base / "START.json").read_text())
p = Path(os.environ["LADON_GATE_OUTPUT"]).resolve()
p.mkdir(exist_ok=True)
repo = (p / "repo").resolve()
repo.mkdir()
shutil.copyfile("tests/fixtures/proof_contract_planned_source/lean-toolchain", repo / "lean-toolchain")
source = """import Lean
import Std
namespace WitnessProbe
def P (w x : Nat) : Prop := x ≤ w
theorem weak (_tag : Unit) : ∀ x : Nat, ∃ w : Nat, P w x := by
  intro x
  exact ⟨x, Nat.le_refl _⟩
theorem use : ∀ x : Nat, ∃ w : Nat, P w x := weak ()
end WitnessProbe
"""
(repo / "Bridge.lean").write_text(source)
started = time.monotonic()
deadline = float(os.environ["LADON_GATE_DEADLINE"])
limits = {"timeout_seconds": 30, "max_rss_bytes": 12 * 1024**3, "max_output_bytes": 8 * 1024**2}


def save(name, value):
    with (p / (name + ".json")).open("x") as stream:
        json.dump(value, stream, sort_keys=True, ensure_ascii=False, indent=2)


save("START", {**prior, "limits": limits, "scope": "constructed witness-dependence-v2 discrepancy and control only; attempt 2 continues original deadline"})
save("prior-attempt-01", {"status": "incomplete-source-extraction", "diagnostic": "The selected declaration used `:= weak` without an exact application head. Replaced the fixture with explicit `weak ()` while preserving the original clock and resource limits.", "extraction": json.loads((base / "extraction.json").read_text())})
save("prior-attempt-02", {"status": "harness-error-before-checker-attempt", "diagnostic": "Qualification script incorrectly expected left/right in generated native artifact payload and supplied analysisId in place of API planId. No proof checker calls occurred; source extraction and planning succeeded.", "extraction": json.loads((base / "attempt-02" / "extraction.json").read_text()), "plannedArtifacts": [json.loads(path.read_text()) for path in sorted((base / "attempt-02").glob("*-artifact.json"))]})
extraction = run_bridge_job("extract-provider", {
    "repoRoot": str(repo), "sourcePath": "Bridge.lean",
    "sourceDigest": "sha256:" + hashlib.sha256(source.encode()).hexdigest(),
    "declaration": "WitnessProbe.use", "application": "WitnessProbe.weak",
}, deadline_monotonic=deadline, limits=limits)
save("extraction", extraction)
assert extraction["status"] == "completed", extraction.get("diagnostic")
actual = extraction["result"]
assert actual["complete"] and not actual["localContext"] and not actual["nodes"][0]["premises"]
save("actual", actual)

symbols = {"P": {"leanName": "WitnessProbe.P", "leanType": "Nat → Nat → Prop"}}


def var(identity):
    return {"tag": "var", "id": identity}


def application(*args):
    return {"tag": "app", "symbol": "P", "args": list(args)}


def reading(index, order):
    witness_order = order == ("exists", "forall")
    rows = (("w", "exists"), ("x", "forall")) if witness_order else (("x", "forall"), ("w", "exists"))
    formula = application(var("w"), var("x"))
    for identity, quantifier in reversed(rows):
        formula = {"tag": quantifier,
            "binder": {"id": identity, "name": identity, "domain": "Nat"}, "body": formula}
    quote = ("There is a natural w such that P(w,x) for every natural x."
        if witness_order else "For every natural x there is a natural w such that P(w,x).")
    raw = (quote + "\n").encode()
    path = f"reading-{index}.txt"
    (repo / path).write_bytes(raw)
    interpretation = {"id": f"witness-reading-{index}",
        "source": {"path": path, "startLine": 1, "endLine": 1, "quote": quote,
                   "sha256": hashlib.sha256(raw).hexdigest()},
        "formula": formula, "symbols": symbols}
    permissions = [] if witness_order else ["x"]
    contract = {
        "profileId": "norm-scale-v1",
        "endpointId": "predicate:WitnessProbe.P",
        "context": {"objectId": "predicate:WitnessProbe.P", "domainId": "domain:Nat",
                    "scaleId": "scale:unmodeled", "representationId": "representation:original"},
        "telescope": [{"binderId": identity, "typeId": "Nat", "quantifier": q} for identity, q in rows],
        "assumptions": [], "conclusionId": "predicate:WitnessProbe.P",
        "features": {
            "regularity": {"state": "unknown", "scaleId": "scale:unmodeled",
                           "offset": None, "reason": "not modeled by witness profile"},
            "constantDependencies": {"state": "unknown", "allowedBinderIds": None,
                                     "reason": "not modeled by witness profile"},
            "witnessDependencies": [{"binderId": "w", "state": "known",
                                     "allowedBinderIds": permissions, "reason": None}],
        }}
    origins = {name: ["/formula"] for name in ("regularity", "constantDependencies", "witnessDependencies")}
    return produce_prose_contract(repo, interpretation, contract, origins,
        alternative_id=interpretation["id"], environment_ref=actual["environment"])


snapshots = [reading(0, ("exists", "forall")), reading(1, ("forall", "exists")),
             reading(2, ("forall", "exists"))]
batch, sides = [], []
for snapshot in snapshots:
    batch.extend(snapshot["artifacts"])
for snapshot in snapshots:
    owner = correspondence_artifacts(bind_native_interpretation(
        prepare_correspondence(snapshot["interpretation"], actual, {}),
        batch, source_root=repo))
    batch.append(owner)
    contract_artifact = next(a for a in snapshot["artifacts"] if a["artifactKind"] == "proofir.contract")
    sides.append({"contractRef": {"artifactRef": contract_artifact["artifactId"], "kind": "contract",
                                  "localId": contract_artifact["payload"]["contractId"]},
        "correspondenceRef": {"artifactRef": owner["artifactId"], "kind": "correspondence",
                              "localId": owner["payload"]["correspondenceId"]}})
save("snapshots", snapshots)
save("context", {"artifacts": batch})
save("actual-sides", sides)


def plan(label, left, right, kind, direction):
    request = {"repoRoot": str(repo), "context": {"artifacts": batch}, "left": left,
        "right": right, "template": {"familyId": "witness-dependence",
        "version": "witness-dependence-v2", "direction": direction, "kind": kind},
        "deadlineMonotonic": deadline, "limits": limits}
    planned = plan_application_probe(request)
    save(label + "-request", request)
    save(label + "-planned", planned)
    assert planned["status"] == "planned", (label, planned.get("diagnostic"))
    validate_envelope_batch([*batch, planned["artifact"]])
    return request, planned


def check(label, request, planned, terms):
    before = time.monotonic()
    checked = check_application_probe(request, planned["planId"], terms)
    save(label + "-checked", checked)
    accepted = 0
    for goal in checked["goals"]:
        compact = goal.get("result")
        if compact:
            raw = load_goal_evidence(repo, compact)
            valid = _accepted_check(raw)
            assert valid == (goal["status"] == "checked-support"), (label, goal["goalId"], goal["status"])
            accepted += valid
    assert accepted == 2, (label, checked.get("diagnostic"))
    assert checked["artifact"]["payload"]["checkRunRefs"] == []
    assert all(goal["status"] == "open" for goal in checked["artifact"]["payload"]["result"]["goals"])
    save(label + "-receipt", {"elapsedSeconds": time.monotonic() - before, "acceptedGoals": accepted,
        "goalStatuses": [g["status"] for g in checked["goals"]]})
    print(label, "accepted", time.monotonic() - started, flush=True)


discrepancy_request, discrepancy = plan("discrepancy", sides[0], sides[1], "counterexample", "right-to-left")
discrepancy_terms = {
    "formal-reading": "Iff.rfl",
    "probe": """by
  constructor
  · exact WitnessProbe.weak ()
  · intro h
    obtain ⟨w, hw⟩ := h
    have bad : Nat.succ w ≤ w := by
      simpa [WitnessProbe.P] using hw (Nat.succ w)
    exact Nat.not_succ_le_self w bad""",
}
save("discrepancy-terms", discrepancy_terms)
check("discrepancy", discrepancy_request, discrepancy, discrepancy_terms)

control_request, control = plan("control", sides[2], sides[1], "implication", "right-to-left")
control_terms = {"formal-reading": "Iff.rfl", "probe": "by intro h; exact h"}
save("control-terms", control_terms)
check("control", control_request, control, control_terms)

save("RESULT", {"status": "PASS", "elapsedSeconds": time.monotonic() - started,
    "budgetSeconds": 1800, "nativeSourceReadings": 3, "plannedCases": 2,
    "actualCheckerAttempts": 4, "acceptedGoals": 4,
    "scope": "constructed authored source-bound witness-dependence-v2 discrepancy/control; no natural-language fidelity or target-paper detection claim"})
