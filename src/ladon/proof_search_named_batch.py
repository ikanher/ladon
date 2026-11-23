"""Ordered, bounded aggregation over independently validated search indexes."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ladon.proof_search_index import ProofSearchIndexError

_SCHEMA = "ladon-proof-search-named-batch-v1"
_MAX_MANIFEST_BYTES = 65536
_MAX_INDEXES = 8
_MAX_EXECUTIONS = 128


def _serialized_size(value):
    return len((json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ProofSearchIndexError(f"manifest {label} must be nonempty text")
    return value


def _manifest(path, default_freshness):
    from ladon.investigation import load_plan

    path = Path(path).resolve()
    try:
        raw = load_plan(path, max_bytes=_MAX_MANIFEST_BYTES)
    except (OSError, ValueError) as error:
        raise ProofSearchIndexError(f"cannot read named-index manifest: {error}") from error
    if not isinstance(raw, list) or not 1 <= len(raw) <= _MAX_INDEXES:
        raise ProofSearchIndexError("named-index manifest must contain 1..8 entries")
    entries, names = [], set()
    for raw_entry in raw:
        entry = _manifest_entry(raw_entry, path.parent, default_freshness)
        if entry["name"] in names:
            raise ProofSearchIndexError(f"duplicate named-index name: {entry['name']}")
        names.add(entry["name"])
        entries.append(entry)
    return entries


def _manifest_entry(raw_entry, base, default_freshness):
    _validate_entry_shape(raw_entry)
    name = _text(raw_entry.get("name"), "name")
    mode = _entry_freshness(raw_entry, default_freshness, name)
    repo_value, index_value = _entry_paths(raw_entry)
    _validate_entry_requirements(name, mode, repo_value, index_value)
    repo = (base / repo_value).resolve() if repo_value is not None else None
    index = (base / index_value).resolve() if index_value is not None else None
    return {"name": name, "repoRoot": repo, "indexPath": index, "freshness": mode}


def _validate_entry_shape(raw_entry):
    allowed = {"name", "repoRoot", "indexPath", "freshness"}
    if not isinstance(raw_entry, dict) or set(raw_entry) - allowed:
        raise ProofSearchIndexError("each named-index entry must be an object with supported fields")


def _entry_freshness(raw_entry, default, name):
    mode = raw_entry.get("freshness", default)
    if not isinstance(mode, str) or mode not in {"verify", "stored"}:
        raise ProofSearchIndexError(f"invalid freshness for named index {name}")
    return mode


def _entry_paths(raw_entry):
    repo_value, index_value = raw_entry.get("repoRoot"), raw_entry.get("indexPath")
    repo_value = _text(repo_value, "repoRoot") if repo_value is not None else None
    index_value = _text(index_value, "indexPath") if index_value is not None else None
    return repo_value, index_value


def _validate_entry_requirements(name, mode, repo_value, index_value):
    if mode == "verify" and repo_value is None:
        raise ProofSearchIndexError(f"verified named index {name} requires repoRoot")
    if mode == "stored" and repo_value is None and index_value is None:
        raise ProofSearchIndexError(f"stored named index {name} requires repoRoot or indexPath")


def run_named_batch(manifest_path, queries, *, freshness="verify", max_output_bytes=1024**2):
    """Run common lexical queries against manifest entries in their declared order.

    Manifest and query shape validation complete before any index is opened. Each
    entry then receives its own normal batch validation window and byte allowance.
    """
    from ladon.proof_search_batch import _requests, run_prepared_batch

    _validate_options(freshness, max_output_bytes)
    requests = _requests(queries)
    entries = _manifest(manifest_path, freshness)
    if len(entries) * len(requests) > _MAX_EXECUTIONS:
        raise ProofSearchIndexError("named-index batch exceeds 128 library-query executions")
    groups = _run_groups(entries, requests, run_prepared_batch, max_output_bytes)
    result = _aggregate(groups, len(entries))
    _ensure_bounded(result, max_output_bytes)
    return result


def _validate_options(freshness, max_output_bytes):
    if not isinstance(freshness, str) or freshness not in {"verify", "stored"}:
        raise ProofSearchIndexError("freshness must be verify or stored")
    if type(max_output_bytes) is not int or not 1024**2 <= max_output_bytes <= 16 * 1024**2:
        raise ProofSearchIndexError("batch output allowance must be 1..16 MiB")


def _run_groups(entries, requests, runner, max_bytes):
    groups = []
    for entry in entries:
        group = _run_group(entry, requests, runner, max_bytes)
        groups.append(group)
        _ensure_bounded(_aggregate(groups, len(entries)), max_bytes)
    return groups


def _run_group(entry, requests, runner, max_bytes):
    group = {"name": entry["name"], "repoRoot": str(entry["repoRoot"]) if entry["repoRoot"] else None,
             "indexPath": str(entry["indexPath"]) if entry["indexPath"] else None,
             "freshness": entry["freshness"]}
    try:
        batch = runner(entry["repoRoot"], requests, index_path=entry["indexPath"],
                       freshness=entry["freshness"], max_output_bytes=max_bytes)
    except (ProofSearchIndexError, OSError, ValueError, sqlite3.Error) as error:
        group.update(status="unavailable", error={"message": str(error)[:512],
                                                   "exitClass": getattr(error, "exit_class", "operational")})
        return group
    _copy_batch_identity(group, batch)
    if group["status"] != "available":
        group["error"] = {"message": f"library batch status: {group['status']}",
                          "freshness": batch.get("freshness"), "exitClass": "operational"}
    return group


def _copy_batch_identity(group, batch):
    group.update(status=batch.get("status", "unavailable"),
                 generationIdentity=batch.get("generationIdentity"), batch=batch)
    group["indexPath"] = batch.get("indexPath", group["indexPath"])
    group["repoRoot"] = batch.get("validation", {}).get("repository", group["repoRoot"])
    group["freshness"] = batch.get("freshness", group["freshness"])


def _aggregate(groups, expected_groups):
    successful = sum(group["status"] == "available" for group in groups)
    status = "available" if successful == expected_groups else "partial" if successful else "unavailable"
    return {"schema": _SCHEMA, "operation": "search-batch", "status": status,
            "groups": groups, "returnedGroups": len(groups),
            "nonclaims": ["Each library has an independent index read and freshness observation.",
                          "Lexical results are not Lean checking or compiled proof dependency evidence."]}


def _ensure_bounded(result, max_bytes):
    if _serialized_size(result) > max_bytes:
        raise ProofSearchIndexError("named-index aggregate exceeds selected byte allowance; no output was published",
                                    exit_class="operational")
