"""Run five synthetic fault/control pairs under one absolute 30-minute deadline.

This writes only into fresh-run-01 and preserves every partial attempt.
"""
from __future__ import annotations

import hashlib
import json
import os
import resource
import shutil
import subprocess
import sys
import time
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.proof_contract_bridge import _accepted_check
from ladon.proof_contract_probes import check_application_probe, plan_application_probe

ROOT = Path(__file__).resolve().parents[5]
GATE = Path(__file__).resolve().parent
OUT = GATE / "fresh-run-01"
if OUT.exists():
    raise SystemExit(f"refusing to overwrite existing attempts: {OUT}")
OUT.mkdir()
START = time.monotonic()
DEADLINE = START + 1800
LIMITS = {"timeout_seconds": 30, "max_rss_bytes": 12 * 1024**3,
          "max_output_bytes": 8 * 1024**2}
RUNS = ROOT / ".codex/state/proof-contract-analysis"
CONSTANT = RUNS / "constant-probes/qualification-01"
WITNESS = RUNS / "witness-feasibility/attempt-07"
CASES = [
    ("regularity-boundary", "fault", CONSTANT / "regularity-checked-request.json",
     CONSTANT / "regularity-checked-terms.json", CONSTANT / "regularity-repo",
     "checked-local-nonimplication"),
    ("regularity-boundary", "control", CONSTANT / "regularity-control-checked-request.json",
     CONSTANT / "regularity-control-checked-terms.json", CONSTANT / "regularity-repo",
     "checked-local-implication"),
    ("constant-uniformity", "fault", CONSTANT / "uniformity-checked-request.json",
     CONSTANT / "uniformity-checked-terms.json", CONSTANT / "uniformity-repo",
     "checked-local-nonimplication"),
    ("constant-uniformity", "control", CONSTANT / "uniformity-control-checked-request.json",
     CONSTANT / "uniformity-control-checked-terms.json", CONSTANT / "uniformity-repo",
     "checked-local-implication"),
    ("witness-dependence", "fault", WITNESS / "discrepancy-request.json",
     WITNESS / "discrepancy-terms.json", RUNS / "witness-feasibility/attempt-04/repo",
     "checked-local-nonimplication"),
    ("witness-dependence", "control", WITNESS / "strong-to-weak-control-request.json",
     WITNESS / "strong-to-weak-control-terms.json",
     RUNS / "witness-feasibility/attempt-04/repo", "checked-local-implication"),
]


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def save_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def remaining() -> float:
    return DEADLINE - time.monotonic()


def run_saved_case(index: int, case) -> dict:
    family, role, request_path, terms_path, source_repo, expected = case
    if remaining() <= 0:
        raise TimeoutError("shared 1800-second gate deadline expired")
    case_dir = OUT / f"{index:02d}-{family}-{role}"
    case_dir.mkdir()
    repo = case_dir / "repo"
    shutil.copytree(source_repo, repo)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    request["repoRoot"] = str(repo.resolve())
    request["deadlineMonotonic"] = DEADLINE
    request["limits"] = LIMITS
    terms = json.loads(terms_path.read_text(encoding="utf-8"))
    save_json(case_dir / "request.json", request)
    save_json(case_dir / "terms.json", terms)
    planned = plan_application_probe(request)
    save_json(case_dir / "planned.json", planned)
    if planned.get("status") != "planned":
        raise RuntimeError(f"{family}/{role}: planning was {planned.get('status')}")
    checked = check_application_probe(request, planned["planId"], terms)
    save_json(case_dir / "checked.json", checked)
    if checked.get("status") != expected:
        raise RuntimeError(f"{family}/{role}: status {checked.get('status')} != {expected}")
    goals = checked.get("goals")
    if not isinstance(goals, list) or len(goals) != 2:
        raise RuntimeError(f"{family}/{role}: expected two checked goals")
    accepted = []
    for goal in goals:
        if goal.get("status") != "checked-support" or not goal.get("result"):
            raise RuntimeError(f"{family}/{role}/{goal.get('goalId')}: no accepted support")
        raw = load_goal_evidence(repo, goal["result"])
        if not _accepted_check(raw):
            raise RuntimeError(f"{family}/{role}/{goal.get('goalId')}: raw receipt rejected")
        if raw["completion"].get("termDigest") != digest(goal["term"].encode()):
            raise RuntimeError(f"{family}/{role}/{goal.get('goalId')}: term digest mismatch")
        accepted.append({"goalId": goal["goalId"], "goalDigest": goal["goalDigest"],
                         "termDigest": digest(goal["term"].encode()),
                         "evidenceRef": goal["result"]["evidenceRef"],
                         "replay": raw["completion"]["replay"]["status"],
                         "trustAccepted": raw["completion"]["trust"]["accepted"]})
    payload = checked.get("artifact", {}).get("payload", {})
    if payload.get("checkRunRefs") != [] or any(
            goal.get("status") != "open" for goal in payload.get("result", {}).get("goals", [])):
        raise RuntimeError(f"{family}/{role}: checker authority leaked into plan artifact")
    result = {"family": family, "role": role, "status": expected,
              "requestSha256": hashlib.sha256((case_dir / "request.json").read_bytes()).hexdigest(),
              "checkedSha256": hashlib.sha256((case_dir / "checked.json").read_bytes()).hexdigest(),
              "acceptedCheckerGoals": accepted}
    save_json(case_dir / "outcome.json", result)
    print(json.dumps({"event": "case-complete", "family": family, "role": role,
                      "elapsedSeconds": time.monotonic() - START, "remainingSeconds": remaining()}),
          flush=True)
    return result


def run_qualifier(name: str, source: Path, output_subdir: str, patches: list[tuple[str, str]]) -> dict:
    if remaining() <= 0:
        raise TimeoutError("shared 1800-second gate deadline expired")
    work = OUT / f"qualifier-{name}"
    work.mkdir()
    script = source.read_text(encoding="utf-8")
    for old, new in patches:
        if old not in script:
            raise RuntimeError(f"qualifier patch anchor missing for {name}: {old!r}")
        script = script.replace(old, new, 1)
    script_path = work / "qualify.py"
    script_path.write_text(script, encoding="utf-8")
    env = dict(os.environ)
    env["LADON_GATE_DEADLINE"] = str(DEADLINE)
    env["LADON_GATE_OUTPUT"] = str(work.resolve())
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    timeout = max(1, int(remaining()))
    command = [sys.executable, str(script_path), output_subdir]
    completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                               text=True, timeout=timeout, check=False)
    (work / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (work / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
    result = {"family": name, "returncode": completed.returncode,
              "elapsedSeconds": time.monotonic() - START,
              "stdoutTail": completed.stdout[-4000:], "stderrTail": completed.stderr[-4000:]}
    qualifier_result_path = work / output_subdir / "RESULT.json"
    if completed.returncode == 0 and qualifier_result_path.is_file():
        qualifier_result = json.loads(qualifier_result_path.read_text(encoding="utf-8"))
        if qualifier_result.get("status") != "PASS" or len(qualifier_result.get("summary", [])) != 2:
            raise RuntimeError(f"{name}: source qualifier did not complete both checked cases")
        if any(len(row.get("acceptedGoals", [])) != 2 for row in qualifier_result["summary"]):
            raise RuntimeError(f"{name}: a case did not accept both goals")
        result["outcomes"] = qualifier_result["summary"]
        result["resultPath"] = qualifier_result_path.relative_to(OUT).as_posix()
    save_json(work / "process-result.json", result)
    if completed.returncode != 0:
        raise RuntimeError(f"{name} qualifier failed with exit {completed.returncode}")
    print(json.dumps({"event": "qualifier-complete", **result}), flush=True)
    return result


outcomes: list[dict] = []
qualifiers: list[dict] = []
try:
    for i, case in enumerate(CASES, 1):
        outcomes.append(run_saved_case(i, case))
    restricted_source = (ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/"
                        "RESTRICTED-DOMAIN-20261019/source-attempt-04/qualify.py")
    restricted = restricted_source.read_text(encoding="utf-8")
    restricted_patches = [
        ("from pathlib import Path", "from pathlib import Path\nimport os"),
        ("base=Path('.codex/state/proof-contract-analysis/restricted-domain')",
         "base=Path(os.environ['LADON_GATE_OUTPUT']).resolve()"),
        ("p=base/'attempt-04'", "p=base/'restricted-domain'"),
        ("shutil.copyfile(base/'lean-toolchain', repo/'lean-toolchain')",
         "shutil.copyfile(Path('.codex/state/proof-contract-analysis/restricted-domain/lean-toolchain'), repo/'lean-toolchain')"),
        ("started=time.monotonic(); deadline=started+1800",
         "started=time.monotonic(); deadline=float(os.environ['LADON_GATE_DEADLINE'])"),
    ]
    qualifiers.append(run_qualifier("restricted-domain", restricted_source,
                                    "restricted-domain", restricted_patches))
    inequality_source = (ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/"
                         "INEQUALITY-DIRECTION-20261019/qualify-final.py")
    inequality_patches = [
        ("import time\n", "import time\nimport os\n"),
        ("base = Path(__file__).resolve().parent",
         "base = Path(os.environ['LADON_GATE_OUTPUT']).resolve()"),
        ("deadline = started + 1800", "deadline = float(os.environ['LADON_GATE_DEADLINE'])"),
    ]
    qualifiers.append(run_qualifier("inequality-direction", inequality_source,
                                    "inequality-direction", inequality_patches))
    status = "PASS"
except (AssertionError, OSError, RuntimeError, TimeoutError, TypeError,
        ValueError, subprocess.SubprocessError, KeyError) as error:
    status = "INCOMPLETE"
    save_json(OUT / "failure.json", {"type": type(error).__name__, "message": str(error),
                                     "elapsedSeconds": time.monotonic() - START,
                                     "remainingSeconds": remaining()})
finally:
    unsupported = []
    for family, version, path in [
        ("constant-uniformity", "constant-uniformity-v1", CONSTANT / "unsupported-constant-uniformity-result.json"),
        ("witness-dependence", "witness-dependence-v1", CONSTANT / "unsupported-witness-dependence-result.json"),
        ("restricted-domain", "restricted-domain-v1", CONSTANT / "unsupported-restricted-domain-result.json"),
        ("inequality-direction", "inequality-direction-v1", CONSTANT / "unsupported-inequality-direction-result.json"),
    ]:
        data = path.read_bytes()
        unsupported.append({"family": family, "templateVersion": version,
                            "status": json.loads(data).get("status"),
                            "sourcePath": path.relative_to(ROOT).as_posix(),
                            "sha256": hashlib.sha256(data).hexdigest()})
    all_records = outcomes + [
        {**row, "family": qualifier["family"]}
        for qualifier in qualifiers for row in qualifier.get("outcomes", [])]
    accepted_goal_count = sum(len(row["acceptedCheckerGoals"]) for row in outcomes)
    status = "PASS" if len(outcomes) == 6 and len(qualifiers) == 2 and len(all_records) == 10 and accepted_goal_count == 12 else "INCOMPLETE"
    result = {
        "schema": "ladon-five-fault-five-control-shared-deadline-v1",
        "status": status,
        "budgetSeconds": 1800,
        "elapsedSeconds": time.monotonic() - START,
        "deadlineMonotonic": DEADLINE,
        "limits": LIMITS,
        "evidenceMode": "fresh bounded plan/check runs; shared absolute deadline; distinct repositories and result outputs",
        "completedCases": len(all_records),
        "requiredDirectRequestCases": 6,
        "qualifiers": qualifiers,
        "outcomes": all_records,
        "acceptedCheckerGoalCount": accepted_goal_count + sum(
            len(row.get("acceptedGoals", [])) for qualifier in qualifiers
            for row in qualifier.get("outcomes", [])),
        "unsupportedTemplates": unsupported,
        "failure": json.loads((OUT / "failure.json").read_text()) if (OUT / "failure.json").exists() else None,
        "scope": "constructed source-bound probes only; no natural-language fidelity or target-paper detection claim",
        "peakRssKiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    save_json(OUT / "RESULT.json", result)
    print(json.dumps({key: result[key] for key in
                      ("status", "elapsedSeconds", "completedCases",
                       "acceptedCheckerGoalCount", "failure")}, sort_keys=True), flush=True)
if status != "PASS":
    raise SystemExit(1)
