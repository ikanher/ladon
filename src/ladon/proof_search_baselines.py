"""Portable contracts and measurements for the proof-search implementation plan.

This module deliberately knows public result shapes and measurement metadata, not
private SQLite table layouts.  Later packets can reuse the trace counter and
identity helpers without making benchmark output part of the proof authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import resource
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


BASELINE_SCHEMA = "ladon-proof-search-baseline-v1"
_SQL_LITERAL = re.compile(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|\b\d+(?:\.\d+)?\b")
_IGNORED_PARTS = {".git", ".ladon", "__pycache__", ".pytest_cache"}


def normalize_sql_statement(statement: str) -> str:
    """Normalize literals and whitespace for stable SQL statement classes."""

    collapsed = " ".join(statement.strip().split())
    return _SQL_LITERAL.sub("?", collapsed).upper()


@dataclass
class SqlTraceCounter:
    """Count normalized SQL statements observed by ``sqlite3``."""

    statements: list[str] = field(default_factory=list)
    _connection: sqlite3.Connection | None = field(default=None, init=False)

    def callback(self, statement: str) -> None:
        """Record one statement unless SQLite emits an empty trace event."""

        normalized = normalize_sql_statement(statement)
        if normalized:
            self.statements.append(normalized)

    def attach(self, connection: sqlite3.Connection) -> "SqlTraceCounter":
        """Attach to ``connection`` and return this counter for fluent use."""

        self._connection = connection
        connection.set_trace_callback(self.callback)
        return self

    def detach(self) -> None:
        """Stop tracing the attached connection."""

        if self._connection is not None:
            self._connection.set_trace_callback(None)
            self._connection = None

    def __enter__(self) -> "SqlTraceCounter":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.detach()

    @property
    def count(self) -> int:
        """Return the number of normalized statements observed."""

        return len(self.statements)

    def classes(self) -> dict[str, int]:
        """Return deterministic statement-class counts."""

        counts: dict[str, int] = {}
        for statement in self.statements:
            operation = statement.split(" ", 1)[0]
            counts[operation] = counts.get(operation, 0) + 1
        return dict(sorted(counts.items()))


def repository_fingerprint(root: Path) -> str:
    """Hash supported repository inputs without including generated state."""

    digest = hashlib.sha256()
    resolved = root.resolve()
    files = (
        path
        for path in resolved.rglob("*")
        if path.is_file() and not _IGNORED_PARTS.intersection(path.parts)
    )
    for path in sorted(files):
        relative = path.relative_to(resolved).as_posix().encode()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def environment_metadata() -> dict[str, str]:
    """Return stable host/runtime labels for observational measurements."""

    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "executable": sys.executable,
        "lean": os.environ.get("LEAN_VERSION", "unknown"),
        "lake": os.environ.get("LAKE_VERSION", "unknown"),
    }


def git_identity(root: Path) -> str | None:
    """Return the current commit when ``root`` is a Git checkout."""

    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


@dataclass(frozen=True)
class CommandMeasurement:
    """One bounded command timing sample."""

    argv: tuple[str, ...]
    elapsed_seconds: float
    return_code: int
    stdout_bytes: int
    stderr_bytes: int
    peak_rss_kb: int

    def as_json(self) -> dict[str, Any]:
        return {
            "argv": list(self.argv),
            "elapsedSeconds": self.elapsed_seconds,
            "returnCode": self.return_code,
            "stdoutBytes": self.stdout_bytes,
            "stderrBytes": self.stderr_bytes,
            "peakRssKb": self.peak_rss_kb,
        }


def measure_command(argv: Sequence[str], *, timeout: float = 120.0) -> CommandMeasurement:
    """Measure one argv without invoking a shell."""

    started = time.monotonic()
    rss_before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    completed = subprocess.run(
        list(argv),
        check=False,
        capture_output=True,
        timeout=timeout,
    )
    return CommandMeasurement(
        argv=tuple(argv),
        elapsed_seconds=round(time.monotonic() - started, 6),
        return_code=completed.returncode,
        stdout_bytes=len(completed.stdout),
        stderr_bytes=len(completed.stderr),
        peak_rss_kb=max(
            0,
            int(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss - rss_before),
        ),
    )


def measure_command_phases(
    argv: Sequence[str], *, warm_runs: int = 1, timeout: float = 120.0
) -> dict[str, Any]:
    """Measure a cold invocation followed by bounded warm invocations."""

    samples = [measure_command(argv, timeout=timeout)]
    samples.extend(
        measure_command(argv, timeout=timeout) for _ in range(max(0, warm_runs))
    )
    return {
        "cold": samples[0].as_json(),
        "warm": [sample.as_json() for sample in samples[1:]],
    }


def measure_named_commands(
    commands: Mapping[str, Sequence[str]],
    *,
    warm_runs: int = 1,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Measure named build/query probes with explicit cold and warm phases."""

    return {
        name: {
            "argv": list(argv),
            "phases": measure_command_phases(
                argv, warm_runs=warm_runs, timeout=timeout
            ),
        }
        for name, argv in sorted(commands.items())
    }


def database_bytes(paths: Iterable[Path]) -> dict[str, int]:
    """Return deterministic byte counts for existing database paths."""

    return {
        str(path): path.stat().st_size
        for path in sorted(paths)
        if path.is_file()
    }


def baseline_metadata(
    root: Path,
    *,
    command: Sequence[str],
    schema: str = BASELINE_SCHEMA,
    measurements: Iterable[CommandMeasurement] = (),
) -> dict[str, Any]:
    """Build an identity-bearing baseline document."""

    return {
        "schema": schema,
        "repository": str(root.resolve()),
        "repositoryFingerprint": repository_fingerprint(root),
        "git": git_identity(root),
        "command": list(command),
        "environment": environment_metadata(),
        "measurements": [sample.as_json() for sample in measurements],
        "observational": True,
        "semanticGates": [
            "public-contract-predicates",
            "deterministic-ordering",
            "authority-and-freshness-fields",
            "bounds-and-omissions",
        ],
    }


def write_baseline(path: Path, payload: Mapping[str, Any], *, overwrite: bool = False) -> None:
    """Write a canonical baseline, refusing accidental overwrite by default."""

    if path.exists() and not overwrite:
        raise FileExistsError(f"baseline exists; pass overwrite explicitly: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_public_contract(payload: Mapping[str, Any]) -> None:
    """Validate shared public evidence fields without inspecting storage tables."""

    required = {"schema", "operation", "status", "results", "coverage", "nonclaims"}
    missing = sorted(required.difference(payload))
    if missing:
        raise AssertionError(f"public contract missing fields: {missing}")
    if not isinstance(payload["results"], list):
        raise AssertionError("public contract results must be a list")
    if not isinstance(payload["coverage"], Mapping):
        raise AssertionError("public contract coverage must be an object")
    if not isinstance(payload["nonclaims"], list):
        raise AssertionError("public contract nonclaims must be a list")


def load_contract_fixture(path: Path) -> dict[str, Any]:
    """Load and validate a canonical public-contract fixture."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("contract fixture root must be an object")
    for operation, result in payload.get("contracts", {}).items():
        if not isinstance(result, Mapping):
            raise ValueError(f"contract fixture {operation} must be an object")
        assert_public_contract(result)
    return payload
