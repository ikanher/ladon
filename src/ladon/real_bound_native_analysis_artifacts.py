"""Native, historical-only Real comparisons bound to exact relation evidence."""

import hashlib
import math
from copy import deepcopy

from ladon.proof_contract_payloads import closed
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import MAX_BATCH_BYTES, canonical_bytes, validate_envelope_batch
from ladon.real_bound_native_analysis import _context, _contract_ref
from ladon.real_bound_native_analysis_codec import decode_replay, encode_replay
from ladon.real_bound_native_artifacts import _envelope, external
from ladon.real_bound_native_payload import LIMITATIONS
from ladon.real_bound_native_production import _verify_production
from ladon.real_bound_native_profile import PROFILE_DIGEST
from ladon.real_bound_native_relation_history import checked_relation_evidence

SCHEMA = "ladon-real-bound-comparison-bundle-v1"


def _relation_artifact(productions, run, evidence, env, *, operation="real-bound:predicate-relation",
                       statement="Recorded predicate equivalence; fresh semantic use requires rechecking."):
    actual = evidence["check"]
    capture_env = actual["capture"]["capture"]["environment"]
    structural = actual["typedSubject"]["subject"]["structural"]
    digest = "sha256:" + hashlib.sha256(structural.encode()).hexdigest()
    goal = {"kind": "statement", "localId": "goal:" + digest[7:]}
    descriptor = {**goal, "fingerprint": {"scheme": {"name": "lean-typed-goal", "version": "1"},
                                         "digest": digest}}
    contracts = [_contract_ref(row) for row in productions]
    statements = [row["artifacts"][-1]["payload"]["statementRef"] for row in productions]
    check_id = "check:" + snapshot_identity({"run": run, "contractRefs": contracts})[7:]
    receipt = actual["completion"]["processReceipts"][-1]
    inputs = [*contracts, *statements]
    return _envelope("check-run", env, [{"kind": "check-run", "localId": check_id}, descriptor], {
        "checkRunId": check_id, "operation": operation,
        "checker": {"name": "Lean", "version": capture_env["leanVersion"],
                    "implementationDigest": evidence["checkerIdentity"],
                    "executableDigest": capture_env["executableDigest"]},
        "inputs": {"environmentRef": env, "subjectRefs": [goal, *inputs],
                   "artifactRefs": list(dict.fromkeys(ref["artifactRef"] for ref in inputs))},
        "results": [{"subjectRef": goal, "result": "accepted", "diagnostics": []}],
        "outputs": {key: receipt[key] for key in ("stdoutDigest", "stderrDigest")},
        "bounds": {"timeoutMs": math.ceil(run["bounds"]["effectiveTimeoutSeconds"] * 1000),
                   "maxOutputBytes": run["bounds"]["max_output_bytes"]},
        "guarantee": {"scope": "declaration-value", "authorityBasis": "stored-observation",
                      "statement": statement},
    }), digest


def _components(replay):
    try:
        productions, run = decode_replay(replay)
        for production in productions:
            _verify_production(production)
            if production["status"] != "admitted":
                raise ValueError("Real comparison requires admitted historical owners")
        left, right = productions
        context = _context(left)
        if context != _context(right):
            raise ValueError("recorded Real comparison has different typed contexts")
        evidence = checked_relation_evidence(productions, run)
        env = left["artifacts"][-1]["environmentRef"]
        relation, typed_digest = _relation_artifact(productions, run, evidence, env)
        analysis_id = "analysis:" + snapshot_identity(replay)[7:]
        payload = {
            "analysisId": analysis_id, "profileDigest": PROFILE_DIGEST, "stage": "comparison",
            "contractRefs": [_contract_ref(row) for row in productions],
            "checkRunRefs": [external(relation, "check-run", relation["payload"]["checkRunId"])],
            "replay": deepcopy(replay),
            "result": {"status": "recorded-checked", "relation": "equivalent", "authority": "none",
                       "sourceTheoremProof": "not-checked", "paperNormBridge": "unresolved",
                       "mathematicalFalsity": "not-established", "goalDigest": evidence["goal"]["sha256"],
                       "typedGoalDigest": typed_digest, "checkerIdentity": evidence["checkerIdentity"],
                       "contextDigest": snapshot_identity(context)},
            "residuals": [],
        }
        owners = _unique([*left["artifacts"], *right["artifacts"], relation])
        return payload, owners, env
    except (KeyError, TypeError, IndexError, AttributeError, RecursionError) as error:
        raise ValueError("malformed Real comparison replay evidence") from error


def _unique(artifacts):
    owners = {}
    for artifact in artifacts:
        identity = artifact["artifactId"]
        if identity in owners and owners[identity] != artifact:
            raise ValueError("conflicting Real comparison artifact owner")
        owners[identity] = artifact
    return list(owners.values())


def validate_comparison_payload(p, value, subjects, env):
    closed(p, {"analysisId", "profileDigest", "stage", "contractRefs", "checkRunRefs",
               "replay", "result", "residuals"}, "Real comparison payload")
    expected, _owners, expected_env = _components(p["replay"])
    if p != expected or env != expected_env:
        raise ValueError("Real comparison differs from its exact recorded evidence")
    if ("contract-analysis", p["analysisId"]) not in subjects:
        raise ValueError("Real comparison must own its analysis subject")
    if not set(LIMITATIONS) <= {row["id"] for row in value["limitations"]}:
        raise ValueError("Real comparison requires historical authority limitations")
    if value["coverage"]["status"] != "partial":
        raise ValueError("Real comparison cannot claim complete source coverage")


def validate_comparison_owners(artifacts, payload):
    _expected, owners, _env = _components(payload["replay"])
    for owner in owners:
        actual = artifacts.get(owner["artifactId"])
        if actual != owner:
            raise ValueError("Real comparison requires each exact historical evidence owner")


def recorded_comparison(productions, relation_run):
    """Record checked evidence without asserting its origin or current validity."""
    normalized = deepcopy(productions)
    if not isinstance(normalized, list) or len(normalized) != 2:
        raise ValueError("Real comparison requires two ordered productions")
    for production in normalized:
        _verify_production(production)
        production["authority"] = "none"
        production["snapshotId"] = snapshot_identity(production)
    replay = encode_replay(normalized, relation_run)
    payload, owners, env = _components(replay)
    artifact = _envelope("contract-analysis", env,
                         [{"kind": "contract-analysis", "localId": payload["analysisId"]}], payload)
    artifacts = [*owners, artifact]
    validate_envelope_batch(artifacts)
    bundle = {"schema": SCHEMA, "status": "recorded-checked", "authority": "none",
              "analysisRef": external(artifact, "contract-analysis", payload["analysisId"]),
              "artifacts": artifacts}
    bundle["snapshotId"] = snapshot_identity(bundle)
    canonical_bytes(bundle, max_bytes=MAX_BATCH_BYTES)
    return bundle
