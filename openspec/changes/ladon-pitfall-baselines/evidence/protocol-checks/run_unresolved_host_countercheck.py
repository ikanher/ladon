"""Exercise host continuation after a qualified unresolved capture.

This is a protocol countercheck, not a scored family batch: it injects an
unparseable goal for the first otherwise registered case, then lets cases 2–4
run through the preserved runtime unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


CHECK_DIR = Path(__file__).resolve().parent
RUNNER = CHECK_DIR.parents[1] / "scripts" / "feasibility_baseline.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-existing", action="store_true",
                        help="verify an already completed run without rerunning Lean")
    args = parser.parse_args()

    spec = importlib.util.spec_from_file_location("feasibility_baseline", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the frozen feasibility runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not args.verify_existing:
        original_prepare = module._prepare_case

        def prepare(case, runtime_root, workspace, artifacts):
            prepared = original_prepare(case, runtime_root, workspace, artifacts)
            if case["caseId"] == "assumption-feasibility-01":
                prepared["request"] = {
                    "goal": "∀ n : Nat, (",
                    "module": prepared["request"]["module"],
                }
            return prepared

        module._prepare_case = prepare
        try:
            code = module.run_host(args)
        finally:
            module._prepare_case = original_prepare
    else:
        code = 0

    index_path = args.output / "acceptance-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert code == 0
    assert index["status"] == "pending-independent-adjudication"
    assert index["orderedCases"] == [
        "assumption-feasibility-01", "assumption-feasibility-02",
        "assumption-feasibility-03", "assumption-feasibility-04",
    ]
    first = json.loads((args.output / "case-01" / "case-record.json").read_text())
    report = first["worker"]["reportData"]
    injected = {"caseId": "assumption-feasibility-01", **report["operationalInput"]}
    assert injected["goal"] == "∀ n : Nat, ("
    assert report["formalOutcome"] == "unresolved"
    assert len(report["attempts"]) == 2
    assert all(a["attemptState"] == "unresolved" and not a["proofEstablished"]
               for a in report["attempts"])

    later = []
    for ordinal in range(2, 5):
        record = json.loads((args.output / f"case-{ordinal:02d}" / "case-record.json").read_text())
        assert record["worker"]["launcherReceipt"]["returnCode"] == 0
        assert record["worker"]["reportData"]["operationalInput"]["module"]
        later.append(record["caseId"])

    (args.output / "injected-input.json").write_text(json.dumps({
        "kind": "protocol-countercheck-input",
        "reason": "exercise unresolved capture handling; never a scored baseline input",
        **injected,
    }, indent=2) + "\n", encoding="utf-8")
    summary = {
        "schema": "ladon-feasibility-host-unresolved-continuation-countercheck-v1",
        "runnerSha256": sha(RUNNER),
        "countercheckScriptSha256": sha(Path(__file__)),
        "acceptanceIndexSha256": sha(index_path),
        "injectedInput": injected,
        "firstCaseFormalOutcome": report["formalOutcome"],
        "firstCaseAttemptStates": [a["attemptState"] for a in report["attempts"]],
        "laterCasesCompleted": later,
        "scoredBaseline": False,
        "result": "passed",
    }
    (args.output / "host-continuation-countercheck.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
