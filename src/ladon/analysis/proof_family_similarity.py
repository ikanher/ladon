"""Deterministic similarity features for repeated Lean declaration families."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Mapping

from ladon.ir import LeanDeclaration


SIMILARITY_THRESHOLD = 0.75
COARSE_ONLY_CAP = 0.5


def proof_family_similarity_candidates(
    declarations: Mapping[str, LeanDeclaration],
    edges: Mapping[str, list[str]],
    unresolved_profiles: Mapping[str, dict[str, int]],
) -> list[dict[str, Any]]:
    """Return promoted and explanatory coarse-only family candidates."""

    candidates = [
        candidate
        for names in grouped_family_names(declarations).values()
        for candidate in [family_candidate(names, declarations, edges, unresolved_profiles)]
        if candidate is not None
        and (candidate["promoted"] or candidate["coarse_only"])
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
    identifier_overlap = jaccard(
        normalized_identifiers(declarations[left]),
        normalized_identifiers(declarations[right]),
    )
    profile_overlap = weighted_jaccard(
        unresolved_profiles.get(left, {}),
        unresolved_profiles.get(right, {}),
    )
    coarse_only = (
        profile_overlap > 0
        and reference_overlap == 0
        and identifier_overlap == 0
    )
    score = max(
        reference_overlap,
        identifier_overlap,
        min(profile_overlap, COARSE_ONLY_CAP),
    )
    return {
        "best_pair": [left, right],
        "similarity_score": round(score, 3),
        "max_reference_overlap": round(reference_overlap, 3),
        "max_concrete_identifier_overlap": round(identifier_overlap, 3),
        "max_unresolved_profile_overlap": round(profile_overlap, 3),
        "coarse_only": coarse_only,
        "coarse_only_cap": COARSE_ONLY_CAP,
        "promoted": score >= SIMILARITY_THRESHOLD and not coarse_only,
        "evidence_basis": similarity_evidence_basis(
            reference_overlap,
            identifier_overlap,
            profile_overlap,
        ),
        "explanation": similarity_explanation(coarse_only),
        "fan_out_delta": abs(len(edges.get(left, [])) - len(edges.get(right, []))),
        "shared_kind": shared_kind(declarations[left], declarations[right]),
    }


def normalized_identifiers(declaration: LeanDeclaration) -> set[str]:
    """Return exact normalized reference identifiers from extraction."""

    return {
        normalized
        for reference in declaration.references
        for normalized in [normalize_identifier(reference)]
        if normalized
    }


def normalize_identifier(value: str) -> str:
    """Normalize harmless root/punctuation syntax without collapsing names."""

    return value.strip().removeprefix("_root_.").rstrip(",;")


def similarity_evidence_basis(
    reference_overlap: float,
    identifier_overlap: float,
    profile_overlap: float,
) -> list[str]:
    """Name every non-zero similarity feature used for review."""

    rows = []
    if reference_overlap:
        rows.append("resolved_declarations")
    if identifier_overlap:
        rows.append("concrete_normalized_identifiers")
    if profile_overlap:
        rows.append("coarse_unresolved_classes")
    return rows


def similarity_explanation(coarse_only: bool) -> str:
    """Explain why coarse-only evidence cannot reach high confidence."""

    if coarse_only:
        return (
            "Only coarse unresolved-reference classes overlap; the score is "
            "capped below the high-confidence promotion band."
        )
    return (
        "Similarity is supported by resolved declarations or concrete "
        "normalized identifiers; coarse classes are annotation only."
    )


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
