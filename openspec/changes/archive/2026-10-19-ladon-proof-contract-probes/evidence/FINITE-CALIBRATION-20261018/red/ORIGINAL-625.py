"""Pure red contract tests for the finite probe-calibration public boundary.

These tests intentionally target the future public API. They contain no Lean,
worker invocation, repository scan, fixture receipt, or mocked accepted proof.
"""
from __future__ import annotations

import math
import time
from copy import deepcopy

import pytest

from ladon.proof_contract_probe_calibration import (
    probe_calibration_profile,
    run_probe_calibration,
)


VALUES_A = [False, False, False, False, False]
VALUES_B = [False, False, False, False, True]
FULL_FAMILY = [0, 1, 2, 3, 4]


def request(tmp_path, *, left=None, right=None, family=None, certificate=None):
    return {
        "repoRoot": str(tmp_path),
        "left": list(VALUES_A if left is None else left),
        "right": list(VALUES_A if right is None else right),
        "family": list(FULL_FAMILY if family is None else family),
        "certificateRef": deepcopy(certificate),
        "deadlineMonotonic": time.monotonic() + 30,
        "limits": {"timeoutSeconds": 1, "maxOutputBytes": 1024},
    }


def assert_no_equivalence_claim(result):
    """Public finite comparison is descriptive; it never certifies objects."""
    assert result["status"] in {"scoped-agreement", "observed-response-difference"}
    assert result.get("objectEquivalence") is not True
    assert result.get("equivalent") is not True


def test_unverified_agreement_and_empty_family_never_claim_equivalence(tmp_path):
    full = run_probe_calibration(request(tmp_path))
    empty = run_probe_calibration(request(tmp_path, family=[]))
    assert_no_equivalence_claim(full)
    assert_no_equivalence_claim(empty)


def test_full_family_unverified_disagreement_is_only_observed_difference(tmp_path):
    result = run_probe_calibration(request(tmp_path, right=VALUES_B))
    assert result["status"] == "observed-response-difference"
    assert result.get("objectEquivalence") is not True
    assert result.get("equivalent") is not True


def test_full_certificate_cannot_be_replayed_for_incomplete_family(tmp_path):
    certificate = probe_calibration_profile()
    result = run_probe_calibration(
        request(tmp_path, family=[0, 1, 2, 3], certificate=certificate)
    )
    assert result["status"] == "rejected"


@pytest.mark.parametrize("bad_family", [[True, 1], [0, 0], [0, 5], [0, -1], [0.0]])
def test_family_indices_are_strict_unique_and_in_range(tmp_path, bad_family):
    result = run_probe_calibration(request(tmp_path, family=bad_family))
    assert result["status"] == "rejected"


@pytest.mark.parametrize("bad_values", [[False, False, False, False, 0], [False] * 4, [False] * 6])
def test_objects_are_exactly_five_booleans(tmp_path, bad_values):
    result = run_probe_calibration(request(tmp_path, left=bad_values))
    assert result["status"] == "rejected"


def test_request_is_closed_to_caller_supplied_formula_or_proof(tmp_path):
    req = request(tmp_path)
    req["formula"] = "True"
    result = run_probe_calibration(req)
    assert result["status"] == "rejected"


def test_mutated_registered_certificate_identity_rejects(tmp_path):
    registered = probe_calibration_profile()
    for field, value in (
        ("objectClassId", "forged-class"),
        ("observationId", "forged-observation"),
        ("templateVersion", "forged-template"),
        ("sourceDigest", "sha256:" + "0" * 64),
        ("family", [0, 1, 2, 3]),
    ):
        mutated = deepcopy(registered)
        mutated[field] = value
        result = run_probe_calibration(request(tmp_path, certificate=mutated))
        assert result["status"] == "rejected", field


def test_expired_or_nan_deadline_fails_closed(tmp_path):
    for deadline in (time.monotonic() - 1, math.nan):
        req = request(tmp_path)
        req["deadlineMonotonic"] = deadline
        result = run_probe_calibration(req)
        assert result["status"] in {"rejected", "incomplete"}


def test_oversized_aggregate_request_fails_closed_before_work(tmp_path):
    req = request(tmp_path)
    # repoRoot is an allowed string field; aggregate preflight must stop before
    # attempting path validation or starting any worker.
    req["repoRoot"] = "x" * (8 * 1024 * 1024 + 1)
    result = run_probe_calibration(req)
    assert result["status"] == "rejected"
