"""Independent scratch replay for a selected zero-residual candidate."""

from __future__ import annotations

import hashlib
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from ladon.lean_toolchain import LeanToolchainContext, verify_toolchain_identities
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


def build_scratch_source(
    module: str,
    goal: str,
    candidate: str,
    local_context: Sequence[Mapping[str, str]] = (),
    max_output_bytes: int = 8 * 1024 * 1024,
    max_rss_bytes: int = 2 * 1024 * 1024 * 1024,
) -> str:
    """Return exact source for an independent closed application replay."""
    if local_context and goal.lstrip().startswith(("∀", "forall")):
        intros = "\n".join(f"  intro {row['name']}" for row in local_context)
        return f"import {module}\n\nexample : {goal} := by\n{intros}\n  exact {candidate}\n"
    binders = " ".join(f"({row['name']} : {row['type']})" for row in local_context)
    prefix = f" {binders}" if binders else ""
    return f"import {module}\n\nexample{prefix} : {goal} := by\n  exact {candidate}\n"


def replay_scratch(
    *,
    repo_root: Path,
    module: str,
    goal: str,
    candidate: str,
    toolchain: LeanToolchainContext | None,
    timeout_seconds: float = 120.0,
    local_context: Sequence[Mapping[str, str]] = (),
    max_output_bytes: int = 8 * 1024 * 1024,
    max_rss_bytes: int = 2 * 1024 * 1024 * 1024,
    runner: Callable[..., ProcessResult] = run_bounded_target_process,
) -> ScratchReplayResult:
    source = build_scratch_source(module, goal, candidate, local_context)
    source_digest = "sha256:" + hashlib.sha256(source.encode()).hexdigest()
    if toolchain is None:
        return ScratchReplayResult(
            "not-run", source, source_digest, diagnostic="explicit toolchain required"
        )
    if isinstance(toolchain, LeanToolchainContext):
        verify_toolchain_identities(toolchain)
    with tempfile.TemporaryDirectory(prefix="ladon-scratch-") as directory:
        path = Path(directory) / "Scratch.lean"
        path.write_text(source, encoding="utf-8")
        process = runner(
            (str(toolchain.lake_path), "env", str(toolchain.lean_path), str(path)),
            cwd=repo_root,
            env=toolchain.environment,
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
            max_rss_bytes=max_rss_bytes,
        )
    if isinstance(toolchain, LeanToolchainContext):
        verify_toolchain_identities(toolchain)
    output_digest = (
        "sha256:" + hashlib.sha256((process.stdout + process.stderr).encode()).hexdigest()
    )
    status = _replay_status(process)
    if status == "compiled":
        return ScratchReplayResult("compiled", source, source_digest, output_digest)
    return ScratchReplayResult(
        status,
        source,
        source_digest,
        output_digest,
        (process.stderr or process.stdout).strip() or "scratch replay failed",
    )


def _replay_status(process: ProcessResult) -> str:
    if process.timed_out:
        return "timeout"
    if process.output_limited:
        return "output-limited"
    if process.memory_limited:
        return "memory-limited"
    return "lean-rejected" if process.returncode != 0 else "compiled"


__all__ = ["ScratchReplayResult", "build_scratch_source", "replay_scratch"]
