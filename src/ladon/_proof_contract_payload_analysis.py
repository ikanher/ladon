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
    return {
        "probes": ("ladon._proof_contract_probe_native", "validate_probe_payload"),
        "obligations": ("ladon._proof_contract_obligation_native", "validate_obligation_payload"),
        "rational-branch": ("ladon._proof_contract_rational_native", "validate_rational_branch_payload"),
        "rational-branch-check": ("ladon._proof_contract_rational_native", "validate_rational_branch_check_payload"),
        "propagation": ("ladon.proof_contract_payloads", "_validate_propagation_payload"),
    }.get(payload.get("stage"))


def _recompute_analysis_stage(artifacts, payload):
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
