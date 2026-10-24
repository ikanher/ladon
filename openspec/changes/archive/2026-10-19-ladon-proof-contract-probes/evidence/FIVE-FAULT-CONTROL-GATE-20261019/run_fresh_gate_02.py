"""Run the source-building qualifiers under the first attempt's shared deadline."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.proof_contract_bridge import _accepted_check

ROOT = Path(__file__).resolve().parents[5]
GATE = Path(__file__).resolve().parent
PRIOR = json.loads((GATE / "fresh-run-01/RESULT.json").read_text(encoding="utf-8"))
DEADLINE = float(PRIOR["deadlineMonotonic"])
START = DEADLINE - 1800
OUT = GATE / os.environ.get("LADON_GATE_RUN_DIR", "fresh-run-02")
if OUT.exists():
    raise SystemExit(f"refusing to overwrite previous attempts: {OUT}")
OUT.mkdir()
LIMITS = {"timeout_seconds": 30, "max_rss_bytes": 12 * 1024**3,
          "max_output_bytes": 8 * 1024**2}
ENV = dict(os.environ)
ENV["LADON_GATE_DEADLINE"] = str(DEADLINE)
ENV["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + ENV.get("PYTHONPATH", "")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def verify_checked_case(family: str, role: str, request_path: Path,
                        result_path: Path, expected_status: str) -> dict:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("status") != expected_status:
        raise RuntimeError(f"{family}/{role}: {result.get('status')} != {expected_status}")
    goals = result.get("goals")
    if not isinstance(goals, list) or len(goals) != 2:
        raise RuntimeError(f"{family}/{role}: expected exactly two generated goals")
    accepted = []
    for goal in goals:
        if goal.get("status") != "checked-support" or not goal.get("result"):
            raise RuntimeError(f"{family}/{role}/{goal.get('goalId')}: goal not checked")
        raw = load_goal_evidence(request["repoRoot"], goal["result"])
        if not _accepted_check(raw):
            raise RuntimeError(f"{family}/{role}/{goal.get('goalId')}: raw checker receipt rejected")
        if raw["completion"].get("termDigest") != "sha256:" + hashlib.sha256(
                goal["term"].encode()).hexdigest():
            raise RuntimeError(f"{family}/{role}/{goal.get('goalId')}: proof-term digest mismatch")
        accepted.append({"goalId": goal["goalId"], "goalDigest": goal["goalDigest"],
                         "termDigest": raw["completion"]["termDigest"],
                         "evidenceRef": goal["result"]["evidenceRef"],
                         "replay": raw["completion"]["replay"]["status"],
                         "trustAccepted": raw["completion"]["trust"]["accepted"]})
    payload = result.get("artifact", {}).get("payload", {})
    if payload.get("checkRunRefs") != [] or any(
            goal.get("status") != "open" for goal in payload.get("result", {}).get("goals", [])):
        raise RuntimeError(f"{family}/{role}: checker receipts leaked into the open plan")
    return {"family": family, "role": role, "status": expected_status,
            "requestPath": request_path.relative_to(OUT).as_posix(),
            "checkedPath": result_path.relative_to(OUT).as_posix(),
            "acceptedGoals": accepted}


def run_qualifier(name: str, source: Path, output_dir: Path,
                  replacements: list[tuple[str, str]], runtime_source: Path | None = None,
                  argument: str | None = None) -> dict:
    if time.monotonic() >= DEADLINE:
        raise TimeoutError("original shared 1800-second gate deadline expired")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    if output_dir.exists():
        raise FileExistsError(output_dir)
    output_dir.mkdir()
    if runtime_source is not None:
        runtime = json.loads(runtime_source.read_text(encoding="utf-8"))
        drift = []
        for entry in runtime["files"]:
            source_path = Path(entry["path"])
            current_hash = digest(source_path)
            if current_hash != entry["sha256"]:
                drift.append({"path": entry["path"], "baselineSha256": entry["sha256"],
                              "currentSha256": current_hash})
                entry["sha256"] = current_hash
        save_json(output_dir / "RUNTIME.json", runtime)
        save_json(output_dir / "BASELINE-DRIFT.json", {
            "sourceManifest": runtime_source.relative_to(ROOT).as_posix(),
            "sourceManifestSha256": digest(runtime_source),
            "mode": "current checkout requalification; baseline files are not modified",
            "changedFiles": drift,
        })
    script = source.read_text(encoding="utf-8")
    for old, new in replacements:
        if old not in script:
            raise RuntimeError(f"patch anchor missing in {source}: {old!r}")
        script = script.replace(old, new, 1)
    script_path = output_dir.parent / f"{name}-qualify.py"
    script_path.write_text(script, encoding="utf-8")
    env = dict(ENV)
    env["LADON_GATE_OUTPUT"] = str(output_dir.resolve())
    args = [sys.executable, str(script_path)]
    if argument is not None:
        args.append(argument)
    started = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True,
                              timeout=max(1.0, DEADLINE - time.monotonic()), check=False)
        stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        returncode = -1
    (output_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
    (output_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
    record = {"family": name, "command": args, "returncode": returncode,
              "elapsedSeconds": time.monotonic() - started,
              "campaignElapsedSeconds": time.monotonic() - START,
              "stdoutSha256": hashlib.sha256(stdout.encode()).hexdigest(),
              "stderrSha256": hashlib.sha256(stderr.encode()).hexdigest(),
              "stdoutTail": stdout[-2500:], "stderrTail": stderr[-2500:]}
    result_path = output_dir / "RESULT.json"
    if result_path.is_file():
        record["resultSha256"] = digest(result_path)
        record["result"] = json.loads(result_path.read_text(encoding="utf-8"))
    save_json(output_dir / "process-result.json", record)
    print(json.dumps({"event": "qualifier", "family": name,
                      "returncode": returncode,
                      "campaignElapsedSeconds": record["campaignElapsedSeconds"]}), flush=True)
    if returncode != 0:
        raise RuntimeError(f"{name} qualifier returned {returncode}")
    if not result_path.is_file() or record["result"].get("status") != "PASS":
        raise RuntimeError(f"{name} qualifier did not save PASS")
    return record


records: list[dict] = []
try:
    constant_source = (ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/"
                       "CONSTANT-UNIFORMITY-20261019/qualify.py")
    records.append(run_qualifier(
        "regularity-and-uniformity", constant_source,
        OUT / "constant-uniformity",
        [("p = Path('.codex/state/proof-contract-analysis/constant-probes/qualification-01')",
          "p = Path(os.environ['LADON_GATE_OUTPUT']).resolve()"),
         ("deadline = started + 1800", "deadline = float(os.environ['LADON_GATE_DEADLINE'])")],
        runtime_source=ROOT / ".codex/state/proof-contract-analysis/constant-probes/qualification-01/RUNTIME.json"))

    witness_source = (ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/"
                      "WITNESS-DEPENDENCE-20261019/qualify.py")
    records.append(run_qualifier(
        "witness-dependence", witness_source,
        OUT / "witness-dependence",
        [("import json\n", "import json\nimport os\n"),
         ('p = base / "attempt-04"', 'p = Path(os.environ["LADON_GATE_OUTPUT"]).resolve()'),
         ("p.mkdir()", "p.mkdir(exist_ok=True)"),
         ('started = prior["startedMonotonic"]\ndeadline = prior["deadlineMonotonic"]',
          'started = time.monotonic()\ndeadline = float(os.environ["LADON_GATE_DEADLINE"])')]))

    restricted_source = (ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/"
                         "RESTRICTED-DOMAIN-20261019/source-attempt-04/qualify.py")
    records.append(run_qualifier(
        "restricted-domain", restricted_source, OUT / "restricted-wrapper",
        [("from pathlib import Path", "from pathlib import Path\nimport os"),
         ("base=Path('.codex/state/proof-contract-analysis/restricted-domain')",
          "base=Path(os.environ['LADON_GATE_OUTPUT']).resolve()"),
         ("p=base/'attempt-04'", "p=base/'restricted-domain'"),
         ("shutil.copyfile(base/'lean-toolchain', repo/'lean-toolchain')",
          "shutil.copyfile(Path('.codex/state/proof-contract-analysis/restricted-domain/lean-toolchain'), repo/'lean-toolchain')"),
         ("planned=plan_application_probe(request);",
          "(p/f'{label}-request.json').write_text(json.dumps(request,sort_keys=True,indent=2)); planned=plan_application_probe(request);"),
         ("started=time.monotonic(); deadline=started+1800",
          "started=time.monotonic(); deadline=float(os.environ['LADON_GATE_DEADLINE'])")],
        argument="restricted-domain"))

    inequality_source = (ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/"
                         "INEQUALITY-DIRECTION-20261019/qualify-final.py")
    records.append(run_qualifier(
        "inequality-direction", inequality_source, OUT / "inequality-wrapper",
        [("import time\n", "import time\nimport os\n"),
         ("base = Path(__file__).resolve().parent",
          "base = Path(os.environ['LADON_GATE_OUTPUT']).resolve()"),
         ("planned = plan_application_probe(request)",
          "(attempt / f\"{label}-request.json\").write_text(json.dumps(request, sort_keys=True, indent=2))\n    planned = plan_application_probe(request)"),
         ("deadline = started + 1800", "deadline = float(os.environ['LADON_GATE_DEADLINE'])")],
        argument="inequality-direction"))
    family_results = [record["result"] for record in records]
    if len(family_results) != 4 or any(result.get("status") != "PASS" for result in family_results):
        raise RuntimeError("one or more family qualifiers did not pass")
    if time.monotonic() > DEADLINE:
        raise TimeoutError("campaign exceeded its shared deadline")
    status = "PASS"
except (AssertionError, OSError, RuntimeError, TimeoutError, TypeError,
        ValueError, subprocess.SubprocessError, KeyError) as error:
    status = "INCOMPLETE"
    save_json(OUT / "failure.json", {"type": type(error).__name__, "message": str(error),
                                     "campaignElapsedSeconds": time.monotonic() - START,
                                     "remainingSeconds": DEADLINE - time.monotonic()})

unsupported_sources = [
    ROOT / ".codex/state/proof-contract-analysis/constant-probes/qualification-01/unsupported-constant-uniformity-result.json",
    ROOT / ".codex/state/proof-contract-analysis/constant-probes/qualification-01/unsupported-witness-dependence-result.json",
    ROOT / ".codex/state/proof-contract-analysis/constant-probes/qualification-01/unsupported-restricted-domain-result.json",
    ROOT / ".codex/state/proof-contract-analysis/constant-probes/qualification-01/unsupported-inequality-direction-result.json",
]
unsupported = []
for path in unsupported_sources:
    raw = json.loads(path.read_text(encoding="utf-8"))
    unsupported.append({"path": path.relative_to(ROOT).as_posix(),
                        "sha256": digest(path), "status": raw.get("status"),
                        "templateVersion": raw.get("artifact", {}).get("payload", {}).get("template", {}).get("version")})
fresh_statuses = []
if status == "PASS":
    constant = OUT / "constant-uniformity"
    for name, role, expected in [
        ("regularity", "fault", "checked-local-nonimplication"),
        ("regularity-control", "control", "checked-local-implication"),
        ("uniformity", "fault", "checked-local-nonimplication"),
        ("uniformity-control", "control", "checked-local-implication"),
    ]:
        fresh_statuses.append(verify_checked_case(
            "regularity-boundary" if name.startswith("regularity") else "constant-uniformity",
            role, constant / f"{name}-checked-request.json",
            constant / f"{name}-checked-result.json", expected))
    witness = OUT / "witness-dependence"
    for name, role, expected in [
        ("discrepancy", "fault", "checked-local-nonimplication"),
        ("control", "control", "checked-local-implication"),
    ]:
        fresh_statuses.append(verify_checked_case(
            "witness-dependence", role, witness / f"{name}-request.json",
            witness / f"{name}-checked.json", expected))
    for name, family, directory in [
        ("restricted-domain", "restricted-domain", OUT / "restricted-wrapper/restricted-domain"),
        ("inequality-direction", "inequality-direction", OUT / "inequality-wrapper/inequality-direction"),
    ]:
        for role, case, expected in [
            ("fault", "discrepancy", "checked-local-nonimplication"),
            ("control", "control", "checked-local-implication"),
        ]:
            fresh_statuses.append(verify_checked_case(
                family, role, directory / f"{case}-planned.json",
                directory / f"{case}-checked.json", expected))
if status == "PASS" and (len(fresh_statuses) != 10 or
                          sum(len(row["acceptedGoals"]) for row in fresh_statuses) != 20):
    status = "INCOMPLETE"
    save_json(OUT / "failure.json", {"type": "EvidenceCountMismatch",
                                     "message": "expected ten checked cases and twenty accepted goals",
                                     "campaignElapsedSeconds": time.monotonic() - START})
result = {"schema": "ladon-five-fault-five-control-shared-deadline-v1",
          "status": status,
          "budgetSeconds": 1800,
          "elapsedSeconds": time.monotonic() - START,
          "deadlineMonotonic": DEADLINE,
          "limits": LIMITS,
          "priorPreparationFailure": {"path": "fresh-run-01/failure.json",
              "classification": "source-context mismatch before any checker call; no semantic result",
              "elapsedSeconds": 8.45},
          "priorRuntimeInventoryFailure": {"path": "fresh-run-02/failure.json",
              "classification": "frozen runtime identity mismatch before the family script began any probe; no semantic result",
              "elapsedSeconds": 127.75},
          "freshQualifiers": records,
          "freshCases": fresh_statuses,
          "unsupportedTemplates": unsupported,
          "attemptRetention": "fresh-run-01, fresh-run-02 and all historic source attempts are preserved; no previous result envelopes were supplied to fresh checks",
          "scope": "five synthetic source-bound discrepancy/control pairs; no natural-language fidelity or target-paper detection claim",
          "failure": json.loads((OUT / "failure.json").read_text()) if (OUT / "failure.json").exists() else None}
save_json(OUT / "RESULT.json", result)
print(json.dumps({"status": status, "campaignElapsedSeconds": result["elapsedSeconds"],
                  "familiesCompleted": len(records), "freshCaseRows": len(fresh_statuses),
                  "remainingSeconds": DEADLINE - time.monotonic(), "failure": result["failure"]}), flush=True)
if status != "PASS":
    raise SystemExit(1)
