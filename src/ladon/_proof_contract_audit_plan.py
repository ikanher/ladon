"""Closed audit-plan validation, source identity, and canonical JSON helpers."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path

from .proof_contract_payloads import closed
from .resource_limits import DEFAULT_MAX_RSS_BYTES

PLAN_SCHEMA = "ladon-contract-audit-plan-v1"
MAX_PLAN_BYTES = 8 * 1024**2
MAX_STAGES = 64
MAX_OUTPUT = 8 * 1024**2
DEFAULT_OUTPUT = MAX_OUTPUT
MAX_SOURCE_BYTES = 8 * 1024**2
MAX_TOTAL_SOURCE_BYTES = 128 * 1024**2
DEFAULT_TIMEOUT = 90 * 60
OPERATIONS = frozenset({"produce-prose", "produce-formal", "propagate", "obligations",
                         "probe", "check-probe", "inspect", "refine"})
_ID = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")

def _load_plan(plan):
    if isinstance(plan, (str, os.PathLike)):
        with Path(plan).open("rb") as stream:
            raw = stream.read(MAX_PLAN_BYTES + 1)
        if len(raw) > MAX_PLAN_BYTES:
            raise ValueError("audit plan exceeds 8 MiB")
        from .proof_contract_io import _decode
        return _decode(raw), raw
    if not isinstance(plan, dict):
        raise TypeError("audit plan must be a path or JSON object")
    raw = _json_bytes(plan)
    if len(raw) > MAX_PLAN_BYTES:
        raise ValueError("audit plan exceeds 8 MiB")
    return json.loads(raw), raw

def _validate_plan(value):
    closed(value, {"schema", "repoRoot", "sourceFiles", "limits", "stages"}, "audit plan")
    if value["schema"] != PLAN_SCHEMA:
        raise ValueError("unsupported audit plan schema")
    if value["repoRoot"] is not None and (not isinstance(value["repoRoot"], str) or not value["repoRoot"]):
        raise ValueError("repoRoot must be null or a selected root path")
    if not isinstance(value["sourceFiles"], list) or len(value["sourceFiles"]) > 4096:
        raise ValueError("sourceFiles must be a bounded list")
    if value["repoRoot"] is None and value["sourceFiles"]:
        raise ValueError("sourceFiles require repoRoot")
    for name in value["sourceFiles"]:
        _safe_relative(name, "sourceFiles path")
    limits = _limits(value["limits"])
    _validate_stages(value["stages"], value["repoRoot"])
    return {"schema": PLAN_SCHEMA, "repoRoot": value["repoRoot"],
            "sourceFiles": list(value["sourceFiles"]), "limits": limits,
            "stages": value["stages"]}

def _validate_stages(stages, repo_root):
    if not isinstance(stages, list) or not 1 <= len(stages) <= MAX_STAGES:
        raise ValueError("stages must contain between 1 and 64 entries")
    ids, prose_position, match_positions = set(), [], []
    for index, row in enumerate(stages):
        _validate_stage_row(row, ids)
        operation = row["operation"]
        if operation == "produce-prose":
            prose_position.append(index)
        elif operation in {"produce-formal", "propagate", "obligations", "probe", "check-probe"}:
            match_positions.append(index)
        _require_source_root(operation, repo_root)
    _validate_pre_match_order(prose_position, match_positions)

def _validate_stage_row(row, ids):
    closed(row, {"id", "operation", "request"}, "audit stage")
    if not isinstance(row["id"], str) or not _ID.fullmatch(row["id"]) or row["id"] in ids:
        raise ValueError("stage IDs must be unique safe identifiers")
    ids.add(row["id"])
    if row["operation"] not in OPERATIONS:
        raise ValueError("unknown audit stage operation")
    if not isinstance(row["request"], dict):
        raise TypeError("stage request must be an object")
    _find_refs(row["request"], ids - {row["id"]})

def _require_source_root(operation, repo_root):
    if operation in {"produce-prose", "produce-formal", "probe", "check-probe"} and repo_root is None:
        raise ValueError(f"{operation} requires repoRoot")

def _validate_pre_match_order(prose, matching):
    if prose and matching and max(prose) > min(matching):
        raise ValueError("all produce-prose stages must precede formal/matching stages")

def _limits(value):
    defaults = {"timeout_seconds": float(DEFAULT_TIMEOUT),
                "max_rss_bytes": DEFAULT_MAX_RSS_BYTES,
                "max_output_bytes": DEFAULT_OUTPUT}
    if value is None:
        return defaults
    if not isinstance(value, dict) or not set(value) <= set(defaults):
        raise ValueError("limits must use existing timeout/RSS/output fields")
    result = dict(defaults)
    for key, raw in value.items():
        result[key] = _validated_limit(key, raw)
    return result

def _validated_limit(key, raw):
    if key == "timeout_seconds":
        if type(raw) not in (int, float) or not math.isfinite(raw) or raw <= 0 or raw > DEFAULT_TIMEOUT:
            raise ValueError("timeout_seconds must be finite, positive and at most 5400")
        return float(raw)
    if type(raw) is not int or raw <= 0:
        raise ValueError(f"{key} must be a positive integer")
    maximum = DEFAULT_MAX_RSS_BYTES if key == "max_rss_bytes" else DEFAULT_OUTPUT
    if raw > maximum:
        raise ValueError(f"{key} cannot exceed its default cap")
    return raw

def _root(value):
    if value is None:
        return None
    path = Path(value).resolve(strict=True)
    if not path.is_dir() or str(path) != value:
        raise ValueError("repoRoot must be an existing canonical directory path")
    return path

def _source_binding(root, names):
    if root is None:
        return None
    rows = []
    total = 0
    for name in names:
        path = _source_path(root, name)
        with path.open("rb") as stream:
            data = stream.read(MAX_SOURCE_BYTES + 1)
        if len(data) > MAX_SOURCE_BYTES:
            raise ValueError("audit source file exceeds 8 MiB")
        total += len(data)
        if total > MAX_TOTAL_SOURCE_BYTES:
            raise ValueError("audit source files exceed 128 MiB")
        rows.append({"path": name, "sha256": _sha(data)})
    from .proof_slice import pinned_toolchain
    try:
        context = pinned_toolchain(root).context_identity
    except (ValueError, TypeError, OSError) as error:
        raise ValueError("selected source root has no verified toolchain context") from error
    return {"root": str(root), "files": rows, "toolchainContext": context}

def _source_path(root, name):
    relative = _safe_relative(name, "source path")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("source paths may not traverse symlinks")
    path = current.resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("source path escapes the selected root or is not a file")
    return path

def _safe_relative(value, label):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError(f"{label} must be a relative POSIX path")
    path = Path(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError(f"{label} must be a safe relative path")
    return path

def _find_refs(value, earlier, depth=0):
    if depth > 64:
        raise ValueError("audit JSON/reference nesting exceeds depth 64")
    if isinstance(value, dict):
        if set(value) == {"auditStage", "pointer"}:
            if value["auditStage"] not in earlier:
                raise ValueError("stage references must name an earlier stage")
            if not isinstance(value["pointer"], str):
                raise ValueError("reference pointer must be JSON Pointer text")
            _pointer_parts(value["pointer"])
            return
        for child in value.values():
            _find_refs(child, earlier, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _find_refs(child, earlier, depth + 1)

def _resolve_refs(value, results, depth=0):
    if depth > 64:
        raise ValueError("audit JSON/reference nesting exceeds depth 64")
    if isinstance(value, dict) and set(value) == {"auditStage", "pointer"}:
        return _resolve_reference(value, results)
    if isinstance(value, dict):
        return {key: _resolve_refs(child, results, depth + 1) for key, child in value.items()}
    if isinstance(value, list):
        return [_resolve_refs(child, results, depth + 1) for child in value]
    return value

def _resolve_reference(reference, results):
    stage = reference["auditStage"]
    if stage not in results:
        raise ValueError("reference names a stage without a completed result")
    current = results[stage]
    for part in _pointer_parts(reference["pointer"]):
        current = _pointer_child(current, part)
    return current

def _pointer_child(current, part):
    if isinstance(current, dict) and part in current:
        return current[part]
    if isinstance(current, list) and part.isdecimal() and int(part) < len(current):
        return current[int(part)]
    raise ValueError("JSON Pointer does not resolve in the earlier stage result")

def _pointer_parts(pointer):
    if pointer == "":
        return []
    if not pointer.startswith("/") or len(pointer) > 4096 or pointer.count("/") > 64:
        raise ValueError("invalid or over-deep JSON Pointer")
    parts = []
    for part in pointer[1:].split("/"):
        if re.search(r"~(?![01])", part):
            raise ValueError("invalid JSON Pointer escape")
        parts.append(part.replace("~1", "/").replace("~0", "~"))
    return parts

def _validate_operation_request(operation, request, plan, root):
    if operation in {"propagate", "obligations"}:
        _validate_graph_request(request, operation)
    elif operation == "produce-prose":
        _validate_prose_request(request, plan)
    elif operation == "produce-formal":
        _validate_formal_request(request, plan)
    elif operation in {"probe", "check-probe"}:
        _validate_probe_request(request, operation, root)
    elif operation == "inspect":
        _validate_inspect_request(request, root)
    elif operation == "refine" and not isinstance(request, dict):
        raise TypeError("refinement request must be an object")

def _validate_graph_request(request, operation):
    label = "propagation stage" if operation == "propagate" else "obligations stage"
    closed(request, {"graph", "contracts", "request", "analysisId"}, label)

def _validate_prose_request(request, plan):
    closed(request, {"interpretation", "contract", "featureOrigins", "alternativeId",
                     "environmentRef", "author"}, "prose production stage")
    source = request.get("interpretation", {}).get("source", {})
    if not isinstance(source, dict) or source.get("path") not in plan["sourceFiles"]:
        raise ValueError("prose source path must be included in sourceFiles")

def _validate_formal_request(request, plan):
    closed(request, {"sourceFile", "module", "declaration"}, "formal production stage")
    if request["sourceFile"] not in plan["sourceFiles"]:
        raise ValueError("formal sourceFile must be included in sourceFiles")

def _validate_probe_request(request, operation, root):
    if root is None:
        raise ValueError("probe stages require repoRoot")
    if operation == "check-probe":
        closed(request, {"request", "planId", "terms"}, "probe check stage")
        closed(request["request"], {"context", "left", "right", "template"},
               "probe check request")
    elif not isinstance(request, dict):
        raise TypeError("probe request must be an object")
    else:
        closed(request, {"context", "left", "right", "template"}, "probe request")

def _validate_inspect_request(request, root):
    if not isinstance(request, dict):
        raise TypeError("inspect request must be an object")
    if set(request) == {"snapshot"} and root is None:
        raise ValueError("source snapshot inspection requires repoRoot")

def _runtime_identity():
    package = Path(__file__).resolve().parent
    rows = []
    for path in sorted([*package.rglob("*.py"), *package.rglob("*.lean")]):
        rows.append((path.relative_to(package).as_posix(), _sha(path.read_bytes())))
    return "sha256:" + _sha(_json_bytes(rows))

def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                        allow_nan=False) + "\n").encode("utf-8")

def _compact_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")

def _sha(data):
    return hashlib.sha256(data).hexdigest()
