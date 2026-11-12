"""Run the frozen feasibility baseline through the preserved Ladon runtime.

The default host mode prepares one restricted workspace per accepted case. The
worker mode is launched under runtime_custody.py exec, so capture and replay
share one pinned Python environment, HOME and TMPDIR.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
CHANGE = Path(__file__).resolve().parents[1]
POLICY = CHANGE / "evidence" / "feasibility-policy-v1.json"
CASES = CHANGE / "evidence" / "corpus" / "cases.json"
ARTIFACTS = CHANGE / "evidence" / "runtime-freeze" / "source-artifacts-v2.json"
TACTIC = "by first | assumption | rfl | simp | omega"
MAX_OUTPUT = 8 * 1024 * 1024
MAX_RSS = 12 * 1024**3
DEFAULT_TIMEOUT = 600
RUNNER_LOCK = CHANGE / "evidence" / "feasibility-runner-lock-v1.json"


class BaselineError(RuntimeError):
    """The frozen batch or its execution evidence is invalid."""


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BaselineError(f"expected JSON object: {path}")
    return value


def _capture_source_binding_valid(
    capture: dict[str, Any], capture_rc: int, expected_source_digest: str,
) -> bool:
    """Reject a claimed success unless it is bound to the attempted source."""
    if capture.get("status") != "captured":
        return False
    capture_data = capture.get("capture")
    capture_source = capture_data.get("source") if isinstance(capture_data, dict) else None
    if (capture_rc != 0 or not isinstance(capture_source, dict)
        or capture_source.get("digest") != expected_source_digest):
        raise BaselineError("capture claims success without a valid expected-source binding")
    return True


def _case_module(case: dict[str, Any]) -> tuple[str, str]:
    source = case.get("leanSource")
    if not isinstance(source, str) or "#" not in source:
        raise BaselineError("case has no qualified Lean source")
    rel, declaration = source.split("#", 1)
    path = Path(rel)
    if path.parts[0] in {"lean", "mathlib"}:
        path = Path(*path.parts[1:])
    module = path.with_suffix("").as_posix().replace("/", ".")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+", declaration):
        raise BaselineError("case source locator does not name a qualified Lean declaration")
    return module, rel


def _acceptance_inputs(
    runtime_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    policy = _load_json(POLICY)
    corpus = _load_json(CASES)
    artifacts = _load_json(ARTIFACTS)
    if digest(CASES) != policy["corpus"]["sha256"]:
        raise BaselineError("accepted corpus bytes differ from the frozen baseline policy")
    accepted = _load_json(CHANGE / "evidence" / "runtime-freeze" / "acceptance-v3.json")
    if accepted.get("status") != "accepted" or accepted.get("manifestIdentity") != policy["runtime"]["manifestIdentity"]:
        raise BaselineError("runtime acceptance differs from the frozen baseline policy")
    bundle = REPO / ".codex/state/pitfall-runtime/bundles/baseline-v3"
    if not bundle.is_dir():
        raise BaselineError(f"pinned runtime bundle is unavailable: {bundle}")
    cases = corpus.get("cases")
    if not isinstance(cases, list):
        raise BaselineError("corpus has no case list")
    selected = [c for c in cases if c.get("caseId") in policy["corpus"]["orderedCases"]]
    observed = [c.get("caseId") for c in selected]
    if observed != policy["corpus"]["orderedCases"]:
        raise BaselineError(f"fixed feasibility case order changed: {observed}")
    if any(c.get("family") != "assumption-feasibility" for c in selected):
        raise BaselineError("fixed batch contains a case from another family")
    if digest(CHANGE / "evidence" / "runtime-freeze" / "acceptance-v3.json") != policy["runtime"]["acceptanceSha256"]:
        raise BaselineError("runtime acceptance record changed")
    if digest(ARTIFACTS) != policy["runtime"]["sourceArtifactInventorySha256"]:
        raise BaselineError("source/artifact inventory changed")
    lock = _load_json(RUNNER_LOCK)
    if lock.get("policySha256") != digest(POLICY):
        raise BaselineError("frozen policy differs from the runner lock")
    if lock.get("runnerSha256") != digest(Path(__file__)):
        raise BaselineError("runner bytes differ from the frozen runner lock")
    if (policy["automaticRoute"]["tacticScript"] != TACTIC
        or policy["limits"]["secondsPerCaseIncludingPreparation"] != DEFAULT_TIMEOUT
        or policy["limits"]["maxRssBytesPerProcessTree"] != MAX_RSS
        or policy["limits"]["maxOutputBytesPerProcess"] != MAX_OUTPUT):
        raise BaselineError("executed tactic or resource bounds differ from frozen policy")
    return policy, {c["caseId"]: c for c in selected}, {
        c["caseId"]: c for c in cases
    }, artifacts


def _artifact_entry(artifacts: dict[str, Any], relative: str) -> dict[str, Any]:
    rows = [row for row in artifacts.get("pairs", []) if row.get("source") == relative]
    if len(rows) != 1:
        raise BaselineError(f"source has no unique accepted artifact mapping: {relative}")
    return rows[0]


def _prepare_case(
    case: dict[str, Any], runtime_root: Path, workspace: Path,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    module, source_rel = _case_module(case)
    # Corpus CoreCases files live under lean/CoreCases; runtime custody stores
    # their exact byte-identical counterparts under core-fixture/CoreCases.
    source_path = Path(source_rel)
    if source_path.parts[0] == "lean":
        runtime_fixture = "core-fixture"
        runtime_relative = Path(*source_path.parts[1:])
    else:
        runtime_fixture = "mathlib-fixture"
        runtime_relative = Path(*source_path.parts[1:])
    runtime_source_rel = f"{runtime_fixture}/{runtime_relative.as_posix()}"
    runtime_artifact_rel = (
        f"{runtime_fixture}/.lake/build/lib/lean/" + module.replace(".", "/") + ".olean"
    )
    pair = _artifact_entry(artifacts, runtime_source_rel)
    source_in_corpus = CHANGE / "evidence" / "corpus" / source_rel
    source_in_runtime = runtime_root / runtime_source_rel
    artifact = runtime_root / runtime_artifact_rel
    if digest(source_in_corpus) != pair["sourceSha256"] or digest(source_in_runtime) != pair["sourceSha256"]:
        raise BaselineError(f"selected source bytes do not match accepted source identity: {source_rel}")
    if digest(artifact) != pair["artifactSha256"]:
        raise BaselineError(f"selected compiled artifact is stale or changed: {runtime_artifact_rel}")

    shared_source_rel = "core-fixture/Pitfalls.lean"
    shared_artifact_rel = "core-fixture/.lake/build/lib/lean/Pitfalls.olean"
    shared_pair = _artifact_entry(artifacts, shared_source_rel)
    shared_source = runtime_root / shared_source_rel
    shared_artifact = runtime_root / shared_artifact_rel
    if digest(shared_source) != shared_pair["sourceSha256"]:
        raise BaselineError("shared Pitfalls source differs from the accepted artifact inventory")
    if digest(shared_artifact) != shared_pair["artifactSha256"]:
        raise BaselineError("shared Pitfalls artifact differs from the accepted artifact inventory")

    workspace.mkdir(parents=True, exist_ok=False)
    for relative in ("lean-toolchain", "Pitfalls.lean", "lakefile.toml"):
        shutil.copy2(runtime_root / "core-fixture" / relative, workspace / relative)
    with (workspace / "lakefile.toml").open("a", encoding="utf-8") as stream:
        stream.write('\n[[lean_lib]]\nname = "CoreCases"\n')
    source_target = workspace / source_rel.removeprefix("lean/")
    source_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_in_runtime, source_target)
    library = workspace / ".lake/build/lib/lean"
    case_artifact_target = library / (module.replace(".", "/") + ".olean")
    case_artifact_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(artifact, case_artifact_target)
    shutil.copy2(
        runtime_root / "core-fixture/.lake/build/lib/lean/Pitfalls.olean",
        library / "Pitfalls.olean",
    )

    subprocess.run(["/usr/bin/git", "init", "-q", str(workspace)], check=True)
    tracked = ["lakefile.toml", "lean-toolchain", "Pitfalls.lean", source_target.relative_to(workspace).as_posix()]
    subprocess.run(["/usr/bin/git", "-C", str(workspace), "add", *tracked], check=True)

    goal = case["comparisonGoal"].get("formalClaim")
    if not isinstance(goal, str) or not goal.strip():
        raise BaselineError("case lacks its accepted formal claim")
    # The worker sees only a formal target and module. It does not
    # receive case role, expected outcome, prose label, oracle, or validation.
    request = {"module": module, "goal": goal}
    return {
        "request": request,
        "corpusSource": source_rel,
        "corpusSourceSha256": digest(source_in_corpus),
        "runtimeSource": runtime_source_rel,
        "runtimeSourceSha256": pair["sourceSha256"],
        "runtimeArtifact": runtime_artifact_rel,
        "runtimeArtifactSha256": pair["artifactSha256"],
        "copiedArtifact": case_artifact_target.relative_to(workspace).as_posix(),
        "sharedSource": shared_source_rel,
        "sharedSourceSha256": shared_pair["sourceSha256"],
        "sharedArtifact": shared_artifact_rel,
        "sharedArtifactSha256": shared_pair["artifactSha256"],
        "trackedInputs": tracked,
    }


def _excluded_modules(cases: dict[str, dict[str, Any]], selected_id: str) -> list[str]:
    result = []
    for case_id, case in cases.items():
        if case_id == selected_id:
            continue
        module, _ = _case_module(case)
        result.append(module)
    return list(dict.fromkeys([*result, "CoreCases", "Validation"]))


def _request_worker(
    runtime_root: Path, workspace: Path, output: Path, request: dict[str, Any],
    excluded: list[str], bundle: Path, identity: str, deadline: float,
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    request_path = output / "operational-input.json"
    request_path.write_text(json.dumps(request, sort_keys=True) + "\n", encoding="utf-8")
    excluded_path = output / "excluded-modules.json"
    excluded_path.write_text(json.dumps(excluded, sort_keys=True) + "\n", encoding="utf-8")
    command = [
        sys.executable,
        str(CHANGE / "scripts/runtime_custody.py"),
        "exec", "--bundle", str(bundle), "--identity", identity,
        "--root", str(runtime_root), "--profile", "python", "--",
        "-I", "-B", str(Path(__file__).resolve()), "worker",
        str(runtime_root), str(workspace), str(output), str(request_path), str(excluded_path),
        str(deadline),
    ]
    started = time.monotonic()
    proc = subprocess.Popen(
        command, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=max(deadline - time.monotonic(), 0.01))
    except subprocess.TimeoutExpired:
        timed_out = True
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGTERM)
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate()
    wall = time.monotonic() - started
    receipt = {
        "command": command,
        "returnCode": proc.returncode,
        "wallSeconds": wall,
        "stdout": stdout,
        "stderr": stderr,
        "timedOut": timed_out,
        "terminal": True,
    }
    (output / "launcher-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if timed_out:
        raise BaselineError(f"case deadline expired; worker process tree stopped; see {output / 'launcher-receipt.json'}")
    if proc.returncode != 0:
        raise BaselineError(f"pinned runtime worker failed; see {output / 'launcher-receipt.json'}")
    try:
        result = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise BaselineError("pinned runtime worker did not return its evidence index") from error
    result["launcherReceipt"] = {
        "returnCode": proc.returncode,
        "wallSeconds": wall,
        "stdoutSha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "stderrSha256": hashlib.sha256(stderr.encode()).hexdigest(),
    }
    report_path = Path(result["report"])
    if not report_path.is_file():
        raise BaselineError("worker report path is missing")
    result["reportSha256"] = digest(report_path)
    result["reportData"] = _load_json(report_path)
    result["evidenceFiles"] = [
        {"path": path.relative_to(output).as_posix(), "sha256": digest(path)}
        for path in sorted(output.rglob("*")) if path.is_file()
    ]
    return result


def run_host(args: argparse.Namespace) -> int:
    runtime_root = args.runtime_root.resolve(strict=True)
    policy, cases, all_cases, artifacts = _acceptance_inputs(runtime_root)
    bundle = REPO / ".codex/state/pitfall-runtime/bundles/baseline-v3"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    records = []
    batch_started = time.monotonic()
    for index, case_id in enumerate(policy["corpus"]["orderedCases"], start=1):
        case = cases[case_id]
        case_root = output / f"case-{index:02d}"
        workspace = case_root / "workspace"
        result_dir = case_root / "results"
        case_started = time.monotonic()
        deadline = case_started + DEFAULT_TIMEOUT
        try:
            prepared = _prepare_case(case, runtime_root, workspace, artifacts)
            prep_seconds = time.monotonic() - case_started
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BaselineError(f"case preparation consumed its entire budget: {case_id}")
            worker = _request_worker(
                runtime_root, workspace, result_dir, prepared["request"],
                _excluded_modules(all_cases, case_id), bundle, policy["runtime"]["manifestIdentity"],
                deadline,
            )
            prepared["attemptSources"] = [
                {"path": attempt["sourcePath"],
                 "sha256": digest(workspace / attempt["sourcePath"])}
                for attempt in worker["reportData"]["attempts"]
            ]
        except Exception as error:
            case_root.mkdir(parents=True, exist_ok=True)
            terminal = {
                "caseId": case_id, "ordinal": index, "status": "qualification-failed",
                "errorType": type(error).__name__, "error": str(error),
                "elapsedSeconds": time.monotonic() - case_started,
                "deadlineSeconds": DEFAULT_TIMEOUT,
                "partialEvidenceFiles": [
                    {"path": p.relative_to(case_root).as_posix(), "sha256": digest(p)}
                    for p in sorted(case_root.rglob("*")) if p.is_file()
                ],
            }
            (case_root / "case-terminal.json").write_text(json.dumps(terminal, indent=2) + "\n")
            failed_index = {
                "schema": "ladon-pitfall-family-baseline-index-v1",
                "policyId": policy["policyId"], "policySha256": digest(POLICY),
                "runnerSha256": digest(Path(__file__)), "runnerLockSha256": digest(RUNNER_LOCK),
                "corpusSha256": policy["corpus"]["sha256"],
                "runtimeIdentity": policy["runtime"]["manifestIdentity"],
                "status": "qualification-interrupted",
                "completedCases": [row["caseId"] for row in records],
                "failedCase": f"case-{index:02d}/case-terminal.json",
                "failedCaseSha256": digest(case_root / "case-terminal.json"),
                "batchElapsedSeconds": time.monotonic() - batch_started,
                "cases": [{"ordinal": row["ordinal"], "caseId": row["caseId"],
                           "record": f"case-{row['ordinal']:02d}/case-record.json",
                           "recordSha256": digest(output / f"case-{row['ordinal']:02d}/case-record.json"),
                           "totalElapsedSeconds": row["totalElapsedSeconds"]} for row in records],
            }
            (output / "acceptance-index.json").write_text(json.dumps(failed_index, indent=2) + "\n")
            raise
        total_elapsed = time.monotonic() - case_started
        record = {
            "ordinal": index,
            "caseId": case_id,
            "preparationSeconds": prep_seconds,
            "totalElapsedSeconds": total_elapsed,
            "inputCustody": prepared,
            "worker": worker,
        }
        (case_root / "case-record.json").write_text(json.dumps(record, indent=2) + "\n")
        records.append(record)
    index_path = output / "acceptance-index.json"
    index = {
        "schema": "ladon-pitfall-family-baseline-index-v1",
        "policyId": policy["policyId"],
        "policySha256": digest(POLICY),
        "runnerSha256": digest(Path(__file__)),
        "runnerLockSha256": digest(RUNNER_LOCK),
        "corpusSha256": policy["corpus"]["sha256"],
        "runtimeIdentity": policy["runtime"]["manifestIdentity"],
        "status": "pending-independent-adjudication",
        "orderedCases": [row["caseId"] for row in records],
        "batchElapsedSeconds": time.monotonic() - batch_started,
        "cases": [
            {"ordinal": row["ordinal"], "caseId": row["caseId"],
             "record": f"case-{row['ordinal']:02d}/case-record.json",
             "recordSha256": digest(output / f"case-{row['ordinal']:02d}/case-record.json"),
             "totalElapsedSeconds": row["totalElapsedSeconds"]}
            for row in records
        ],
    }
    index_path.write_text(json.dumps(index, indent=2) + "\n")
    print(index_path)
    return 0


def _diagnostic_class(result: dict[str, Any], module: str) -> str:
    if result.get("returnCode") == 0:
        return "imported"
    text = result.get("stdout", "") + result.get("stderr", "")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    errors = [line.split("error:", 1)[1].strip() for line in lines if "error:" in line]
    if result.get("returnCode") != 1 or len(errors) != 1 or not lines or "error:" not in lines[0]:
        return "unrelated-failure"
    expected_file = re.fullmatch(
        r"object file '[^'\n]+' of module " + re.escape(module) + r" does not exist",
        errors[0],
    )
    prefix = module.split(".", 1)[0]
    expected_prefix = errors[0] == f"unknown module prefix '{prefix}'"
    if expected_file and len(lines) == 1:
        return "module-unavailable"
    if expected_prefix:
        banner = f"No directory '{prefix}' or file '{prefix}.olean' in the search path entries:"
        if len(lines) >= 3 and lines[1] == banner and all(Path(line).is_absolute() for line in lines[2:]):
            return "module-unavailable"
    return "unrelated-failure"


def _probe_import(module: str, repo: Path, lean: Path, env: dict[str, str],
                  output: Path, timeout: float) -> dict[str, Any]:
    from ladon.process_supervisor import run_bounded_target_process

    source = output / ("probe-" + hashlib.sha256(module.encode()).hexdigest()[:12] + ".lean")
    source.write_text(f"import {module}\n", encoding="utf-8")
    measured = run_bounded_target_process(
        [str(lean), str(source)], cwd=repo, env=env,
        timeout_seconds=max(timeout, 0.1), max_output_bytes=MAX_OUTPUT,
        max_rss_bytes=MAX_RSS, observe_resources=True,
    )
    return {
        "module": module,
        "returnCode": measured.returncode,
        "stdout": measured.stdout,
        "stderr": measured.stderr,
        "elapsedSeconds": measured.elapsed_seconds,
        "peakRssBytes": measured.peak_rss_bytes,
        "timedOut": measured.timed_out,
        "outputLimited": measured.output_limited,
        "memoryLimited": measured.memory_limited,
        "diagnosticClass": _diagnostic_class(
            {"returnCode": measured.returncode, "stdout": measured.stdout,
             "stderr": measured.stderr}, module,
        ),
    }


def run_worker(runtime_root: Path, repo: Path, output: Path,
               request_path: Path, excluded_path: Path, deadline: float) -> int:
    runtime_root, repo, output = runtime_root.resolve(), repo.resolve(), output.resolve()
    started = time.monotonic()
    if deadline <= started:
        raise BaselineError("case deadline expired before worker initialization")
    request = _load_json(request_path)
    excluded = json.loads(excluded_path.read_text(encoding="utf-8"))
    if set(request) != {"module", "goal"} or not isinstance(excluded, list):
        raise BaselineError("operational request contains an unexpected field")
    sys.path.insert(0, str(runtime_root / "src"))
    from ladon.entrypoint import main
    from ladon.lean_toolchain import resolve_toolchain_context

    lean = runtime_root / "lean-core/bin/lean"
    lake = runtime_root / "lean-core/bin/lake"
    context = resolve_toolchain_context(
        repo, lake_path=lake, lean_path=lean, selection_mode="explicit",
    )
    if set(context.library_roots) != {repo / ".lake/build/lib/lean"}:
        raise BaselineError("operational Lean path is not the selected-case overlay")
    if any((context.library_roots[0] / (module.replace(".", "/") + ".olean")).exists()
           for module in excluded):
        raise BaselineError("forbidden module artifact is present before operational execution")
    goal = request["goal"]
    module = request["module"]
    output.mkdir(parents=True, exist_ok=True)
    probes_dir = output / "imports"
    probes_dir.mkdir()
    env = dict(context.environment)
    probe_records = []
    # Selected positive import and exact negative diagnostics occur in the
    # same restricted Lean path used by the operational command.
    for requested, label in [(module, "selected"), *[(m, "excluded") for m in excluded]]:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BaselineError("case deadline expired during isolation checks")
        row = _probe_import(requested, repo, lean, env, probes_dir, remaining)
        probe_records.append({"role": label, **row})
        (output / "isolation-probes.json").write_text(
            json.dumps(probe_records, indent=2) + "\n", encoding="utf-8",
        )
        if label == "selected" and row["diagnosticClass"] != "imported":
            raise BaselineError(
                f"selected module failed to import: {requested}: {row['diagnosticClass']}"
            )
        if label == "excluded" and row["diagnosticClass"] != "module-unavailable":
            raise BaselineError(
                f"excluded module was not proven unavailable: {requested}: "
                f"{row['diagnosticClass']} (exit {row['returnCode']})"
            )

    # The same guard must reject an unrelated elaboration failure.
    unrelated = probes_dir / "unrelated-failure.lean"
    unrelated.write_text("def notAnImport : Nat := noSuchIdentifier\n", encoding="utf-8")
    from ladon.process_supervisor import run_bounded_target_process

    bad = run_bounded_target_process(
        [str(lean), str(unrelated)], cwd=repo, env=env,
        timeout_seconds=max(deadline - time.monotonic(), 0.1),
        max_output_bytes=MAX_OUTPUT, max_rss_bytes=MAX_RSS, observe_resources=True,
    )
    rejected_unrelated = _diagnostic_class(
        {"returnCode": bad.returncode, "stdout": bad.stdout, "stderr": bad.stderr},
        "Validation",
    ) == "unrelated-failure"
    (output / "unrelated-failure-receipt.json").write_text(json.dumps({
        "returnCode": bad.returncode, "stdout": bad.stdout, "stderr": bad.stderr,
        "elapsedSeconds": bad.elapsed_seconds, "peakRssBytes": bad.peak_rss_bytes,
        "timedOut": bad.timed_out, "memoryLimited": bad.memory_limited,
        "outputLimited": bad.output_limited, "acceptedAsIsolation": rejected_unrelated,
    }, indent=2) + "\n", encoding="utf-8")
    if not rejected_unrelated:
        raise BaselineError("isolation guard accepted an unrelated compiler failure")

    # Inject an actually available excluded artifact. The same guard must now
    # refuse to call the module unavailable.
    injected_module = excluded[0]
    # All corpus case sources use CoreCases/<slug>.lean.
    frozen_olean = runtime_root / "core-fixture/.lake/build/lib/lean" / (injected_module.replace(".", "/") + ".olean")
    injected_olean = context.library_roots[0] / (injected_module.replace(".", "/") + ".olean")
    injected_olean.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(frozen_olean, injected_olean)
    try:
        injected = _probe_import(injected_module, repo, lean, env, probes_dir,
                                 max(deadline - time.monotonic(), 0.1))
        guard_detected_injection = injected["diagnosticClass"] == "imported" and injected["returnCode"] == 0
        (output / "injected-module-receipt.json").write_text(json.dumps({
            **injected, "acceptedAsAvailable": guard_detected_injection,
        }, indent=2) + "\n", encoding="utf-8")
    finally:
        injected_olean.unlink(missing_ok=True)
    if not guard_detected_injection:
        raise BaselineError("isolation guard accepted the deliberately exposed forbidden module")

    rows = []
    compiled_rows = []
    for polarity, proposition, output_path, term in (
        ("positive", f"({goal})", output / "capture-positive.json", output / "complete-positive.json"),
        ("negative", f"¬ ({goal})", output / "capture-negative.json", output / "complete-negative.json"),
    ):
        probe_module = "Probe"
        # Put the selected polarity first and retain the other polarity as a
        # following incomplete example. Lean's frontend associates the first
        # target's tactic InfoTree when it elaborates the following command.
        following = f"¬ ({goal})" if polarity == "positive" else goal
        source_text = (
            f"import {module}\n\nexample : {proposition} := by\n  skip\n\n"
            f"example : {following} := by\n  skip\n"
        )
        probe_dir = repo / f"attempt-{polarity}"
        probe_dir.mkdir(exist_ok=False)
        probe_source = probe_dir / "Probe.lean"
        probe_source.write_text(source_text, encoding="utf-8")
        source_digest = "sha256:" + hashlib.sha256(source_text.encode()).hexdigest()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BaselineError("case deadline expired before goal attempt")
        common = [
            "--repo-root", str(repo), "--toolchain-mode", "explicit",
            "--lean-path", str(lean), "--lake-path", str(lake),
            "--timeout-seconds", str(remaining),
            "--max-rss-mib", str(MAX_RSS // (1024**2)),
            "--max-output-mib", str(MAX_OUTPUT // (1024**2)),
            "--format", "json",
        ]
        cap_args = [
            "proof-search", "goal", "capture", *common,
            "--source", probe_source.relative_to(repo).as_posix(), "--module", probe_module,
            "--line", "4", "--column", "2", "--goal-ordinal", "0",
            "--expected-source-digest", source_digest, "--output", str(output_path),
        ]
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            capture_rc = main(cap_args)
        capture_stdout, capture_stderr = stdout.getvalue(), stderr.getvalue()
        (output / f"{polarity}-cli.json").write_text(json.dumps({
            "captureArgv": cap_args,
            "captureReturnCode": capture_rc, "captureStdout": capture_stdout,
            "captureStderr": capture_stderr,
        }, indent=2) + "\n", encoding="utf-8")
        if not output_path.is_file():
            raise BaselineError(f"capture produced no terminal report for {polarity}")
        capture = _load_json(output_path)
        capture_bound = _capture_source_binding_valid(capture, capture_rc, source_digest)
        if capture_rc != 0 or capture.get("status") != "captured" or not capture_bound:
            rows.append({
                "polarity": polarity, "goal": proposition,
                "sourcePath": probe_source.relative_to(repo).as_posix(),
                "sourceDigest": source_digest,
                "capturePath": output_path.name, "captureSha256": digest(output_path),
                "captureStatus": capture.get("status"), "captureReturnCode": capture_rc,
                "captureDiagnostic": capture.get("diagnostic"),
                "sourceBindingValid": capture_bound,
                "attemptState": "unresolved", "proofEstablished": False,
            })
            (output / "attempt-progress.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
            continue
        # Current helper emits a large compiled inventory; summarize its rows
        # after binding their complete digest to keep the acceptance index small.
        compiled = capture.get("capture", {}).get("environment", {}).get("compiledInventory", {})
        compiled_rows = compiled.get("modules", []) if isinstance(compiled, dict) else []
        visible_forbidden = [row.get("module") for row in compiled_rows if row.get("module") in excluded]
        if visible_forbidden:
            raise BaselineError(f"forbidden modules entered the capture environment: {visible_forbidden}")
        rows.append({
            "polarity": polarity,
            "goal": proposition,
            "sourcePath": probe_source.relative_to(repo).as_posix(),
            "sourceDigest": source_digest,
            "capturePath": output_path.name,
            "captureSha256": digest(output_path),
            "captureId": capture.get("capture", {}).get("captureId"),
            "captureStatus": capture.get("status"),
            "compiledModuleCount": len(compiled_rows),
            "compiledForbiddenModules": visible_forbidden,
            "captureElapsedSeconds": capture.get("resourceAccounting", {}).get("elapsedSeconds"),
        })
        # Re-read remaining time after capture. The same fixed generic script
        # is attempted against every positive and negative goal.
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BaselineError("case deadline expired before completion attempt")
        complete_common = [
            "--repo-root", str(repo), "--toolchain-mode", "explicit",
            "--lean-path", str(lean), "--lake-path", str(lake),
            "--timeout-seconds", str(remaining),
            "--max-rss-mib", str(MAX_RSS // (1024**2)),
            "--max-output-mib", str(MAX_OUTPUT // (1024**2)),
            "--format", "json",
        ]
        complete_args = [
            "proof-search", "goal", "complete", *complete_common,
            "--capture-file", str(output_path), "--term", TACTIC,
            "--output", str(term),
        ]
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            complete_rc = main(complete_args)
        completion_stdout, completion_stderr = stdout.getvalue(), stderr.getvalue()
        (output / f"{polarity}-cli.json").write_text(json.dumps({
            "captureArgv": cap_args, "captureReturnCode": capture_rc,
            "captureStdout": capture_stdout, "captureStderr": capture_stderr,
            "completionArgv": complete_args, "completionReturnCode": complete_rc,
            "completionStdout": completion_stdout, "completionStderr": completion_stderr,
        }, indent=2) + "\n", encoding="utf-8")
        if not term.is_file():
            rows[-1].update({"completionStatus": "unresolved", "completionReturnCode": complete_rc,
                             "completionDiagnostic": "completion produced no terminal report",
                             "attemptState": "unresolved", "proofEstablished": False})
            (output / "attempt-progress.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
            continue
        completion = _load_json(term)
        rows[-1].update({
            "completionPath": term.name,
            "completionSha256": digest(term),
            "completionStatus": completion.get("status"),
            "completionReturnCode": complete_rc,
            "completionDiagnostic": completion.get("diagnostic"),
            "replay": completion.get("replay"),
            "trust": completion.get("trust"),
            "resourceAccounting": completion.get("resourceAccounting"),
            "proofEstablished": (
                completion.get("status") == "completed"
                and completion.get("trust", {}).get("accepted") is True
                and completion.get("replay", {}).get("status") == "accepted"
                and "sorryAx" not in completion.get("trust", {}).get("observedAxioms", [])
            ),
            "attemptState": "complete",
        })
        (output / "attempt-progress.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

    elapsed = time.monotonic() - started
    if time.monotonic() > deadline:
        raise BaselineError("case deadline expired before terminal worker report")
    positive = next(row["proofEstablished"] for row in rows if row["polarity"] == "positive")
    negative = next(row["proofEstablished"] for row in rows if row["polarity"] == "negative")
    formal_outcome = (
        "conflicting-checked-proofs" if positive and negative
        else "witnessed" if positive
        else "inconsistent" if negative
        else "unresolved"
    )
    report = {
        "schema": "ladon-feasibility-baseline-case-v1",
        "operationalInput": request,
        "tacticScript": TACTIC,
        "attempts": rows,
        "formalOutcome": formal_outcome,
        "isolation": {
            "libraryRoots": [str(path) for path in context.library_roots],
            "selectedAndExcludedProbes": probe_records,
            "unrelatedFailureRejected": rejected_unrelated,
            "forbiddenModuleInjectionDetected": guard_detected_injection,
            "injectedModule": injected_module,
            "standardLibraryModuleCount": len(compiled_rows),
        },
        "elapsedSeconds": elapsed,
        "status": "attempts-complete",
        "interpretation": "Only independently replayed, trust-accepted proof outcomes can establish the corresponding formal proposition. All other outcomes are unresolved.",
    }
    (output / "worker-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(output / "worker-report.json"), "elapsedSeconds": elapsed}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    host = sub.add_parser("run")
    host.add_argument("--runtime-root", type=Path, required=True)
    host.add_argument("--output", type=Path, required=True)
    worker = sub.add_parser("worker")
    worker.add_argument("runtime_root", type=Path)
    worker.add_argument("repo", type=Path)
    worker.add_argument("output", type=Path)
    worker.add_argument("request", type=Path)
    worker.add_argument("excluded", type=Path)
    worker.add_argument("deadline", type=float)
    args = parser.parse_args()
    if args.mode == "worker":
        try:
            return run_worker(args.runtime_root, args.repo, args.output, args.request, args.excluded, args.deadline)
        except Exception as error:
            args.output.mkdir(parents=True, exist_ok=True)
            (args.output / "worker-terminal.json").write_text(json.dumps({
                "status": "worker-failed", "errorType": type(error).__name__,
                "error": str(error), "observedAtMonotonic": time.monotonic(),
            }, indent=2) + "\n")
            print(json.dumps({"workerError": type(error).__name__, "message": str(error)}), file=sys.stderr)
            return 1
    try:
        return run_host(args)
    except (BaselineError, OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"baseline refused: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
