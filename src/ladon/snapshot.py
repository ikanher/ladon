"""Immutable analysis-input snapshot identity and verification."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping


SNAPSHOT_SCHEMA = "ladon-analysis-snapshot-v1"
SNAPSHOT_STATUSES = frozenset({"present", "absent", "unreadable"})
SNAPSHOT_KINDS = frozenset(
    {"lean_source", "layout_state", "policy", "configuration", "evidence"}
)


class SnapshotError(ValueError):
    """Raised when analysis inputs cannot share one snapshot identity."""


class SnapshotMismatch(SnapshotError):
    """Raised before bytes from outside the captured snapshot are consumed."""

    def __init__(
        self,
        path: str,
        *,
        expected: str | None,
        actual: str | None,
    ) -> None:
        self.path = path
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"source_changed_during_analysis: {path}: "
            f"expected {expected!r}, observed {actual!r}"
        )


@dataclass(frozen=True)
class SnapshotEntry:
    """Captured state for one analysis-affecting filesystem path."""

    path: str
    kind: str
    status: str
    byte_count: int
    sha256: str | None
    collection_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_snapshot_entry(self)

    @classmethod
    def present(
        cls,
        *,
        path: str,
        kind: str,
        content: bytes,
        collection_refs: Iterable[str] = (),
    ) -> SnapshotEntry:
        """Capture one byte string under a portable relative path."""

        return cls(
            path=path,
            kind=kind,
            status="present",
            byte_count=len(content),
            sha256=_sha256(content),
            collection_refs=tuple(sorted(set(collection_refs))),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical snapshot-entry payload."""

        return {
            "path": self.path,
            "kind": self.kind,
            "status": self.status,
            "bytes": self.byte_count,
            "sha256": self.sha256,
            "collectionRefs": list(self.collection_refs),
        }

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> SnapshotEntry:
        """Parse one canonical snapshot entry."""

        refs = row.get("collectionRefs", [])
        if not isinstance(refs, list) or any(
            not isinstance(reference, str) for reference in refs
        ):
            raise SnapshotError(
                "snapshot collectionRefs must be an array of strings"
            )
        return cls(
            path=str(row.get("path", "")),
            kind=str(row.get("kind", "")),
            status=str(row.get("status", "")),
            byte_count=_nonnegative_int(row.get("bytes"), "snapshot bytes"),
            sha256=(
                str(row["sha256"]) if row.get("sha256") is not None else None
            ),
            collection_refs=tuple(refs),
        )


@dataclass(frozen=True)
class SnapshotDecision:
    """One final comparison shared by every renderer."""

    status: str
    mismatches: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {"stable", "changed"}:
            raise SnapshotError(f"unsupported snapshot decision: {self.status}")
        if self.status == "stable" and self.mismatches:
            raise SnapshotError("a stable snapshot cannot contain mismatches")
        if self.status == "changed" and not self.mismatches:
            raise SnapshotError("a changed snapshot requires mismatch evidence")

    def to_dict(self) -> dict[str, Any]:
        """Return one structured final snapshot decision."""

        return {
            "status": self.status,
            "diagnostic": (
                None
                if self.status == "stable"
                else "source_changed_during_analysis"
            ),
            "mismatches": [dict(row) for row in self.mismatches],
            "nonclaim": (
                "Matching analyzed bytes and final state do not prove that no "
                "unobserved transient filesystem event occurred."
            ),
        }


@dataclass(frozen=True)
class AnalysisSnapshot:
    """Canonical manifest for every registered analysis input."""

    source_index_fingerprint: str
    entries: Mapping[str, SnapshotEntry]
    configuration: Mapping[str, Any] = field(default_factory=dict)
    schema: str = SNAPSHOT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SNAPSHOT_SCHEMA:
            raise SnapshotError(f"unsupported snapshot schema: {self.schema}")
        if not self.source_index_fingerprint:
            raise SnapshotError("source-index fingerprint must be non-empty")
        rows = dict(self.entries)
        for path, entry in rows.items():
            if path != entry.path:
                raise SnapshotError("snapshot entry key must match its path")
        object.__setattr__(
            self,
            "entries",
            MappingProxyType(dict(sorted(rows.items()))),
        )
        normalized_configuration = _copy_json(
            _thaw_json(self.configuration)
        )
        object.__setattr__(
            self,
            "configuration",
            _freeze_json(normalized_configuration),
        )

    @property
    def identity(self) -> str:
        """Return the content identity used by analysis and renderers."""

        return _sha256(
            _canonical_json_bytes(
                {
                    "schema": self.schema,
                    "sourceIndexFingerprint": self.source_index_fingerprint,
                    "entries": {
                        path: entry.to_dict()
                        for path, entry in self.entries.items()
                    },
                    "configuration": _thaw_json(self.configuration),
                }
            )
        )

    def verify_bytes(self, path: str, content: bytes) -> None:
        """Fail before consuming bytes that do not match the capture."""

        entry = self.entries.get(path)
        actual = _sha256(content)
        if (
            entry is None
            or entry.status != "present"
            or entry.byte_count != len(content)
            or entry.sha256 != actual
        ):
            raise SnapshotMismatch(
                path,
                expected=entry.sha256 if entry is not None else None,
                actual=actual,
            )

    def register(self, entry: SnapshotEntry) -> AnalysisSnapshot:
        """Return a snapshot with one idempotent analysis input registered."""

        entries = dict(self.entries)
        existing = entries.get(entry.path)
        if existing is not None and existing != entry:
            raise SnapshotError(
                "snapshot path already registered with different state: "
                f"{entry.path}"
            )
        entries[entry.path] = entry
        return AnalysisSnapshot(
            source_index_fingerprint=self.source_index_fingerprint,
            entries=entries,
            configuration=self.configuration,
        )

    def register_bytes(
        self,
        *,
        path: str,
        kind: str,
        content: bytes,
        collection_refs: Iterable[str] = (),
    ) -> AnalysisSnapshot:
        """Register one content-addressed later-producer input."""

        return self.register(
            SnapshotEntry.present(
                path=path,
                kind=kind,
                content=content,
                collection_refs=collection_refs,
            )
        )

    def register_consumed_bytes(
        self,
        *,
        path: str,
        kind: str,
        content: bytes,
        collection_refs: Iterable[str] = (),
    ) -> AnalysisSnapshot:
        """Verify one consumed byte set and add its analysis collection refs."""

        requested_refs = tuple(sorted(set(collection_refs)))
        existing = self.entries.get(path)
        if existing is None:
            return self.register_bytes(
                path=path,
                kind=kind,
                content=content,
                collection_refs=requested_refs,
            )
        self.verify_bytes(path, content)
        if existing.kind != kind:
            raise SnapshotError(
                f"snapshot path {path} is already registered as "
                f"{existing.kind}, not {kind}"
            )
        return self.with_collection_refs(path, requested_refs)

    def with_collection_refs(
        self,
        path: str,
        collection_refs: Iterable[str],
    ) -> AnalysisSnapshot:
        """Return this snapshot with additional affected-collection refs."""

        existing = self.entries.get(path)
        if existing is None:
            raise SnapshotError(f"snapshot path is not registered: {path}")
        merged_refs = tuple(
            sorted({*existing.collection_refs, *collection_refs})
        )
        if merged_refs == existing.collection_refs:
            return self
        entries = dict(self.entries)
        entries[path] = SnapshotEntry(
            path=existing.path,
            kind=existing.kind,
            status=existing.status,
            byte_count=existing.byte_count,
            sha256=existing.sha256,
            collection_refs=merged_refs,
        )
        return AnalysisSnapshot(
            source_index_fingerprint=self.source_index_fingerprint,
            entries=entries,
            configuration=self.configuration,
        )

    def compare(self, current: Mapping[str, SnapshotEntry]) -> SnapshotDecision:
        """Compare final registered state, including added and removed paths."""

        mismatches: list[Mapping[str, Any]] = []
        for path in sorted(set(self.entries) | set(current)):
            expected = self.entries.get(path)
            actual = current.get(path)
            if expected == actual:
                continue
            mismatches.append(
                {
                    "path": path,
                    "expected": (
                        expected.to_dict() if expected is not None else None
                    ),
                    "actual": actual.to_dict() if actual is not None else None,
                    "collectionRefs": sorted(
                        {
                            *(
                                expected.collection_refs
                                if expected is not None
                                else ()
                            ),
                            *(
                                actual.collection_refs
                                if actual is not None
                                else ()
                            ),
                        }
                    ),
                }
            )
        return SnapshotDecision(
            status="changed" if mismatches else "stable",
            mismatches=tuple(mismatches),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical snapshot registry."""

        return {
            "schema": self.schema,
            "identity": self.identity,
            "sourceIndexFingerprint": self.source_index_fingerprint,
            "entries": {
                path: entry.to_dict() for path, entry in self.entries.items()
            },
            "configuration": _thaw_json(self.configuration),
        }

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> AnalysisSnapshot:
        """Parse and verify one canonical snapshot registry."""

        raw_entries = raw.get("entries", {})
        if not isinstance(raw_entries, Mapping):
            raise SnapshotError("snapshot entries must be an object")
        malformed = [
            str(path)
            for path, row in raw_entries.items()
            if not isinstance(row, Mapping)
        ]
        if malformed:
            raise SnapshotError(
                "snapshot entry rows must be objects: "
                f"{sorted(malformed)}"
            )
        snapshot = cls(
            source_index_fingerprint=str(
                raw.get("sourceIndexFingerprint", "")
            ),
            entries={
                str(path): SnapshotEntry.from_mapping(row)
                for path, row in raw_entries.items()
            },
            configuration=(
                dict(raw["configuration"])
                if isinstance(raw.get("configuration"), Mapping)
                else {}
            ),
            schema=str(raw.get("schema", "")),
        )
        identity = raw.get("identity")
        if identity is not None and identity != snapshot.identity:
            raise SnapshotError("snapshot identity does not match its manifest")
        return snapshot


def snapshot_from_source_index_manifest(
    *,
    source_index_fingerprint: str,
    manifest: Mapping[str, Any],
    configuration: Mapping[str, Any] | None = None,
) -> AnalysisSnapshot:
    """Adopt the source index's captured source and layout states."""

    entries: dict[str, SnapshotEntry] = {}
    for row in _mapping_rows(manifest.get("sources")):
        entry = _manifest_entry(
            row,
            kind="lean_source",
            collection_refs=(
                "source_index.modules",
                "source_index.imports",
                "source_index.declarations",
            ),
        )
        entries[entry.path] = entry
    layout = manifest.get("layout", {})
    if isinstance(layout, Mapping):
        for row in _mapping_rows(layout.get("stateFiles")):
            entry = _manifest_entry(
                row,
                kind="layout_state",
                collection_refs=("source_index.modules",),
            )
            entries[entry.path] = entry
    return AnalysisSnapshot(
        source_index_fingerprint=source_index_fingerprint,
        entries=entries,
        configuration=configuration or {},
    )


def register_policy_snapshot(
    snapshot: AnalysisSnapshot,
    policies: Mapping[str, Mapping[str, Any]],
) -> AnalysisSnapshot:
    """Bind normalized policy identities without treating them as source text."""

    registered = snapshot
    for name, row in sorted(policies.items()):
        registered = registered.register_bytes(
            path=f".ladon-snapshot/policies/{name}.json",
            kind="policy",
            content=_canonical_json_bytes(dict(row)),
            collection_refs=(
                "module_dag.modules",
                "report.findings",
                "report.review_regions",
            ),
        )
    return registered


def _manifest_entry(
    row: Mapping[str, Any],
    *,
    kind: str,
    collection_refs: tuple[str, ...],
) -> SnapshotEntry:
    raw_digest = row.get("sha256")
    digest = None if raw_digest is None else str(raw_digest)
    if digest is not None and not digest.startswith("sha256:"):
        digest = f"sha256:{digest}"
    return SnapshotEntry(
        path=str(row.get("path") or row.get("name") or ""),
        kind=kind,
        status=str(row.get("status", "unreadable")),
        byte_count=_nonnegative_int(row.get("bytes", 0), "snapshot bytes"),
        sha256=digest,
        collection_refs=collection_refs,
    )


def _validate_snapshot_entry(entry: SnapshotEntry) -> None:
    if (
        not entry.path
        or entry.path.startswith("/")
        or ".." in entry.path.split("/")
    ):
        raise SnapshotError(
            "snapshot paths must be non-empty repository-relative paths"
        )
    if entry.kind not in SNAPSHOT_KINDS:
        raise SnapshotError(f"unsupported snapshot entry kind: {entry.kind}")
    if entry.status not in SNAPSHOT_STATUSES:
        raise SnapshotError(
            f"unsupported snapshot status: {entry.status}"
        )
    _nonnegative_int(entry.byte_count, "snapshot byte count")
    _validate_snapshot_digest(entry)
    if any(not reference for reference in entry.collection_refs):
        raise SnapshotError("snapshot collection references must be non-empty")


def _validate_snapshot_digest(entry: SnapshotEntry) -> None:
    if entry.status == "present":
        if not _valid_sha256(entry.sha256):
            raise SnapshotError(
                "present snapshot entries require a sha256:<hex> digest"
            )
        return
    if entry.sha256 is not None:
        raise SnapshotError(
            "absent or unreadable snapshot entries cannot claim a digest"
        )


def _mapping_rows(raw: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(raw, list):
        return ()
    return tuple(row for row in raw if isinstance(row, Mapping))


def _sha256(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _valid_sha256(value: str | None) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _copy_json(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, sort_keys=True, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise SnapshotError("snapshot configuration must be JSON-compatible") from exc


def _freeze_json(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType(
            {str(key): _freeze_json(row) for key, row in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze_json(row) for row in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _thaw_json(row)
            for key, row in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_thaw_json(row) for row in value]
    return value


def _nonnegative_int(raw: Any, label: str) -> int:
    if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0:
        raise SnapshotError(f"{label} must be a non-negative integer")
    return raw


__all__ = [
    "SNAPSHOT_KINDS",
    "SNAPSHOT_SCHEMA",
    "SNAPSHOT_STATUSES",
    "AnalysisSnapshot",
    "SnapshotDecision",
    "SnapshotEntry",
    "SnapshotError",
    "SnapshotMismatch",
    "register_policy_snapshot",
    "snapshot_from_source_index_manifest",
]
