#!/usr/bin/env python3
"""Read-only audit of the Ladon proof-reading-guides r47 receipts."""
import hashlib
import json
import subprocess
from pathlib import Path

REPO = Path("/home/codex/projects/ladon")
CACHE = Path("/home/codex/.cache/ladon-qualification-r47")
CANDIDATE = CACHE / "ladon-guides-r47b-9nrffih0"
PREDECESSOR = CACHE / "ladon-guides-r47-10957q49"
EVIDENCE = REPO / "openspec/changes/ladon-proof-reading-guides/evidence/guide-r47"
GUIDE = REPO / "openspec/changes/ladon-proof-reading-guides/full-acceptance-r47.json"
CLAIMS = REPO / "openspec/changes/ladon-result-claim-correspondence/full-acceptance-r47.json"
DOSSIER = REPO / "openspec/changes/ladon-result-formalization-dossier/full-acceptance-r47.json"
UMBRELLA = REPO / "openspec/changes/ladon-result-understanding-and-release-umbrella/integration-requalification-r47.json"
QUAL = CANDIDATE / "full-qualification"


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def tracked(root: Path, *paths: str) -> set[str]:
    return set(subprocess.check_output(["git", "-C", str(root), "ls-files", *paths], text=True).splitlines())


def walk_refs(value, at="$", out=None):
    out = [] if out is None else out
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("digest"), str):
            out.append((at, value["path"], value["digest"]))
        for key, child in value.items():
            walk_refs(child, f"{at}.{key}", out)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_refs(child, f"{at}[{index}]", out)
    return out


guide = json.loads(GUIDE.read_text())
claims = json.loads(CLAIMS.read_text())
dossier = json.loads(DOSSIER.read_text())
umbrella = json.loads(UMBRELLA.read_text())
receipts = [GUIDE, CLAIMS, DOSSIER, UMBRELLA]
checks = []

# Evidence inventory and every path/digest reference named by the acceptance receipts.
inventory = json.loads((EVIDENCE / "inventory.json").read_text())["files"]
inventory_bad = []
for relative, expected in inventory.items():
    path = EVIDENCE / relative
    if not path.is_file() or digest(path) != expected:
        inventory_bad.append(relative)
checks.append({"check": "inventory", "files": len(inventory), "mismatches": inventory_bad})
refs = []
for receipt in receipts:
    for location, path_text, expected in walk_refs(json.loads(receipt.read_text())):
        path = Path(path_text)
        refs.append((str(receipt), location, path_text, path.is_file() and digest(path) == expected))
checks.append({"check": "receipt_path_digests", "references": len(refs), "mismatches": [x[:3] for x in refs if not x[3]]})

# Candidate, prerequisite receipts and their evidence contracts agree on one immutable tuple.
tuple_keys = ("candidateCommit", "candidateIdentity", "sourceTreeIdentity", "wheelDigest")
tuple_match = all(all(receipt.get(k) == guide.get(k) for k in tuple_keys) for receipt in (claims, dossier))
for item in (claims.get("qualification", {}),):
    path = Path(item.get("path", ""))
    tuple_match &= path.is_file() and digest(path) == item.get("digest")
for item in guide["prerequisites"].values():
    path = Path(item["path"])
    tuple_match &= path.is_file() and digest(path) == item["digest"]
contract_hashes = []
for relative, expected in guide["evidenceContractIdentities"].items():
    path = REPO / relative
    contract_hashes.append((relative, path.is_file() and digest(path) == expected))
checks.append({"check": "candidate_and_contract_identities", "tuple_match": bool(tuple_match), "contract_mismatches": [p for p, ok in contract_hashes if not ok], "omissions": guide["omissions"]})

# The candidate metadata correction changed no source, tests, scripts, docs, or installed wheel.
new_files, old_files = tracked(CANDIDATE / "candidate"), tracked(PREDECESSOR / "candidate")
tracked_diffs = []
for relative in sorted(new_files | old_files):
    new_path, old_path = CANDIDATE / "candidate" / relative, PREDECESSOR / "candidate" / relative
    if relative not in new_files or relative not in old_files or digest(new_path) != digest(old_path):
        tracked_diffs.append(relative)
code_files_new = tracked(CANDIDATE / "candidate", "src", "tests", "scripts", "docs")
code_files_old = tracked(PREDECESSOR / "candidate", "src", "tests", "scripts", "docs")
code_diffs = []
for relative in sorted(code_files_new | code_files_old):
    a, b = CANDIDATE / "candidate" / relative, PREDECESSOR / "candidate" / relative
    if relative not in code_files_new or relative not in code_files_old or digest(a) != digest(b):
        code_diffs.append(relative)
wheel = json.loads((EVIDENCE / "default-wheel-match.json").read_text())
wheel_bad = []
for relative, expected in wheel["files"].items():
    path = Path(wheel["sitePackages"]) / relative
    if not path.is_file() or digest(path) != expected:
        wheel_bad.append(relative)
checks.append({"check": "candidate_equivalence", "tracked_new": len(new_files), "tracked_predecessor": len(old_files), "tracked_diffs": tracked_diffs, "code_files": len(code_files_new), "code_diffs": code_diffs, "default_wheel_files": wheel["fileCount"], "wheel_mismatches": wheel_bad})

# Baseline identity and field/dossier read-only captures.
identity = json.loads((EVIDENCE / "identity.json").read_text())
baseline = json.loads((EVIDENCE / "baseline.json").read_text())
head_index_match = identity["sourceHead"] == baseline["head"] and identity["sourceIndexSha256"] == baseline["indexSha256"]
field_inputs = json.loads((EVIDENCE / "field-installed/inputs.json").read_text())
live_capture_matches = [Path(p).is_file() and digest(Path(p)) == row["digest"] for p, row in field_inputs["before"].items()]
field_measurements = json.loads((EVIDENCE / "field-installed/measurements.json").read_text())
field_invocations = sorted({arg for row in field_measurements for arg in row.get("argv", []) if isinstance(arg, str) and "/ladon-guides-r47-" in arg and "/bin/ladon" in arg})
dossier_store = json.loads((EVIDENCE / "dossier-compatibility/input-store.json").read_text())
dossier_measurements = json.loads((EVIDENCE / "dossier-compatibility/measurements.json").read_text())
dossier_invocations = sorted({arg for row in dossier_measurements for arg in row.get("argv", []) if isinstance(arg, str) and "/ladon-guides-r47-" in arg and "/bin/ladon" in arg})
checks.append({"check": "unchanged_captures", "head_index_match": head_index_match, "field_inputs_before_after_match": field_inputs["before"] == field_inputs["after"], "field_live_matches": sum(live_capture_matches), "field_capture_files": len(live_capture_matches), "field_calls": len(field_measurements), "field_exit_failures": [x.get("label") for x in field_measurements if x.get("exitCode") != 0], "field_origins": field_invocations, "dossier_store_unchanged": dossier_store["unchanged"] and dossier_store["sha256Before"] == dossier_store["sha256After"], "dossier_calls": len(dossier_measurements), "dossier_exit_failures": [x for x in dossier_measurements if x.get("exitCode") != 0], "dossier_origins": dossier_invocations})

# Candidate-specific suite receipts/logs and mutation records.
suite_counts = {"discovery": 137, "integration": 2688, "correctness": 147, "authority": 1060}
suite_bad = []
for name, expected in suite_counts.items():
    for runtime in ("py311", "py312"):
        path = QUAL / f"{name}-r47-{runtime}.json"
        data = json.loads(path.read_text())
        if not (data["runtime"] == runtime and data["exitCode"] == 0 and len(data["passed"]) == expected and len(data["collected"]) == expected and not data["failed"] and not data["skipped"] and data["candidateIdentity"] == guide["candidateIdentity"] and data["sourceTreeIdentity"] == guide["sourceTreeIdentity"] and data["wheelDigest"] == guide["wheelDigest"]):
            suite_bad.append(path.name)
suite_logs = {}
for filename, expected in (("discovery-r47-py311.log", "137 passed"), ("integration-r47-py311.log", "2688 passed"), ("correctness-r47-py311.log", "147 passed"), ("authority-r47-py311.log", "1060 passed"), ("prerequisites-r47/clean-candidate.log", "2863 passed"), ("prerequisites-r47/installed-distribution.log", "29 passed")):
    path = QUAL / filename
    suite_logs[filename] = path.is_file() and expected in path.read_text(errors="replace")
contract_logs = {}
for runtime in ("py311", "py312"):
    path = EVIDENCE / f"{runtime}-contracts.log"
    contract_logs[runtime] = path.is_file() and "194 passed" in path.read_text(errors="replace")
nodeids_path = CANDIDATE / "candidate/.pytest_cache/v/cache/nodeids"
guide_nodeids = json.loads(nodeids_path.read_text()) if nodeids_path.is_file() else []
guide_test_count = sum("result_guide" in node or "result_guides" in node for node in guide_nodeids)
gate_logs = [g for g in umbrella["prerequisites"] if g.get("status") != "passed" or g.get("exitCode") != 0 or not Path(g.get("logPath", "")).is_file()]
damage = {}
for runtime in ("py311", "py312"):
    discovery = json.loads((QUAL / f"discovery-validation-r47-{runtime}.json").read_text())["networkMutations"]
    integration = json.loads((QUAL / f"integration-mutations-r47-{runtime}.json").read_text())
    damage[runtime] = {"discovery_cases": len(discovery), "discovery_rejected": sum(x.get("status") == "rejected" for x in discovery), "integration_cases": len(integration), "integration_rejected": sum(x.get("status") == "rejected" for x in integration)}
checks.append({"check": "qualification", "suite_counts": suite_counts, "suite_mismatches": suite_bad, "summary_logs_match": suite_logs, "installed_result_logs_match": contract_logs, "installed_guide_tests": guide_test_count, "gate_count": len(umbrella["prerequisites"]), "bad_gates": [g.get("gateId") for g in gate_logs], "damaged_receipt_cases": damage})

# Independent audit and qualitative-use receipts are board-backed and not human approval.
checks.append({"check": "review_scope", "independent_code_audit_post": guide["outcomes"]["independentCodeAuditPost"], "qualitative_reader_post": guide["outcomes"]["qualitativeReaderFeedbackPost"], "limitations": guide["limitations"]})

passed = True
for row in checks:
    passed &= not row.get("mismatches") and not row.get("bad_gates") and not row.get("suite_mismatches") and not row.get("code_diffs") and not row.get("wheel_mismatches")
    passed &= row.get("tuple_match", True) and row.get("head_index_match", True) and row.get("field_inputs_before_after_match", True) and row.get("dossier_store_unchanged", True)
    passed &= all(row.get("summary_logs_match", {}).values()) and all(row.get("installed_result_logs_match", {}).values())
    passed &= row.get("installed_guide_tests", 42) == 42
    passed &= all(all(part["discovery_cases"] == part["discovery_rejected"] and part["integration_cases"] == part["integration_rejected"] for part in row.get("damaged_receipt_cases", {}).values()) for _ in (0,))

result = {
    "status": "passed" if passed else "failed",
    "candidateCommit": guide["candidateCommit"],
    "candidateIdentity": guide["candidateIdentity"],
    "sourceTreeIdentity": guide["sourceTreeIdentity"],
    "wheelDigest": guide["wheelDigest"],
    "receipts": {str(p): digest(p) for p in receipts},
    "inventoryDigest": digest(EVIDENCE / "inventory.json"),
    "checks": checks,
}
print(json.dumps(result, indent=2, sort_keys=True))
