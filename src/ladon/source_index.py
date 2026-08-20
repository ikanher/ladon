"""Reusable, process-free source indexing for Lean repositories.

The index is a lexical inventory.  It reuses Ladon's Lake-layout discovery and
text extractor, and deliberately does not invoke Lake, Lean, Git, or target
initializers.  Cache entries are content addressed and committed atomically.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ladon.extraction import parse_lean_module
from ladon.lean_layout import LeanSourceMap, discover_lean_source_map
from ladon.lexical_command_skeleton import (
    command_skeleton_evidence_complete,
)
from ladon.source_index_audit import audit_command_evidence_complete
from ladon.source_index_cache import (
    SourceIndexCache,
    SourceIndexCacheLookup,
    default_source_index_cache_dir,
    manifest_digest,
)
from ladon.source_index_models import (
    SOURCE_FAILURE_DIAGNOSTIC,
    SOURCE_INDEX_FINGERPRINT_VERSION,
    SOURCE_INDEX_SCHEMA,
    SourceIndex,
    SourceIndexCacheOutcome,
    SourceIndexEntry,
    SourceIndexError,
    SourceIndexResult,
)

SOURCE_INDEX_ALGORITHM_VERSION = 5
SOURCE_INDEX_STABILIZATION_ATTEMPTS = 3
LAYOUT_STATE_FILES = ("lakefile.toml", "lakefile.lean", "lake-manifest.json")


@dataclass(frozen=True)
class _SourceEntryAttempt:
    entry: SourceIndexEntry | None
    reused: bool = False
    diagnostic: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class _EntryBuild:
    entries: tuple[SourceIndexEntry, ...]
    diagnostics: tuple[Mapping[str, Any], ...]
    reused_entries: int
    rebuilt_entries: int
    failed_entries: int


@dataclass(frozen=True)
class _StableIndexBuild:
    index: SourceIndex
    reused_entries: int
    rebuilt_entries: int
    failed_entries: int


class _SourceInventoryDrift(SourceIndexError):
    """One source changed between its manifest snapshot and parse read."""

    def __init__(self, module: str) -> None:
        self.module = module
        super().__init__(f"Lean source changed while indexing {module}")


def build_source_index(
    repo_root: Path,
    *,
    options: Mapping[str, Any] | None = None,
    cache_dir: Path | None = None,
    use_cache: bool = True,
    source_map: LeanSourceMap | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> SourceIndexResult:
    """Load or build one deterministic lexical source index.

    `source_map` is an injectable, already-discovered layout for library users
    and tests.  The default path performs only local filesystem reads.
    """

    root = repo_root.resolve()
    if not root.is_dir():
        raise SourceIndexError(f"source-index repository does not exist: {root}")
    layout = source_map or discover_lean_source_map(root)
    normalized_options, options_reason = _normalize_options(options or {})
    manifest = _fingerprint_manifest(root, layout, normalized_options)
    fingerprint = manifest_digest(manifest)
    store, lookup = _lookup_source_index(
        root,
        manifest,
        fingerprint,
        cache_dir=cache_dir,
        use_cache=use_cache,
        bypass_reason=options_reason,
    )
    cached = _decode_cached_index(root, fingerprint, lookup)
    if cached is not None and _manifest_is_current(
        root,
        layout,
        normalized_options,
        manifest,
        source_map=source_map,
    ):
        if progress_callback is not None:
            progress_callback(len(cached.entries), len(cached.entries))
        return SourceIndexResult(cached, _hit_outcome(lookup, cached))
    if lookup.payload is not None and cached is None:
        lookup = _invalid_payload_lookup(store, fingerprint)
    reusable = cached or _decode_previous_index(root, lookup.previous_payload)
    stable = _construct_stable_index(
        root,
        layout,
        normalized_options,
        manifest,
        fingerprint,
        reusable=reusable,
        source_map=source_map,
        progress_callback=progress_callback,
    )
    outcome = _completed_outcome(
        root,
        stable.index,
        store,
        lookup.outcome,
        stable.reused_entries,
        stable.rebuilt_entries,
        stable.failed_entries,
    )
    return SourceIndexResult(stable.index, outcome)


def capture_source_index_manifest(
    repo_root: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Capture current source/layout bytes without constructing index rows."""

    root = repo_root.resolve()
    if not root.is_dir():
        raise SourceIndexError(f"source-index repository does not exist: {root}")
    normalized_options, options_reason = _normalize_options(options or {})
    if options_reason is not None:
        raise SourceIndexError(
            "source-index options cannot be fingerprinted for verification"
        )
    return _fingerprint_manifest(
        root,
        discover_lean_source_map(root),
        normalized_options,
    )


def _construct_stable_index(
    repo_root: Path,
    layout: LeanSourceMap,
    options: Mapping[str, Any],
    manifest: Mapping[str, Any],
    fingerprint: str,
    *,
    reusable: SourceIndex | None,
    source_map: LeanSourceMap | None,
    progress_callback: Callable[[int, int], None] | None,
) -> _StableIndexBuild:
    """Incrementally restabilize bounded source drift before cache commit."""

    current_layout = layout
    current_manifest = dict(manifest)
    current_fingerprint = fingerprint
    working_reusable = reusable
    for attempt in range(SOURCE_INDEX_STABILIZATION_ATTEMPTS):
        try:
            index, _, _, _ = _construct_index(
                repo_root,
                current_layout,
                options,
                current_manifest,
                current_fingerprint,
                reusable=working_reusable,
                progress_callback=progress_callback if attempt == 0 else None,
            )
        except _SourceInventoryDrift as exc:
            if attempt + 1 == SOURCE_INDEX_STABILIZATION_ATTEMPTS:
                raise SourceIndexError(unstable_module_message(exc.module)) from exc
            current_layout = source_map or discover_lean_source_map(repo_root)
            current_manifest = _fingerprint_manifest(
                repo_root,
                current_layout,
                options,
            )
            current_fingerprint = manifest_digest(current_manifest)
            continue
        next_layout = source_map or discover_lean_source_map(repo_root)
        next_manifest = _fingerprint_manifest(
            repo_root,
            next_layout,
            options,
        )
        if next_manifest == current_manifest:
            return stable_build_counts(index, reusable)
        if attempt + 1 == SOURCE_INDEX_STABILIZATION_ATTEMPTS:
            raise SourceIndexError(
                unstable_inventory_message(current_manifest, next_manifest)
            )
        current_layout = next_layout
        current_manifest = next_manifest
        current_fingerprint = manifest_digest(next_manifest)
        working_reusable = index
    raise AssertionError("source-index stabilization loop did not terminate")


def _manifest_is_current(
    repo_root: Path,
    layout: LeanSourceMap,
    options: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    source_map: LeanSourceMap | None,
) -> bool:
    """Verify an exact cache hit against a second bounded source snapshot."""

    current_layout = source_map or discover_lean_source_map(repo_root)
    return _fingerprint_manifest(repo_root, current_layout, options) == manifest


def stable_build_counts(
    index: SourceIndex,
    reusable: SourceIndex | None,
) -> _StableIndexBuild:
    """Classify final entries against only the invocation's cache input."""

    candidates = _reusable_entry_map(
        reusable,
        index.fingerprint_manifest,
        index.options,
    )
    states = _source_state_map(index.fingerprint_manifest)
    reused = sum(
        _entry_matches_state(
            candidates.get(name),
            entry.path,
            states[name],
        )
        for name, entry in ((row.name, row) for row in index.entries)
    )
    return _StableIndexBuild(
        index=index,
        reused_entries=reused,
        rebuilt_entries=len(index.entries) - reused,
        failed_entries=len(states) - len(index.entries),
    )


def unstable_inventory_message(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> str:
    """Name a bounded changed-module sample after repeated source drift."""

    previous = _source_state_map(before)
    current = _source_state_map(after)
    changed = sorted(
        name
        for name in set(previous) | set(current)
        if previous.get(name) != current.get(name)
    )
    sample = ", ".join(changed[:5]) or "Lake layout/state files"
    suffix = f" (+{len(changed) - 5} more)" if len(changed) > 5 else ""
    return (
        "source inventory did not stabilize after "
        f"{SOURCE_INDEX_STABILIZATION_ATTEMPTS} snapshots; "
        f"changed: {sample}{suffix}"
    )


def unstable_module_message(module: str) -> str:
    """Explain repeated drift in one source parsed between snapshots."""

    return (
        "source inventory did not stabilize after "
        f"{SOURCE_INDEX_STABILIZATION_ATTEMPTS} snapshots; changed: {module}"
    )


def load_or_build_source_index(
    repo_root: Path,
    **kwargs: Any,
) -> SourceIndexResult:
    """Compatibility spelling for callers emphasizing cache reuse."""

    return build_source_index(repo_root, **kwargs)


def _lookup_source_index(
    repo_root: Path,
    manifest: Mapping[str, Any],
    fingerprint: str,
    *,
    cache_dir: Path | None,
    use_cache: bool,
    bypass_reason: str | None,
) -> tuple[SourceIndexCache | None, SourceIndexCacheLookup]:
    reason = "cache_disabled" if not use_cache else bypass_reason
    if reason is not None:
        outcome = SourceIndexCacheOutcome(
            "bypass",
            reason,
            SOURCE_INDEX_FINGERPRINT_VERSION,
            fingerprint,
            None,
        )
        return None, SourceIndexCacheLookup(outcome)
    store = SourceIndexCache(cache_dir or default_source_index_cache_dir())
    return store, store.lookup(repo_root, fingerprint, manifest)


def _decode_cached_index(
    repo_root: Path,
    fingerprint: str,
    lookup: SourceIndexCacheLookup,
) -> SourceIndex | None:
    if lookup.payload is None:
        return None
    try:
        cached = SourceIndex.from_payload(
            repo_root,
            lookup.payload,
            expected_fingerprint=fingerprint,
        )
    except (SourceIndexError, TypeError, ValueError):
        return None
    return cached if _cache_evidence_complete(cached) else None


def _hit_outcome(
    lookup: SourceIndexCacheLookup,
    cached: SourceIndex,
) -> SourceIndexCacheOutcome:
    return SourceIndexCacheOutcome(
        status=lookup.outcome.status,
        reason=lookup.outcome.reason,
        fingerprint_version=lookup.outcome.fingerprint_version,
        fingerprint=lookup.outcome.fingerprint,
        cache_path=lookup.outcome.cache_path,
        reused_entries=len(cached.entries),
    )


def _invalid_payload_lookup(
    store: SourceIndexCache | None,
    fingerprint: str,
) -> SourceIndexCacheLookup:
    path = store.entry_path(fingerprint) if store is not None else None
    return SourceIndexCacheLookup(
        SourceIndexCacheOutcome(
            "invalidation",
            "cache_payload_invalid",
            SOURCE_INDEX_FINGERPRINT_VERSION,
            fingerprint,
            path,
        )
    )


def _decode_previous_index(
    repo_root: Path,
    payload: Mapping[str, Any] | None,
) -> SourceIndex | None:
    if payload is None or not isinstance(payload.get("fingerprint"), str):
        return None
    try:
        previous = SourceIndex.from_payload(
            repo_root,
            payload,
            expected_fingerprint=str(payload["fingerprint"]),
        )
    except (SourceIndexError, TypeError, ValueError):
        return None
    return previous if _cache_evidence_complete(previous) else None


def _cache_evidence_complete(index: SourceIndex) -> bool:
    """Require every current-fingerprint additive producer before reuse."""

    return index.index_status == "complete" and all(
        command_skeleton_evidence_complete(entry.module)
        and audit_command_evidence_complete(entry.module)
        for entry in index.entries
    )


def _completed_outcome(
    repo_root: Path,
    index: SourceIndex,
    store: SourceIndexCache | None,
    outcome: SourceIndexCacheOutcome,
    reused_entries: int,
    rebuilt_entries: int,
    failed_entries: int,
) -> SourceIndexCacheOutcome:
    path = outcome.cache_path
    committed = False
    reason = outcome.reason
    if index.index_status == "partial":
        path = None
        if store is not None:
            reason = "partial_index_not_cached"
    elif store is not None:
        path = store.store(repo_root, index)
        committed = True
    return SourceIndexCacheOutcome(
        status=outcome.status,
        reason=reason,
        fingerprint_version=outcome.fingerprint_version,
        fingerprint=index.fingerprint,
        cache_path=path,
        committed=committed,
        reused_entries=reused_entries,
        rebuilt_entries=rebuilt_entries,
        failed_entries=failed_entries,
    )


def _construct_index(
    repo_root: Path,
    layout: LeanSourceMap,
    options: Mapping[str, Any],
    manifest: Mapping[str, Any],
    fingerprint: str,
    *,
    reusable: SourceIndex | None,
    progress_callback: Callable[[int, int], None] | None,
) -> tuple[SourceIndex, int, int, int]:
    source_states = _source_state_map(manifest)
    reusable_entries = _reusable_entry_map(reusable, manifest, options)
    built = _build_entries(
        repo_root,
        layout,
        source_states,
        reusable_entries,
        progress_callback=progress_callback,
    )
    roots = tuple(root.to_dict(repo_root) for root in layout.roots)
    diagnostics = _ordered_diagnostics(
        (
            *(_normalize_diagnostic(row, repo_root) for row in layout.diagnostics),
            *built.diagnostics,
        )
    )
    return (
        SourceIndex(
            repo_root=repo_root,
            fingerprint=fingerprint,
            fingerprint_manifest=dict(manifest),
            layout_status=layout.status,
            source_roots=roots,
            entries=built.entries,
            options=dict(options),
            index_status=("partial" if built.failed_entries else "complete"),
            diagnostics=diagnostics,
        ),
        built.reused_entries,
        built.rebuilt_entries,
        built.failed_entries,
    )


def _build_entries(
    repo_root: Path,
    layout: LeanSourceMap,
    source_states: Mapping[str, Mapping[str, Any]],
    reusable_entries: Mapping[str, SourceIndexEntry],
    *,
    progress_callback: Callable[[int, int], None] | None,
) -> _EntryBuild:
    entries: list[SourceIndexEntry] = []
    diagnostics: list[Mapping[str, Any]] = []
    reused_count = 0
    rebuilt_count = 0
    failed_count = 0
    selected = sorted(layout.modules.items())
    total = len(selected)
    for completed, (name, path) in enumerate(selected, start=1):
        state = source_states.get(name)
        if state is None:
            raise SourceIndexError(f"source fingerprint is missing for {name}")
        attempt = _source_entry(
            repo_root,
            name,
            path,
            state,
            reusable_entries.get(name),
        )
        if attempt.entry is None:
            failed_count += 1
            if attempt.diagnostic is not None:
                diagnostics.append(attempt.diagnostic)
        else:
            entries.append(attempt.entry)
            if attempt.reused:
                reused_count += 1
            else:
                rebuilt_count += 1
        if progress_callback is not None:
            progress_callback(completed, total)
    return _EntryBuild(
        tuple(entries),
        tuple(diagnostics),
        reused_count,
        rebuilt_count,
        failed_count,
    )


def _source_state_map(
    manifest: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    return {
        str(row["module"]): row
        for row in manifest.get("sources", [])
        if isinstance(row, Mapping)
    }


def _reusable_entry_map(
    reusable: SourceIndex | None,
    manifest: Mapping[str, Any],
    options: Mapping[str, Any],
) -> dict[str, SourceIndexEntry]:
    if reusable is None or not _entry_reuse_compatible(
        reusable,
        manifest,
        options,
    ):
        return {}
    return {entry.name: entry for entry in reusable.entries}


def _source_entry(
    repo_root: Path,
    name: str,
    path: Path,
    state: Mapping[str, Any],
    reusable: SourceIndexEntry | None,
) -> _SourceEntryAttempt:
    expected_path = _relative_path(repo_root, path)
    if _entry_matches_state(reusable, expected_path, state):
        if reusable is None:
            raise AssertionError("matching reusable source-index entry is absent")
        return _SourceEntryAttempt(reusable, reused=True)
    try:
        source_bytes = path.read_bytes()
    except OSError as exc:
        return _failed_source_attempt(
            repo_root,
            name,
            expected_path,
            "read_error",
            exc,
        )
    try:
        source_text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        return _failed_source_attempt(
            repo_root,
            name,
            expected_path,
            "invalid_utf8",
            exc,
        )
    digest = hashlib.sha256(source_bytes).hexdigest()
    if digest != state.get("sha256"):
        raise _SourceInventoryDrift(name)
    try:
        module = parse_lean_module(
            repo_root,
            path,
            resolved_name=name,
            source_text=source_text,
        )
    except Exception as exc:  # noqa: BLE001 - source adapter boundary records failures
        return _failed_source_attempt(
            repo_root,
            name,
            expected_path,
            "parse_error",
            exc,
        )
    return _SourceEntryAttempt(SourceIndexEntry(module, digest, len(source_bytes)))


def _failed_source_attempt(
    repo_root: Path,
    module: str,
    path: str,
    cause: str,
    exc: Exception,
) -> _SourceEntryAttempt:
    detail = _failure_detail(exc, repo_root)
    return _SourceEntryAttempt(
        None,
        diagnostic={
            "id": SOURCE_FAILURE_DIAGNOSTIC,
            "severity": "warning",
            "status": "partial",
            "subject": module,
            "module": module,
            "path": path,
            "cause": cause,
            "detail": detail,
            "message": (
                f"Skipped Lean source module {module} at {path}: {cause} ({detail})."
            ),
        },
    )


def _failure_detail(exc: Exception, repo_root: Path) -> str:
    if isinstance(exc, UnicodeDecodeError):
        return f"byte {exc.start}: {exc.reason}"
    if isinstance(exc, OSError):
        errno = exc.errno if exc.errno is not None else "unknown"
        return f"{type(exc).__name__}(errno={errno})"
    message = " ".join(str(exc).split()).replace(str(repo_root), ".")
    return f"{type(exc).__name__}: {message}" if message else type(exc).__name__


def _entry_matches_state(
    entry: SourceIndexEntry | None,
    expected_path: str,
    state: Mapping[str, Any],
) -> bool:
    return (
        entry is not None
        and entry.path == expected_path
        and entry.content_sha256 == state.get("sha256")
        and entry.source_bytes == state.get("bytes")
    )


def _fingerprint_manifest(
    repo_root: Path,
    layout: LeanSourceMap,
    options: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "fingerprintVersion": SOURCE_INDEX_FINGERPRINT_VERSION,
        "indexSchema": SOURCE_INDEX_SCHEMA,
        "algorithmVersion": SOURCE_INDEX_ALGORITHM_VERSION,
        "layout": {
            "status": layout.status,
            "roots": [root.to_dict(repo_root) for root in layout.roots],
            "modules": [
                {
                    "module": module,
                    "path": _relative_path(repo_root, path),
                }
                for module, path in sorted(layout.modules.items())
            ],
            "stateFiles": [
                _file_state(repo_root, repo_root / name, name=name)
                for name in LAYOUT_STATE_FILES
            ],
        },
        "options": dict(options),
        "sources": [
            {
                "module": module,
                **_source_file_state(
                    repo_root,
                    path,
                    name=_relative_path(repo_root, path),
                ),
            }
            for module, path in sorted(layout.modules.items())
        ],
    }


def _source_file_state(
    repo_root: Path,
    path: Path,
    *,
    name: str,
) -> dict[str, Any]:
    """Fingerprint one source or retain a stable unreadable state."""

    if not path.is_file():
        return {
            "path": name,
            "status": "absent",
            "bytes": 0,
            "sha256": None,
        }
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return {
            "path": name,
            "status": "unreadable",
            "bytes": _safe_file_size(path),
            "sha256": None,
            "cause": _failure_detail(exc, repo_root),
        }
    return {
        "path": name,
        "status": "present",
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _file_state(repo_root: Path, path: Path, *, name: str) -> dict[str, Any]:
    if not path.is_file():
        return {
            "path": name,
            "status": "absent",
            "bytes": 0,
            "sha256": None,
        }
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise SourceIndexError(f"cannot fingerprint {path}: {exc}") from exc
    return {
        "path": name,
        "status": "present",
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _safe_file_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def _relative_path(repo_root: Path, path: Path) -> str:
    resolved_root = repo_root.resolve()
    try:
        path.resolve().relative_to(resolved_root)
    except ValueError as exc:
        raise SourceIndexError(f"source path escapes repository: {path}") from exc
    try:
        return path.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise SourceIndexError(
            f"source path has no repository-relative identity: {path}"
        ) from exc


def _normalize_options(
    options: Mapping[str, Any],
) -> tuple[dict[str, Any], str | None]:
    try:
        encoded = json.dumps(
            dict(options),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        normalized = json.loads(encoded)
    except (TypeError, ValueError):
        return {}, "unfingerprintable_options"
    if not isinstance(normalized, dict):
        return {}, "unfingerprintable_options"
    return normalized, None


def _entry_reuse_compatible(
    previous: SourceIndex,
    current_manifest: Mapping[str, Any],
    options: Mapping[str, Any],
) -> bool:
    prior = previous.fingerprint_manifest
    return (
        previous.schema == SOURCE_INDEX_SCHEMA
        and previous.options == options
        and prior.get("fingerprintVersion")
        == current_manifest.get("fingerprintVersion")
        and prior.get("indexSchema") == current_manifest.get("indexSchema")
        and prior.get("algorithmVersion") == current_manifest.get("algorithmVersion")
    )


def _normalize_diagnostic(
    diagnostic: Mapping[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    root_text = str(repo_root)
    result: dict[str, Any] = {}
    for key, value in diagnostic.items():
        if isinstance(value, str):
            result[str(key)] = value.replace(root_text, ".")
        else:
            result[str(key)] = value
    return result


def _ordered_diagnostics(
    diagnostics: tuple[Mapping[str, Any], ...],
) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        sorted(
            (dict(row) for row in diagnostics),
            key=lambda row: (
                str(row.get("id", "")),
                str(row.get("module", "")),
                str(row.get("path", "")),
                str(row.get("cause", "")),
                str(row.get("subject", "")),
                str(row.get("message", "")),
            ),
        )
    )
