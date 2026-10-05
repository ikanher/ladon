"""Sanitized command, lock, collection, and source-audit primitives."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path

from release_gate_types import GateError

TEXT_AUDIT_SUFFIXES = frozenset(
    {".cfg", ".ini", ".json", ".md", ".py", ".sh", ".toml", ".yaml", ".yml"}
)
MAINTAINER_PATH_PATTERNS = (
    re.compile(r"/(?:home|Users)/[^/\s\"'`]+/"),
    re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\s\"'`]+\\\\"),
)


def inferred_elan_home(original: Mapping[str, str]) -> str | None:
    """Return an explicit or conventional Elan home when one exists."""

    configured = original.get("ELAN_HOME")
    if configured:
        return configured
    home = original.get("HOME")
    if home and (Path(home) / ".elan").is_dir():
        return str(Path(home) / ".elan")
    return None


def sanitized_environment(runtime_root: Path, candidate_root: Path) -> dict[str, str]:
    """Return a process environment isolated from host Python/project state."""

    original = os.environ
    environment = dict(original)
    remove_host_python_state(environment)
    home = runtime_root / "home"
    cache = runtime_root / "cache"
    project_environment = runtime_root / "environment"
    for path in (home, cache, project_environment):
        path.mkdir(parents=True, exist_ok=True)
    environment.update(
        {
            "CI": "1",
            "HOME": str(home),
            "NO_COLOR": "1",
            "PYTHONNOUSERSITE": "1",
            "UV_BUILD_CONSTRAINT": str(candidate_root / "build-constraints.txt"),
            "UV_CACHE_DIR": str(cache),
            "UV_PROJECT_ENVIRONMENT": str(project_environment),
            "XDG_CACHE_HOME": str(cache / "xdg"),
        }
    )
    elan_home = inferred_elan_home(original)
    if elan_home:
        environment["ELAN_HOME"] = elan_home
    preserve_rust_toolchain_locations(original, environment)
    return environment


def preserve_rust_toolchain_locations(
    original: Mapping[str, str], environment: dict[str, str],
) -> None:
    """Keep explicit compiler/cache locations when the gate replaces HOME."""

    for key, directory in (("RUSTUP_HOME", ".rustup"), ("CARGO_HOME", ".cargo")):
        if original.get(key):
            environment[key] = original[key]
        elif original.get("HOME"):
            location = Path(original["HOME"]) / directory
            if location.is_dir():
                environment[key] = str(location)


def remove_host_python_state(environment: dict[str, str]) -> None:
    """Remove variables that can redirect Python or uv into host state."""

    for key in (
        "CONDA_PREFIX",
        "PIP_CONFIG_FILE",
        "PYTHONHOME",
        "PYTHONPATH",
        "UV_ACTIVE",
        "UV_CONFIG_FILE",
        "UV_PROJECT",
        "UV_PROJECT_ENVIRONMENT",
        "UV_PYTHON",
        "UV_WORKING_DIR",
        "VIRTUAL_ENV",
    ):
        environment.pop(key, None)


def run_checked(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run one required command and propagate any nonzero result."""

    print("+ " + " ".join(str(part) for part in command), flush=True)
    result = subprocess.run(
        list(command),
        cwd=cwd,
        env=dict(environment),
        check=False,
        text=True,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None,
    )
    if result.returncode != 0:
        raise GateError(command_failure(command, result))
    return result


def command_failure(
    command: Sequence[str],
    result: subprocess.CompletedProcess[str],
) -> str:
    """Render one failed command without exposing environment values."""

    details = "\n".join(
        part.strip()
        for part in (result.stdout or "", result.stderr or "")
        if part.strip()
    )
    suffix = f"\n{details}" if details else ""
    return (
        f"required command failed ({result.returncode}): "
        f"{' '.join(command)}{suffix}"
    )


def uv_executable() -> str:
    """Return the required uv executable or fail clearly."""

    executable = shutil.which("uv")
    if executable is None:
        raise GateError("required executable is unavailable: uv")
    return executable


def lock_digest(candidate_root: Path) -> str:
    """Return the candidate lockfile's SHA-256 digest."""

    path = candidate_root / "uv.lock"
    if not path.is_file():
        raise GateError("candidate uv.lock is absent")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_lock_unchanged(candidate_root: Path, expected: str) -> None:
    """Fail if any gate subcommand rewrote the application lock."""

    actual = lock_digest(candidate_root)
    if actual != expected:
        raise GateError(
            f"uv.lock changed during candidate verification: {expected} -> {actual}"
        )


def prepare_locked_environment(
    candidate_root: Path,
    environment: Mapping[str, str],
) -> str:
    """Check the lock and sync a noneditable environment outside the candidate."""

    expected = lock_digest(candidate_root)
    uv = uv_executable()
    run_checked(
        [uv, "lock", "--check"],
        cwd=candidate_root,
        environment=environment,
    )
    run_checked(
        [uv, "sync", "--locked", "--no-editable"],
        cwd=candidate_root,
        environment=environment,
    )
    assert_lock_unchanged(candidate_root, expected)
    return expected


def pytest_node_ids(output: str) -> tuple[str, ...]:
    """Extract stable pytest node IDs from quiet collection output."""

    return tuple(
        sorted(
            line.strip()
            for line in output.splitlines()
            if "::" in line and line.lstrip().startswith("tests/")
        )
    )


def collect_live_node_ids(repo_root: Path) -> tuple[str, ...]:
    """Collect maintained tests from the live source using the invoking Python."""

    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    result = run_checked(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=repo_root,
        environment=environment,
        capture_output=True,
    )
    return require_nonempty_collection(result.stdout)


def collect_candidate_node_ids(
    candidate_root: Path,
    environment: Mapping[str, str],
) -> tuple[str, ...]:
    """Collect maintained tests from the locked candidate environment."""

    result = run_checked(
        [
            uv_executable(),
            "run",
            "--locked",
            "--no-sync",
            "python",
            "-m",
            "pytest",
            "--collect-only",
            "-q",
        ],
        cwd=candidate_root,
        environment=environment,
        capture_output=True,
    )
    return require_nonempty_collection(result.stdout)


def require_nonempty_collection(output: str) -> tuple[str, ...]:
    """Return parsed collection or fail rather than accepting pytest status 5."""

    nodes = pytest_node_ids(output)
    if not nodes:
        raise GateError("maintained pytest collection is empty")
    return nodes


def assert_collection_parity(live: Sequence[str], candidate: Sequence[str]) -> None:
    """Require exact live/candidate maintained-test node parity."""

    if tuple(live) == tuple(candidate):
        return
    detail = {
        "liveOnly": sorted(set(live) - set(candidate)),
        "candidateOnly": sorted(set(candidate) - set(live)),
    }
    raise GateError(f"live/candidate pytest collection differs: {json.dumps(detail)}")


def run_candidate_quality(
    candidate_root: Path,
    environment: Mapping[str, str],
) -> None:
    """Run the locked strict quality and maintained test gate."""

    prepare_candidate_lean_fixture(candidate_root, environment)
    run_checked(
        [
            uv_executable(),
            "run",
            "--locked",
            "--no-sync",
            "python",
            "scripts/python_quality.py",
            "--strict",
        ],
        cwd=candidate_root,
        environment=environment,
    )


def prepare_candidate_lean_fixture(
    candidate_root: Path, environment: Mapping[str, str],
) -> None:
    """Explicitly build the tracked test fixture when Lean tests can run."""

    lake = shutil.which("lake", path=environment.get("PATH", ""))
    if lake is None:
        return
    fixture = candidate_root / "tests" / "fixtures" / "lean_integration"
    if not (fixture / "lean-toolchain").is_file():
        raise GateError("candidate omits the pinned Lean integration fixture")
    run_checked([lake, "build"], cwd=fixture, environment=environment)


def candidate_audit_files(candidate_root: Path) -> Iterator[Path]:
    """Yield required source/document surfaces subject to local-path audit."""

    for relative in ("README.md", "pyproject.toml"):
        path = candidate_root / relative
        if path.is_file():
            yield path
    for relative in ("docs", "scripts", "src"):
        root = candidate_root / relative
        if root.is_dir():
            yield from (
                path
                for path in sorted(root.rglob("*"))
                if path.is_file() and path.suffix in TEXT_AUDIT_SUFFIXES
            )


def absolute_maintainer_paths(candidate_root: Path) -> tuple[str, ...]:
    """Return repository-relative source rows containing host-user paths."""

    findings: list[str] = []
    for path in candidate_audit_files(candidate_root):
        findings.extend(maintainer_path_rows(candidate_root, path))
    return tuple(findings)


def maintainer_path_rows(candidate_root: Path, path: Path) -> list[str]:
    """Return matching rows for one audited text file."""

    rows: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if any(pattern.search(line) for pattern in MAINTAINER_PATH_PATTERNS):
            relative = path.relative_to(candidate_root)
            rows.append(f"{relative}:{line_number}: {line.strip()}")
    return rows


def assert_no_absolute_maintainer_paths(candidate_root: Path) -> None:
    """Reject required package/docs/scripts that depend on a maintainer home."""

    findings = absolute_maintainer_paths(candidate_root)
    if findings:
        rendered = "\n".join(f"  - {finding}" for finding in findings)
        raise GateError(f"required absolute maintainer paths:\n{rendered}")


def runtime_directory(prefix: str) -> tempfile.TemporaryDirectory[str]:
    """Return one cleanup-managed outside-repository runtime directory."""

    return tempfile.TemporaryDirectory(prefix=prefix)
