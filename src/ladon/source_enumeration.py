"""Bind the auxiliary Git selection used to enumerate source material.

The owner supplies already sanitized environments. Git is selected using the
caller's original search path and runs with the final Lean environment. Neither
enumeration nor verification reads the current host environment. This binds
process inputs; it does not isolate Git from repository or user configuration.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from ladon.process_supervisor import ProcessResult, run_bounded_target_process

SOURCE_LIST_TIMEOUT_SECONDS = 10.0
SOURCE_LIST_MAX_OUTPUT_BYTES = 16 * 1024 * 1024
SOURCE_LIST_MAX_RSS_BYTES = 256 * 1024 * 1024


class SourceEnumerationError(ValueError):
    """Selected source enumeration cannot retain its recorded binding."""


@dataclass(frozen=True)
class SourceEnumerationContext:
    """Captured auxiliary executable and exact, privately hashed environment."""

    git_path: Path | None
    git_identity: str | None
    environment: Mapping[str, str]

    def __post_init__(self) -> None:
        if (self.git_path is None) != (self.git_identity is None):
            raise SourceEnumerationError("source enumeration selection is incomplete")
        if self.git_path is not None and not self.git_path.is_absolute():
            raise SourceEnumerationError("source enumeration executable must be absolute")
        object.__setattr__(self, "environment", MappingProxyType(dict(self.environment)))

    @property
    def mode(self) -> str:
        """Selection policy, including the possible nonrepository fallback."""
        return "filesystem" if self.git_path is None else "git-with-nonrepository-fallback"

    @property
    def context_identity(self) -> str:
        """Hash exact execution values without exposing them in public metadata."""
        payload = {
            "schemaVersion": 1,
            "mode": self.mode,
            "gitPath": str(self.git_path) if self.git_path is not None else None,
            "gitIdentity": self.git_identity,
            "environment": dict(sorted(self.environment.items())),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, object]:
        """Describe executable provenance without an environment-value dump."""
        return {
            "schemaVersion": 1,
            "mode": self.mode,
            "gitPath": str(self.git_path) if self.git_path is not None else None,
            "gitIdentity": self.git_identity,
            "environmentKeys": sorted(self.environment),
            "contextIdentity": self.context_identity,
        }

    def verify(self) -> None:
        """Reject changed or unavailable selected executable bytes."""
        if self.git_path is not None and _identity(self.git_path) != self.git_identity:
            raise SourceEnumerationError("source enumeration executable identity changed")

    def paths(self, root: Path) -> tuple[str, ...] | None:
        """Return Git's raw relative paths, or request bounded filesystem walking.

        Nonrepository classification retains Git's English diagnostic. Other
        locales fail closed when that diagnostic cannot be recognized; bounded
        failures never trigger fallback. Path validation belongs to the source
        fingerprint owner.
        """
        if self.git_path is None:
            return None
        self.verify()
        try:
            result = run_bounded_target_process(
                (
                    str(self.git_path), "-C", str(root), "ls-files", "-z",
                    "--cached", "--others", "--exclude-standard",
                ),
                cwd=root,
                env=dict(self.environment),
                timeout_seconds=SOURCE_LIST_TIMEOUT_SECONDS,
                max_output_bytes=SOURCE_LIST_MAX_OUTPUT_BYTES,
                max_rss_bytes=SOURCE_LIST_MAX_RSS_BYTES,
            )
        except OSError as exc:
            raise SourceEnumerationError("cannot launch source enumeration executable") from exc
        finally:
            self.verify()
        return _enumerated_paths(result)


def _enumerated_paths(result: ProcessResult) -> tuple[str, ...] | None:
    if result.succeeded:
        return _successful_paths(result.stdout)
    if result.output_limited:
        raise SourceEnumerationError("VCS-visible source path list exceeds its byte limit")
    if result.timed_out or result.memory_limited:
        raise SourceEnumerationError("source enumeration exceeded its process bounds")
    if result.returncode == 128 and result.stderr.lower().startswith("fatal: not a git repository"):
        return None
    raise SourceEnumerationError("cannot enumerate VCS-visible source material")


def _successful_paths(output: str) -> tuple[str, ...]:
    if output and not output.endswith("\0"):
        raise SourceEnumerationError("source enumeration returned an invalid path list")
    return tuple(path for path in output.split("\0") if path)


def resolve_source_enumeration(
    search_environment: Mapping[str, str], execution_environment: Mapping[str, str]
) -> SourceEnumerationContext:
    """Select Git only from a supplied search path, then capture final run inputs."""
    search_path = search_environment.get("PATH", "")
    selected = shutil.which("git", path=search_path) if search_path else None
    git = Path(selected).resolve() if selected is not None else None
    return SourceEnumerationContext(
        git, _identity(git) if git is not None else None, execution_environment
    )


def _identity(path: Path) -> str:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise SourceEnumerationError("source enumeration executable is unavailable") from exc
