"""Prepare mutation-free direct-Lean execution from existing compiled libraries."""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ladon.lean_toolchain import LeanToolchainContext, LeanToolchainError

MAX_COMPILED_LIBRARY_ROOTS = 2048
MAX_LAKE_MANIFEST_BYTES = 16 * 1024 * 1024


class DirectLeanPreflightError(LeanToolchainError):
    """A read-only prerequisite failed before the Lean worker was launched."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class DirectLeanExecution:
    """One direct executable and read-only compiled-library search environment."""

    command: tuple[str, ...]
    environment: dict[str, str]
    library_roots: tuple[Path, ...]


def prepare_direct_lean_execution(
    repo_root: Path,
    module: str | Sequence[str] | None,
    toolchain: LeanToolchainContext | None,
    *,
    require_compiled_module: bool | None = None,
) -> DirectLeanExecution:
    """Fail closed when an explicit check lacks its precompiled target module."""

    root = repo_root.resolve()
    _require_manifest_package_directories(root)
    library_roots = _compiled_library_roots(root)
    modules = (
        ()
        if module is None
        else ((module,) if isinstance(module, str) else tuple(module))
    )
    require_compiled = (
        toolchain is not None
        if require_compiled_module is None
        else require_compiled_module
    )
    if require_compiled:
        if not modules:
            raise DirectLeanPreflightError(
                "compiled-module-unavailable",
                "mutation-free execution requires at least one compiled module",
            )
        for module_name in modules:
            _require_compiled_module(module_name, library_roots)
    if toolchain is not None:
        command = (str(toolchain.lean_path),)
        environment = dict(toolchain.environment)
    else:
        command = ("lean",)
        environment = _ambient_environment()
    if library_roots:
        environment["LEAN_PATH"] = os.pathsep.join(str(path) for path in library_roots)
    return DirectLeanExecution(command, environment, library_roots)


def _require_manifest_package_directories(repo_root: Path) -> None:
    """Reject a partially reconciled Lake state without asking Lake to repair it."""

    manifest = repo_root / "lake-manifest.json"
    if not manifest.is_file():
        return
    packages, packages_dir = _read_manifest_packages(manifest)
    missing = _missing_git_package_directories(
        packages,
        (repo_root / packages_dir).resolve(),
    )
    if missing:
        rendered = ", ".join(sorted(missing)[:20])
        raise DirectLeanPreflightError(
            "dependency-state-unavailable",
            "Lake dependency checkout is unavailable for mutation-free checking: "
            f"{rendered}; restore dependencies explicitly outside Ladon"
        )


def _read_manifest_packages(manifest: Path) -> tuple[list[object], str]:
    """Read one bounded Lake package inventory without running Lake."""

    if manifest.stat().st_size > MAX_LAKE_MANIFEST_BYTES:
        raise DirectLeanPreflightError(
            "dependency-state-invalid",
            "Lake manifest exceeds the mutation-free preflight byte limit",
        )
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DirectLeanPreflightError(
            "dependency-state-invalid",
            "Lake manifest is unreadable during mutation-free preflight",
        ) from exc
    packages = payload.get("packages")
    packages_dir = payload.get("packagesDir", ".lake/packages")
    if not isinstance(packages, list) or not isinstance(packages_dir, str):
        raise DirectLeanPreflightError(
            "dependency-state-invalid", "Lake manifest package inventory is malformed"
        )
    if len(packages) > MAX_COMPILED_LIBRARY_ROOTS:
        raise DirectLeanPreflightError(
            "dependency-state-invalid",
            "Lake manifest package population exceeds the supported limit",
        )
    return packages, packages_dir


def _missing_git_package_directories(
    packages: list[object],
    package_root: Path,
) -> list[str]:
    """Validate package rows and return absent Git checkout names."""

    missing: list[str] = []
    for row in packages:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise DirectLeanPreflightError(
                "dependency-state-invalid", "Lake manifest package row is malformed"
            )
        if row.get("type") != "git":
            continue
        name = row["name"]
        if not name or "/" in name or "\\" in name or name in {".", ".."}:
            raise DirectLeanPreflightError(
                "dependency-state-invalid", "Lake manifest package name is unsafe"
            )
        if not (package_root / name).is_dir():
            missing.append(name)
    return missing


def _compiled_library_roots(repo_root: Path) -> tuple[Path, ...]:
    roots: list[Path] = []
    local = repo_root / ".lake" / "build" / "lib" / "lean"
    if local.is_dir():
        roots.append(local.resolve())
    packages = repo_root / ".lake" / "packages"
    if packages.is_dir():
        try:
            children = sorted(packages.iterdir(), key=lambda path: path.name)
        except OSError as exc:
            raise LeanToolchainError("cannot inspect compiled Lake package roots") from exc
        if len(children) > MAX_COMPILED_LIBRARY_ROOTS:
            raise LeanToolchainError(
                "compiled Lake package population exceeds the supported root limit"
            )
        for package in children:
            if len(package.name.encode()) > 255:
                raise LeanToolchainError("compiled Lake package name exceeds the byte limit")
            candidate = package / ".lake" / "build" / "lib" / "lean"
            if candidate.is_dir():
                roots.append(candidate.resolve())
    if len(roots) > MAX_COMPILED_LIBRARY_ROOTS:
        raise LeanToolchainError("compiled Lean library population exceeds the root limit")
    return tuple(dict.fromkeys(roots))


def _require_compiled_module(module: str, roots: tuple[Path, ...]) -> None:
    relative = Path(*module.split(".")).with_suffix(".olean")
    if any((root / relative).is_file() for root in roots):
        return
    raise DirectLeanPreflightError(
        "compiled-module-unavailable",
        f"compiled module is unavailable for mutation-free checking: {module}; "
        "run the repository's build explicitly before invoking Ladon"
    )


def _ambient_environment() -> dict[str, str]:
    allowed = {"PATH", "HOME", "TMPDIR", "USER", "LANG", "LC_ALL"}
    return {key: value for key, value in os.environ.items() if key in allowed}


__all__ = [
    "DirectLeanExecution",
    "DirectLeanPreflightError",
    "prepare_direct_lean_execution",
]
