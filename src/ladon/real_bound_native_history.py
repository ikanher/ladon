"""Replay versioned plan structure without requiring today's historical helper bytes."""

from copy import deepcopy

from ladon.derivative_prefix import plan_derivative_prefix
from ladon.proof_contract_formal import _verify_summary
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import _digest
from ladon.real_bound_binding import plan_bound_prefix
from ladon.real_bound_native_plan import plan_real_bound
from ladon.real_bound_observation import _from_verified


def _identity(value, key):
    if not isinstance(value, dict):
        raise TypeError("recorded plan must be an object")
    expected = snapshot_identity({k: v for k, v in value.items() if k != key})
    if value.get(key) != expected:
        raise ValueError("recorded plan or observation identity changed")


def _historical(expected, recorded, digest_keys, id_key):
    """Historical byte identities remain data; versioned goal structure is replayed."""
    _identity(recorded, id_key)
    expected = deepcopy(expected)
    for key in digest_keys:
        if not _digest(recorded.get(key)):
            raise ValueError("invalid historical helper digest")
        expected[key] = recorded[key]
    expected[id_key] = recorded[id_key]
    if expected != recorded:
        raise ValueError("recorded plan differs from its exact versioned structure")


def validate_recorded_plan(plan):
    _identity(plan, "planId")
    binding = plan["bindingPlan"]
    observation = binding["observation"]
    snapshot = observation["statementSnapshot"]
    _identity(snapshot, "snapshotId")
    _verify_summary(snapshot)
    _historical(_from_verified(snapshot), observation, ["implementationDigest"], "snapshotId")
    derivative = binding.get("schema") == "ladon-derivative-prefix-plan-v1"
    expected_binding = (plan_derivative_prefix(observation) if derivative else
                        plan_bound_prefix(observation, binding["measure"]))
    keys = ["familySourceDigest", "bindingSourceDigest"]
    if derivative:
        keys.append("derivativeSourceDigest")
    _historical(expected_binding, binding, keys, "planId")
    # plan_real_bound validates live helper bytes. Build from the structurally
    # identical current binding, then restore the recorded nested plan identity.
    expected = plan_real_bound(expected_binding)
    expected["bindingPlan"] = deepcopy(binding)
    _historical(expected, plan, ["scalarSourceDigest"], "planId")
