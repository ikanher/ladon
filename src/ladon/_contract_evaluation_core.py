"""Bounded JSON, hashing, and race-resistant artifact access primitives."""
from __future__ import annotations

import hashlib
import json
import math
import ntpath
import os
import re
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import Any

MAX_JSON = 8 * 1024 * 1024
MAX_DEPTH = 32
MAX_ROWS = 256
MAX_FINDINGS = 4096
MAX_OUTPUT = 2 * 1024 * 1024
_HEX = re.compile(r"^sha256:[0-9a-f]{64}$")
_LABEL_TOKENS = {"mismatch", "valid", "unknown", "matching", "discrepancy", "unsupported", "fault", "control"}

def _fail(msg: str) -> None:
    raise ValueError(msg)


def _keys(obj: Any, required: set[str], optional: set[str] = frozenset(), where: str = "object") -> None:
    if not isinstance(obj, dict): _fail(f"{where} must be an object")
    if any(not isinstance(k, str) for k in obj): _fail(f"{where} keys must be strings")
    missing = required - obj.keys()
    extra = obj.keys() - required - optional
    if missing: _fail(f"{where} missing fields: {', '.join(sorted(missing))}")
    if extra: _fail(f"{where} has unknown fields: {', '.join(sorted(extra))}")


def _walk_bounds(value: Any, depth: int = 0) -> None:
    if depth > MAX_DEPTH: _fail("JSON nesting exceeds limit")
    if isinstance(value, dict):
        _walk_mapping_bounds(value, depth)
    elif isinstance(value, list):
        _walk_list_bounds(value, depth)
    elif isinstance(value, str):
        if len(value) > 65536: _fail("JSON string exceeds limit")
    elif isinstance(value, float) and not math.isfinite(value):
        _fail("non-finite number")


def _walk_mapping_bounds(value: dict, depth: int) -> None:
    for key, item in value.items():
        if not isinstance(key, str) or len(key) > 256: _fail("invalid or oversized JSON key")
        _walk_bounds(item, depth + 1)


def _walk_list_bounds(value: list, depth: int) -> None:
    if len(value) > MAX_ROWS * MAX_FINDINGS: _fail("JSON array exceeds limit")
    for item in value: _walk_bounds(item, depth + 1)


def _pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out: _fail(f"duplicate JSON key: {k}")
        out[k] = v
    return out


def _loads(data: bytes, label: str) -> Any:
    if not isinstance(data, (bytes, bytearray)) or len(data) > MAX_JSON: _fail(f"{label} exceeds JSON byte limit")
    try:
        value = json.loads(bytes(data).decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=lambda x: _fail(f"invalid JSON constant {x}"))
    except (UnicodeError, json.JSONDecodeError) as e: _fail(f"invalid {label} JSON: {e}")
    _walk_bounds(value)
    return value


def read_bytes_bounded(path: str | os.PathLike[str], label: str, limit: int = MAX_JSON) -> bytes:
    """Read one regular file with a strict byte cap and no final-component symlink."""
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > limit: _fail(f"{label} is not regular or exceeds byte limit")
        chunks = bytearray()
        while len(chunks) <= limit:
            piece = os.read(fd, min(65536, limit + 1 - len(chunks)))
            if not piece: break
            chunks.extend(piece)
        if len(chunks) > limit: _fail(f"{label} exceeds byte limit")
        return bytes(chunks)
    finally:
        os.close(fd)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _digest(s: Any, where: str) -> None:
    if not isinstance(s, str) or not _HEX.fullmatch(s): _fail(f"{where} must be sha256 digest")


def _number(value: Any, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
        _fail(f"invalid {name}")


def _counter(value: Any, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 10**9:
        _fail(f"invalid {name}")


def _nullable_int(value: Any, name: str) -> None:
    if value is not None: _counter(value, name)


def _opaque_identifier(value: Any, pattern: str, where: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        _fail(f"{where} must be bounded opaque text")
    compact = re.sub(r"[^a-z0-9]", "", value.lower())
    if any(label in compact for label in _LABEL_TOKENS):
        _fail(f"{where} contains an answer label")
    return value


def _identity(obj: dict) -> str:
    body = dict(obj); body.pop("registrationIdentity", None)
    return sha256(canonical_json(body))


def _normalize_python_json(value: Any, depth: int = 0) -> Any:
    """Copy a loader-supplied mapping into bounded JSON-native values."""
    if depth > MAX_DEPTH: _fail("key nesting exceeds limit")
    if isinstance(value, Mapping):
        return _normalize_mapping(value, depth)
    if isinstance(value, list):
        return _normalize_list(value, depth)
    return _normalize_scalar(value)


def _normalize_mapping(value: Mapping[Any, Any], depth: int) -> dict[str, Any]:
    if len(value) > MAX_ROWS * MAX_FINDINGS: _fail("key object exceeds limit")
    out = {}
    for key, item in value.items():
        if not isinstance(key, str) or len(key) > 256: _fail("key object has invalid field name")
        out[key] = _normalize_python_json(item, depth + 1)
    return out


def _normalize_list(value: list[Any], depth: int) -> list[Any]:
    if len(value) > MAX_ROWS * MAX_FINDINGS: _fail("key array exceeds limit")
    return [_normalize_python_json(item, depth + 1) for item in value]


def _normalize_scalar(value: Any) -> Any:
    if value is None or isinstance(value, (bool, str)):
        _validate_json_scalar(value)
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        if value.bit_length() > 4096: _fail("key integer exceeds limit")
        return value
    if isinstance(value, float) and math.isfinite(value): return value
    _fail("key contains a non-JSON value")


def _validate_json_scalar(value: None | bool | str) -> None:
    if isinstance(value, str) and len(value) > 65536: _fail("key string exceeds limit")


def _safe_file(root: Path, rel: Any) -> tuple[tuple[int, int], bytes]:
    # Open every path component relative to a pinned directory descriptor to prevent symlink swaps.
    parts = _relative_parts(rel)
    root_abs = Path(root).resolve(strict=True)
    identity, data = _open_artifact(root_abs, parts, rel)
    if len(data) > MAX_JSON: _fail("artifact exceeds hash input limit")
    return identity, data


def _relative_parts(rel: Any) -> tuple[str, ...]:
    _validate_path_text(rel)
    p = Path(rel)
    if p.is_absolute() or not p.parts or "/".join(p.parts) != rel:
        _fail("absolute, noncanonical, or traversing artifact path")
    if any(x in ("", ".", "..") for x in p.parts):
        _fail("absolute, noncanonical, or traversing artifact path")
    return p.parts


def _validate_path_text(rel: Any) -> None:
    if not isinstance(rel, str) or not rel or len(rel) > 1024: _fail("invalid artifact path")
    if "\\" in rel or "\x00" in rel or ntpath.splitdrive(rel)[0]: _fail("noncanonical artifact path")


def _open_artifact(root: Path, parts: tuple[str, ...], rel: str) -> tuple[tuple[int, int], bytes]:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        parent_fd = _open_parent(root, parts[:-1], flags)
        try:
            return _read_artifact_at(parent_fd, parts[-1])
        finally:
            os.close(parent_fd)
    except OSError as e: _fail(f"cannot safely open artifact {rel}: {e}")


def _open_parent(root: Path, parts: tuple[str, ...], flags: int) -> int:
    parent_fd = os.open(root, flags)
    try:
        for part in parts:
            next_fd = os.open(part, flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = next_fd
    except OSError:
        os.close(parent_fd)
        raise
    return parent_fd


def _read_artifact_at(parent_fd: int, name: str) -> tuple[tuple[int, int], bytes]:
    fd = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode): _fail("artifact is not a regular file")
        data = _read_descriptor(fd)
        return (info.st_dev, info.st_ino), data
    finally:
        os.close(fd)


def _read_descriptor(fd: int) -> bytes:
    chunks = bytearray()
    while len(chunks) <= MAX_JSON:
        piece = os.read(fd, min(65536, MAX_JSON + 1 - len(chunks)))
        if not piece: break
        chunks.extend(piece)
    return bytes(chunks)


def _file_rows(rows: Any, root: Path, *, roles: set[str] | None = None, label: str,
               global_files: dict[str, tuple[tuple[int, int], bool]] | None = None,
               allow_shared: bool = False) -> None:
    if not isinstance(rows, list) or not rows or len(rows) > 128: _fail(f"{label} files must be a bounded nonempty array")
    normalized: set[str] = set(); inodes: set[tuple[int, int]] = set()
    for row in rows:
        _validate_file_row(row, root, roles, label, normalized, inodes, global_files, allow_shared)


def _validate_file_row(row: Any, root: Path, roles: set[str] | None, label: str,
                       normalized: set[str], inodes: set[tuple[int, int]],
                       global_files: dict[str, tuple[tuple[int, int], bool]] | None,
                       allow_shared: bool) -> None:
    _keys(row, {"path", "sha256"} | ({"role"} if roles is not None else set()), where=f"{label} file")
    if roles is not None and (not isinstance(row["role"], str) or row["role"] not in roles):
        _fail(f"invalid {label} file role")
    inode, data = _safe_file(root, row["path"])
    _digest(row["sha256"], f"{label} file hash")
    if sha256(data) != row["sha256"]: _fail(f"{label} file hash drift: {row['path']}")
    key = os.path.normcase(os.path.normpath(row["path"]))
    if key in normalized: _fail(f"duplicate/alias path in {label}")
    normalized.add(key)
    if inode in inodes: _fail(f"file aliases detected in {label}")
    inodes.add(inode)
    _record_global_file(global_files, key, inode, allow_shared, row["path"])


def _record_global_file(global_files, key, inode, allow_shared, path) -> None:
    if global_files is None: return
    prior = global_files.get(key)
    if prior is not None:
        if not allow_shared or not prior[1] or prior[0] != inode:
            _fail(f"duplicate registration file reference: {path}")
        return
    if inode in (item[0] for item in global_files.values()):
        _fail(f"file alias across registration paths: {path}")
    global_files[key] = (inode, allow_shared)


