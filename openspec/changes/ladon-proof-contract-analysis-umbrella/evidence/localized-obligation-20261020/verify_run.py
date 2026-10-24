"""Verify exact goal identities, raw receipts and the bounded source campaign."""
from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence

BASE = Path(__file__).resolve().parent
ROOT = next(p for p in BASE.parents if (p / "src/ladon").is_dir())
RUN = BASE / "run"
FOLLOW_UP = BASE / "follow-up-restored"


def load(path):
    return json.loads(path.read_text())


def digest(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()
    return "sha256:" + hashlib.sha256(data).hexdigest()


def save(name, value):
    (BASE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def verify_runtime():
    expected = {r["path"]: r["sha256"] for r in load(BASE / "RUNTIME.json")["files"]}
    changes = load(BASE / "RUNTIME-DELTA.json")["files"]
    assert {r["path"] for r in changes} == {
        "tests/test_proof_contract_probe_review_cli.py",
        "tests/test_proof_contract_constant_probe_native.py",
    }
    current = dict(expected)
    for row in changes:
        assert expected[row["path"]] == row["beforeSha256"]
        current[row["path"]] = row["afterSha256"]
    for name, sha in current.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name
    with tarfile.open(BASE / "runtime.tar.gz") as archive:
        archived = {m.name: hashlib.sha256(archive.extractfile(m).read()).hexdigest()
                    for m in archive.getmembers() if m.isfile()}
    assert archived == expected
    return len(expected)


def retain_raw(goal, source, receipts):
    compact = goal.get("result")
    if not isinstance(compact, dict) or "evidenceRef" not in compact:
        return
    raw = load_goal_evidence(source, compact)
    reference = compact["evidenceRef"]
    if goal["status"] == "checked-support":
        completion = raw["completion"]
        assert completion["status"] == "completed"
        assert completion["replay"]["status"] == "accepted"
        assert completion["trust"]["accepted"] is True
        assert "sorryAx" not in completion["trust"]["observedAxioms"]
    data = (source / reference["path"]).read_bytes()
    target = BASE / "raw-goal-evidence" / (reference["sha256"] + ".json")
    target.parent.mkdir(exist_ok=True)
    if target.exists():
        assert target.read_bytes() == data
    else:
        target.write_bytes(data)
    receipts[reference["sha256"]] = {**reference, "portablePath": str(target.relative_to(BASE))}


def verify_case(name, expected_checked, receipts):
    request = load(RUN / f"{name}-request.json")
    plan = load(RUN / f"{name}-plan.json")
    result = load(RUN / f"{name}-result.json")
    binding = result["binding"]
    assert result["planId"] == plan["planId"] and binding == plan["binding"]
    assert binding["selectedIdentity"] == request["selectedIdentity"]
    assert binding["analysisRef"]["artifactRef"] == request["analysisArtifact"]["artifactId"]
    assert binding["selectedDemandDigest"] == digest(binding["selectedDemand"])
    assert binding["outerDeadlineMonotonic"] == request["deadlineMonotonic"]
    assert binding["limits"] == load(BASE / "RUN-CONTRACT.json")["stageLimits"]
    assert result["routeComparisons"] == request["analysisArtifact"]["payload"]["result"]["routeComparisons"]
    rows = []
    for goal in result["goals"]:
        original = {k: v for k, v in goal.items()
                    if k not in {"term", "result", "supervision", "termOrigin", "goalDigest"}}
        original["status"] = "open"
        assert goal["routeBindingDigest"] == digest(binding)
        assert goal["goalDigest"] == digest(original)
        rows.append({**original, "goalDigest": goal["goalDigest"]})
        retain_raw(goal, Path(request["repoRoot"]), receipts)
    assert result["planId"] == digest({"profile": "route-context-bridge-v1", "binding": binding,
                                       "goals": rows, "residuals": result["residuals"]})
    assert sum(g["status"] == "checked-support" for g in result["goals"]) == expected_checked
    assert (Path(request["repoRoot"]) / "ThreeSteps.lean").read_bytes() == (
        ROOT / "tests/fixtures/proof_contract_planned_source/ThreeSteps.lean").read_bytes()
    return result


def main():
    runtime_count = verify_runtime()
    acceptance = load(FOLLOW_UP / "acceptance.json")
    assert acceptance["status"] == "PASS"
    assert acceptance["elapsedSeconds"] < acceptance["budgetSeconds"] == 1200
    receipts = {}
    positive = verify_case("positive", 13, receipts)
    middle = verify_case("middle", 1, receipts)
    assert positive["status"] == "checked-support" and positive["demandDischarged"] is True
    assert positive["goals"][-1]["termOrigin"] == "composition-of-checked-reading-and-transfer"
    assert middle["status"] == "unresolved-bridge" and middle["demandDischarged"] is False
    assert "result" not in middle["goals"][-1]
    source = Path(load(RUN / "positive-request.json")["repoRoot"])
    for name in ("missing-assumption", "excluded-parent", "closed-reading"):
        directory = RUN if name == "missing-assumption" else FOLLOW_UP
        result = load(directory / f"{name}-result.json")
        assert result["status"] == "unresolved-bridge" and not result["demandDischarged"]
        assert all(g["status"] != "checked-support" for g in result["goals"])
        for goal in result["goals"]:
            retain_raw(goal, source, receipts)
    for name in ("changed-reading", "wrong-provider", "forged-assumption", "forged-rule",
                 "changed-order", "changed-checkpoint"):
        result = load(FOLLOW_UP / f"{name}-result.json")
        assert result["status"] == "rejected" and not result["demandDischarged"]
    for name in ("expired", "expired-native"):
        result = load(FOLLOW_UP / f"{name}-result.json")
        assert result["status"] == "incomplete" and "preparation" not in result
    memory = load(FOLLOW_UP / "memory-stop-result.json")
    assert memory["memoryReportBackRequired"] and not memory["demandDischarged"]
    assert "Stop progress and report back to user" in memory["diagnostic"]["message"]
    failed = load(RUN / "excluded-parent-result.json")
    assert failed["status"] == "incomplete" and failed["diagnostic"]["code"] == "timeout"
    refused = load(BASE / "follow-up/excluded-parent-result.json")
    assert refused["status"] == "rejected" and "stale formal environment" in refused["diagnostic"]["message"]
    residue = load(BASE / "TIMEOUT-RESIDUE.json")
    assert residue["afterContext"] == residue["expectedContext"]
    clock = load(FOLLOW_UP / "INHERITED-CLOCK.json")
    assert clock["deadlineMonotonic"] == load(RUN / "positive-request.json")["deadlineMonotonic"]
    assert clock["limits"] == load(BASE / "RUN-CONTRACT.json")["stageLimits"]
    for path in [*RUN.glob("*-result.json"), *FOLLOW_UP.glob("*-result.json")]:
        result = load(path)
        assert path.stat().st_size <= 8 * 1024**2
        assert result["wholeMethodAuthority"] == "none"
        assert result["mathematicalFalsity"] == "not-established"
    save("RAW-EVIDENCE.json", {"files": list(receipts.values()), "entries": len(receipts)})
    verification = {"status": "PASS", "runtimeEntries": runtime_count,
                    "disclosedTestPathChanges": 2, "productionChanged": False,
                    "positiveGoalsChecked": 13, "middleGoalsChecked": 1,
                    "rawReceiptsVerified": len(receipts), "planAndGoalDigestsRecomputed": True,
                    "originalDriver": "incomplete-at-excluded-parent-timeout",
                    "followUp": "same original deadline and caps; both failed attempts retained",
                    "acceptance": acceptance, "sourcePairGate": "not-established",
                    "sourceFidelity": "attributed-unreviewed", "wholeMethodAuthority": "none",
                    "detectionBenefit": "unmeasured"}
    save("VERIFICATION.json", verification)
    print(json.dumps(verification, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
