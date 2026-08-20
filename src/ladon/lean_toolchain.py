"""Fail-closed local Lean toolchain selection for authority-sensitive workers.

ladon-quality: reviewed-schema-hotspot
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


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
    selection_mode: str
    environment_keys: tuple[str, ...]
    environment: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.selection_mode not in {"explicit", "ambient"}:
            raise ValueError("toolchain selection mode must be explicit or ambient")
        if not self.repo_root.is_absolute() or not self.lake_path.is_absolute() or not self.lean_path.is_absolute():
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
            "selectionMode": self.selection_mode,
            "environmentKeys": list(self.environment_keys),
        }


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
    expected = pin_content.rsplit(":v", maxsplit=1)[-1]
    if expected not in lake_version or expected not in lean_version:
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
        selection_mode,
        tuple(sorted(sanitized)),
        sanitized,
    )


def _resolve_executable(path: Path | None, name: str, environment: Mapping[str, str]) -> Path:
    candidate = path if path is not None else Path(shutil.which(name, path=environment.get("PATH", "")) or "")
    if not candidate or not candidate.is_absolute() or not candidate.is_file():
        raise LeanToolchainError(f"{name} executable is unavailable")
    return candidate.resolve()


def _version(executable: Path, cwd: Path, environment: Mapping[str, str]) -> str:
    try:
        result = subprocess.run(
            [str(executable), "--version"],
            cwd=cwd,
            env=dict(environment),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LeanToolchainError(f"cannot inspect {executable.name} version") from exc
    return result.stdout.strip() or result.stderr.strip()


def _identity(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = ["LeanToolchainContext", "LeanToolchainError", "resolve_toolchain_context"]
