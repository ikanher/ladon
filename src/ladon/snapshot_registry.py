"""Physical input registrations for Ladon's immutable analysis snapshot."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ladon.snapshot import (
    SNAPSHOT_KINDS,
    AnalysisSnapshot,
    SnapshotEntry,
    SnapshotError,
    register_policy_snapshot,
    snapshot_from_source_index_manifest,
)


@dataclass(frozen=True)
class SnapshotFileRegistration:
    """Physical file backing one canonical snapshot-registry entry."""

    registry_path: str
    source_path: Path
    kind: str
    collection_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_registration(
            self.registry_path,
            self.kind,
            self.collection_refs,
        )


@dataclass(frozen=True)
class SnapshotDirectoryRegistration:
    """Directory inventory backing one canonical manifest entry."""

    registry_path: str
    source_path: Path
    kind: str = "evidence"
    collection_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_registration(
            self.registry_path,
            self.kind,
            self.collection_refs,
        )


def current_repository_snapshot(
    repo_root: Path,
    captured: AnalysisSnapshot,
    *,
    source_index_options: Mapping[str, Any],
    policies: Mapping[str, Mapping[str, Any]],
    file_inputs: Iterable[SnapshotFileRegistration] = (),
    directory_inputs: Iterable[SnapshotDirectoryRegistration] = (),
) -> AnalysisSnapshot:
    """Recapture registered repository and policy state for final comparison."""

    from ladon.source_index import capture_source_index_manifest
    from ladon.source_index_cache import manifest_digest

    manifest = capture_source_index_manifest(
        repo_root,
        options=source_index_options,
    )
    current = snapshot_from_source_index_manifest(
        source_index_fingerprint=manifest_digest(manifest),
        manifest=manifest,
        configuration=captured.configuration,
    )
    current = register_policy_snapshot(current, policies)
    current = _recapture_files(current, file_inputs)
    return _recapture_directories(current, directory_inputs)


def snapshot_registry_path(
    repo_root: Path,
    source_path: Path,
    *,
    namespace: str,
) -> str:
    """Return a portable registry path for a repository or external input."""

    root = repo_root.resolve()
    source = source_path.resolve()
    try:
        return source.relative_to(root).as_posix()
    except ValueError:
        digest = hashlib.sha256(str(source).encode("utf-8")).hexdigest()[:20]
        name = _safe_component(source.name, fallback="input")
        safe_namespace = _safe_component(namespace, fallback="input")
        return (
            f".ladon-snapshot/external/{safe_namespace}/"
            f"{digest}-{name}"
        )


def directory_registry_path(
    repo_root: Path,
    directory: Path,
    *,
    namespace: str,
) -> str:
    """Return a stable synthetic path for one captured directory inventory."""

    root = repo_root.resolve()
    source = directory.resolve()
    try:
        display = source.relative_to(root).as_posix()
    except ValueError:
        display = str(source)
    digest = hashlib.sha256(display.encode("utf-8")).hexdigest()[:20]
    safe_namespace = _safe_component(namespace, fallback="directory")
    return (
        f".ladon-snapshot/directories/{safe_namespace}-{digest}.json"
    )


def capture_directory_entry(
    registration: SnapshotDirectoryRegistration,
) -> tuple[SnapshotEntry, tuple[Path, ...]]:
    """Capture one exact regular-file inventory without reading file contents."""

    directory = registration.source_path
    try:
        if not directory.exists():
            return (
                _missing_registration_entry(registration, "absent"),
                (),
            )
        if not directory.is_dir():
            return (
                _missing_registration_entry(registration, "unreadable"),
                (),
            )
        files = tuple(
            sorted(
                path.relative_to(directory)
                for path in directory.rglob("*")
                if path.is_file()
            )
        )
    except OSError:
        return (
            _missing_registration_entry(registration, "unreadable"),
            (),
        )
    content = json.dumps(
        {
            "schema": "ladon-directory-inventory-v1",
            "files": [path.as_posix() for path in files],
        },
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return (
        SnapshotEntry.present(
            path=registration.registry_path,
            kind=registration.kind,
            content=content,
            collection_refs=registration.collection_refs,
        ),
        files,
    )


def validate_registration(
    registry_path: str,
    kind: str,
    collection_refs: tuple[str, ...],
) -> None:
    """Validate non-state fields shared by physical input registrations."""

    if (
        not registry_path
        or registry_path.startswith("/")
        or ".." in registry_path.split("/")
    ):
        raise SnapshotError(
            "snapshot registration paths must be repository-relative"
        )
    if kind not in SNAPSHOT_KINDS:
        raise SnapshotError(f"unsupported snapshot registration kind: {kind}")
    if any(not reference for reference in collection_refs):
        raise SnapshotError(
            "snapshot registration collection references must be non-empty"
        )


def _recapture_files(
    snapshot: AnalysisSnapshot,
    registrations: Iterable[SnapshotFileRegistration],
) -> AnalysisSnapshot:
    current = snapshot
    for registration in sorted(
        registrations,
        key=lambda row: row.registry_path,
    ):
        if registration.registry_path in current.entries:
            current = current.with_collection_refs(
                registration.registry_path,
                registration.collection_refs,
            )
        else:
            current = current.register(_current_file_entry(registration))
    return current


def _recapture_directories(
    snapshot: AnalysisSnapshot,
    registrations: Iterable[SnapshotDirectoryRegistration],
) -> AnalysisSnapshot:
    current = snapshot
    for registration in sorted(
        registrations,
        key=lambda row: row.registry_path,
    ):
        entry, _files = capture_directory_entry(registration)
        current = current.register(entry)
    return current


def _current_file_entry(
    registration: SnapshotFileRegistration,
) -> SnapshotEntry:
    try:
        content = registration.source_path.read_bytes()
    except FileNotFoundError:
        return _missing_registration_entry(registration, "absent")
    except OSError:
        return _missing_registration_entry(registration, "unreadable")
    return SnapshotEntry.present(
        path=registration.registry_path,
        kind=registration.kind,
        content=content,
        collection_refs=registration.collection_refs,
    )


def _missing_registration_entry(
    registration: SnapshotFileRegistration | SnapshotDirectoryRegistration,
    status: str,
) -> SnapshotEntry:
    return SnapshotEntry(
        path=registration.registry_path,
        kind=registration.kind,
        status=status,
        byte_count=0,
        sha256=None,
        collection_refs=registration.collection_refs,
    )


def _safe_component(value: str, *, fallback: str) -> str:
    normalized = "".join(
        char if char.isalnum() or char in "._-" else "_"
        for char in value
    )
    return normalized or fallback


__all__ = [
    "SnapshotDirectoryRegistration",
    "SnapshotFileRegistration",
    "capture_directory_entry",
    "current_repository_snapshot",
    "directory_registry_path",
    "snapshot_registry_path",
    "validate_registration",
]
