"""Meaning of the separately versioned native Real-bound contract profile."""

from ladon.real_bound_admission import _digest

PROFILE_ID = "real-bound-v1"
PROFILE = {
    "profileId": PROFILE_ID,
    "version": 1,
    "predicate": "source-bound Lean equivalence to a declared prefix family",
    "scalars": "ordinary Real nonnegative guards and K*C",
    "scope": "exact observed typed telescope; no dependency minimization",
    "expressions": "opaque typed subjects bound to source and replay context",
    "storedAuthority": "historical; semantic use requires fresh checking",
    "proseNorm": "separate interpretation obligation",
}
PROFILE_DIGEST = _digest(PROFILE)
