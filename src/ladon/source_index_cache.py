"""Atomic content-addressed storage for complete source indexes."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ladon.source_index_models import (
    SOURCE_INDEX_FINGERPRINT_VERSION,
    SourceIndex,
    SourceIndexCacheOutcome,
    SourceIndexError,
)


@dataclass(frozen=True)
class SourceIndexCacheLookup:
    """One exact or prior-manifest cache lookup."""

    outcome: SourceIndexCacheOutcome
    payload: Mapping[str, Any] | None = None
    previous_payload: Mapping[str, Any] | None = None


class SourceIndexCache:
    """Content-addressed source-index storage with atomic latest pointers."""

    def __init__(self, cache_dir: Path) -> None:
        self.root = cache_dir / SOURCE_INDEX_FINGERPRINT_VERSION

    def lookup(
        self,
        repo_root: Path,
        fingerprint: str,
        manifest: Mapping[str, Any],
    ) -> SourceIndexCacheLookup:
        """Return an exact hit or an explicit miss/invalidation outcome."""

        entry = self.entry_path(fingerprint)
        if entry.is_file():
            return self._lookup_entry(entry, fingerprint, manifest)
        return self._lookup_prior(repo_root, entry, fingerprint, manifest)

    def _lookup_entry(
        self,
        entry: Path,
        fingerprint: str,
        manifest: Mapping[str, Any],
    ) -> SourceIndexCacheLookup:
        envelope = read_json_mapping(entry)
        payload = envelope.get("payload")
        if (
            envelope.get("fingerprintManifest") == manifest
            and isinstance(payload, Mapping)
        ):
            return SourceIndexCacheLookup(
                self._outcome("hit", "exact_fingerprint", fingerprint, entry),
                dict(payload),
            )
        return SourceIndexCacheLookup(
            self._outcome(
                "invalidation",
                "cache_entry_invalid",
                fingerprint,
                entry,
            )
        )

    def _lookup_prior(
        self,
        repo_root: Path,
        entry: Path,
        fingerprint: str,
        manifest: Mapping[str, Any],
    ) -> SourceIndexCacheLookup:
        prior = read_json_mapping(self.latest_path(repo_root))
        if not prior:
            return SourceIndexCacheLookup(
                self._outcome("miss", "cold_miss", fingerprint, entry)
            )
        prior_payload = self._prior_payload(prior)
        return SourceIndexCacheLookup(
            self._outcome(
                "invalidation",
                manifest_invalidation_reason(prior, manifest),
                fingerprint,
                entry,
            ),
            previous_payload=prior_payload,
        )

    def _prior_payload(
        self,
        manifest: Mapping[str, Any],
    ) -> Mapping[str, Any] | None:
        envelope = read_json_mapping(
            self.entry_path(manifest_digest(manifest))
        )
        payload = envelope.get("payload")
        if (
            envelope.get("fingerprintManifest") == manifest
            and isinstance(payload, Mapping)
        ):
            return dict(payload)
        return None

    def store(
        self,
        repo_root: Path,
        index: SourceIndex,
    ) -> Path:
        """Atomically commit a complete index and its latest pointer."""

        if index.index_status != "complete":
            raise SourceIndexError("partial source indexes must not be cached")
        entry = self.entry_path(index.fingerprint)
        envelope = {
            "fingerprintManifest": dict(index.fingerprint_manifest),
            "payload": index.to_payload(),
        }
        atomic_write_json(entry, envelope)
        atomic_write_json(
            self.latest_path(repo_root),
            dict(index.fingerprint_manifest),
        )
        return entry

    def entry_path(self, fingerprint: str) -> Path:
        """Return the content-addressed entry path."""

        return self.root / "entries" / f"{fingerprint}.json"

    def latest_path(self, repo_root: Path) -> Path:
        """Return the path-scoped prior-manifest pointer."""

        identity = hashlib.sha256(
            str(repo_root.resolve()).encode("utf-8")
        ).hexdigest()
        return self.root / "latest" / f"{identity}.json"

    @staticmethod
    def _outcome(
        status: str,
        reason: str,
        fingerprint: str,
        cache_path: Path,
    ) -> SourceIndexCacheOutcome:
        return SourceIndexCacheOutcome(
            status=status,
            reason=reason,
            fingerprint_version=SOURCE_INDEX_FINGERPRINT_VERSION,
            fingerprint=fingerprint,
            cache_path=cache_path,
        )


def default_source_index_cache_dir(
    *,
    environ: Mapping[str, str] | None = None,
    platform: str | None = None,
    home: Path | None = None,
) -> Path:
    """Return Ladon's platform user-cache namespace without touching disk."""

    values = os.environ if environ is None else environ
    system = sys.platform if platform is None else platform
    user_home = Path.home() if home is None else home
    if system.startswith("win"):
        base = values.get("LOCALAPPDATA")
        cache_root = Path(base) if base else user_home / "AppData" / "Local"
    elif system == "darwin":
        cache_root = user_home / "Library" / "Caches"
    else:
        base = values.get("XDG_CACHE_HOME")
        cache_root = Path(base) if base else user_home / ".cache"
    return cache_root.expanduser() / "ladon" / "source-index"


def manifest_digest(manifest: Mapping[str, Any]) -> str:
    """Return the stable unlabeled content digest for one manifest."""

    encoded = json.dumps(
        dict(manifest),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def manifest_invalidation_reason(
    prior: Mapping[str, Any],
    current: Mapping[str, Any],
) -> str:
    """Return the first stable cache-identity difference."""

    fields = (
        ("fingerprintVersion", "fingerprint_version_changed"),
        ("indexSchema", "index_schema_changed"),
        ("algorithmVersion", "algorithm_changed"),
        ("layout", "layout_changed"),
        ("options", "options_changed"),
        ("sources", "source_changed"),
    )
    for field, reason in fields:
        if prior.get(field) != current.get(field):
            return reason
    return "cache_entry_missing"


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Durably replace one JSON object without exposing partial bytes."""

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_json_mapping(path: Path) -> Mapping[str, Any]:
    """Read one cache JSON object, treating damaged state as absent."""

    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, Mapping) else {}


__all__ = [
    "SourceIndexCache",
    "SourceIndexCacheLookup",
    "default_source_index_cache_dir",
    "manifest_digest",
]
