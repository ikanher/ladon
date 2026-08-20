"""Explicit, bounded Lake build orchestration for target repositories."""

from __future__ import annotations

import shutil
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ladon.process_supervisor import ProcessResult, run_target_process

DEFAULT_BUILD_TIMEOUT_SECONDS = 300.0
LAKE_MANIFESTS = ("lakefile.lean", "lakefile.toml")


class TargetPreflightError(RuntimeError):
    """An operational target-state prerequisite is unavailable."""


@dataclass(frozen=True)
class BuildPhase:
    """Normalized report evidence for one requested Lake build."""

    status: str
    command: tuple[str, ...]
    toolchain: str
    diagnostics: tuple[str, ...]
    elapsed_seconds: float
    timeout_seconds: float
    required: bool = True

    def to_report_row(self) -> dict[str, Any]:
        """Return the report-v2-compatible phase envelope fields."""

        return {
            "name": "build",
            "status": self.status,
            "required": self.required,
            "command": list(self.command),
            "toolchain": self.toolchain,
            "diagnostics": list(self.diagnostics),
            "elapsed_seconds": self.elapsed_seconds,
            "timeout_seconds": self.timeout_seconds,
        }


def validate_target_repository(repo_root: Path) -> Path:
    """Return a resolved target directory or raise an operational error."""

    if not repo_root.exists():
        raise TargetPreflightError(f"target repository does not exist: {repo_root}")
    if not repo_root.is_dir():
        raise TargetPreflightError(f"target repository is not a directory: {repo_root}")
    return repo_root.resolve()


def validate_lake_preflight(
    repo_root: Path,
    *,
    lake_executable: str | None = None,
) -> tuple[Path, str]:
    """Validate Lake configuration and resolve the executable for a build."""

    resolved_root = validate_target_repository(repo_root)
    if not any((resolved_root / name).is_file() for name in LAKE_MANIFESTS):
        names = " or ".join(LAKE_MANIFESTS)
        raise TargetPreflightError(
            f"target repository has no {names}: {resolved_root}"
        )
    resolved_lake = resolve_lake_executable(lake_executable)
    return resolved_root, resolved_lake


def resolve_lake_executable(requested: str | None) -> str:
    """Resolve an explicit test seam or the ordinary ``lake`` command."""

    if requested:
        path = Path(requested)
        if path.is_file():
            return str(path)
        raise TargetPreflightError(f"Lake executable does not exist: {path}")
    discovered = shutil.which("lake")
    if discovered is None:
        raise TargetPreflightError(
            "Lake executable is unavailable; install the target Lean toolchain"
        )
    return discovered


def validate_compiled_state(repo_root: Path, *, build_requested: bool) -> None:
    """Require project library state before no-build Lean-backed extraction."""

    if build_requested:
        return
    lean_lib = repo_root / ".lake" / "build" / "lib" / "lean"
    if not lean_lib.is_dir():
        raise TargetPreflightError(
            "Lean-backed extraction requires compiled project state at "
            f"{lean_lib}; rerun with --build"
        )


def run_lake_build(
    repo_root: Path,
    *,
    timeout_seconds: float = DEFAULT_BUILD_TIMEOUT_SECONDS,
    lake_executable: str | None = None,
    cancel_event: threading.Event | None = None,
) -> BuildPhase:
    """Run ``lake build`` explicitly and normalize its report phase."""

    resolved_root, resolved_lake = validate_lake_preflight(
        repo_root,
        lake_executable=lake_executable,
    )
    result = run_target_process(
        [resolved_lake, "build"],
        cwd=resolved_root,
        timeout_seconds=timeout_seconds,
        cancel_event=cancel_event,
    )
    return build_phase(result, resolved_root, timeout_seconds)


def build_phase(
    result: ProcessResult,
    repo_root: Path,
    timeout_seconds: float,
) -> BuildPhase:
    """Convert subprocess state into bounded report diagnostics."""

    diagnostics = process_diagnostics(result)
    return BuildPhase(
        status="complete" if result.succeeded else "failed",
        command=result.command,
        toolchain=toolchain_identity(repo_root),
        diagnostics=diagnostics,
        elapsed_seconds=result.elapsed_seconds,
        timeout_seconds=timeout_seconds,
    )


def process_diagnostics(result: ProcessResult) -> tuple[str, ...]:
    """Return concise stderr/stdout or timeout diagnostics."""

    rows: list[str] = []
    if result.timed_out:
        rows.append("lake build exceeded its finite deadline")
    rows.extend(
        row
        for row in (
            bounded_output("stderr", result.stderr),
            bounded_output("stdout", result.stdout),
        )
        if row
    )
    if not rows and not result.succeeded:
        rows.append(f"lake build exited with status {result.returncode}")
    return tuple(rows)


def bounded_output(channel: str, value: str, *, limit: int = 2000) -> str:
    """Bound target-controlled output before placing it in a report."""

    compact = value.strip()
    if not compact:
        return ""
    suffix = "…" if len(compact) > limit else ""
    return f"{channel}: {compact[:limit]}{suffix}"


def toolchain_identity(repo_root: Path) -> str:
    """Return the pinned toolchain text when the target declares one."""

    path = repo_root / "lean-toolchain"
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip()
