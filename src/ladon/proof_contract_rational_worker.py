"""Bounded Lean completion worker for one regenerated rational proposition."""
from __future__ import annotations

import hashlib
import shutil
import tempfile
import time
from pathlib import Path

from ladon.lean_toolchain import (
    LeanToolchainError,
    resolve_toolchain_context,
    verify_toolchain_identities,
)
from ladon.proof_contract_payloads import closed
from ladon.proof_contract_rational_check import _digest_text
from ladon.proof_contract_rational_workspace import rational_workspace_identity
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal

_JOB_KEYS = {
    "version", "operation", "workspaceRoot", "workspaceIdentity", "goalId",
    "goal", "goalDigest", "term", "binding", "deadlineMonotonic", "limits",
}
_MAX_GOAL_BYTES = 256 * 1024


def _compute(job):
    closed(job, _JOB_KEYS, "rational branch check worker job")
    if job["version"] != 1 or job["operation"] != "check-rational-branch-goal":
        raise ValueError("unknown rational branch check operation")
    _validate_job(job)
    if time.monotonic() >= job["deadlineMonotonic"]:
        return _result("incomplete", "timeout", "Shared rational-branch deadline expired before Lean setup.")
    resolved = _resolve_workspace(job)
    if isinstance(resolved, dict):
        return resolved
    workspace, workspace_toolchain, identity = resolved
    with tempfile.TemporaryDirectory(prefix="ladon-rational-branch-") as directory:
        root = Path(directory)
        prepared = _prepare_isolated_workspace(job, root, workspace,
                                               workspace_toolchain, identity)
        if isinstance(prepared, dict):
            return prepared
        context, _source, source_digest, target_positions, receipt = prepared
        captured, stop = _capture_goal(job, root, context, source_digest, target_positions)
        if stop is not None:
            return stop
        return _complete_goal(job, root, context, source_digest, receipt, captured)


def _resolve_workspace(job):
    workspace = Path(job["workspaceRoot"]).resolve(strict=True)
    toolchain = resolve_toolchain_context(workspace, selection_mode="ambient")
    identity = rational_workspace_identity(
        workspace, toolchain, job["deadlineMonotonic"], job["limits"])
    if identity.get("status") != "resolved":
        return _result(identity.get("reason", "incomplete"),
                       "workspace-executable-identity",
                       identity.get("diagnostic", "Pinned Lean executable identity is unavailable."),
                       {"processReceipt": identity.get("processReceipt")})
    if identity["workspaceIdentity"] != job["workspaceIdentity"]:
        return _result("stale", "workspace-context-changed",
                       "Selected Lean workspace context changed after planning.")
    return workspace, toolchain, identity


def _prepare_isolated_workspace(job, root, workspace, workspace_toolchain, identity):
    shutil.copyfile(workspace / "lean-toolchain", root / "lean-toolchain")
    lake_state = workspace / ".lake"
    if not lake_state.is_dir():
        return _result("unsupported", "compiled-library-unavailable",
                       "Selected workspace has no compiled Lake library roots.")
    (root / ".lake").symlink_to(lake_state, target_is_directory=True)
    source, target_positions = _probe_source(job["goal"])
    (root / "RationalProbe.lean").write_text(source, encoding="utf-8")
    source_digest = "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()
    context = _isolated_context(root, workspace_toolchain, identity)
    if isinstance(context, dict):
        return context
    verify_toolchain_identities(context)
    return context, source, source_digest, target_positions, identity["processReceipt"]


def _isolated_context(root, workspace_toolchain, identity):
    context = resolve_toolchain_context(
        root, lake_path=workspace_toolchain.lake_path,
        lean_path=identity["leanExecutablePath"], selection_mode="explicit",
        environment=workspace_toolchain.environment,
    )
    if not _same_toolchain_context(context, workspace_toolchain, identity):
        return _result("stale", "isolated-workspace-mismatch",
                       "Temporary Lean workspace does not resolve to the selected executable and compiled libraries.")
    return context


def _same_toolchain_context(context, workspace_toolchain, identity):
    return (context.lean_identity == identity["leanExecutableDigest"]
            and context.lean_release == workspace_toolchain.lean_release
            and context.lean_commit == workspace_toolchain.lean_commit
            and context.lake_identity == workspace_toolchain.lake_identity
            and context.pin_digest == workspace_toolchain.pin_digest
            and context.library_roots == workspace_toolchain.library_roots)


def _capture_goal(job, root, context, source_digest, target_positions):
    timeout = _remaining(job)
    if timeout <= 0:
        return None, _result("incomplete", "timeout",
                             "Shared rational-branch deadline expired before goal capture.")
    line, column = target_positions
    captured = capture_source_goal(SourceGoalCaptureRequest(
        repo_root=root, source_path="RationalProbe.lean", module="RationalProbe",
        line=line, column=column, toolchain=context, timeout_seconds=timeout,
        max_output_bytes=job["limits"]["max_output_bytes"],
        max_rss_bytes=job["limits"]["max_rss_bytes"],
    ))
    if captured["status"] != "captured":
        return None, _capture_failure(captured)
    if _captured_goal_mismatch(captured, source_digest):
        return None, _result("rejected", "generated-goal-mismatch",
                             "Captured Lean goal differs from the regenerated rational proposition.",
                             {"capture": captured})
    return captured, None


def _capture_failure(captured):
    diagnostic = captured.get("diagnostic", {})
    return _result(captured["status"], diagnostic.get("code", "goal-capture"),
                   diagnostic.get("message", "Lean goal capture did not complete."),
                   {"capture": captured})


def _captured_goal_mismatch(captured, source_digest):
    observed = captured["capture"]["goal"]
    return (captured["capture"]["source"]["digest"] != source_digest
            or not isinstance(observed.get("typeDisplay"), str)
            or not observed["typeDisplay"]
            or not isinstance(observed.get("typeStructural"), str)
            or not observed["typeStructural"])


def _complete_goal(job, root, context, source_digest, resolution_receipt, captured):
    timeout = _remaining(job)
    if timeout <= 0:
        return _result("incomplete", "timeout",
                       "Shared rational-branch deadline expired before completion and replay.",
                       {"capture": captured})
    completion = complete_source_goal(SourceGoalCompletionRequest(
        repo_root=root, capture=captured["capture"], term=job["term"],
        toolchain=context, timeout_seconds=timeout,
        max_output_bytes=job["limits"]["max_output_bytes"],
        max_rss_bytes=job["limits"]["max_rss_bytes"],
    ))
    verify_toolchain_identities(context)
    accepted = _completion_accepted(completion, job["term"])
    return _completion_result(job, context, source_digest, resolution_receipt,
                              captured, completion, accepted)


def _completion_accepted(completion, term):
    return (completion["status"] == "completed"
            and completion.get("replay", {}).get("status") == "accepted"
            and completion.get("trust", {}).get("accepted") is True
            and completion.get("trust", {}).get("coverage") == "complete"
            and completion.get("termDigest") == _digest_text(term))


def _completion_result(job, context, source_digest, resolution_receipt,
                       captured, completion, accepted):
    evidence = {
        "capture": captured, "completion": completion,
        "processReceipts": [resolution_receipt,
                            *captured.get("processReceipts", []),
                            *completion.get("processReceipts", [])],
        "leanExecutableDigest": context.lean_identity,
        "executionContextIdentity": context.context_identity,
        "compiledLibraryRoots": [str(path) for path in context.library_roots],
        "sourceDigest": source_digest,
    }
    raw = _completion_payload(job, completion, evidence, accepted)
    if not accepted:
        raw["diagnostic"] = completion.get("diagnostic")
    return raw


def _completion_payload(job, completion, evidence, accepted):
    return {
        "status": "accepted" if accepted else "rejected",
        "completion": {"status": "completed" if accepted else completion["status"],
                       "termDigest": completion.get("termDigest")},
        "replay": {"status": "replayed" if accepted else completion.get("replay", {}).get("status"),
                   "sourceDigest": completion.get("replay", {}).get("sourceDigest")},
        "trust": {"status": "trusted" if accepted else "untrusted",
                  "observedAxioms": completion.get("trust", {}).get("observedAxioms"),
                  "policy": completion.get("trust", {}).get("policy")},
        "generatedProposition": job["goal"], "binding": job["binding"],
        "evidence": evidence,
    }


def _validate_job(job):
    _validate_job_text(job)
    _validate_job_sizes(job)
    _validate_job_deadline(job)
    closed(job["limits"], {"timeout_seconds", "max_output_bytes", "max_rss_bytes"},
           "rational check limits")
    closed(job["binding"], {
        "planId", "branchId", "branchKind", "sourceSpanIdentities",
        "baseGoalSha256", "derivedGoalSha256", "assignment", "goalId",
        "goalDigest", "generatedProposition", "checkerIdentity",
        "proofCheckerIdentity", "workspaceIdentity", "termDigest",
    }, "rational check binding")
    _validate_job_binding(job)
    _validate_job_digest_identity(job)


def _validate_job_text(job):
    for key in ("workspaceRoot", "goalId", "goal", "term"):
        if type(job[key]) is not str or not job[key].strip():
            raise ValueError(f"rational check {key} must be nonempty text")


def _validate_job_sizes(job):
    for key in ("goal", "term"):
        if len(job[key].encode("utf-8")) > _MAX_GOAL_BYTES:
            raise ValueError(f"rational check {key} exceeds its byte limit")


def _validate_job_deadline(job):
    if (type(job["deadlineMonotonic"]) not in (float, int)
            or job["deadlineMonotonic"] <= 0):
        raise ValueError("invalid rational check deadline")


def _validate_job_binding(job):
    binding = job["binding"]
    if (binding["goalId"] != job["goalId"]
            or binding["generatedProposition"] != job["goal"]
            or binding["termDigest"] != _digest_text(job["term"])):
        raise ValueError("rational check binding differs from exact goal or term")


def _validate_job_digest_identity(job):
    binding = job["binding"]
    if (job["goalDigest"] != _digest_text(job["goal"])
            or binding["goalDigest"] != job["goalDigest"]
            or binding["workspaceIdentity"] != job["workspaceIdentity"]):
        raise ValueError("rational check goal or workspace identity mismatch")


def _probe_source(goal):
    prefix = "import Mathlib\n\ntheorem LadonRationalProbe : " + goal + " := by\n  skip\n"
    lines = prefix.splitlines()
    tactic_line = next(index for index, line in enumerate(lines, start=1) if line == "  skip")
    return prefix, (tactic_line, 2)


def _remaining(job):
    return min(job["limits"]["timeout_seconds"],
               job["deadlineMonotonic"] - time.monotonic())


def _result(status, code, message, details=None):
    return {"status": status, "result": None,
            "diagnostic": {"code": code, "message": str(message)[:1000]},
            "details": details}


def main():
    import sys

    from ladon._proof_contract_planned_source_inputs import _planned_input_size
    from ladon.proof_contract_context_worker import MAX_BYTES, _response
    from ladon.proof_contract_io import _decode

    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("rational check worker input exceeds 8 MiB")
        job = _decode(raw)
        if _planned_input_size(job) > MAX_BYTES:
            raise ValueError("rational check worker input exceeds 8 MiB")
        result = _compute(job)
        sys.stdout.write(_response(result))
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError,
            RecursionError, LeanToolchainError) as error:
        sys.stdout.write(_response({"status": "rejected", "result": None,
                                    "diagnostic": str(error)[:1000]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
