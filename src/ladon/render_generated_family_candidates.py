"""Text rendering for report-projected advisory generated-family candidates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def generated_family_candidate_lines(
    module_dag: Mapping[str, Any],
) -> list[str]:
    """Render candidate evidence without turning regularity into provenance."""

    raw = module_dag.get("generated_family_candidates")
    if not isinstance(raw, Mapping):
        return []
    candidates = _mapping_rows(raw.get("candidates"))
    coverage = _mapping(raw.get("coverage")).get("candidates")
    profile = _mapping(raw.get("profile"))
    lines = [
        "Generated-Looking Family Candidates (Advisory)",
        (
            f"- profile: {profile.get('profileVersion', 'unavailable')} "
            f"digest={profile.get('profileDigest', 'unavailable')}"
        ),
        f"- candidates: {_coverage_count(coverage, len(candidates))}",
    ]
    lines.extend(_candidate_line(row) for row in candidates)
    nonclaims = _mapping_rows(raw.get("nonclaims"))
    if nonclaims:
        lines.append(
            "- authority boundary: "
            + str(nonclaims[0].get("text", "advisory evidence only"))
        )
    return [*lines, ""]


def _candidate_line(candidate: Mapping[str, Any]) -> str:
    sequence = _mapping(candidate.get("sequence"))
    clauses = {
        str(row.get("id")): row for row in _mapping_rows(candidate.get("clauses"))
    }
    populations = _mapping(candidate.get("memberPopulations"))
    population_text = ",".join(
        f"{name}={count}"
        for name, count in sorted(populations.items())
        if isinstance(count, int) and count
    )
    return (
        f"- {candidate.get('id', 'unavailable')}: "
        f"parent={sequence.get('parent', '') or '.'} "
        f"prefix={sequence.get('basenamePrefix', '')} "
        f"members={sequence.get('memberCount', 0)} "
        f"density={_clause_fraction(clauses.get('numeric_density'))} "
        "common-import="
        f"{_clause_fraction(clauses.get('common_direct_internal_import'))} "
        "common-lexical="
        f"{_clause_fraction(clauses.get('common_lexical_witness'))} "
        f"populations={population_text or 'unclassified'}"
    )


def _clause_fraction(raw: Any) -> str:
    clause = _mapping(raw)
    operands = _mapping(clause.get("operands"))
    numerator = operands.get("observedNumerator")
    denominator = operands.get("observedDenominator")
    status = clause.get("status", "unavailable")
    if not isinstance(numerator, int) or not isinstance(denominator, int):
        return str(status)
    return f"{numerator}/{denominator}:{status}"


def _coverage_count(raw: Any, fallback: int) -> str:
    coverage = _mapping(raw)
    visible = coverage.get("visible", fallback)
    total_known = coverage.get("totalKnown")
    total = coverage.get("total")
    if total_known is True and isinstance(total, int):
        return f"{visible}/{total} visible"
    lower = coverage.get("observedLowerBound", visible)
    return f"{visible} visible, total unknown (observed >= {lower})"


def _mapping(raw: Any) -> Mapping[str, Any]:
    return raw if isinstance(raw, Mapping) else {}


def _mapping_rows(raw: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()
    return tuple(row for row in raw if isinstance(row, Mapping))


__all__ = ["generated_family_candidate_lines"]
