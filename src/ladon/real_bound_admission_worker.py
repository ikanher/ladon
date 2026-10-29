"""Compile the fixed family separately, then replay exact source-owned law goals."""

import hashlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

from ladon.correspondence_check import _check_goal
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_contract_io import _decode
from ladon.proof_contract_payloads import closed
from ladon.proof_slice import pinned_toolchain
from ladon.real_bound_admission import FAMILY_SOURCE
from ladon.real_bound_admission_check import checker_identity, verify_plan_source
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES, memory_limit_message
from ladon.semantic_lean_execution import prepare_direct_lean_execution

MAX_BYTES = 8 * 1024**2


def _workspace(job, root, context):
    workspace = Path(job["workspace"]).resolve(strict=True)
    if list(workspace.iterdir()):
        raise ValueError("prefix-law workspace must be empty and request-owned")
    (workspace / "lean-toolchain").write_bytes((root / "lean-toolchain").read_bytes())
    (workspace / ".lake/build/lib/lean").mkdir(parents=True)
    for index, library in enumerate(context.library_roots):
        if (library / "LadonRealBound.olean").exists():
            raise ValueError("selected workspace already contains the reserved family module")
        target = workspace / f".lake/packages/import{index}/.lake/build/lib/lean"
        target.parent.mkdir(parents=True)
        target.symlink_to(library, target_is_directory=True)
    family = FAMILY_SOURCE.read_bytes()
    if "sha256:" + hashlib.sha256(family).hexdigest() != job["plan"]["familySourceDigest"]:
        raise ValueError("stale prefix-family source")
    (workspace / "LadonRealBound.lean").write_bytes(family)
    return workspace


def _compile(workspace, job):
    execution = prepare_direct_lean_execution(
        workspace, None, pinned_toolchain(workspace), require_compiled_module=False)
    remaining = job["deadlineMonotonic"] - time.monotonic()
    if remaining <= 0:
        raise ValueError("shared prefix admission deadline expired")
    return run_bounded_target_process(
        [*execution.command, "-o", ".lake/build/lib/lean/LadonRealBound.olean", "LadonRealBound.lean"],
        cwd=workspace, env=execution.environment, timeout_seconds=min(60, remaining),
        max_output_bytes=MAX_BYTES, max_rss_bytes=DEFAULT_MAX_RSS_BYTES)


def _accepted(actual):
    completion = actual.get("completion", {})
    capture = actual.get("capture", {}).get("capture", {})
    trust = completion.get("trust", {})
    return (actual.get("status") == "supported" and completion.get("status") == "completed"
            and completion.get("replay", {}).get("status") == "accepted"
            and trust.get("accepted") is True and trust.get("coverage") == "complete"
            and not set(trust.get("observedAxioms", [])) - {"propext", "Classical.choice", "Quot.sound"}
            and capture.get("goal", {}).get("typeStructural")
            == actual.get("typedSubject", {}).get("subject", {}).get("structural"))


def _inventory(actual):
    return actual["capture"]["capture"]["environment"]["compiledInventory"]


def _verify_inventory(inventory):
    from ladon._source_goal_inventory import verify_inventory

    rows = inventory["modules"]
    files = {row["module"]: Path(row["path"]) for row in rows}
    environment = {"payload": {"compiledModules": [
        {"module": row["module"], "digest": row["digest"]} for row in rows]}}
    verify_inventory(files, environment, inventory)


def _check_goals(job, root, source, workspace, result):
    inventory = None
    for goal in job["plan"]["goals"]:
        if time.monotonic() >= job["deadlineMonotonic"]:
            return
        term = job["terms"][goal["id"]]
        # The family import precedes target commands; its meaning was compiled in isolation.
        actual = _check_goal(goal["proposition"], term, workspace,
                             b"import LadonRealBound\n" + source, {}, pinned_toolchain(workspace))
        result["checks"].append({"goal": goal, "term": term, "evidence": actual})
        if not _accepted(actual):
            return
        current = _inventory(actual)
        if inventory is not None and current != inventory:
            raise ValueError("compiled inventory changed between prefix-law checks")
        inventory = current
        _verify_inventory(inventory)
        verify_plan_source(root, job["plan"])
    if len(result["checks"]) == 3:
        result["status"] = "checked-laws"


def _compute(job):
    closed(job, {"version", "root", "workspace", "plan", "terms", "deadlineMonotonic",
                 "checkerIdentity"}, "prefix-law job")
    if job["version"] != 1:
        raise ValueError("unsupported prefix-law worker version")
    if job["checkerIdentity"] != checker_identity():
        raise ValueError("stale prefix-law checker")
    root, source, context = verify_plan_source(job["root"], job["plan"])
    workspace = _workspace(job, root, context)
    compiled = _compile(workspace, job)
    result = {"schema": "ladon-prefix-law-check-v1", "status": "unresolved",
              "plan": job["plan"], "admission": "unresolved", "contract": None,
              "checkerIdentity": job["checkerIdentity"],
              "checks": [], "familyCompilation": asdict(compiled),
              "limitations": ["observed-application-binding-unchecked",
                              "historical-receipts-require-fresh-check",
                              "no-composition-or-derivative-interpretation"]}
    if compiled.succeeded:
        _check_goals(job, root, source, workspace, result)
    elif compiled.memory_limited:
        result["diagnostic"] = memory_limit_message(DEFAULT_MAX_RSS_BYTES, compiled.peak_rss_bytes)
    verify_plan_source(root, job["plan"])
    if job["checkerIdentity"] != checker_identity():
        raise ValueError("prefix-law checker changed during execution")
    return result


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("prefix-law worker input exceeds 8 MiB")
        result = _compute(_decode(raw))
        encoded = json.dumps({"status": "completed", "result": result, "diagnostic": None})
        if len(encoded.encode()) > MAX_BYTES:
            raise ValueError("prefix-law evidence exceeds 8 MiB")
        print(encoded)
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        print(json.dumps({"status": "rejected", "result": None, "diagnostic": str(error)[:500]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
