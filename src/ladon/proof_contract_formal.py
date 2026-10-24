"""Immutable statement snapshots and explicit requests for deeper proof slices."""

import hashlib
from copy import deepcopy
from pathlib import Path

from ladon.proof_contract_artifacts import source_contract_artifact
from ladon.proof_contract_rules import PROFILE_DIGEST
from ladon.proof_contract_source import snapshot_identity
from ladon.proof_slice import _validate_selection, extract_proof_slice, pinned_toolchain
from ladon.proofir_v3 import canonical_bytes, make_envelope, validate_envelope_batch
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.source_association_io import _read_regular, _source_path


def _environment(root):
    return pinned_toolchain(Path(root)).context_identity


def _observe(*args, **kwargs):
    from ladon.proof_contract_production import produce_formal_contract

    return produce_formal_contract(*args, **kwargs)


def _helper_digest():
    from ladon.proof_contract_production import DEFAULT_HELPER

    return hashlib.sha256(DEFAULT_HELPER.read_bytes()).hexdigest()


def produce_formal_snapshot(root, source_file, module, declaration, *,
                            timeout_seconds=60, max_rss_bytes=DEFAULT_MAX_RSS_BYTES,
                            max_output_bytes=8 * 1024**2, runner=None):
    """Observe the statement without demanding any proof body or provider slice."""
    result = _observe(root, source_file, module, declaration,
                      timeout_seconds=timeout_seconds, max_rss_bytes=max_rss_bytes,
                      max_output_bytes=max_output_bytes, runner=runner)
    result["profileDigest"] = PROFILE_DIGEST
    result["artifacts"] = _artifacts(result, root)
    result["snapshotId"] = snapshot_identity(result)
    return result


def _position(lines, line, column):
    if not 1 <= line <= len(lines) or not 0 <= column <= len(lines[line - 1].rstrip("\r\n")):
        raise ValueError("formal declaration range is outside the original source")
    prefix = "".join(lines[:line - 1]) + lines[line - 1][:column]
    return {"byte": len(prefix.encode("utf-8")), "line": line, "column": column + 1}


def _artifacts(snapshot, root):
    if snapshot["contract"] is None:
        return []
    source = snapshot["source"]
    selection = snapshot["selection"]
    path = _source_path(Path(root).resolve(strict=True), source["path"], selection["module"])
    raw = _read_regular(path, 8 * 1024**2)
    if hashlib.sha256(raw).hexdigest() != source["sha256"]:
        raise ValueError("stale formal source digest")
    lines = raw.decode("utf-8").splitlines(keepends=True)
    location = snapshot["observation"]["declarationRange"]
    identity = "formal:" + hashlib.sha256(canonical_bytes({
        "source": source, "selection": selection, "environment": snapshot["environment"],
    })).hexdigest()
    source_ref = {"kind": "source-map", "localId": "source-map:" + identity}
    declaration_ref = {"kind": "declaration", "localId": selection["declaration"]}
    policy = {"version": "elaborated-declaration-range-v1"}
    source_map = make_envelope(
        artifact_kind="proofir.source-map",
        producer={"name": "ladon-formal-contract", "version": "1"},
        environment_ref=snapshot["environment"], subject_refs=[source_ref, declaration_ref],
        coverage={"status": "complete", "observed": 1},
        payload={"sourceMapId": source_ref["localId"], "policy": {
            **policy, "digest": "sha256:" + hashlib.sha256(canonical_bytes(policy)).hexdigest(),
        }, "anchors": [{
            "subjectRef": declaration_ref, "sourcePath": source["path"],
            "module": selection["module"], "declName": selection["declaration"],
            "start": _position(lines, location["startLine"], location["startColumn"]),
            "end": _position(lines, location["endLine"], location["endColumn"]),
            "contentDigest": "sha256:" + source["sha256"],
            "matchMethod": "producer-declaration",
        }]}, limitations=[{"id": "statement-summary-fidelity-unreviewed", "message":
                           "An observed declaration range does not certify summary fidelity."}],
    ).to_dict()
    contract = source_contract_artifact(
        snapshot["contract"], contract_id=identity, environment_ref=snapshot["environment"],
        source_map_refs=[{"artifactRef": source_map["artifactId"], **source_ref}],
        mode="extracted", residuals=snapshot["residuals"],
    )
    result = [source_map, contract]
    validate_envelope_batch(result)
    return result


def verify_formal_snapshot(snapshot, root):
    """Check freshness and deterministic attachments; never re-elaborate a body."""
    if (snapshot.get("schema") != "ladon-contract-production-v1"
            or snapshot.get("channel") != "formal"
            or snapshot.get("snapshotId") != snapshot_identity(snapshot)):
        raise ValueError("invalid or altered formal snapshot identity")
    if snapshot.get("profileDigest") != PROFILE_DIGEST:
        raise ValueError("stale mathematical profile")
    if snapshot["environment"] != _environment(root):
        raise ValueError("stale formal environment")
    if snapshot["helper"]["sha256"] != _helper_digest():
        raise ValueError("stale formal helper")
    selection = snapshot["selection"]
    path = _source_path(Path(root).resolve(strict=True), snapshot["source"]["path"],
                        selection["module"])
    if hashlib.sha256(_read_regular(path, 8 * 1024**2)).hexdigest() != snapshot["source"]["sha256"]:
        raise ValueError("stale formal source digest")
    _verify_summary(snapshot)
    if snapshot["artifacts"] != _artifacts(snapshot, root):
        raise ValueError("formal snapshot attachments differ from observation")
    return deepcopy(snapshot)


def _extract_slice(*args, **kwargs):
    return extract_proof_slice(*args, **kwargs)


def expand_formal_snapshot(snapshot, root, *, application, obligation_id, occurrence=0):
    """Expand a named obligation while keeping the frozen statement observation."""
    from ladon.proof_contract_payloads import identifier

    frozen = verify_formal_snapshot(snapshot, root)
    selection = frozen["selection"]
    _validate_selection(selection["module"], selection["declaration"], application, occurrence)
    identifier(obligation_id, "expansion obligation")
    request = {"statementSnapshotId": frozen["snapshotId"], "obligationId": obligation_id,
               "application": application, "occurrence": occurrence}
    sliced = _extract_slice(Path(root), frozen["source"]["path"], selection["module"],
                            selection["declaration"], application, occurrence, scoped=True)
    # Even a successful selected slice does not cover all providers or the whole body.
    result = {"schema": "ladon-contract-expansion-v1", "request": request,
              "statementSnapshot": frozen, "slice": sliced,
              "coverage": {"statementFeatures": frozen["coverage"]["statementFeatures"],
                           "providers": "incomplete", "proofBody": "incomplete"}}
    result["snapshotId"] = snapshot_identity(result)
    return result


def _verify_summary(snapshot):
    from ladon.proof_contract_worker import PROTOCOL_VERSION, _validate_worker

    if snapshot["fidelity"] != "attributed-unreviewed":
        raise ValueError("formal observation cannot establish source fidelity")
    if snapshot["helper"]["profile"] != PROTOCOL_VERSION:
        raise ValueError("stale formal observation protocol")
    worker = snapshot["observation"]
    if worker is None:
        if snapshot["contract"] is not None or snapshot["status"] != "unavailable":
            raise ValueError("missing observation cannot supply an extracted summary")
        return
    selection = snapshot["selection"]
    _validate_worker(worker, selection["module"], snapshot["source"]["path"],
                     selection["declaration"])
    expected = _replay_summary(snapshot, worker, selection["declaration"])
    keys = ("status", "contract", "featureOrigins", "coverage", "residuals")
    if any(snapshot[key] != expected[key] for key in keys):
        raise ValueError("formal summary differs from the observed statement")


def _replay_summary(snapshot, worker, declaration):
    from ladon.proof_contract_expressions import _Unsupported
    from ladon.proof_contract_production import (
        _record_extracted_statement,
        _record_unavailable_statement,
        _record_unsupported_statement,
        _worker_has_statement,
    )
    from ladon.proof_contract_recognition import _recognize_estimate

    expected = deepcopy(snapshot)
    expected.update(status="unavailable", contract=None, residuals=[],
                    featureOrigins={"regularity": [], "constantDependencies": [],
                                    "witnessDependencies": []},
                    coverage={"statementFeatures": "unsupported", "providers": "not-extracted",
                              "proofBody": "not-extracted"})
    if not _worker_has_statement(worker):
        return _record_unavailable_statement(expected, worker)
    try:
        summary = _recognize_estimate(worker["normalizedTypeExpr"])
    except _Unsupported as error:
        return _record_unsupported_statement(expected, error)
    return _record_extracted_statement(expected, worker, summary, declaration)
