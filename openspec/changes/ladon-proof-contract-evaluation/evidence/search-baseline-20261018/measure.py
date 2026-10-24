"""Freeze, then measure the existing checkout; never implement a search policy."""

import hashlib
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

import ladon
from ladon.evaluation_ladon import run_ladon
from ladon.evaluation_metrics import summarize_method
from ladon.evaluation_process import measure_command
from ladon.lean_toolchain import resolve_toolchain_context
from ladon.proof_route_planner import GoalState, PlannerBounds, plan_routes

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASELINE = ROOT / ".codex/state/proof-contract-analysis/baseline"
MANIFEST = ROOT / "openspec/changes/ladon-proof-contract-evaluation/evidence/BASELINE.json"
BOUNDS = {"timeoutSeconds": 60, "maxRssBytes": 12 * 1024**3,
          "maxOutputBytes": 8 * 1024**2, "maxCandidates": 8, "batchSize": 8}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_once(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def route_cases():
    result = []
    for seed in range(64):
        rng = random.Random(20261018 + seed)
        candidates = {}
        support = {}
        for node in reversed(range(8)):
            rows = []
            for branch in range(3):
                parents = [] if node == 7 else [f"g{rng.randrange(node + 1, 8)}"
                                                 for _ in range(rng.randrange(3))]
                if node == 7 and seed % 3 == 0:
                    continue
                rows.append({"name": f"n{node}b{branch}", "verification": "verified",
                             "cost": rng.randrange(1, 5), "residuals": parents})
            candidates[f"g{node}"] = rows
            support[f"g{node}"] = any(all(support[p] for p in row["residuals"])
                                         for row in rows)
        result.append({"id": f"dag-{seed:02}", "candidates": candidates,
                       "expectedSupported": support["g0"]})
    return result


def freeze():
    files = [HERE / "measure.py", HERE / "CASES.json", *sorted((HERE / "inputs").rglob("*"))]
    inputs = {str(path.relative_to(HERE)): digest(path) for path in files if path.is_file()}
    write_once(HERE / "ROUTES.json", {"cases": route_cases()})
    inputs["ROUTES.json"] = digest(HERE / "ROUTES.json")
    write_once(HERE / "FREEZE.json", {
        "schema": "ladon-pre-beam-engineering-baseline-v1", "createdAtUnix": time.time(),
        "baselineManifestSha256": digest(MANIFEST), "inputs": inputs,
        "runtime": str(BASELINE), "bounds": BOUNDS, "seed": 20261018,
        "routeExpansionBudgets": [8, 32, 128], "routeDepthCap": 32, "routeCountCap": 20,
        "caseCount": 8, "positiveCases": 4, "noClosedCandidateControls": 4,
        "routeCaseCount": 64, "routeLabels": "finite acyclic AND/OR truth oracle",
        "metrics": ["closedPositiveCases", "falseClosureControlCases", "unresolvedCases",
                    "verifiedCandidateRecall", "semanticTerminalAssessments", "independentReplayAttempts",
                    "timeToFirstAcceptedCandidateSeconds", "runtimeSeconds", "peakRssSampledBytes",
                    "timeouts", "outputLimits", "memoryLimits", "routeCoverage", "expandedStates"],
        "policy": "All inputs and outcomes retained; no retries or memory increase; serial Lean processes.",
        "nonclaims": ["Development fixtures, no independent fault-discovery estimate.",
                      "No NL interpretation or beam policy is exercised.",
                      "Synthetic verified graph labels are not Lean certificates.",
                      "Existing v3 portable cases are reused, not a new held-out sample."]})
    print("Frozen eight Lean cases and 64 finite graphs before measurement")


def verify():
    assert Path(ladon.__file__).resolve().is_relative_to(BASELINE), ladon.__file__
    frozen = json.loads((HERE / "FREEZE.json").read_text())
    assert digest(MANIFEST) == frozen["baselineManifestSha256"]
    for relative, expected in frozen["inputs"].items():
        assert digest(HERE / relative) == expected, relative
    for row in json.loads(MANIFEST.read_text())["files"]:
        assert digest(BASELINE / row["path"]) == row["sha256"], row["path"]


def prepare(repository, output):
    root = HERE / "inputs" / repository
    name = "EvalLogic" if repository == "portable-logic" else "EvalArithmetic"
    lean = Path(subprocess.check_output(["elan", "which", "lean"], cwd=root, text=True).strip())
    binary = root / ".lake/build/lib/lean" / (name + ".olean")
    binary.parent.mkdir(parents=True, exist_ok=True)
    compile_record = measure_command([str(lean), "-o", str(binary), name + ".lean"],
                                    cwd=root, environment=os.environ, bounds=BOUNDS,
                                    output=output, stem="compile")
    if compile_record["status"] != "passed":
        return None, None, [compile_record]
    context = resolve_toolchain_context(root, lean_path=lean, lake_path=lean.with_name("lake"),
                                        selection_mode="explicit")
    index = output / "index.sqlite"
    argv = [str(BASELINE / "run-ladon"), "proof-search", "index", "build", "--repo-root",
            str(root), "--index", str(index), "--format", "json"]
    index_record = measure_command(argv, cwd=output, environment=context.environment,
                                  bounds=BOUNDS, output=output, stem="index")
    return context, index if index_record["status"] == "passed" else None, [compile_record, index_record]


def graph_measurements():
    results = []
    for budget in [8, 32, 128]:
        for case in json.loads((HERE / "ROUTES.json").read_text())["cases"]:
            started = time.perf_counter()
            result = plan_routes(GoalState("g0"), case["candidates"],
                                 bounds=PlannerBounds(max_states=budget, max_depth=32, max_routes=20))
            results.append({"case": case["id"], "expansionBudget": budget,
                            "expectedSupported": case["expectedSupported"],
                            "runtimeSeconds": time.perf_counter() - started, "result": result})
    return results


def measure():
    verify()
    output = HERE / "results"
    output.mkdir()
    rows, preparation = [], {}
    for repository in ("portable-logic", "portable-arithmetic"):
        target = output / repository
        target.mkdir()
        context, index, preparation[repository] = prepare(repository, target)
        cases = [case for case in json.loads((HERE / "CASES.json").read_text())["cases"]
                 if case["repository"] == repository]
        for case in cases:
            directory = target / case["id"]
            directory.mkdir()
            try:
                if index is None:
                    raise ValueError("bounded preparation failed")
                result = run_ladon(case, context, BOUNDS, directory,
                                   console=BASELINE / "run-ladon", index=index)
                metrics = summarize_method(result, case["expectedAcceptableCandidates"])
                row = {"case": case["id"], "role": case["baselineRole"], "result": result,
                       "metrics": metrics}
            except (ValueError, KeyError, TypeError, OSError, RuntimeError) as error:
                row = {"case": case["id"], "role": case["baselineRole"],
                       "status": "unresolved", "reason": str(error)}
            rows.append(row)
            write_once(directory / "FIRST.json", row)
            print(case["id"], row.get("metrics", {}).get("closedCandidates", row.get("reason")), flush=True)
    graph_rows = graph_measurements()
    verify()
    write_once(output / "MEASUREMENTS.json", {"schema": "ladon-pre-beam-engineering-measurements-v1",
               "runtimeImport": ladon.__file__, "freezeSha256": digest(HERE / "FREEZE.json"),
               "preparation": preparation, "cases": rows, "graphs": graph_rows})


if __name__ == "__main__":
    {"freeze": freeze, "measure": measure}[sys.argv[1]]()
