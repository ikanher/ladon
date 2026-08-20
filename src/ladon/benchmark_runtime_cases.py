"""Installed-CLI cache invalidation, timeout, and cancellation benchmark cases."""

from __future__ import annotations

import os
import signal
import subprocess
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.benchmark_process import run_measured
from ladon.benchmark_suite import (
    PROCESS_DEADLINE_SECONDS,
    expand_command,
    prepare_case,
    run_json_representation,
)

CACHE_MUTATIONS = {
    "source": "source_changed",
    "helper": "helper_changed",
    "toolchain": "toolchain_changed",
    "lake_manifest": "lake_state_changed",
    "imported_source": "transitive_import_changed",
}


def run_runtime_cases(
    candidate_root: Path,
    runtime_root: Path,
    analyzer: Path,
    installed_helper: Path,
    environment: Mapping[str, str],
    case: Mapping[str, Any],
    budgets: Mapping[str, Any],
) -> dict[str, Any]:
    """Run the required installed cache and process-control matrix."""

    cache_rows = [
        run_invalidation_case(
            candidate_root,
            runtime_root,
            analyzer,
            installed_helper,
            environment,
            case,
            mutation,
            expected,
        )
        for mutation, expected in CACHE_MUTATIONS.items()
    ]
    timeout = run_timeout_case(
        candidate_root,
        runtime_root,
        analyzer,
        environment,
        case,
        float(budgets["timeoutCleanupSeconds"]),
    )
    cancellation = run_cancellation_case(
        candidate_root,
        runtime_root,
        analyzer,
        environment,
        case,
        float(budgets["timeoutCleanupSeconds"]),
    )
    return {
        "cacheInvalidation": cache_rows,
        "timeout": timeout,
        "cancellation": cancellation,
        "passed": all(row["passed"] for row in cache_rows)
        and timeout["passed"]
        and cancellation["passed"],
    }


def run_invalidation_case(
    candidate_root: Path,
    runtime_root: Path,
    analyzer: Path,
    installed_helper: Path,
    environment: Mapping[str, str],
    case: Mapping[str, Any],
    mutation: str,
    expected: str,
) -> dict[str, Any]:
    """Prime one cache, mutate exactly one input, and classify the miss."""

    mutation_case = {**case, "id": f"cache-invalidation-{mutation}"}
    context = prepare_case(
        candidate_root,
        runtime_root,
        environment,
        mutation_case,
    )
    run_json_representation(
        context,
        analyzer,
        cache_name="cache",
        output_name="before.json",
    )
    restore = apply_cache_mutation(context.fixture, installed_helper, mutation)
    try:
        payload, _measured = run_json_representation(
            context,
            analyzer,
            cache_name="cache",
            output_name="after.json",
        )
    finally:
        restore()
    observed = root_cache_reason(payload)
    return {
        "input": mutation,
        "expectedReason": expected,
        "observedReason": observed,
        "passed": observed == expected,
    }


def apply_cache_mutation(
    fixture: Path,
    installed_helper: Path,
    mutation: str,
):
    """Mutate one fingerprint input and return its restoration callback."""

    path = mutation_path(fixture, installed_helper, mutation)
    original = path.read_bytes()
    path.write_bytes(original + f"\nbenchmark-mutation:{mutation}\n".encode())
    return lambda: path.write_bytes(original)


def mutation_path(
    fixture: Path,
    installed_helper: Path,
    mutation: str,
) -> Path:
    """Return the exact file owned by one cache mutation case."""

    return {
        "source": fixture / "Pkg/Surface/Deep.lean",
        "helper": installed_helper,
        "toolchain": fixture / "lean-toolchain",
        "lake_manifest": fixture / "lake-manifest.json",
        "imported_source": fixture / "Pkg/Dep.lean",
    }[mutation]


def root_cache_reason(payload: Mapping[str, Any]) -> str | None:
    """Return the root module's inspectable cache invalidation reason."""

    rows = payload["phases"]["lean_extraction"]["data"]["cache"]
    row = next(
        item
        for item in rows
        if item.get("module") == "Pkg.Surface.Deep"
    )
    return row.get("invalidationReason")


def run_timeout_case(
    candidate_root: Path,
    runtime_root: Path,
    analyzer: Path,
    environment: Mapping[str, str],
    case: Mapping[str, Any],
    cleanup_budget: float,
) -> dict[str, Any]:
    """Require a helper deadline to preserve prefix rows and clean descendants."""

    context, child_pid = control_context(
        candidate_root,
        runtime_root,
        environment,
        case,
        "timeout-control",
    )
    output = context.root / "timeout.json"
    command = control_command(context, analyzer, output, "0.3")
    measured = run_measured(
        command,
        cwd=context.root,
        environment=context.environment,
        timeout_seconds=PROCESS_DEADLINE_SECONDS,
    )
    payload = read_json_if_present(output)
    timed_out_batches = (
        payload.get("phases", {})
        .get("lean_extraction", {})
        .get("counters", {})
        .get("timed_out_batches", 0)
    )
    child_clean = child_is_clean(child_pid)
    passed = (
        measured.returncode == 1
        and not measured.timed_out
        and measured.wall_seconds <= cleanup_budget
        and timed_out_batches == 1
        and child_clean
    )
    return {
        "returncode": measured.returncode,
        "wallSeconds": round(measured.wall_seconds, 6),
        "cleanupBudgetSeconds": cleanup_budget,
        "timedOutBatches": timed_out_batches,
        "partialReportPresent": bool(payload),
        "orphanPresent": not child_clean,
        "passed": passed,
    }


def run_cancellation_case(
    candidate_root: Path,
    runtime_root: Path,
    analyzer: Path,
    environment: Mapping[str, str],
    case: Mapping[str, Any],
    cleanup_budget: float,
) -> dict[str, Any]:
    """Send SIGTERM during helper execution and require group cleanup."""

    context, child_pid = control_context(
        candidate_root,
        runtime_root,
        environment,
        case,
        "cancellation-control",
    )
    command = control_command(
        context,
        analyzer,
        context.root / "cancelled.json",
        "60",
    )
    started = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=context.root,
        env=dict(context.environment),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    child_started = wait_for_path(child_pid, cleanup_budget)
    if process.poll() is None:
        process.send_signal(signal.SIGTERM)
    try:
        stdout, stderr = process.communicate(timeout=cleanup_budget)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
    wall = time.monotonic() - started
    child_clean = child_is_clean(child_pid)
    return {
        "returncode": process.returncode,
        "wallSeconds": round(wall, 6),
        "cleanupBudgetSeconds": cleanup_budget,
        "childStarted": child_started,
        "orphanPresent": not child_clean,
        "stdoutEmpty": not stdout,
        "stderr": stderr.strip(),
        "passed": (
            child_started
            and process.returncode == 128 + signal.SIGTERM
            and wall <= cleanup_budget
            and child_clean
            and not stdout
        ),
    }


def control_context(
    candidate_root: Path,
    runtime_root: Path,
    environment: Mapping[str, str],
    case: Mapping[str, Any],
    identifier: str,
):
    """Prepare a fake helper that blocks after its first successful frame."""

    control_case = {**case, "id": identifier}
    context = prepare_case(
        candidate_root,
        runtime_root,
        environment,
        control_case,
    )
    child_pid = context.root / "child.pid"
    mutable_environment = dict(context.environment)
    mutable_environment["LADON_BENCH_FAKE_MODE"] = "timeout"
    mutable_environment["LADON_BENCH_CHILD_PID"] = str(child_pid)
    context = type(context)(
        case=context.case,
        fixture=context.fixture,
        root=context.root,
        environment=mutable_environment,
        helper_log=context.helper_log,
    )
    return context, child_pid


def control_command(
    context,
    analyzer: Path,
    output: Path,
    timeout: str,
) -> list[str]:
    """Return the ordinary installed command with a public Lean deadline."""

    command = expand_command(
        context.case["command"],
        analyzer,
        context.fixture,
        context.root / "cache",
        output,
    )
    format_index = command.index("--format")
    command[format_index:format_index] = ["--lean-timeout", timeout]
    return command


def read_json_if_present(path: Path) -> dict[str, Any]:
    """Return a partial report or an empty sentinel."""

    if not path.is_file():
        return {}
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def wait_for_path(path: Path, timeout: float) -> bool:
    """Wait within a finite budget for a helper child identity."""

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file():
            return True
        time.sleep(0.01)
    return False


def child_is_clean(path: Path) -> bool:
    """Return whether an observed child is absent or a reaping zombie."""

    if not path.is_file():
        return False
    return not process_is_live(int(path.read_text(encoding="utf-8")))


def process_is_live(pid: int) -> bool:
    """Treat a zombie as cleaned while the host init finishes reaping it."""

    status = Path(f"/proc/{pid}/status")
    if not status.exists():
        return False
    state = next(
        (
            line
            for line in status.read_text(encoding="utf-8").splitlines()
            if line.startswith("State:")
        ),
        "",
    )
    if "\tZ" in state:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True
