"""Summary rows derived from architecture-policy findings."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def finding_summary(findings: list[dict[str, Any]]) -> dict[str, int]:
    """Count findings by kind."""

    counts: dict[str, int] = defaultdict(int)
    for row in findings:
        counts[str(row["kind"])] += 1
    return dict(sorted(counts.items()))


def direct_pair_summary(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize unique direct violations by source/target group pair."""

    pairs: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    for row in direct_findings(findings):
        edge = (str(row.get("sourceModule", "")), str(row.get("targetModule", "")))
        for pair in row.get("groupPairs", []):
            if isinstance(pair, dict):
                pairs[pair_key(pair)].add(edge)
    return [
        direct_pair_row(source_group, target_group, edges)
        for (source_group, target_group), edges in sorted(
            pairs.items(),
            key=lambda item: (-len(item[1]), item[0][0], item[0][1]),
        )
    ]


def direct_pair_row(
    source_group: str,
    target_group: str,
    edges: set[tuple[str, str]],
) -> dict[str, Any]:
    """Build one direct pair summary row."""

    return {
        "sourceGroup": source_group,
        "targetGroup": target_group,
        "uniqueDirectEdgeCount": len(edges),
        "sampleEdges": [
            {"sourceModule": source, "targetModule": target}
            for source, target in sorted(edges)[:5]
        ],
    }


def pair_key(pair: dict[str, Any]) -> tuple[str, str]:
    """Return a normalized group-pair key."""

    return str(pair.get("sourceGroup", "")), str(pair.get("targetGroup", ""))


def direct_offending_file_summary(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize direct policy violations by source file for text-first review."""

    grouped: dict[str, dict[str, Any]] = {}
    for row in direct_findings(findings):
        key = str(row.get("sourcePath") or row.get("sourceModule") or "")
        if key:
            add_direct_file_summary_row(grouped, key, row)
    return render_direct_file_summary(grouped)


def direct_context_summary(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize direct policy violations by triage context."""

    counts: dict[str, int] = defaultdict(int)
    severities: dict[str, set[str]] = defaultdict(set)
    for row in direct_findings(findings):
        context = str(row.get("policyContext", "core-looking"))
        counts[context] += 1
        severities[context].add(str(row.get("triageSeverity", row.get("severity", "warning"))))
    return [
        {
            "policyContext": context,
            "count": counts[context],
            "triageSeverities": sorted(severities[context]),
        }
        for context in sorted(counts, key=lambda item: (-counts[item], item))
    ]


def direct_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return direct forbidden-import findings only."""

    return [
        row
        for row in findings
        if row.get("kind") == "architecture_policy.direct_forbidden_import"
    ]


def add_direct_file_summary_row(
    grouped: dict[str, dict[str, Any]],
    key: str,
    row: dict[str, Any],
) -> None:
    """Accumulate one direct policy violation into a file summary row."""

    entry = grouped.setdefault(key, empty_file_summary_entry(row))
    entry["edges"].add((str(row.get("sourceModule", "")), str(row.get("targetModule", ""))))
    entry["pairs"].add((str(row.get("sourceGroup", "")), str(row.get("targetGroup", ""))))
    if len(entry["sampleImports"]) < 5:
        entry["sampleImports"].append(import_sample(row))


def empty_file_summary_entry(row: dict[str, Any]) -> dict[str, Any]:
    """Return mutable state for one offending-file summary row."""

    return {
        "sourcePath": row.get("sourcePath", ""),
        "sourceModule": row.get("sourceModule", ""),
        "edges": set(),
        "pairs": set(),
        "sampleImports": [],
    }


def import_sample(row: dict[str, Any]) -> dict[str, Any]:
    """Return a compact direct import sample for one finding."""

    return {
        "line": row.get("line"),
        "importText": row.get("importText", ""),
        "targetModule": row.get("targetModule", ""),
        "sourceGroup": row.get("sourceGroup", ""),
        "targetGroup": row.get("targetGroup", ""),
        "policyContext": row.get("policyContext", ""),
    }


def render_direct_file_summary(grouped: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert mutable grouped direct violation state into JSON-safe rows."""

    rows = [
        direct_file_summary_row(key, entry)
        for key, entry in grouped.items()
    ]
    return sorted(rows, key=lambda row: (-int(row["uniqueDirectEdgeCount"]), row["summaryKey"]))


def direct_file_summary_row(key: str, entry: dict[str, Any]) -> dict[str, Any]:
    """Render one offending-file summary row."""

    return {
        "sourcePath": entry["sourcePath"],
        "sourceModule": entry["sourceModule"],
        "uniqueDirectEdgeCount": len(entry["edges"]),
        "groupPairs": [
            {"sourceGroup": source_group, "targetGroup": target_group}
            for source_group, target_group in sorted(entry["pairs"])
        ],
        "sampleImports": entry["sampleImports"],
        "summaryKey": key,
    }


def shared_dependency_summary(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return ranked common-layer extraction candidates."""

    rows = [
        shared_dependency_summary_row(row)
        for row in findings
        if row.get("kind") == "architecture_policy.shared_dependency_candidate"
    ]
    return sorted(
        rows,
        key=lambda row: (
            -int(row["confidenceScore"]),
            -int(row["sourceGroupCount"]),
            -int(row["importerCount"]),
            row["targetModule"],
        ),
    )


def shared_dependency_summary_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize one shared dependency finding for report summaries."""

    return {
        "targetModule": str(row.get("targetModule", "")),
        "sourceGroupCount": int(row.get("sourceGroupCount", len(row.get("sourceGroups", [])))),
        "importerCount": int(row.get("importerCount", 0)),
        "dependencyScope": str(row.get("dependencyScope", "policy_targets")),
        "confidence": str(row.get("confidence", "low")),
        "confidenceScore": int(row.get("confidenceScore", 0)),
        "confidenceReason": str(row.get("confidenceReason", "")),
        "sourceGroups": list(row.get("sourceGroups", [])),
        "sampleImporters": row.get("sampleImporters", {}),
    }


def group_membership_counts(membership: dict[str, tuple[str, ...]]) -> dict[str, int]:
    """Count modules matched by each policy group."""

    counts: dict[str, int] = defaultdict(int)
    for groups in membership.values():
        for group in groups:
            counts[group] += 1
    return dict(sorted(counts.items()))
