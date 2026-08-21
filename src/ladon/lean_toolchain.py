"""Fail-closed local Lean toolchain selection for authority-sensitive workers.

ladon-quality: reviewed-schema-hotspot
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from ladon.process_supervisor import run_bounded_target_process

_RELEASE = re.compile(r"(?<![0-9])([0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.]+)?)(?![0-9])")
_COMMIT = re.compile(r"\bcommit\s+([0-9a-f]{7,64})\b", re.IGNORECASE)
PREFLIGHT_TIMEOUT_SECONDS = 10.0
PREFLIGHT_MAX_OUTPUT_BYTES = 64 * 1024


class LeanToolchainError(ValueError):
    """A requested local Lean toolchain cannot be trusted or resolved."""


@dataclass(frozen=True)
class LeanToolchainContext:
    """Immutable executable, repository-pin, and environment selection."""

    repo_root: Path
    lake_path: Path
    lean_path: Path
    pin_content: str
    pin_digest: str
    lake_identity: str
    lean_identity: str
    source_tree_identity: str
    lean_release: str
    lean_commit: str | None
    selection_mode: str
    environment_keys: tuple[str, ...]
    environment: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "environment", MappingProxyType(dict(self.environment)))
        object.__setattr__(self, "environment_keys", tuple(sorted(self.environment)))
        if self.selection_mode not in {"explicit", "ambient"}:
            raise ValueError("toolchain selection mode must be explicit or ambient")
        if (
            not self.repo_root.is_absolute()
            or not self.lake_path.is_absolute()
            or not self.lean_path.is_absolute()
        ):
            raise ValueError("toolchain paths must be absolute")
        if not self.lake_path.is_file() or not self.lean_path.is_file():
            raise ValueError("toolchain executables must be existing files")

    def to_dict(self) -> dict[str, object]:
        return {
            "repositoryRoot": str(self.repo_root),
            "lakePath": str(self.lake_path),
            "leanPath": str(self.lean_path),
            "pinContent": self.pin_content,
            "pinDigest": self.pin_digest,
            "lakeIdentity": self.lake_identity,
            "leanIdentity": self.lean_identity,
            "sourceTreeIdentity": self.source_tree_identity,
            "leanRelease": self.lean_release,
            "leanCommit": self.lean_commit,
            "selectionMode": self.selection_mode,
            "environmentKeys": list(self.environment_keys),
            "contextIdentity": self.context_identity,
        }

    @property
    def context_identity(self) -> str:
        """Digest the exact non-secret execution context without exposing values."""
        payload = {
            "repositoryRoot": str(self.repo_root),
            "lakePath": str(self.lake_path),
            "leanPath": str(self.lean_path),
            "pinDigest": self.pin_digest,
            "lakeIdentity": self.lake_identity,
            "leanIdentity": self.lean_identity,
            "sourceTreeIdentity": self.source_tree_identity,
            "leanRelease": self.lean_release,
            "leanCommit": self.lean_commit,
            "selectionMode": self.selection_mode,
            "environment": dict(sorted(self.environment.items())),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(encoded).hexdigest()


def resolve_toolchain_context(
    repo_root: Path,
    *,
    lake_path: Path | None = None,
    lean_path: Path | None = None,
    selection_mode: str = "explicit",
    environment: Mapping[str, str] | None = None,
) -> LeanToolchainContext:
    """Resolve and verify a pinned or explicitly ambient local toolchain."""
    root = repo_root.resolve()
    pin_path = root / "lean-toolchain"
    if not pin_path.is_file():
        raise LeanToolchainError(f"repository toolchain pin is missing: {pin_path}")
    pin_content = pin_path.read_text(encoding="utf-8").strip()
    if not pin_content:
        raise LeanToolchainError("repository toolchain pin is empty")
    if selection_mode == "explicit" and (lake_path is None or lean_path is None):
        raise LeanToolchainError("explicit toolchain selection requires lake and lean paths")
    source_env = dict(environment or os.environ)
    allowed = {"PATH", "HOME", "TMPDIR", "USER", "LANG", "LC_ALL"}
    sanitized = {key: value for key, value in source_env.items() if key in allowed}
    lake = _resolve_executable(lake_path, "lake", source_env)
    lean = _resolve_executable(lean_path, "lean", source_env)
    sanitized["PATH"] = str(lake.parent) + os.pathsep + str(lean.parent)
    lake_version = _version(lake, root, sanitized)
    lean_version = _version(lean, root, sanitized)
    expected = _pinned_release(pin_content)
    if _lake_releases(lake_version) != {expected} or _reported_releases(lean_version) != {
        expected
    }:
        raise LeanToolchainError(
            f"toolchain pin mismatch: expected {expected}, lake={lake_version!r}, lean={lean_version!r}"
        )
    return LeanToolchainContext(
        root,
        lake,
        lean,
        pin_content,
        "sha256:" + hashlib.sha256(pin_content.encode()).hexdigest(),
        _identity(lake),
        _identity(lean),
        _source_tree_identity(root),
        expected,
        _reported_commit(lean_version),
        selection_mode,
        tuple(sorted(sanitized)),
        sanitized,
    )


def _resolve_executable(path: Path | None, name: str, environment: Mapping[str, str]) -> Path:
    candidate = (
        path
        if path is not None
        else Path(shutil.which(name, path=environment.get("PATH", "")) or "")
    )
    if not candidate or not candidate.is_absolute() or not candidate.is_file():
        raise LeanToolchainError(f"{name} executable is unavailable")
    return candidate.resolve()


def _version(executable: Path, cwd: Path, environment: Mapping[str, str]) -> str:
    try:
        result = run_bounded_target_process(
            [str(executable), "--version"],
            cwd=cwd,
            env=dict(environment),
            timeout_seconds=PREFLIGHT_TIMEOUT_SECONDS,
            max_output_bytes=PREFLIGHT_MAX_OUTPUT_BYTES,
        )
    except OSError as exc:
        raise LeanToolchainError(f"cannot inspect {executable.name} version") from exc
    if not result.succeeded:
        reason = "timed out" if result.timed_out else "failed or exceeded output bounds"
        raise LeanToolchainError(f"cannot inspect {executable.name} version: {reason}")
    return result.stdout.strip() or result.stderr.strip()


def _pinned_release(pin_content: str) -> str:
    match = re.search(r":v([0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.]+)?)$", pin_content)
    if match is None:
        raise LeanToolchainError("repository toolchain pin does not name an exact Lean release")
    return match.group(1)


def _reported_releases(output: str) -> frozenset[str]:
    return frozenset(_RELEASE.findall(output))


def _reported_commit(output: str) -> str | None:
    match = _COMMIT.search(output)
    return match.group(1).lower() if match else None


def _lake_releases(output: str) -> frozenset[str]:
    """Read Lake's embedded Lean release, ignoring Lake's own release number."""
    labelled = frozenset(re.findall(r"Lean version\s+" + _RELEASE.pattern, output))
    return labelled or _reported_releases(output)


def _identity(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _source_tree_identity(root: Path) -> str:
    digest = hashlib.sha256()
    excluded = {".git", ".lake", "__pycache__", ".pytest_cache"}
    source_roots = [root / name for name in ("src", "tests", "scripts")]
    config_names = {
        "lean-toolchain",
        "lake-manifest.json",
        "lakefile.lean",
        "lakefile.toml",
        "lakefile.json",
    }
    paths = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and (path.name in config_names or any(path.is_relative_to(item) for item in source_roots))
        and not any(part in excluded for part in path.parts)
    )
    for path in paths:
        relative = path.relative_to(root).as_posix().encode()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return "sha256:" + digest.hexdigest()


def verify_toolchain_identities(context: LeanToolchainContext) -> None:
    """Fail when selected pin or executable bytes changed after context creation."""
    observed = {
        "lake": _identity(context.lake_path),
        "lean": _identity(context.lean_path),
    }
    expected = {"lake": context.lake_identity, "lean": context.lean_identity}
    changed = [name for name in expected if observed[name] != expected[name]]
    pin_path = context.repo_root / "lean-toolchain"
    if not pin_path.is_file() or (
        "sha256:"
        + hashlib.sha256(pin_path.read_text(encoding="utf-8").strip().encode()).hexdigest()
        != context.pin_digest
    ):
        changed.append("lean-toolchain")
    if changed:
        raise LeanToolchainError("toolchain executable identity changed: " + ", ".join(changed))
    if _source_tree_identity(context.repo_root) != context.source_tree_identity:
        raise LeanToolchainError("source tree identity changed")


__all__ = [
    "LeanToolchainContext",
    "LeanToolchainError",
    "resolve_toolchain_context",
    "verify_toolchain_identities",
]
