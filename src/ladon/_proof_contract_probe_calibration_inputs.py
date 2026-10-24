"""Closed input admission and safe Fin 5 Boolean terms.

The public worker supplies its own registered profile. This helper never starts
Lean, reads a proof receipt, or validates caller-supplied proof authority.
"""
from __future__ import annotations

import copy
import math
import re
from pathlib import Path

from ladon._proof_contract_planned_source_inputs import _planned_input_size
from ladon.proof_contract_bridge_supervision import bridge_limits

MAX_BYTES = 8 * 1024**2
_FAMILY = [0, 1, 2, 3, 4]
_KEYS = {"repoRoot", "left", "right", "family", "certificateRef",
         "deadlineMonotonic", "limits"}
_PROFILE_KEYS = {"objectClassId", "observationId", "family", "theorem",
                 "sourceDigest", "templateVersion"}
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


def own_inputs(request, profile):
    """Own a bounded closed request and resolve an existing nonsymlink root."""
    _preflight_request(request)
    _check_request_shape(request)
    left, right, family = _validated_vectors(request)
    _check_certificate(request["certificateRef"], profile, family)
    _check_deadline(request["deadlineMonotonic"])
    return _owned_request(request, left, right, family)


def _check_request_shape(request):
    if not isinstance(request, dict) or set(request) != _KEYS:
        raise ValueError("probe calibration request must use the closed schema")
    if not isinstance(request["repoRoot"], str) or not request["repoRoot"]:
        raise ValueError("repoRoot must be nonempty text")


def _preflight_request(request):
    try:
        size = _planned_input_size(request)
    except (RecursionError, OverflowError, ValueError) as error:
        raise ValueError("probe calibration request is malformed or cyclic") from error
    if size > MAX_BYTES:
        raise ValueError("probe calibration request exceeds 8 MiB")


def _validated_vectors(request):
    left = _values(request["left"], "left")
    right = _values(request["right"], "right")
    family = _family(request["family"])
    return left, right, family


def _check_certificate(certificate, profile, family):
    _validate_profile(profile)
    if certificate is None:
        return
    if not isinstance(certificate, dict) or set(certificate) != _PROFILE_KEYS:
        raise ValueError("certificateRef has invalid descriptor schema")
    _family(certificate["family"])
    if certificate != profile:
        raise ValueError("certificateRef differs from the exact registered profile")
    if family != _FAMILY:
        raise ValueError("full-family certificate cannot be used for a subset")


def _check_deadline(deadline):
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("deadlineMonotonic must be finite numeric absolute time")


def _owned_request(request, left, right, family):
    root = _safe_repo_root(request["repoRoot"])
    limits = bridge_limits(request["limits"])
    owned = copy.deepcopy(request)
    owned.update(repoRoot=str(root), left=left, right=right, family=family,
                 limits=limits)
    return owned


def _validate_profile(profile):
    if not isinstance(profile, dict) or set(profile) != _PROFILE_KEYS:
        raise ValueError("implementation profile descriptor has invalid schema")
    _family(profile["family"])
    _validate_profile_identity(profile)


def _validate_profile_identity(profile):
    text_fields = ("objectClassId", "observationId", "theorem", "templateVersion")
    if any(not isinstance(profile[key], str) or not profile[key] for key in text_fields):
        raise ValueError("implementation profile descriptor has invalid text identity")
    digest = profile["sourceDigest"]
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
        raise ValueError("implementation profile descriptor has invalid source digest")


def _safe_repo_root(value):
    from ladon.correspondence_preparation import PreparedSourceContext

    path = Path(value).absolute()
    # The existing directory fingerprint checks lstat(S_ISDIR) and requires
    # resolve(strict=True) == path, rejecting symlink roots and symlink ancestors.
    PreparedSourceContext.directory_fingerprint(path)
    return path


def _values(value, label):
    if not isinstance(value, list) or len(value) != 5 or any(type(bit) is not bool for bit in value):
        raise ValueError(f"{label} must be exactly five strict Booleans")
    return list(value)


def _family(value):
    if not isinstance(value, list) or len(value) > 5:
        raise ValueError("family must be an ordered subset of Fin 5 coordinates")
    if any(type(index) is not int or not 0 <= index < 5 for index in value):
        raise ValueError("family indices must be strict integers in [0,4]")
    if len(set(value)) != len(value):
        raise ValueError("family indices must be unique")
    return list(value)


def encode_object(values):
    """Encode five Booleans as a closed, injection-free `Fin 5 → Bool` lambda."""
    bits = _values(values, "object")
    tail = "false"
    for index in reversed(range(5)):
        value = "true" if bits[index] else "false"
        tail = f"(if i.val = {index} then {value} else {tail})"
    return f"(fun (i : Fin 5) => {tail})"


def application_goal(left, right):
    """Return a checked equality or coordinate-witness disequality proposition."""
    left_bits, right_bits = _values(left, "left"), _values(right, "right")
    left_term, right_term = encode_object(left_bits), encode_object(right_bits)
    if left_bits == right_bits:
        return {
            "goal": f"({left_term}) = ({right_term})",
            "term": ("LadonProbeCalibration.full_separates "
                     f"({left_term}) ({right_term}) (by decide)"),
        }

    index = next(i for i, (a, b) in enumerate(zip(left_bits, right_bits)) if a != b)
    left_bit, right_bit = ("true" if left_bits[index] else "false",
                           "true" if right_bits[index] else "false")
    term = (
        "by\n"
        "  intro h\n"
        f"  have hbit := congrFun h ({index} : Fin 5)\n"
        f"  change {left_bit} = {right_bit} at hbit\n"
        "  cases hbit"
    )
    return {"goal": f"({left_term}) ≠ ({right_term})", "term": term}
