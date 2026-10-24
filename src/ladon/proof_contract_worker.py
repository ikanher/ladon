"""Bounded formal contract worker helpers."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from importlib import resources
from pathlib import Path

from ladon.resource_limits import memory_limit_message

SCHEMA = "ladon-contract-production-v1"

CHANNEL = "formal"

PROFILE = "norm-scale-v1"

HELPER_VERSION = "ladon-formal-contract-helper-v2"

PROTOCOL_VERSION = "ladon-formal-contract-observation-v2"

MAX_SOURCE_BYTES = 8 * 1024 * 1024

MAX_OUTPUT_BYTES = 8 * 1024 * 1024

MAX_EXPR_NODES = 100_000

_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*\Z")

DEFAULT_HELPER = Path(
    str(resources.files("ladon").joinpath("lean", "ladon_formal_contract_helper.lean"))
)

def _validate_worker(worker, module, source_file, declaration):
    common = {
        "version": "1",
        "helperVersion": HELPER_VERSION,
        "protocolVersion": PROTOCOL_VERSION,
        "module": module,
        "file": source_file,
        "target": declaration,
    }
    if not isinstance(worker, dict) or any(
        worker.get(key) != value for key, value in common.items()
    ):
        raise ValueError("Lean worker identity does not match the requested source target")
    if worker.get("status") not in {
        "observed",
        "not_found",
        "module_mismatch",
        "elaboration_failed",
    }:
        raise ValueError("Lean worker status is invalid")
    expected_keys = _worker_keys(common, worker["status"])
    if set(worker) != expected_keys:
        raise ValueError("Lean worker observation has unexpected or missing fields")
    if worker["status"] == "observed":
        _validate_observed_worker(worker)

def _worker_keys(common, status):
    base = set(common) | {"status", "leanVersion"}
    if status != "observed":
        return base | {"reason"}
    return base | {
        "typeFingerprint",
        "typeExpr",
        "normalizedTypeFingerprint",
        "normalizedTypeExpr",
        "sourceModuleOwned",
        "declarationRange",
    }

def _validate_observed_worker(worker):
    if any(
        not isinstance(worker.get(field), expected)
        for field, expected in (
            ("typeExpr", dict),
            ("normalizedTypeExpr", dict),
            ("typeFingerprint", str),
            ("normalizedTypeFingerprint", str),
        )
    ):
        raise ValueError("Lean worker statement expression is incomplete")
    if worker.get("sourceModuleOwned") is not True or not isinstance(
        worker.get("declarationRange"), dict
    ):
        raise ValueError("Lean worker statement source ownership is incomplete")
    _validate_declaration_range(worker["declarationRange"])

def _parse_worker(encoded):
    _ensure_json_depth(encoded, 256)
    try:
        payload = json.loads(encoded, object_pairs_hook=_unique_json_object)
    except RecursionError as error:
        raise ValueError("Lean worker JSON exceeds the decoder recursion bound") from error
    if not isinstance(payload, dict):
        raise TypeError("Lean worker observation must be an object")
    return payload

def _ensure_json_depth(encoded, maximum):
    depth = 0
    in_string = False
    escaped = False
    for char in encoded:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
            if depth > maximum:
                raise ValueError("Lean worker JSON exceeds the nesting bound")
        elif char in "]}":
            depth -= 1

def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Lean worker JSON contains a duplicate object key")
        result[key] = value
    return result

def _validate_declaration_range(value):
    fields = {
        "startLine",
        "startColumn",
        "endLine",
        "endColumn",
        "selectionStartLine",
        "selectionStartColumn",
        "selectionEndLine",
        "selectionEndColumn",
    }
    if set(value) != fields:
        raise ValueError("Lean worker declaration range has unexpected fields")
    if any(type(value[field]) is not int or value[field] < 0 for field in fields):
        raise ValueError("Lean worker declaration range must contain nonnegative integers")
    if value["startLine"] < 1 or value["endLine"] < value["startLine"]:
        raise ValueError("Lean worker declaration range is outside source coordinates")
    if (
        value["selectionStartLine"] < value["startLine"]
        or value["selectionEndLine"] > value["endLine"]
    ):
        raise ValueError("Lean worker selection range is outside its declaration range")

def _process_receipt(process, timeout, rss):
    receipt = asdict(process)
    receipt["command"] = list(receipt["command"])
    for stream in ("stdout", "stderr"):
        raw = receipt.pop(stream).encode("utf-8")
        receipt[stream + "Bytes"] = len(raw)
        receipt[stream + "Digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    receipt["phase"] = "lean-statement-observation"
    receipt["requestedTimeoutSeconds"] = timeout
    receipt["requestedMaxRssBytes"] = rss
    return receipt

def _process_failure_code(process):
    if process.timed_out:
        return "lean-timeout"
    if process.memory_limited:
        return "lean-memory-limit"
    if process.output_limited:
        return "lean-output-limit"
    return "lean-process-failed"

def _process_failure_message(process, max_rss_bytes):
    if process.timed_out:
        return "bounded Lean statement observation timed out"
    if process.memory_limited:
        return memory_limit_message(max_rss_bytes, process.peak_rss_bytes)
    if process.output_limited:
        return "bounded Lean statement observation exceeded its output limit"
    return "bounded Lean statement observation failed"
