"""Bounded formal contract production helpers."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from typing import Any

from ladon.lean_toolchain import verify_toolchain_identities
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_contract_expressions import _Unsupported
from ladon.proof_contract_recognition import _contract_record, _recognize_estimate
from ladon.proof_contract_worker import (
    _NAME,
    CHANNEL,
    DEFAULT_HELPER,
    MAX_OUTPUT_BYTES,
    MAX_SOURCE_BYTES,
    PROTOCOL_VERSION,
    SCHEMA,
    _parse_worker,
    _process_failure_code,
    _process_failure_message,
    _process_receipt,
    _validate_worker,
)
from ladon.proof_slice import pinned_toolchain
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.semantic_candidate_limits import validate_semantic_bounds
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.source_association_io import _read_regular, _source_path


def produce_formal_contract(
    repo_root: Path,
    source_file: str,
    module: str,
    declaration: str,
    *,
    timeout_seconds: float = 60,
    max_rss_bytes: int = DEFAULT_MAX_RSS_BYTES,
    max_output_bytes: int = MAX_OUTPUT_BYTES,
    runner=None,
) -> dict[str, Any]:
    """Observe one exact Lean statement and recognize a narrow estimate shape."""

    root = _validate_request(
        repo_root, module, declaration, timeout_seconds, max_rss_bytes, max_output_bytes
    )
    captured = _capture_inputs(root, source_file, module)
    process = _run_worker(
        captured, source_file, module, declaration, timeout_seconds, max_rss_bytes,
        max_output_bytes=max_output_bytes, runner=runner,
    )
    _verify_inputs(captured, MAX_SOURCE_BYTES)
    return _process_observation(
        captured, process, source_file, module, declaration, timeout_seconds, max_rss_bytes,
        max_output_bytes=max_output_bytes,
    )

def _validate_request(repo_root, module, declaration, timeout_seconds, max_rss_bytes,
                      max_output_bytes=MAX_OUTPUT_BYTES):
    root = Path(repo_root).resolve(strict=True)
    if not _NAME.fullmatch(module) or not _NAME.fullmatch(declaration):
        raise ValueError("module and declaration must be ordinary qualified names")
    validate_semantic_bounds(timeout_seconds, max_output_bytes, max_rss_bytes)
    return root

def _capture_inputs(root, source_file, module):
    source_path = _source_path(root, source_file, module)
    source_bytes = _read_regular(source_path, MAX_SOURCE_BYTES)
    toolchain = pinned_toolchain(root)
    execution = prepare_direct_lean_execution(root, None, toolchain, require_compiled_module=False)
    helper_bytes = DEFAULT_HELPER.read_bytes()
    return {
        "root": root,
        "sourcePath": source_path,
        "sourceBytes": source_bytes,
        "sourceHash": hashlib.sha256(source_bytes).hexdigest(),
        "toolchain": toolchain,
        "execution": execution,
        "helperBytes": helper_bytes,
        "helperHash": hashlib.sha256(helper_bytes).hexdigest(),
    }

def _run_worker(captured, source_file, module, declaration, timeout_seconds, max_rss_bytes,
                *, max_output_bytes=MAX_OUTPUT_BYTES, runner=None):
    with tempfile.TemporaryDirectory(prefix="ladon-formal-contract-") as temporary:
        private = Path(temporary)
        source_snapshot = private / "target.lean"
        helper_snapshot = private / "helper.lean"
        source_snapshot.write_bytes(captured["sourceBytes"])
        helper_snapshot.write_bytes(captured["helperBytes"])
        result_path = private / "statement.json"
        supervise = run_bounded_target_process if runner is None else runner
        process = supervise(
            [
                *captured["execution"].command,
                "--run",
                str(helper_snapshot),
                module,
                source_file,
                str(source_snapshot),
                declaration,
                str(result_path),
            ],
            cwd=captured["root"],
            env=captured["execution"].environment,
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
            max_rss_bytes=max_rss_bytes,
        )
        captured["workerJson"] = (
            _read_regular(result_path, max_output_bytes).decode("utf-8")
            if result_path.exists() else None
        )
        return process

def _verify_inputs(captured, max_source_bytes):
    source_after = _read_regular(captured["sourcePath"], max_source_bytes)
    if (
        source_after != captured["sourceBytes"]
        or DEFAULT_HELPER.read_bytes() != captured["helperBytes"]
    ):
        raise ValueError("source or helper changed during formal statement observation")
    verify_toolchain_identities(captured["toolchain"])

def _process_observation(captured, process, source_file, module, declaration, timeout, max_rss,
                          *, max_output_bytes=MAX_OUTPUT_BYTES):
    receipt = _process_receipt(process, timeout, max_rss)
    receipt["requestedMaxOutputBytes"] = max_output_bytes
    envelope = {
        "schema": SCHEMA,
        "channel": CHANNEL,
        "status": "unavailable",
        "contract": None,
        "featureOrigins": {
            "regularity": [],
            "constantDependencies": [],
            "witnessDependencies": [],
        },
        "residuals": [],
        "source": {"path": source_file, "sha256": captured["sourceHash"]},
        "selection": {"module": module, "declaration": declaration},
        "environment": captured["toolchain"].context_identity,
        "helper": {"sha256": captured["helperHash"], "profile": PROTOCOL_VERSION},
        "processReceipts": [receipt],
        "observation": None,
        "coverage": {
            "statementFeatures": "unsupported",
            "providers": "not-extracted",
            "proofBody": "not-extracted",
        },
        "fidelity": "attributed-unreviewed",
    }
    if not process.succeeded:
        return _record_process_failure(envelope, process, max_rss)
    return _consume_worker_observation(
        envelope, captured["workerJson"], captured["toolchain"], module, source_file, declaration
    )

def _record_process_failure(envelope, process, max_rss):
    envelope["residuals"] = [
        {
            "code": _process_failure_code(process),
            "message": _process_failure_message(process, max_rss),
            "feature": "statement",
        }
    ]
    return envelope

def _consume_worker_observation(envelope, encoded, toolchain, module, source_file, declaration):
    if encoded is None:
        envelope["residuals"] = [{"code": "helper-result-missing", "feature": "statement",
                                  "message": "Lean exited without a completed helper result"}]
        return envelope
    envelope["processReceipts"][0]["helperResultDigest"] = "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()
    envelope["processReceipts"][0]["helperResultBytes"] = len(encoded.encode())
    worker = _parse_worker(encoded)
    envelope["observation"] = worker
    _validate_worker(worker, module, source_file, declaration)
    if worker.get("leanVersion") != toolchain.lean_release:
        raise ValueError("Lean worker version differs from the pinned toolchain")
    if not _worker_has_statement(worker):
        return _record_unavailable_statement(envelope, worker)

    try:
        summary = _recognize_estimate(worker["normalizedTypeExpr"])
    except _Unsupported as error:
        return _record_unsupported_statement(envelope, error)
    return _record_extracted_statement(envelope, worker, summary, declaration)

def _worker_has_statement(worker):
    return (
        worker["status"] == "observed"
        and isinstance(worker.get("typeExpr"), dict)
        and isinstance(worker.get("normalizedTypeExpr"), dict)
    )

def _record_unavailable_statement(envelope, worker):
    envelope["residuals"] = [
        {
            "code": "statement-unavailable",
            "message": str(worker.get("reason") or "Lean did not return a statement type"),
            "feature": "statement",
        }
    ]
    return envelope

def _record_unsupported_statement(envelope, error):
    envelope["status"] = "unsupported"
    envelope["residuals"] = [{"code": error.code, "message": str(error), "feature": error.feature}]
    envelope["coverage"]["statementFeatures"] = "unsupported"
    return envelope

def _record_extracted_statement(envelope, worker, summary, declaration):
    record = _contract_record(summary)
    from ladon.proof_contracts import validate_contract

    envelope["contract"] = validate_contract(record)
    envelope["status"] = "extracted"
    envelope["coverage"]["statementFeatures"] = "complete"
    envelope["featureOrigins"] = _feature_origins(worker, summary, declaration)
    return envelope

def _feature_origins(worker, summary, declaration):
    scale_ref = summary["regularityOriginPath"]
    coefficient_ref = _constant_origin(summary)
    witnesses = [
        f"{declaration}#{binder['originPath']}"
        for binder in summary["binders"]
        if binder["quantifier"] == "exists"
    ]
    return {
        "regularity": [f"{declaration}#{scale_ref or '/normalizedTypeExpr'}"],
        "constantDependencies": [f"{declaration}#{coefficient_ref or '/normalizedTypeExpr'}"],
        "witnessDependencies": witnesses,
    }

def _constant_origin(summary):
    anchor = summary["constantAnchor"]
    if anchor is None:
        return summary["constantOriginPath"]
    return next(row["originPath"] for row in summary["binders"] if row["binderId"] == anchor)

# Compatibility exports for the observation protocol boundary.
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
