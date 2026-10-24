"""Pin the rational-branch workspace to its version-selected Lean binary."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from ladon.lean_toolchain import LeanToolchainContext, verify_toolchain_identities
from ladon.process_supervisor import run_bounded_target_process


def rational_workspace_identity(root, toolchain, deadline, limits):
    """Resolve elan's pin-selected Lean binary and bind its exact bytes."""
    if not isinstance(toolchain, LeanToolchainContext):
        raise TypeError("rational workspace identity requires a pinned toolchain")
    remaining = min(10.0, float(deadline) - time.monotonic())
    if remaining <= 0:
        return _stop(
            "timeout", "Shared rational-branch deadline expired before executable identity check."
        )
    try:
        process = _run_prefix_check(root, toolchain, remaining, limits)
    except (OSError, ValueError) as error:
        return _stop("unsupported", str(error))
    receipt = _process_receipt(process)
    stopped = _process_failure(process, receipt)
    if stopped is not None:
        return stopped
    prefix = Path(process.stdout.strip())
    if not _valid_prefix(prefix):
        return _stop(
            "unsupported", "Pinned Lean prefix did not identify a regular executable.", receipt
        )
    try:
        executable = (prefix / "bin" / "lean").resolve(strict=True)
        lean_digest = _file_digest(executable)
    except OSError as error:
        return _stop("unsupported", str(error), receipt)
    return _resolved_identity(toolchain, executable, lean_digest, receipt)


def _run_prefix_check(root, toolchain, remaining, limits):
    process = run_bounded_target_process(
        [str(toolchain.lean_path), "--print-prefix"],
        cwd=root,
        env=dict(toolchain.environment),
        timeout_seconds=remaining,
        max_output_bytes=4096,
        max_rss_bytes=min(limits["max_rss_bytes"], 512 * 1024**2),
    )
    verify_toolchain_identities(toolchain)
    return process


def _process_failure(process, receipt):
    if process.timed_out or process.memory_limited or process.output_limited:
        if process.timed_out:
            code = "timeout"
        elif process.memory_limited:
            code = "memory-limit"
        else:
            code = "output-limit"
        return _stop(
            code, "Pinned Lean executable identity check stopped within its bound.", receipt
        )
    if not process.succeeded:
        return _stop(
            "unsupported", "Selected Lean launcher did not report a toolchain prefix.", receipt
        )
    return None


def _valid_prefix(prefix):
    executable = prefix / "bin" / "lean"
    return prefix.is_absolute() and executable.is_file() and not executable.is_symlink()


def _resolved_identity(toolchain, executable, lean_digest, receipt):
    identity = _digest(
        {
            "schema": "ladon-rational-workspace-v1",
            "toolchainContextIdentity": toolchain.context_identity,
            "leanExecutablePath": str(executable),
            "leanExecutableDigest": lean_digest,
            "compiledLibraryRoots": [str(path) for path in toolchain.library_roots],
        }
    )
    return {
        "status": "resolved",
        "workspaceIdentity": identity,
        "leanExecutablePath": executable,
        "leanExecutableDigest": lean_digest,
        "processReceipt": receipt,
    }


def _file_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _digest(value):
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _process_receipt(process):
    return {
        "command": list(process.command),
        "returnCode": process.returncode,
        "elapsedSeconds": process.elapsed_seconds,
        "peakRssBytes": process.peak_rss_bytes,
        "timedOut": process.timed_out,
        "memoryLimited": process.memory_limited,
        "outputLimited": process.output_limited,
        "stdoutDigest": "sha256:" + hashlib.sha256(process.stdout.encode()).hexdigest(),
        "stderrDigest": "sha256:" + hashlib.sha256(process.stderr.encode()).hexdigest(),
    }


def _stop(reason, diagnostic, receipt=None):
    return {
        "schema": "ladon-rational-workspace-identity-v1",
        "status": "incomplete",
        "reason": reason,
        "diagnostic": str(diagnostic)[:500],
        "processReceipt": receipt,
    }
