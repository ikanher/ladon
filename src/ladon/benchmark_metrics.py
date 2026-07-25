"""Separate correctness and coverage metrics for labeled benchmark rows."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


@dataclass
class ClassificationCounts:
    """Mutable confusion counts while labels are accumulated."""

    true_positive: int = 0
    false_positive: int = 0
    false_negative: int = 0
    true_negative: int = 0

    def to_json(self) -> dict[str, Any]:
        """Return counts plus defined precision and recall."""

        return {
            "truePositive": self.true_positive,
            "falsePositive": self.false_positive,
            "falseNegative": self.false_negative,
            "trueNegative": self.true_negative,
            "precision": safe_ratio(
                self.true_positive,
                self.true_positive + self.false_positive,
            ),
            "recall": safe_ratio(
                self.true_positive,
                self.true_positive + self.false_negative,
            ),
        }


def classification_metrics(
    labels: Sequence[Mapping[str, Any]],
    passed: Sequence[bool],
) -> dict[str, dict[str, Any]]:
    """Return per-signal confusion metrics from labeled oracle outcomes."""

    if len(labels) != len(passed):
        raise ValueError("labels and oracle outcomes must have equal lengths")
    counts: dict[str, ClassificationCounts] = defaultdict(ClassificationCounts)
    for label, outcome in zip(labels, passed, strict=True):
        update_counts(counts[str(label["signalKind"])], label, outcome)
    return {
        kind: row.to_json()
        for kind, row in sorted(counts.items())
    }


def update_counts(
    counts: ClassificationCounts,
    label: Mapping[str, Any],
    passed: bool,
) -> None:
    """Update confusion counts for one reviewed expectation."""

    expected_present = label.get("expectedOutcome") != "absent"
    observed_present = passed if expected_present else not passed
    if expected_present and observed_present:
        counts.true_positive += 1
    elif expected_present:
        counts.false_negative += 1
    elif observed_present:
        counts.false_positive += 1
    else:
        counts.true_negative += 1


def safe_ratio(numerator: int, denominator: int) -> float | None:
    """Return a stable ratio or null when the metric is undefined."""

    return round(numerator / denominator, 6) if denominator else None


def known_case_recall(
    expected: Iterable[str],
    observed: Iterable[str],
) -> dict[str, Any]:
    """Return set-based recall for a reviewed known-case inventory."""

    expected_set = set(expected)
    observed_set = set(observed)
    hits = expected_set.intersection(observed_set)
    misses = expected_set - observed_set
    return {
        "expected": sorted(expected_set),
        "observed": sorted(observed_set),
        "hits": sorted(hits),
        "misses": sorted(misses),
        "recall": safe_ratio(len(hits), len(expected_set)),
    }


def extraction_coverage(
    expected: Mapping[str, Iterable[str]],
    observed: Mapping[str, Iterable[str]],
) -> dict[str, Any]:
    """Return per-surface and total set coverage without conflating kinds."""

    rows = {
        kind: known_case_recall(values, observed.get(kind, ()))
        for kind, values in sorted(expected.items())
    }
    expected_count = sum(len(row["expected"]) for row in rows.values())
    hit_count = sum(len(row["hits"]) for row in rows.values())
    return {
        "byKind": rows,
        "expectedCount": expected_count,
        "hitCount": hit_count,
        "coverage": safe_ratio(hit_count, expected_count),
    }


def semantic_parity(json_payload: Mapping[str, Any], text: str) -> dict[str, Any]:
    """Check stable report facts represented in both JSON and text."""

    metadata = json_payload.get("metadata", {})
    dag = json_payload.get("module_dag", {})
    expected_fragments = (
        str(metadata.get("analysis_root_module", "")),
        str(dag.get("module_count", "")),
        str(dag.get("edge_count", "")),
    )
    missing = [fragment for fragment in expected_fragments if fragment not in text]
    return {
        "checkedFacts": len(expected_fragments),
        "missingFacts": missing,
        "passed": not missing,
    }
