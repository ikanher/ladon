"""Fresh production, offline inspection, and explicit Real prefix replay."""

from copy import deepcopy

from ladon import real_bound_native_production as production_api
from ladon.proof_contract_payloads import closed
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import MAX_BATCH_BYTES, canonical_bytes, validate_envelope_batch
from ladon.real_bound_native_analysis import _deadline, _remaining
from ladon.real_bound_native_analysis_codec import decode_replay
from ladon.real_bound_native_prefix import _prefix_run
from ladon.real_bound_native_prefix_artifacts import SCHEMA, recorded_prefix

FRESH_AUTHORITY = "fresh-source-predicate-scalar-and-prefix-checks"


def _validated(bundle):
    canonical_bytes(bundle, max_bytes=MAX_BATCH_BYTES)
    closed(bundle, {"schema", "status", "authority", "analysisRef", "artifacts", "snapshotId"},
           "Real prefix bundle")
    if (bundle["schema"] != SCHEMA or bundle["snapshotId"] != snapshot_identity(bundle)
            or bundle["authority"] not in {"none", FRESH_AUTHORITY}):
        raise ValueError("invalid Real prefix bundle identity or authority claim")
    validate_envelope_batch(bundle["artifacts"])
    try:
        matches = [row for row in bundle["artifacts"]
                   if row["artifactId"] == bundle["analysisRef"]["artifactRef"]]
        if len(matches) != 1:
            raise ValueError("Real prefix bundle requires one exact analysis owner")
        productions, run = decode_replay(matches[0]["payload"]["replay"])
        expected = recorded_prefix(productions, run)
        expected["authority"] = bundle["authority"]
        expected["snapshotId"] = snapshot_identity(expected)
        if expected != bundle:
            raise ValueError("Real prefix bundle differs from reconstructed evidence")
        return productions, matches[0]["payload"]
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("malformed Real prefix bundle") from error


def produce_prefix_bundle(stronger, weaker, root, *, timeout_seconds=600):
    """Record the exact fresh owners and their individually checked prefix edge."""
    deadline = _deadline(timeout_seconds)
    result, fresh = _prefix_run(stronger, weaker, root, timeout_seconds=_remaining(deadline))
    if result['status'] != 'resolved':
        return result
    bundle = recorded_prefix(fresh, result['relationCheckRun'])
    for production in fresh:
        production_api._current_source(production, root)
    _remaining(deadline)
    bundle['authority'] = FRESH_AUTHORITY
    bundle['snapshotId'] = snapshot_identity(bundle)
    return bundle


def inspect_prefix_bundle(bundle, root=None):
    """Inspect history; even a saved fresh claim confers no checking authority."""
    productions, payload = _validated(bundle)
    if root is not None:
        for production in productions:
            production_api._current_source(production, root)
    return {"schema": "ladon-real-bound-prefix-inspection-v1", "status": "validated-historical",
            "authority": "none", "freshCheck": False, "evidenceAuthentication": "not-established",
            "sourceFreshness": "current" if root is not None else "not-checked",
            "analysisRef": deepcopy(bundle["analysisRef"]), "recordedResult": deepcopy(payload["result"]),
            "sourceTheoremProof": "not-checked", "paperNormBridge": "unresolved",
            "mathematicalFalsity": "not-established"}


def replay_prefix_bundle(bundle, root, *, timeout_seconds=600):
    """Validate the saved owners, then spend one shared budget on fresh checks."""
    deadline = _deadline(timeout_seconds)
    productions, _payload = _validated(bundle)
    return produce_prefix_bundle(*productions, root, timeout_seconds=_remaining(deadline))
