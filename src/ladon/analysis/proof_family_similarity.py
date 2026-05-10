"""Deterministic similarity features for repeated Lean declaration families."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Mapping

from ladon.ir import LeanDeclaration


SIMILARITY_THRESHOLD = 0.75


def proof_family_similarity_candidates(
    declarations: Mapping[str, LeanDeclaration],
    edges: Mapping[str, list[str]],
    unresolved_profiles: Mapping[str, dict[str, int]],
) -> list[dict[str, Any]]:
    """Return high-similarity repeated declaration-family candidates."""

    candidates = [
        candidate
        for names in grouped_family_names(declarations).values()
        for candidate in [family_candidate(names, declarations, edges, unresolved_profiles)]
        if candidate is not None and candidate["similarity_score"] >= SIMILARITY_THRESHOLD
    ]
    return sorted(candidates, key=lambda row: (-row["similarity_score"], row["suffix"]))[:15]


def family_candidate(
    names: list[str],
    declarations: Mapping[str, LeanDeclaration],
    edges: Mapping[str, list[str]],
    unresolved_profiles: Mapping[str, dict[str, int]],
) -> dict[str, Any] | None:
    """Return the best pairwise candidate for one suffix family."""

    if len(names) < 2:
        return None
    pairs = [
        pair_similarity(left, right, declarations, edges, unresolved_profiles)
        for left, right in combinations(sorted(names), 2)
    ]
    best = max(pairs, key=lambda row: row["similarity_score"])
    return {**family_summary(names), **best}


def pair_similarity(
    left: str,
    right: str,
    declarations: Mapping[str, LeanDeclaration],
    edges: Mapping[str, list[str]],
    unresolved_profiles: Mapping[str, dict[str, int]],
) -> dict[str, Any]:
    """Compute deterministic similarity features for one declaration pair."""

    reference_overlap = jaccard(set(edges.get(left, [])), set(edges.get(right, [])))
    profile_overlap = weighted_jaccard(
        unresolved_profiles.get(left, {}),
        unresolved_profiles.get(right, {}),
    )
    return {
        "best_pair": [left, right],
        "similarity_score": round(max(reference_overlap, profile_overlap), 3),
        "max_reference_overlap": round(reference_overlap, 3),
        "max_unresolved_profile_overlap": round(profile_overlap, 3),
        "fan_out_delta": abs(len(edges.get(left, [])) - len(edges.get(right, []))),
        "shared_kind": shared_kind(declarations[left], declarations[right]),
    }


def grouped_family_names(
    declarations: Mapping[str, LeanDeclaration],
) -> dict[str, list[str]]:
    """Group declaration names by repeated suffix."""

    grouped: dict[str, list[str]] = {}
    for name in declarations:
        suffix = declaration_family_suffix(name)
        if suffix:
            grouped.setdefault(suffix, []).append(name)
    return grouped


def family_summary(names: list[str]) -> dict[str, Any]:
    """Return stable family-level fields for a candidate row."""

    return {
        "suffix": declaration_family_suffix(names[0]),
        "count": len(names),
        "sample_declarations": sorted(names)[:12],
    }


def declaration_family_suffix(name: str) -> str | None:
    """Return the repeated-shape suffix for a declaration name."""

    basename = name.rsplit(".", 1)[-1]
    if "_" not in basename:
        return None
    return basename.split("_", 1)[1]


def jaccard(left: set[str], right: set[str]) -> float:
    """Return Jaccard overlap, treating two empty sets as no signal."""

    if not left and not right:
        return 0.0
    return len(left & right) / len(left | right)


def weighted_jaccard(left: Mapping[str, int], right: Mapping[str, int]) -> float:
    """Return weighted Jaccard overlap for class-count profiles."""

    keys = set(left) | set(right)
    if not keys:
        return 0.0
    numerator = sum(min(int(left.get(key, 0)), int(right.get(key, 0))) for key in keys)
    denominator = sum(max(int(left.get(key, 0)), int(right.get(key, 0))) for key in keys)
    return numerator / denominator


def shared_kind(left: LeanDeclaration, right: LeanDeclaration) -> bool:
    """Return true when both declarations expose the same non-empty kind."""

    return left.kind is not None and left.kind == right.kind
