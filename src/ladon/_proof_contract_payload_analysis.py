"""Private stage routing for closed contract-analysis payloads."""
from __future__ import annotations


def validate_analysis_payload(p, value, subjects, env):
    from ladon import proof_contract_payloads as core

    specialized = _analysis_validator(p)
    if specialized is None:
        return core._validate_comparison_payload(p, value, subjects, env)
    module_name, function_name = specialized
    from importlib import import_module

    validator = getattr(import_module(module_name), function_name)
    return validator(p, value, subjects, env)


def _analysis_validator(payload):
    if not isinstance(payload, dict):
        return None
    from ladon.real_bound_native_chain_artifacts import is_chain
    from ladon.real_bound_native_coefficient_artifacts import is_coefficient
    from ladon.real_bound_native_profile import PROFILE_DIGEST as REAL_PROFILE
    from ladon.real_bound_native_transfer_artifacts import is_transfer

    if is_chain(payload):
        return ("ladon.real_bound_native_chain_artifacts", "validate_chain_payload")
    if is_coefficient(payload):
        return ("ladon.real_bound_native_coefficient_artifacts", "validate_coefficient_payload")
    if is_transfer(payload):
        return ("ladon.real_bound_native_transfer_artifacts", "validate_transfer_payload")

    if payload.get("profileDigest") == REAL_PROFILE and payload.get("stage") == "comparison":
        if payload.get("analysisKind") == "real-bound-prefix-v1":
            return ("ladon.real_bound_native_prefix_artifacts", "validate_prefix_payload")
        return ("ladon.real_bound_native_analysis_artifacts", "validate_comparison_payload")
    return {
        "probes": ("ladon._proof_contract_probe_native", "validate_probe_payload"),
        "obligations": ("ladon._proof_contract_obligation_native", "validate_obligation_payload"),
        "rational-branch": ("ladon._proof_contract_rational_native", "validate_rational_branch_payload"),
        "rational-branch-check": ("ladon._proof_contract_rational_native", "validate_rational_branch_check_payload"),
        "propagation": ("ladon.proof_contract_payloads", "_validate_propagation_payload"),
    }.get(payload.get("stage"))


def _recompute_analysis_stage(artifacts, payload):
    from ladon.real_bound_native_chain_artifacts import is_chain, validate_chain_owners
    from ladon.real_bound_native_coefficient_artifacts import (
        is_coefficient,
        validate_coefficient_owners,
    )
    from ladon.real_bound_native_profile import PROFILE_DIGEST as REAL_PROFILE
    from ladon.real_bound_native_transfer_artifacts import is_transfer, validate_transfer_owners

    if is_chain(payload):
        return validate_chain_owners(artifacts, payload)
    if is_coefficient(payload):
        return validate_coefficient_owners(artifacts, payload)
    if is_transfer(payload):
        return validate_transfer_owners(artifacts, payload)

    stage = payload.get("stage")
    if payload.get("profileDigest") == REAL_PROFILE and stage == "comparison":
        return _real_comparison_owners(artifacts, payload)
    return _recompute_other_stages(artifacts, payload)


def _recompute_other_stages(artifacts, payload):
    stage = payload.get("stage")
    if stage == "probes":
        from ladon._proof_contract_probe_native import recompute_probe_inputs

        return recompute_probe_inputs(artifacts, payload)
    if stage == "obligations":
        from ladon._proof_contract_obligation_native import recompute_obligation_inputs

        return recompute_obligation_inputs(artifacts, payload)
    if stage == "rational-branch":
        if payload.get("contractRefs") != [] or payload.get("checkRunRefs") != []:
            raise ValueError("rational branch plan cannot reference external proof artifacts")
        return None
    if stage == "rational-branch-check":
        from ladon._proof_contract_rational_native import recompute_rational_branch_check

        return recompute_rational_branch_check(artifacts, payload)
    if stage == "propagation":
        from ladon.proof_contract_payloads import _recompute_propagation

        return _recompute_propagation(artifacts, payload)
    from ladon.proof_contract_payloads import _recompute_contract_comparison

    return _recompute_contract_comparison(artifacts, payload)


def _real_comparison_owners(artifacts, payload):
    if payload.get("analysisKind") == "real-bound-prefix-v1":
        from ladon.real_bound_native_prefix_artifacts import validate_prefix_owners

        return validate_prefix_owners(artifacts, payload)
    from ladon.real_bound_native_analysis_artifacts import validate_comparison_owners

    return validate_comparison_owners(artifacts, payload)
