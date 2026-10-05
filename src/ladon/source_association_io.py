"""Source association io for exact source-to-compiled observations."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any

from ladon import semantic_candidate_limits
from ladon.process_supervisor import ProcessResult
from ladon.proofir_v3 import (
    MAX_COMPILED_MODULES,
)

MAX_EVIDENCE_FILE_BYTES = 512 * 1024 * 1024
MAX_COMPILED_ENVIRONMENT_BYTES = semantic_candidate_limits.MAX_COMPILED_ENVIRONMENT_BYTES
MAX_AUXILIARY_OBSERVED_BYTES = 8 * 1024 * 1024 * 1024
MAX_SETUP_BYTES = 8 * 1024 * 1024
MAX_MODULES = MAX_COMPILED_MODULES
_MODULE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
_ProcessRunner = Callable[..., ProcessResult]

class _AssociationError(ValueError):
    def __init__(self, status: str, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


def _source_path(root: Path, relative: str, module: str) -> Path:
    path = _safe_repo_file(root, relative)
    parts = PurePosixPath(relative).parts
    module_parts = tuple(module.split("."))
    directories = parts[:-1]
    module_directories = module_parts[:-1]
    directory_suffix = directories[-len(module_directories) :] if module_directories else ()
    if (
        not relative.endswith(".lean")
        or Path(parts[-1]).stem != module_parts[-1]
        or len(directories) < len(module_directories)
        or tuple(directory_suffix) != module_directories
    ):
        raise _AssociationError("unavailable", "source-module-path", "source path does not end in the selected module components")
    return path


def _safe_repo_file(root: Path, relative: str) -> Path:
    pure = _normalized_relative_path(relative)
    path = root.joinpath(*pure.parts)
    _reject_path_symlinks(root, pure)
    if not path.resolve(strict=True).is_relative_to(root):
        raise _AssociationError("unavailable", "path-escape", "path escapes repository root")
    if not path.is_file():
        raise _AssociationError("unavailable", "not-a-file", "source or setup path is not a regular file")
    return path


def _normalized_relative_path(relative: str) -> PurePosixPath:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise _AssociationError("unavailable", "unsafe-path", "path must be a normalized repository-relative path")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts) or pure.as_posix() != relative:
        raise _AssociationError("unavailable", "unsafe-path", "path must be a normalized repository-relative path")

    return pure


def _reject_path_symlinks(root: Path, pure: PurePosixPath) -> None:
    current = root
    for part in pure.parts:
        current = current / part
        info = current.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise _AssociationError("unavailable", "symlink-path", "source and setup paths cannot contain symlinks")


def _read_regular(path: Path, maximum: int) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > maximum:
            raise _AssociationError("unavailable", "evidence-file-bound", "evidence file is not regular or exceeds its byte limit")
        content = stream.read(maximum + 1)
    if len(content) > maximum:
        raise _AssociationError("unavailable", "evidence-file-bound", "evidence file exceeds its byte limit")
    return content


def _file_identity(path: Path) -> tuple[str, int]:
    descriptor = os.open(
        path,
        os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0),
    )
    digest = hashlib.sha256()
    with os.fdopen(descriptor, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_EVIDENCE_FILE_BYTES:
            raise _AssociationError("unavailable", "evidence-file-bound", "compiled evidence is not regular or exceeds its per-file limit")
        bytes_read = 0
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            bytes_read += len(chunk)
            if bytes_read > MAX_EVIDENCE_FILE_BYTES:
                raise _AssociationError("unavailable", "evidence-file-bound", "compiled evidence grew beyond its byte limit")
        final = os.fstat(stream.fileno())
    if (
        bytes_read != metadata.st_size
        or (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns)
        != (final.st_dev, final.st_ino, final.st_size, final.st_mtime_ns, final.st_ctime_ns)
    ):
        raise _AssociationError("stale", "file-changed-during-read", "evidence file changed while its bytes were being hashed")
    return "sha256:" + digest.hexdigest(), bytes_read


def _check_unchanged(path: Path, expected_digest: str, label: str) -> None:
    if not expected_digest or _file_identity(path)[0] != expected_digest:
        raise _AssociationError("stale", f"{label}-changed", f"{label} bytes changed during source association")


def _reject_unsupported_output_sidecars(output: Path) -> None:
    for suffix in (".server", ".private"):
        if Path(str(output) + suffix).exists():
            raise _AssociationError("unavailable", "unsupported-output-sidecar", "modular Lean output is unsupported")


def _digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _unique_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("JSON object contains a duplicate key")
        value[key] = item
    return value



def _strict_json(raw: bytes | str) -> Any:
    try:
        return json.loads(raw, object_pairs_hook=_unique_object_pairs, parse_constant=_reject_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError("source metadata requires strict bounded JSON with unique keys") from exc


def _reject_constant(_value: str) -> None:
    raise ValueError("non-finite JSON value")
