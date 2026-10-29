"""Immutable typed shape observations, separate from admitted proof contracts."""

import hashlib
from pathlib import Path

from ladon.proof_contract_formal import verify_formal_snapshot
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import canonical_bytes
from ladon.real_bound_shape import observe_bound_shape

SCHEMA = "ladon-real-bound-observation-v1"
PROFILE = {
    "profileId": "real-bound-shape-v1",
    "meaning": "typed syntax only; no predicate, scalar or order-law admission",
    "shape": "forall context, exists K, nonnegative K and forall inputs, J f S (n+d) C -> J (A f) S n (K*C)",
    "scope": "ordered typed binders and all observed premises; no dependency minimization",
    "shift": "same Nat index or builtin Nat addition with a literal",
    "bounds": {"nodes": 100_000, "depth": 128, "binders": 64},
    "authority": "syntax-only",
}
PROFILE_DIGEST = "sha256:" + hashlib.sha256(canonical_bytes(PROFILE)).hexdigest()


def _implementation_digest():
    directory = Path(__file__).parent
    names = ("real_bound_observation.py", "real_bound_shape.py", "_real_bound_terms.py",
             "proof_contract_expressions.py")
    identities = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                  for name in names}
    return "sha256:" + hashlib.sha256(canonical_bytes(identities)).hexdigest()


def observe_bound_snapshot(snapshot, root):
    """Verify an original formal snapshot, then observe its typed estimate shape."""
    return _from_verified(verify_formal_snapshot(snapshot, root))


def _from_verified(snapshot):
    worker = snapshot["observation"]
    if worker is None or worker["status"] != "observed":
        shape = {"candidate": None, "admission": "unresolved", "residuals": [{
            "code": "statement-unavailable", "feature": "statement",
            "message": "The original snapshot contains no observed statement.",
        }]}
    else:
        shape = observe_bound_shape(worker["normalizedTypeExpr"])
    result = {
        "schema": SCHEMA, "profileId": PROFILE["profileId"], "profileDigest": PROFILE_DIGEST,
        "implementationDigest": _implementation_digest(), "statementSnapshot": snapshot,
        "status": "observed" if shape["candidate"] is not None else "unsupported",
        **shape, "contract": None, "authority": "syntax-only",
        "mathematicalFalsity": "not-established",
    }
    result["snapshotId"] = snapshot_identity(result)
    return result


def verify_bound_observation(observation, root):
    """Replay closed syntax extraction; never certify predicate or law admission."""
    if not isinstance(observation, dict) or observation.get("schema") != SCHEMA:
        raise ValueError("unsupported bound observation schema")
    if observation.get("snapshotId") != snapshot_identity(observation):
        raise ValueError("invalid or altered bound observation identity")
    if observation.get("implementationDigest") != _implementation_digest():
        raise ValueError("stale bound observation implementation")
    expected = observe_bound_snapshot(observation["statementSnapshot"], root)
    if observation != expected:
        raise ValueError("bound observation differs from exact source-shape replay")
    return expected
