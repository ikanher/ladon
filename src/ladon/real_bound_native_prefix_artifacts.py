"""Native, historical-only Real prefix implications bound to exact evidence."""

from copy import deepcopy

from ladon.proof_contract_payloads import closed
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import MAX_BATCH_BYTES, canonical_bytes, validate_envelope_batch
from ladon.real_bound_native_analysis import _contract_ref
from ladon.real_bound_native_analysis_artifacts import _relation_artifact, _unique
from ladon.real_bound_native_analysis_codec import decode_replay, encode_replay
from ladon.real_bound_native_artifacts import _envelope, external
from ladon.real_bound_native_payload import LIMITATIONS
from ladon.real_bound_native_prefix import _prefix_context
from ladon.real_bound_native_prefix_history import checked_prefix_evidence
from ladon.real_bound_native_production import _verify_production
from ladon.real_bound_native_profile import PROFILE_DIGEST

SCHEMA = "ladon-real-bound-prefix-bundle-v1"
ANALYSIS_KIND = "real-bound-prefix-v1"


def _components(replay):
    try:
        productions, run = decode_replay(replay)
        for production in productions:
            _verify_production(production)
            if production["status"] != "admitted":
                raise ValueError("Real prefix requires admitted historical owners")
        left, right = productions
        context = _prefix_context(left)
        evidence = checked_prefix_evidence(productions, run)
        env = left["artifacts"][-1]["environmentRef"]
        relation, typed_digest = _relation_artifact(
            productions, run, evidence, env, operation="real-bound:input-prefix",
            statement="Recorded directional input-predicate implication; fresh use requires rechecking.")
        analysis_id = "analysis:" + snapshot_identity(replay)[7:]
        payload = {
            "analysisId": analysis_id, "profileDigest": PROFILE_DIGEST, "stage": "comparison",
            "analysisKind": ANALYSIS_KIND,
            "contractRefs": [_contract_ref(row) for row in productions],
            "checkRunRefs": [external(relation, "check-run", relation["payload"]["checkRunId"])],
            "replay": deepcopy(replay),
            "result": {"status": "recorded-checked", "relation": "input-prefix-implies", "authority": "none",
                       "rule": "order-prefix-v1",
                       "sourceTheoremProof": "not-checked", "paperNormBridge": "unresolved",
                       "mathematicalFalsity": "not-established", "goalDigest": evidence["request"]["goal"]["sha256"],
                       "typedGoalDigest": typed_digest, "checkerIdentity": evidence["checkerIdentity"],
                       "contextDigest": snapshot_identity(context)},
            "residuals": [],
        }
        owners = _unique([*left["artifacts"], *right["artifacts"], relation])
        return payload, owners, env
    except (KeyError, TypeError, IndexError, AttributeError, RecursionError) as error:
        raise ValueError("malformed Real prefix replay evidence") from error


def validate_prefix_payload(p, value, subjects, env):
    closed(p, {"analysisId", "profileDigest", "stage", "contractRefs", "checkRunRefs",
               "replay", "result", "residuals", "analysisKind"}, "Real prefix payload")
    expected, _owners, expected_env = _components(p["replay"])
    if p != expected or env != expected_env:
        raise ValueError("Real prefix differs from its exact recorded evidence")
    if ("contract-analysis", p["analysisId"]) not in subjects:
        raise ValueError("Real prefix must own its analysis subject")
    if not set(LIMITATIONS) <= {row["id"] for row in value["limitations"]}:
        raise ValueError("Real prefix requires historical authority limitations")
    if value["coverage"]["status"] != "partial":
        raise ValueError("Real prefix cannot claim complete source coverage")


def validate_prefix_owners(artifacts, payload):
    _expected, owners, _env = _components(payload["replay"])
    for owner in owners:
        actual = artifacts.get(owner["artifactId"])
        if actual != owner:
            raise ValueError("Real prefix requires each exact historical evidence owner")


def recorded_prefix(productions, relation_run):
    """Record checked evidence without asserting its origin or current validity."""
    normalized = deepcopy(productions)
    if not isinstance(normalized, list) or len(normalized) != 2:
        raise ValueError("Real prefix requires two ordered productions")
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
