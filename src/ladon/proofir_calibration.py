"""Opt-in, read-only calibration records for stored ProofIR queries."""

from __future__ import annotations

import hashlib
import subprocess
import time
from pathlib import Path
from typing import Any, Sequence


def run_calibration(repo_root: Path, command: Sequence[str], *, index_path: Path | None = None, predicates: Sequence[str] = ()) -> dict[str, Any]:
    """Record an ordinary command and semantic predicates without mutating the repo."""
    root = repo_root.resolve()
    database = index_path or root / ".ladon" / "index" / "proof-search.sqlite"
    before = _fingerprint(root, database)
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    elapsed = time.perf_counter() - started
    after = _fingerprint(root, database)
    return {"schema": "ladon-proofir-calibration-v1", "repository": str(root), "command": list(command), "elapsedSeconds": elapsed, "returnCode": completed.returncode, "stdoutBytes": len(completed.stdout.encode()), "stderrBytes": len(completed.stderr.encode()), "before": before, "after": after, "databaseMutated": before.get("databaseSha256") != after.get("databaseSha256"), "predicates": {name: _predicate(completed.stdout, name) for name in predicates}}


def _fingerprint(root: Path, database: Path) -> dict[str, Any]:
    return {"repositoryCommit": _git_head(root), "databasePath": str(database), "databaseSha256": _sha256(database), "configSha256": _sha256(root / ".ladon" / "proofir.json")}


def _predicate(output: str, name: str) -> bool:
    return name in output


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head(root: Path) -> str | None:
    try:
        return subprocess.run(("git", "rev-parse", "HEAD"), cwd=root, capture_output=True, text=True, check=False).stdout.strip() or None
    except OSError:
        return None


__all__ = ["run_calibration"]
