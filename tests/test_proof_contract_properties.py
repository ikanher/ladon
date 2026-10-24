"""Finite order oracle and actual Lean checks for the declared profile."""

import itertools
import shutil
import subprocess
from pathlib import Path

import pytest
from support.proof_contract_native import contract_record

from ladon.proof_contracts import compare_contracts, validate_contract


def profile_case(offset, dependencies):
    value = contract_record()
    value["telescope"].append({"binderId": "v", "typeId": "Nat", "quantifier": "forall"})
    value["features"]["regularity"]["offset"] = offset
    value["features"]["constantDependencies"]["allowedBinderIds"] = list(dependencies)
    return value


def oracle_relation(a, b):
    forward = a[0] <= b[0] and set(a[1]).issubset(b[1])
    backward = b[0] <= a[0] and set(b[1]).issubset(a[1])
    return {(True, True): "equivalent", (True, False): "dominates",
            (False, True): "dominated", (False, False): "incomparable"}[forward, backward]


def test_all_small_correlated_frontier_comparisons_match_the_order_oracle():
    cases = list(itertools.product(range(4), [(), ("u",), ("v",), ("u", "v")]))
    for a, b in itertools.product(cases, repeat=2):
        actual = compare_contracts(profile_case(*a), profile_case(*b))
        assert actual["relation"] == oracle_relation(a, b)
        assert actual["mathematicalFalsity"] == "not-established"


@pytest.mark.parametrize("change", [
    lambda v: v.update(endpointId="a" * 513),
    lambda v: v["features"]["regularity"].update(offset=2**53),
    lambda v: v.update(telescope=[v["telescope"][0]] * 4097),
    lambda v: v["features"]["constantDependencies"].update(allowedBinderIds=["u"] * 4097),
])
def test_record_api_enforces_finite_scalar_and_collection_caps(change):
    value = contract_record()
    change(value)
    with pytest.raises(ValueError):
        validate_contract(value)


def test_profile_rules_really_compile_in_pinned_lean():
    lean = shutil.which("lean")
    assert lean is not None, "Lean is required for mathematical profile qualification"
    fixture = Path(__file__).parent / "fixtures/proof_contracts"
    version = subprocess.run([lean, "--version"], cwd=fixture, capture_output=True,
                             text=True, check=False, timeout=30)
    assert version.returncode == 0 and "4.32.1" in version.stdout
    result = subprocess.run([lean, "ContractMath.lean"], cwd=fixture, capture_output=True,
                            text=True, check=False, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "sorryAx" not in result.stdout
    for name in ("dominance_sound", "Compose", "max_requirement_and",
                 "lower_offset_implies_higher_offset", "permission_pair_union",
                 "route_tradeoff_incomparable"):
        assert f"ContractMath.{name}" in result.stdout
