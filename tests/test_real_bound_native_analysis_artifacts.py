"""Small red test for explicit versioned Real analysis routing."""

from ladon._proof_contract_payload_analysis import _analysis_validator
from ladon.real_bound_native_profile import PROFILE_DIGEST


def test_native_comparison_routes_by_exact_real_profile_without_new_stage():
    # Keep the existing closed comparison stage and route its Real profile to
    # a profile-specific validator without changing Nat comparison handling.
    assert _analysis_validator({
        "stage": "comparison",
        "profileDigest": PROFILE_DIGEST,
    }) == (
        "ladon.real_bound_native_analysis_artifacts",
        "validate_comparison_payload",
    )


def test_nat_comparison_and_unknown_profiles_keep_legacy_dispatch():
    assert _analysis_validator({
        "stage": "comparison",
        "profileDigest": "the-existing-nat-profile",
    }) is None
    assert _analysis_validator({
        "stage": "comparison",
        "profileDigest": "sha256:unknown-profile",
    }) is None
    assert _analysis_validator({"stage": "made-up-analysis-stage"}) is None
