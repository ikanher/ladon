"""Versioned cache fingerprints for Lean extraction payloads."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from ladon.ir import LeanModule
from ladon.lean_protocol import HELPER_VERSION, PROTOCOL_VERSION


CACHE_FINGERPRINT_VERSION = "ladon-lean-cache-v2"
LAKE_STATE_FILES = ("lakefile.toml", "lakefile.lean", "lake-manifest.json")
TOOLCHAIN_FILES = ("lean-toolchain",)
INVALIDATION_FIELDS = (
    ("protocolVersion", "protocol_changed"),
    ("helper", "helper_changed"),
    ("options", "options_changed"),
    ("leanVersion", "lean_version_changed"),
    ("toolchain", "toolchain_changed"),
    ("lakeState", "lake_state_changed"),
    ("source", "source_changed"),
    ("importClosure", "transitive_import_changed"),
    ("compiledState", "compiled_state_changed"),
)


@dataclass
class FileHashMemo:
    """Run-local content hashes reused across overlapping import closures."""

    values: dict[Path, tuple[int, int, str]] = field(default_factory=dict)

    def digest(self, path: Path) -> str:
        """Hash a file once per unchanged size/mtime tuple."""

        stat = path.stat()
        key = (stat.st_size, stat.st_mtime_ns)
        cached = self.values.get(path)
        if cached is not None and cached[:2] == key:
            return cached[2]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        self.values[path] = (*key, digest)
        return digest


@dataclass(frozen=True)
class CacheFingerprint:
    """One complete cache-validity manifest and its address."""

    digest: str
    manifest: Mapping[str, Any]
    cacheable: bool
    bypass_reason: str | None = None


@dataclass(frozen=True)
class CacheLookup:
    """Cache result with an inspectable invalidation classification."""

    status: str
    fingerprint: CacheFingerprint
    payload: Mapping[str, Any] | None = None
    invalidation_reason: str | None = None


class LeanCacheStore:
    """Content-addressed cache with per-module prior-manifest pointers."""

    def __init__(self, cache_dir: Path) -> None:
        self.root = cache_dir / CACHE_FINGERPRINT_VERSION

    def lookup(self, module: str, fingerprint: CacheFingerprint) -> CacheLookup:
        """Read an exact hit or classify a miss without weak hit claims."""

        if not fingerprint.cacheable:
            return CacheLookup(
                "bypassed",
                fingerprint,
                invalidation_reason=fingerprint.bypass_reason,
            )
        entry = self.entry_path(fingerprint)
        if entry.is_file():
            payload = read_cache_payload(entry, fingerprint)
            if payload is not None:
                return CacheLookup("hit", fingerprint, payload=payload)
        prior = read_json_mapping(self.latest_path(module))
        reason = invalidation_reason(prior, fingerprint.manifest)
        return CacheLookup("miss", fingerprint, invalidation_reason=reason)

    def store(
        self,
        module: str,
        fingerprint: CacheFingerprint,
        payload: Mapping[str, Any],
    ) -> None:
        """Persist a sound entry and its latest-manifest pointer."""

        if not fingerprint.cacheable:
            return
        entry = self.entry_path(fingerprint)
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text(
            json.dumps(
                {
                    "fingerprint": fingerprint.manifest,
                    "payload": payload,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        latest = self.latest_path(module)
        latest.parent.mkdir(parents=True, exist_ok=True)
        latest.write_text(
            json.dumps(fingerprint.manifest, sort_keys=True),
            encoding="utf-8",
        )

    def entry_path(self, fingerprint: CacheFingerprint) -> Path:
        """Return the content-addressed payload path."""

        return self.root / "entries" / f"{fingerprint.digest}.json"

    def latest_path(self, module: str) -> Path:
        """Return the prior-manifest pointer for one module."""

        key = hashlib.sha256(module.encode()).hexdigest()
        return self.root / "latest" / f"{key}.json"


def build_cache_fingerprint(
    *,
    repo_root: Path,
    module: str,
    source_path: Path,
    helper_path: Path,
    modules: Mapping[str, LeanModule],
    lean_version: str,
    extraction_options: Mapping[str, Any],
    hashes: FileHashMemo,
) -> CacheFingerprint:
    """Fingerprint every required local, helper, option, and environment input."""

    closure = resolved_local_import_closure(module, modules)
    compiled = compiled_state(repo_root, (module, *closure), hashes)
    cacheable = compiled["status"] == "fingerprinted"
    bypass_reason = None if cacheable else str(compiled["reason"])
    manifest = {
        "fingerprintVersion": CACHE_FINGERPRINT_VERSION,
        "protocolVersion": PROTOCOL_VERSION,
        "helperVersion": HELPER_VERSION,
        "helper": file_state(helper_path, hashes),
        "options": normalized_json(extraction_options),
        "leanVersion": lean_version,
        "toolchain": named_file_states(repo_root, TOOLCHAIN_FILES, hashes),
        "lakeState": named_file_states(repo_root, LAKE_STATE_FILES, hashes),
        "module": module,
        "source": file_state(source_path, hashes),
        "importClosure": [
            module_source_state(repo_root, name, modules[name], hashes)
            for name in closure
        ],
        "compiledState": compiled,
        "cacheSafety": {
            "status": "sound" if cacheable else "bypassed",
            "reason": bypass_reason,
        },
    }
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return CacheFingerprint(
        hashlib.sha256(encoded).hexdigest(),
        manifest,
        cacheable,
        bypass_reason,
    )


def resolved_local_import_closure(
    module: str,
    modules: Mapping[str, LeanModule],
) -> tuple[str, ...]:
    """Return the sorted transitive closure of locally resolved imports."""

    visited: set[str] = {module}
    pending = list(modules.get(module, LeanModule(module, "")).imports)
    while pending:
        current = pending.pop()
        if current in visited or current not in modules:
            continue
        visited.add(current)
        pending.extend(modules[current].imports)
    return tuple(sorted(visited - {module}))


def compiled_state(
    repo_root: Path,
    modules: Sequence[str],
    hashes: FileHashMemo,
) -> dict[str, Any]:
    """Fingerprint compiled local state or classify an unsafe cache bypass."""

    states: list[dict[str, Any]] = []
    missing: list[str] = []
    for module in modules:
        path = compiled_module_path(repo_root, module)
        if path is None:
            missing.append(module)
        else:
            states.append(
                {
                    "module": module,
                    "path": str(path.relative_to(repo_root)),
                    "sha256": hashes.digest(path),
                }
            )
    if missing:
        return {
            "status": "unavailable",
            "reason": "compiled state is unavailable for: " + ", ".join(missing),
            "files": states,
        }
    return {"status": "fingerprinted", "reason": None, "files": states}


def compiled_module_path(repo_root: Path, module: str) -> Path | None:
    """Find one conventional Lake compiled module artifact."""

    relative = Path(*module.split(".")).with_suffix(".olean")
    candidates = (
        repo_root / ".lake" / "build" / "lib" / "lean" / relative,
        repo_root / ".lake" / "build" / "lib" / relative,
    )
    return next((path for path in candidates if path.is_file()), None)


def named_file_states(
    repo_root: Path,
    names: Sequence[str],
    hashes: FileHashMemo,
) -> list[dict[str, Any]]:
    """Fingerprint present files and record absence explicitly."""

    return [
        {"name": name, **file_state(repo_root / name, hashes)}
        for name in names
    ]


def file_state(path: Path, hashes: FileHashMemo) -> dict[str, Any]:
    """Return explicit absent or SHA-256 file state."""

    if not path.is_file():
        return {"status": "absent", "path": str(path), "sha256": None}
    return {
        "status": "present",
        "path": str(path),
        "sha256": hashes.digest(path),
    }


def module_source_state(
    repo_root: Path,
    module: str,
    row: LeanModule,
    hashes: FileHashMemo,
) -> dict[str, Any]:
    """Fingerprint one resolved local import source."""

    state = file_state(repo_root / row.path, hashes)
    return {"module": module, **state}


def normalized_json(value: Mapping[str, Any]) -> dict[str, Any]:
    """Copy JSON-compatible options through a stable serialization."""

    return json.loads(json.dumps(dict(value), sort_keys=True))


def read_cache_payload(
    path: Path,
    fingerprint: CacheFingerprint,
) -> Mapping[str, Any] | None:
    """Read one entry only when its embedded manifest exactly matches."""

    row = read_json_mapping(path)
    if row.get("fingerprint") != fingerprint.manifest:
        return None
    payload = row.get("payload")
    return dict(payload) if isinstance(payload, Mapping) else None


def read_json_mapping(path: Path) -> Mapping[str, Any]:
    """Read a mapping or return an empty invalid-entry sentinel."""

    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, Mapping) else {}


def invalidation_reason(
    prior: Mapping[str, Any],
    current: Mapping[str, Any],
) -> str:
    """Return the first stable reason why a prior module entry is not valid."""

    if not prior:
        return "cold_miss"
    if prior.get("fingerprintVersion") != CACHE_FINGERPRINT_VERSION:
        return "fingerprint_version_changed"
    for field, reason in INVALIDATION_FIELDS:
        if prior.get(field) != current.get(field):
            return reason
    return "cache_entry_missing_or_invalid"
