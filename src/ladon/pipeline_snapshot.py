"""Single-source filesystem reads joined to the analysis snapshot registry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ladon.snapshot import (
    AnalysisSnapshot,
    SnapshotEntry,
    SnapshotMismatch,
)
from ladon.snapshot_registry import (
    SnapshotDirectoryRegistration,
    SnapshotFileRegistration,
    capture_directory_entry,
    directory_registry_path,
    snapshot_registry_path,
)


class SnapshotReadContext(Protocol):
    """Run-context state needed by the canonical registered-read boundary."""

    repo_root: Path
    analysis_snapshot: AnalysisSnapshot | None
    snapshot_read_mismatches: list[Mapping[str, Any]]
    snapshot_file_inputs: dict[str, SnapshotFileRegistration]
    snapshot_directory_inputs: dict[str, SnapshotDirectoryRegistration]


@dataclass(frozen=True)
class DirectoryInventory:
    """One captured directory state and its regular-file names."""

    status: str
    files: tuple[Path, ...]

    @property
    def exists(self) -> bool:
        """Return whether the captured input was a readable directory."""

        return self.status == "present"


def read_registered_bytes(
    context: SnapshotReadContext,
    source_path: Path,
    *,
    kind: str,
    collection_refs: tuple[str, ...],
    namespace: str,
    registry_path: str | None = None,
    register_unreadable: bool = False,
) -> bytes | None:
    """Read once, reject mixed bytes, and register the consumed input."""

    source = source_path.resolve()
    registered_path = registry_path or snapshot_registry_path(
        context.repo_root,
        source,
        namespace=namespace,
    )
    snapshot = context.analysis_snapshot
    try:
        content = source.read_bytes()
    except OSError as exc:
        existing = (
            snapshot.entries.get(registered_path)
            if snapshot is not None
            else None
        )
        if existing is not None:
            record_snapshot_mismatch(
                context,
                SnapshotMismatch(
                    registered_path,
                    expected=existing.sha256,
                    actual=None,
                ),
                collection_refs=collection_refs,
            )
            return None
        if snapshot is None or not register_unreadable:
            raise
        registration = SnapshotFileRegistration(
            registry_path=registered_path,
            source_path=source,
            kind=kind,
            collection_refs=tuple(sorted(set(collection_refs))),
        )
        context.analysis_snapshot = snapshot.register(
            SnapshotEntry(
                path=registered_path,
                kind=kind,
                status=(
                    "absent"
                    if isinstance(exc, FileNotFoundError)
                    else "unreadable"
                ),
                byte_count=0,
                sha256=None,
                collection_refs=registration.collection_refs,
            )
        )
        _remember_file_registration(context, registration)
        return None
    if snapshot is None:
        return content
    registration = SnapshotFileRegistration(
        registry_path=registered_path,
        source_path=source,
        kind=kind,
        collection_refs=tuple(sorted(set(collection_refs))),
    )
    try:
        context.analysis_snapshot = snapshot.register_consumed_bytes(
            path=registration.registry_path,
            kind=registration.kind,
            content=content,
            collection_refs=registration.collection_refs,
        )
    except SnapshotMismatch as exc:
        record_snapshot_mismatch(
            context,
            exc,
            collection_refs=registration.collection_refs,
        )
        return None
    _remember_file_registration(context, registration)
    return content


def read_registered_text(
    context: SnapshotReadContext,
    source_path: Path,
    *,
    kind: str,
    collection_refs: tuple[str, ...],
    namespace: str,
    registry_path: str | None = None,
    errors: str = "strict",
    register_unreadable: bool = False,
) -> str | None:
    """Read and decode one registered UTF-8 input without a second open."""

    content = read_registered_bytes(
        context,
        source_path,
        kind=kind,
        collection_refs=collection_refs,
        namespace=namespace,
        registry_path=registry_path,
        register_unreadable=register_unreadable,
    )
    if content is None:
        return None
    return content.decode("utf-8", errors=errors)


def register_captured_bytes(
    context: SnapshotReadContext,
    source_path: Path,
    content: bytes,
    *,
    kind: str,
    collection_refs: tuple[str, ...],
    namespace: str,
) -> None:
    """Register already-captured bytes and their physical drift source."""

    snapshot = context.analysis_snapshot
    if snapshot is None:
        raise ValueError("captured bytes require an initialized snapshot")
    source = source_path.resolve()
    registration = SnapshotFileRegistration(
        registry_path=snapshot_registry_path(
            context.repo_root,
            source,
            namespace=namespace,
        ),
        source_path=source,
        kind=kind,
        collection_refs=tuple(sorted(set(collection_refs))),
    )
    context.analysis_snapshot = snapshot.register_consumed_bytes(
        path=registration.registry_path,
        kind=registration.kind,
        content=content,
        collection_refs=registration.collection_refs,
    )
    _remember_file_registration(context, registration)


def capture_registered_directory(
    context: SnapshotReadContext,
    directory: Path,
    *,
    namespace: str,
    collection_refs: tuple[str, ...],
) -> DirectoryInventory:
    """Capture one directory inventory for analysis and final drift checks."""

    registration = SnapshotDirectoryRegistration(
        registry_path=directory_registry_path(
            context.repo_root,
            directory,
            namespace=namespace,
        ),
        source_path=directory.resolve(),
        collection_refs=tuple(sorted(set(collection_refs))),
    )
    entry, files = capture_directory_entry(registration)
    snapshot = context.analysis_snapshot
    if snapshot is not None:
        existing = snapshot.entries.get(registration.registry_path)
        if existing is not None and existing != entry:
            record_snapshot_mismatch(
                context,
                SnapshotMismatch(
                    registration.registry_path,
                    expected=existing.sha256,
                    actual=entry.sha256,
                ),
                collection_refs=registration.collection_refs,
            )
            return DirectoryInventory(status="unstable", files=())
        if existing is None:
            context.analysis_snapshot = snapshot.register(entry)
        else:
            context.analysis_snapshot = snapshot.with_collection_refs(
                registration.registry_path,
                registration.collection_refs,
            )
        _remember_directory_registration(context, registration)
    return DirectoryInventory(status=entry.status, files=files)


def record_snapshot_mismatch(
    context: SnapshotReadContext,
    mismatch: SnapshotMismatch,
    *,
    collection_refs: tuple[str, ...],
) -> None:
    """Retain an observed mixed read for the shared final decision."""

    context.snapshot_read_mismatches.append(
        {
            "path": mismatch.path,
            "expected": mismatch.expected,
            "actual": mismatch.actual,
            "collectionRefs": sorted(set(collection_refs)),
        }
    )


def _remember_file_registration(
    context: SnapshotReadContext,
    registration: SnapshotFileRegistration,
) -> None:
    existing = context.snapshot_file_inputs.get(registration.registry_path)
    if existing is None:
        context.snapshot_file_inputs[registration.registry_path] = registration
        return
    if (
        existing.source_path != registration.source_path
        or existing.kind != registration.kind
    ):
        raise ValueError(
            "snapshot registry path maps to multiple physical inputs: "
            f"{registration.registry_path}"
        )
    context.snapshot_file_inputs[registration.registry_path] = (
        SnapshotFileRegistration(
            registry_path=registration.registry_path,
            source_path=registration.source_path,
            kind=registration.kind,
            collection_refs=tuple(
                sorted(
                    {
                        *existing.collection_refs,
                        *registration.collection_refs,
                    }
                )
            ),
        )
    )


def _remember_directory_registration(
    context: SnapshotReadContext,
    registration: SnapshotDirectoryRegistration,
) -> None:
    existing = context.snapshot_directory_inputs.get(
        registration.registry_path
    )
    if existing is None:
        context.snapshot_directory_inputs[
            registration.registry_path
        ] = registration
        return
    if (
        existing.source_path != registration.source_path
        or existing.kind != registration.kind
    ):
        raise ValueError(
            "snapshot directory registry path maps to multiple inputs: "
            f"{registration.registry_path}"
        )
    context.snapshot_directory_inputs[registration.registry_path] = (
        SnapshotDirectoryRegistration(
            registry_path=registration.registry_path,
            source_path=registration.source_path,
            kind=registration.kind,
            collection_refs=tuple(
                sorted(
                    {
                        *existing.collection_refs,
                        *registration.collection_refs,
                    }
                )
            ),
        )
    )


__all__ = [
    "DirectoryInventory",
    "SnapshotReadContext",
    "capture_registered_directory",
    "read_registered_bytes",
    "read_registered_text",
    "record_snapshot_mismatch",
    "register_captured_bytes",
]
