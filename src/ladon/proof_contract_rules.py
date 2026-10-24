"""Versioned mathematical meaning of the bounded natural-scale profile."""

import hashlib
import json

PROFILE_ID = "norm-scale-v1"
PROFILE = {
    "profileId": PROFILE_ID,
    "scalars": "nonnegative naturals",
    "estimate": "forall s x, M s (f x) <= c * N (s + loss) x",
    "nesting": "forall i j x, i <= j -> N i x <= N j x",
    "permission": "valuation agreement on allowed binders preserves witness",
    "constantScope": "explicit existential binderId, or a separate implicit constant after telescope",
    "constantCoherence": "known constant and anchored witness permission sets agree",
    "rules": {
        "identity": "id",
        "compose": "ContractMath.Compose",
        "weaken-loss": "ContractMath.lower_offset_implies_higher_offset",
        "combine-requirements": "ContractMath.max_requirement_and",
        "combine-estimates": "ContractMath.combine_estimates",
        "sum-permissions": "ContractMath.permission_sum_union",
        "weaken-permission": "ContractMath.permission_monotone",
        "pair-permissions": "ContractMath.permission_pair_union",
        "dominance": "ContractMath.route_dominance_sound",
    },
    "authority": "conditional structural analysis; exact applications require checks",
}
PROFILE_DIGEST = "sha256:" + hashlib.sha256(
    json.dumps(PROFILE, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
