"""Build isolated generated-goal contexts from only the original source prefix."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from ladon.proof_contract_formal import verify_formal_snapshot
from ladon.proof_slice import pinned_toolchain
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal


HERE = Path(__file__).parent
ORIGINAL_ROOT = HERE / "repo"
ALT_ROOT = HERE / "alternative" / "repo"
ALT_ROOT.mkdir(parents=True, exist_ok=True)
shutil.copyfile(ORIGINAL_ROOT / "lean-toolchain", ALT_ROOT / "lean-toolchain")

formal = json.loads((ORIGINAL_ROOT / "formal_snapshot.json").read_text())
verify_formal_snapshot(formal, ORIGINAL_ROOT)
source = (ORIGINAL_ROOT / "ObligationsRed.lean").read_bytes()
decl = formal["observation"]["declarationRange"]
lines = source.decode("utf-8").splitlines(keepends=True)
prefix_offset = len("".join(lines[:decl["startLine"] - 1]).encode("utf-8"))
prefix_offset += len(lines[decl["startLine"] - 1][:decl["startColumn"]].encode("utf-8"))
prefix = source[:prefix_offset]
assert prefix == source[:prefix_offset]
assert b"theorem threeStep" not in prefix
assert b"theorem firstBound" in prefix and b"theorem middleBound" in prefix
assert b"theorem lastBound" in prefix
assert formal["source"]["sha256"] == hashlib.sha256(source).hexdigest()
closed_prefix = prefix + b"\nend ObligationsRed\n\n"
(ALT_ROOT / "prefix.digest").write_text(hashlib.sha256(prefix).hexdigest() + "\n")

middle_statement = """theorem generatedMiddleGoal (s y : Nat) :
    ObligationsRed.N2 s (ObligationsRed.F2 y) ≤
      ObligationsRed.C * ObligationsRed.N1 (s + 0) y := by
  skip
"""
middle_text = closed_prefix.decode("utf-8") + middle_statement
(ALT_ROOT / "GeneratedMiddle.lean").write_text(middle_text)

sufficiency_text = closed_prefix.decode("utf-8") + """theorem bridgeIsSufficient (s x : Nat)
    (h : ObligationsRed.N2 s (ObligationsRed.F2 (ObligationsRed.F1 x)) ≤
      ObligationsRed.C * ObligationsRed.N1 (s + 0) (ObligationsRed.F1 x)) :
    ObligationsRed.N3 s (ObligationsRed.H x) ≤
      ObligationsRed.C * ObligationsRed.N0 (s + 0) x := by
  calc
    ObligationsRed.N3 s (ObligationsRed.H x) ≤
        ObligationsRed.C * ObligationsRed.N2 (s + 0)
          (ObligationsRed.F2 (ObligationsRed.F1 x)) := by
      simpa [ObligationsRed.H] using
        ObligationsRed.lastBound s (ObligationsRed.F2 (ObligationsRed.F1 x))
    _ = ObligationsRed.N2 s (ObligationsRed.F2 (ObligationsRed.F1 x)) := by
      simp [ObligationsRed.N2, ObligationsRed.C]
    _ ≤ ObligationsRed.C * ObligationsRed.N1 (s + 0) (ObligationsRed.F1 x) := h
    _ = ObligationsRed.N1 s (ObligationsRed.F1 x) := by
      simp [ObligationsRed.N1, ObligationsRed.C]
    _ ≤ ObligationsRed.C * ObligationsRed.N0 (s + 0) x :=
      ObligationsRed.firstBound s x
"""
(ALT_ROOT / "BridgeSufficiency.lean").write_text(sufficiency_text)

direct_statement = """theorem directEndpointGoal (s x : Nat) :
    ObligationsRed.N3 s (ObligationsRed.H x) ≤
      ObligationsRed.C * ObligationsRed.N0 (s + 0) x := by
  skip
"""
direct_text = closed_prefix.decode("utf-8") + direct_statement
(ALT_ROOT / "DirectEndpoint.lean").write_text(direct_text)

toolchain = pinned_toolchain(ALT_ROOT)


def capture(file: str, module: str, marker: str):
    contents = (ALT_ROOT / file).read_text()
    line = contents.splitlines().index("  skip") + 1
    return capture_source_goal(SourceGoalCaptureRequest(
        repo_root=ALT_ROOT,
        source_path=file,
        module=module,
        line=line,
        column=6,
        toolchain=toolchain,
        timeout_seconds=60,
        expected_source_digest="sha256:" + hashlib.sha256((ALT_ROOT / file).read_bytes()).hexdigest(),
    ))


middle_capture = capture("GeneratedMiddle.lean", "GeneratedMiddle", "middle")
assert middle_capture["status"] == "captured", middle_capture
middle_goal = middle_capture["capture"]
middle_locals = middle_goal["goal"]["localContext"]
middle_assumptions = [row for row in middle_locals if not row["implementationDetail"]]
assert [row["userName"] for row in middle_assumptions] == ["s", "y"], middle_locals
assert len(middle_locals) == 3 and middle_locals[0]["userName"] == "generatedMiddleGoal"
assert "threeStep" not in (ALT_ROOT / "GeneratedMiddle.lean").read_text()
valid_middle = complete_source_goal(SourceGoalCompletionRequest(
    repo_root=ALT_ROOT,
    capture=middle_goal,
    term="by simpa using ObligationsRed.middleBound s y",
    toolchain=toolchain,
    timeout_seconds=60,
))

wrong_middle = complete_source_goal(SourceGoalCompletionRequest(
    repo_root=ALT_ROOT,
    capture=middle_goal,
    term="by sorry",
    toolchain=toolchain,
    timeout_seconds=60,
))
assert valid_middle["status"] == "completed", valid_middle
assert valid_middle["replay"]["status"] == "accepted", valid_middle
assert valid_middle["trust"]["accepted"] is True, valid_middle
assert wrong_middle["status"] == "trust-rejected", wrong_middle
assert wrong_middle["replay"]["status"] == "accepted", wrong_middle
assert wrong_middle["trust"]["accepted"] is False, wrong_middle

direct_capture = capture("DirectEndpoint.lean", "DirectEndpoint", "direct")
assert direct_capture["status"] == "captured", direct_capture
direct_goal = direct_capture["capture"]
direct_locals = direct_goal["goal"]["localContext"]
direct_assumptions = [row for row in direct_locals if not row["implementationDetail"]]
assert [row["userName"] for row in direct_assumptions] == ["s", "x"], direct_locals
direct_result = complete_source_goal(SourceGoalCompletionRequest(
    repo_root=ALT_ROOT,
    capture=direct_goal,
    term="by simp [ObligationsRed.N0, ObligationsRed.N3, ObligationsRed.C, "
         "ObligationsRed.H, ObligationsRed.F1, ObligationsRed.F2, ObligationsRed.F3]",
    toolchain=toolchain,
    timeout_seconds=60,
))
assert direct_result["status"] == "completed", direct_result
assert direct_result["replay"]["status"] == "accepted", direct_result
assert direct_result["trust"]["accepted"] is True, direct_result

sufficiency_result = __import__("subprocess").run(
    [str(toolchain.lean_path), "--root=.", "BridgeSufficiency.lean"],
    cwd=ALT_ROOT, text=True, capture_output=True, timeout=60,
)
assert sufficiency_result.returncode == 0, sufficiency_result.stdout + sufficiency_result.stderr

sufficiency_path = ALT_ROOT / "BridgeSufficiency.lean"
sufficiency_module = "BridgeSufficiency"
assert sufficiency_path.name == sufficiency_module + ".lean"

result = {
    "schema": "scratch-obligation-alternative-feasibility-v1",
    "originalFormalSnapshotId": formal["snapshotId"],
    "originalProseSnapshotId": json.loads((ORIGINAL_ROOT / "prose_snapshot.json").read_text())["snapshotId"],
    "originalSource": formal["source"],
    "originalDeclarationRange": decl,
    "copiedPrefixSha256": hashlib.sha256(prefix).hexdigest(),
    "generatedSources": {
        name: {"sha256": hashlib.sha256((ALT_ROOT / name).read_bytes()).hexdigest(),
               "sourceFile": name}
        for name in ("GeneratedMiddle.lean", "BridgeSufficiency.lean", "DirectEndpoint.lean")
    },
    "generatedMiddleGoal": {
        "status": middle_capture["status"], "captureId": middle_goal["captureId"],
        "typeStructural": middle_goal["goal"]["typeStructural"],
        "typeDisplay": middle_goal["goal"]["typeDisplay"],
        "localContext": middle_locals,
        "validCompletion": valid_middle,
        "nearbyWrongCompletion": wrong_middle,
    },
    "directEndpointAlternative": {
        "status": direct_capture["status"], "captureId": direct_goal["captureId"],
        "typeStructural": direct_goal["goal"]["typeStructural"],
        "localContext": direct_locals, "completion": direct_result,
        "scope": "separate source-bound generated endpoint route; not imported into the middle-goal context",
    },
    "sufficiencyModule": {
        "module": "BridgeSufficiency", "status": "compiled",
        "stdout": sufficiency_result.stdout, "stderr": sufficiency_result.stderr,
    },
}
(HERE / "alternative" / "completion-evidence.json").write_text(
    json.dumps(result, indent=2) + "\n"
)
print(json.dumps({
    "originalFormalSnapshotId": result["originalFormalSnapshotId"],
    "originalProseSnapshotId": result["originalProseSnapshotId"],
    "prefixSha256": result["copiedPrefixSha256"],
    "middleCaptureStatus": middle_capture["status"],
    "middleLocals": [row["userName"] for row in middle_assumptions],
    "validMiddleStatus": valid_middle["status"],
    "validMiddleReplay": valid_middle["replay"]["status"],
    "validMiddleTrust": valid_middle["trust"]["accepted"],
    "wrongMiddleStatus": wrong_middle["status"],
    "directCaptureStatus": direct_capture["status"],
    "directLocals": [row["userName"] for row in direct_assumptions],
    "directCompletionStatus": direct_result["status"],
    "directCompletionReplay": direct_result["replay"]["status"],
    "directCompletionTrust": direct_result["trust"]["accepted"],
}, indent=2))
