"""Independent scratch replay for a selected zero-residual candidate."""

from __future__ import annotations

import hashlib
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ladon.lean_toolchain import LeanToolchainContext
from ladon.process_supervisor import ProcessResult, run_bounded_target_process


@dataclass(frozen=True)
class ScratchReplayResult:
    status: str
    source: str
    source_digest: str
    output_digest: str | None = None
    diagnostic: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "status": self.status,
            "source": self.source,
            "sourceDigest": self.source_digest,
            "outputDigest": self.output_digest,
            "diagnostic": self.diagnostic,
        }


def build_scratch_source(module: str, goal: str, candidate: str) -> str:
    """Return exact source for an independent closed application replay."""
    return f"import {module}\n\nexample : {goal} := by\n  exact {candidate}\n"


def replay_scratch(
    *,
    repo_root: Path,
    module: str,
    goal: str,
    candidate: str,
    toolchain: LeanToolchainContext | None,
    timeout_seconds: float = 120.0,
    runner: Callable[..., ProcessResult] = run_bounded_target_process,
) -> ScratchReplayResult:
    source = build_scratch_source(module, goal, candidate)
    source_digest = "sha256:" + hashlib.sha256(source.encode()).hexdigest()
    if toolchain is None:
        return ScratchReplayResult("not-run", source, source_digest, diagnostic="explicit toolchain required")
    with tempfile.TemporaryDirectory(prefix="ladon-scratch-") as directory:
        path = Path(directory) / "Scratch.lean"
        path.write_text(source, encoding="utf-8")
        process = runner(
            (str(toolchain.lake_path), "env", str(toolchain.lean_path), str(path)),
            cwd=repo_root,
            env=toolchain.environment,
            timeout_seconds=timeout_seconds,
            max_output_bytes=8 * 1024 * 1024,
            max_rss_bytes=2 * 1024 * 1024 * 1024,
        )
    output_digest = "sha256:" + hashlib.sha256((process.stdout + process.stderr).encode()).hexdigest()
    if process.succeeded:
        return ScratchReplayResult("compiled", source, source_digest, output_digest)
    return ScratchReplayResult("rejected", source, source_digest, output_digest, (process.stderr or process.stdout).strip() or "scratch replay failed")


__all__ = ["ScratchReplayResult", "build_scratch_source", "replay_scratch"]
