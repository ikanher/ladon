"""Fresh production, offline inspection, and explicit Real comparison replay."""

from copy import deepcopy

from ladon import real_bound_native_production as production_api
from ladon.proof_contract_payloads import closed
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import MAX_BATCH_BYTES, canonical_bytes, validate_envelope_batch
from ladon.real_bound_native_analysis import _bound_inputs, _comparison_run, _deadline, _remaining
from ladon.real_bound_native_analysis_artifacts import SCHEMA, recorded_comparison
from ladon.real_bound_native_analysis_codec import decode_replay

FRESH_AUTHORITY = "fresh-source-predicate-scalar-and-relation-checks"


def _validated(bundle):
    canonical_bytes(bundle, max_bytes=MAX_BATCH_BYTES)
    closed(bundle, {"schema", "status", "authority", "analysisRef", "artifacts", "snapshotId"},
           "Real comparison bundle")
    if (bundle["schema"] != SCHEMA or bundle["snapshotId"] != snapshot_identity(bundle)
            or bundle["authority"] not in {"none", FRESH_AUTHORITY}):
        raise ValueError("invalid Real comparison bundle identity or authority claim")
    validate_envelope_batch(bundle["artifacts"])
    try:
        matches = [row for row in bundle["artifacts"]
                   if row["artifactId"] == bundle["analysisRef"]["artifactRef"]]
        if len(matches) != 1:
            raise ValueError("Real comparison bundle requires one exact analysis owner")
        productions, run = decode_replay(matches[0]["payload"]["replay"])
        expected = recorded_comparison(productions, run)
        expected["authority"] = bundle["authority"]
        expected["snapshotId"] = snapshot_identity(expected)
        if expected != bundle:
            raise ValueError("Real comparison bundle differs from reconstructed evidence")
        return productions, matches[0]["payload"]
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("malformed Real comparison bundle") from error


def _semantic_owner(production):
    production_api._verify_production(production)
    contract = production["artifacts"][-1]
    payload = contract["payload"]
    record = deepcopy(payload["record"])
    for key in ("predicateCheckRef", "scalarCheckRef", "evidenceDigest"):
        record["admission"].pop(key)
    return {"request": production["request"], "sourceText": production["sourceText"],
            "environmentRef": contract["environmentRef"], "subjectRefs": contract["subjectRefs"],
            "contractId": payload["contractId"], "profileDigest": payload["profileDigest"],
            "statementRef": payload["statementRef"], "sourceMapRefs": payload["sourceMapRefs"],
            "record": record}


def produce_comparison_bundle(left, right, root, *, timeout_seconds=600):
    """Recheck both source admissions and their exact relation before recording."""
    deadline = _deadline(timeout_seconds)
    _bound_inputs([left, right])
    for row in (left, right):
        production_api._verify_production(row)
        production_api._current_source(row, root)
    result, fresh = _comparison_run(left, right, root, timeout_seconds=_remaining(deadline))
    for saved, current in zip((left, right), fresh, strict=True):
        if _semantic_owner(saved) != _semantic_owner(current):
            raise ValueError("fresh Real replay substituted a different semantic owner or request")
    if result["status"] != "resolved":
        return result
    for row in fresh:
        production_api._current_source(row, root)
    bundle = recorded_comparison(fresh, result["relationCheckRun"])
    bundle["authority"] = FRESH_AUTHORITY
    bundle["snapshotId"] = snapshot_identity(bundle)
    return bundle


def inspect_comparison_bundle(bundle, root=None):
    """Inspect history; even a saved fresh claim confers no checking authority."""
    productions, payload = _validated(bundle)
    if root is not None:
        for production in productions:
            production_api._current_source(production, root)
    return {"schema": "ladon-real-bound-comparison-inspection-v1", "status": "validated-historical",
            "authority": "none", "freshCheck": False, "evidenceAuthentication": "not-established",
            "sourceFreshness": "current" if root is not None else "not-checked",
            "analysisRef": deepcopy(bundle["analysisRef"]), "recordedResult": deepcopy(payload["result"]),
            "sourceTheoremProof": "not-checked", "paperNormBridge": "unresolved",
            "mathematicalFalsity": "not-established"}


def replay_comparison_bundle(bundle, root, *, timeout_seconds=600):
    """Validate the saved owners, then spend one shared budget on fresh checks."""
    deadline = _deadline(timeout_seconds)
    productions, _payload = _validated(bundle)
    return produce_comparison_bundle(*productions, root, timeout_seconds=_remaining(deadline))
