"""Live source-delta diagnostics for a published lexical generation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ladon.proof_search_schema import (
    EVIDENCE_INDEX_SCHEMA,
    EVIDENCE_SCHEMA_GENERATION,
    PROOF_SEARCH_HELPER_IDENTITY,
    PROOF_SEARCH_INDEX_SCHEMA,
    PROOF_SEARCH_SCHEMA_GENERATION,
)

if TYPE_CHECKING:
    from ladon.proof_search_index import RepositorySnapshot


def _freshness_details(
    repo_root: Path,
    metadata: Mapping[str, str],
    stored_sources: Mapping[str, tuple[str, str, str, bool, int]],
    *,
    verify_sources: bool,
    changed_limit: int,
    capture,
    scope: str | None = None,
    roots: Sequence[str] = (),
) -> tuple[str, str | None, dict[str, Any]]:
    if not verify_sources:
        return "unchecked", None, {"status": "not-checked", "queryImpact": "not-checked"}
    snapshot = capture(repo_root)
    current_sources = {
        source.module: (
            source.relative_path, source.sha256, source.package,
            source.generated, source.source_bytes,
        )
        for source in snapshot.sources
    }
    changes = _changed_sources(current_sources, stored_sources)
    detail = {
        "status": "compared",
        "counts": {kind: len(rows) for kind, rows in changes.items()},
        "samples": {kind: rows[:changed_limit] for kind, rows in changes.items()},
        "truncated": {kind: len(rows) > changed_limit for kind, rows in changes.items()},
        "currentConfigurationFingerprint": snapshot.configuration_fingerprint,
        "currentSourceFingerprint": snapshot.source_fingerprint,
        "currentLayoutStatus": snapshot.layout.status,
    }
    if capture(repo_root).generation_identity != snapshot.generation_identity:
        return "unstable-source", None, {"status": "unstable"}
    freshness, generation = _freshness_from_snapshot(snapshot, metadata)
    detail["queryImpact"] = _query_impact(freshness, changes, scope, roots)
    return freshness, generation, detail


def _changed_sources(current_sources, stored_sources) -> dict[str, list[dict[str, str]]]:
    changes: dict[str, list[dict[str, str]]] = {key: [] for key in ("added", "changed", "removed")}
    for module in sorted(current_sources.keys() | stored_sources.keys()):
        if module not in stored_sources:
            kind = "added"
            path = current_sources[module][0]
        elif module not in current_sources:
            kind = "removed"
            path = stored_sources[module][0]
        elif current_sources[module] != stored_sources[module]:
            kind = "changed"
            path = current_sources[module][0]
        else:
            continue
        changes[kind].append({"module": module, "path": path})
    return changes


def _query_impact(
    freshness: str,
    changes: Mapping[str, list[dict[str, str]]],
    scope: str | None,
    roots: Sequence[str],
) -> str:
    if freshness == "fresh":
        return "current"
    if freshness != "stale-source":
        return "unknown"
    changed_modules = _changed_values(changes, "module")
    if scope in {"repository", "project"}:
        return "affected" if changed_modules else "unknown"
    if scope == "module":
        return _selected_impact(changed_modules, roots)
    if scope == "file":
        changed_paths = _changed_values(changes, "path")
        return _selected_impact(changed_paths, roots)
    return "unknown"


def _changed_values(changes: Mapping[str, list[dict[str, str]]], key: str) -> set[str]:
    return {row[key] for rows in changes.values() for row in rows}


def _selected_impact(changed: set[str], roots: Sequence[str]) -> str:
    return "affected" if changed & set(roots) else "unaffected"


def _freshness_from_snapshot(
    snapshot: RepositorySnapshot, metadata: Mapping[str, str]
) -> tuple[str, str]:
    if (metadata.get("indexSchema"), metadata.get("schemaGeneration")) not in {
        (PROOF_SEARCH_INDEX_SCHEMA, PROOF_SEARCH_SCHEMA_GENERATION),
        (EVIDENCE_INDEX_SCHEMA, EVIDENCE_SCHEMA_GENERATION),
    }:
        return "incompatible-schema", snapshot.generation_identity
    if metadata.get("toolchainIdentity") != snapshot.toolchain_identity:
        return "incompatible-toolchain", snapshot.generation_identity
    if metadata.get("configurationFingerprint") != snapshot.configuration_fingerprint:
        return "stale-configuration", snapshot.generation_identity
    if metadata.get("sourceFingerprint") != snapshot.source_fingerprint:
        return "stale-source", snapshot.generation_identity
    if metadata.get("helperIdentity") != PROOF_SEARCH_HELPER_IDENTITY or (
        metadata.get("layoutStatus") != snapshot.layout.status
    ):
        return "stale-configuration", snapshot.generation_identity
    if metadata.get("generationIdentity") != snapshot.generation_identity:
        return "stale-configuration", snapshot.generation_identity
    return "fresh", snapshot.generation_identity


def inspect_freshness(repo_root, *, index_path=None, expected_generation=None):
    """Check supported current inputs without auditing historical databases."""
    import time

    from ladon.proof_search_index import (
        _resolved_index_path,
        capture_repository_snapshot,
    )

    root = repo_root.resolve()
    path = _resolved_index_path(root, index_path)
    started = time.monotonic()
    metadata, sources = _read_freshness_identity(path)
    read_seconds = time.monotonic() - started
    freshness, current, changes = _freshness_details(
        root, metadata, sources, verify_sources=True, changed_limit=5,
        capture=capture_repository_snapshot,
    )
    generation = metadata.get('generationIdentity')
    return {
        'schema': 'ladon-proof-search-freshness-v1', 'operation': 'freshness',
        'status': 'available', 'indexPath': str(path), 'repository': str(root),
        **{key: metadata.get(key) for key in ('sourceFingerprint', 'configurationFingerprint',
                                             'toolchainIdentity', 'helperIdentity', 'indexSchema')},
        'generationIdentity': generation, 'currentGenerationIdentity': current,
        'freshness': freshness, 'sourceChanges': changes,
        'expectedGenerationIdentity': expected_generation,
        'unchangedSinceExpectedGeneration': (
            freshness == 'fresh' and generation == expected_generation
            if expected_generation is not None else None
        ),
        'historyIntegrity': 'not-assessed',
        'phaseSeconds': {'storedIdentity': read_seconds,
                         'sourceValidation': time.monotonic() - started - read_seconds},
        'elapsedSeconds': time.monotonic() - started,
        'nonclaim': 'Observation of supported source/configuration inputs against the read index generation; not proof replay or a guarantee against later edits.',
    }


def _read_freshness_identity(path):
    import sqlite3
    from contextlib import closing

    from ladon.proof_search_index import (
        ProofSearchIndexError,
        _metadata,
        _open_readonly,
        _require_query_schema,
        _stored_sources,
    )

    try:
        with closing(_open_readonly(path)) as connection:
            connection.execute("BEGIN")
            metadata = _metadata(connection)
            _require_query_schema(metadata)
            return metadata, _stored_sources(connection)
    except (OSError, sqlite3.Error) as error:
        raise ProofSearchIndexError(f"index unavailable for freshness check: {error}",
                                    exit_class="operational") from error
