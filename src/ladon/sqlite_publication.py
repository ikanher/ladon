"""Ownership-safe locking and durable replacement for SQLite publishers."""

from __future__ import annotations

import fcntl
import json
import os
import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PublicationLockBusy(RuntimeError):
    """Another process owns the destination's publication lock."""


@dataclass(frozen=True)
class PublicationLock:
    """One kernel-held lock whose metadata path is never deleted on release."""

    path: Path
    destination: Path
    nonce: str
    device: int
    inode: int
    descriptor: int


def acquire_publication_lock(destination: Path) -> PublicationLock:
    """Acquire the persistent sibling lock for one publication destination."""

    resolved = Path(destination).resolve()
    if resolved.exists() and resolved.stat().st_nlink > 1:
        raise ValueError(f'hardlinked publication destination is unsupported: {resolved}')
    if resolved.parent.name.endswith('.history') and re.fullmatch(
        r'[0-9a-f]{64}\.sqlite', resolved.name
    ):
        raise ValueError(f'historical snapshot is immutable: {resolved}')
    path = resolved.with_name(f"{resolved.name}.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        os.close(descriptor)
        raise PublicationLockBusy(f"publication already active for {resolved}") from error
    try:
        descriptor_stat = os.fstat(descriptor)
        path_stat = path.stat()
        if (descriptor_stat.st_dev, descriptor_stat.st_ino) != (
            path_stat.st_dev,
            path_stat.st_ino,
        ):
            raise PublicationLockBusy(f"publication lock path changed for {resolved}")
        nonce = secrets.token_hex(16)
        payload = json.dumps(
            {
                "schemaVersion": 1,
                "pid": os.getpid(),
                "destination": str(resolved),
                "nonce": nonce,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        os.ftruncate(descriptor, 0)
        os.write(descriptor, payload)
        os.fsync(descriptor)
        return PublicationLock(
            path,
            resolved,
            nonce,
            descriptor_stat.st_dev,
            descriptor_stat.st_ino,
            descriptor,
        )
    except Exception:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)
        raise


def release_publication_lock(lock: PublicationLock) -> None:
    """Release kernel ownership without unlinking another owner's pathname."""

    try:
        fcntl.flock(lock.descriptor, fcntl.LOCK_UN)
    finally:
        os.close(lock.descriptor)


def publication_lock_status(destination: Path) -> dict[str, Any]:
    """Inspect lock ownership without trusting PID metadata as authority."""

    resolved = Path(destination).resolve()
    path = resolved.with_name(f"{resolved.name}.lock")
    if not path.exists():
        return {"path": str(path), "status": "absent"}
    descriptor = os.open(path, os.O_RDWR)
    active = False
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            active = True
        metadata = _lock_metadata(descriptor)
        if not active:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)
    result: dict[str, Any] = {
        "path": str(path),
        "status": "active" if active else "inactive",
    }
    if isinstance(metadata.get("pid"), int):
        result["pid"] = metadata["pid"]
    if isinstance(metadata.get("nonce"), str):
        result["ownerToken"] = metadata["nonce"]
    return result


def durable_replace(temporary: Path, destination: Path) -> None:
    """Fsync a complete file, replace its destination, then fsync the directory."""

    with temporary.open("rb") as stream:
        os.fsync(stream.fileno())
    os.replace(temporary, destination)
    descriptor = os.open(destination.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _lock_metadata(descriptor: int) -> dict[str, Any]:
    os.lseek(descriptor, 0, os.SEEK_SET)
    try:
        value = json.loads(os.read(descriptor, 64 * 1024).decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


__all__ = [
    "PublicationLock",
    "PublicationLockBusy",
    "acquire_publication_lock",
    "durable_replace",
    "publication_lock_status",
    "release_publication_lock",
]
