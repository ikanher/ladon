"""Configurable source-pattern scans for project-local review conventions.

The analyzer owns only the generic matching contract. Projects provide the
terms, regexes, severities, and generated-code filtering policy.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


DEFAULT_MAX_MATCHES = 200
SEVERITIES = {"info", "warning", "error", "critical"}


@dataclass(frozen=True)
class SourceDocument:
    """One source file supplied by the pipeline boundary."""

    module: str
    path: str
    text: str
    tags: tuple[str, ...] = ()

    @property
    def generated(self) -> bool:
        """Return whether extraction classified this source as generated."""

        return "generated" in self.tags


@dataclass(frozen=True)
class SourcePattern:
    """Normalized source-pattern policy row."""

    pattern_id: str
    pattern: str
    kind: str
    severity: str
    regex: bool
    case_sensitive: bool
    exclude_generated: bool
    max_matches: int
    message: str


def summarize_source_patterns(
    documents: Iterable[SourceDocument],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Return matches for one configurable source-pattern policy."""

    patterns, diagnostics = normalize_patterns(policy)
    matches, pattern_summary = collect_matches(tuple(documents), patterns)
    match_count = sum(int(row["matchCount"]) for row in pattern_summary)
    kind_summary = summary_counts(pattern_summary, "kind")
    severity_summary = summary_counts(pattern_summary, "severity")
    findings = [match_finding(match) for match in matches]
    findings.extend(diagnostic_finding(diagnostic) for diagnostic in diagnostics)
    return {
        "artifactKind": "ladon_source_pattern_report",
        "schemaVersion": 1,
        "status": "ok" if not diagnostics else "policy_diagnostics",
        "policyId": str(policy.get("id") or policy.get("policyId") or ""),
        "patternCount": len(patterns),
        "matchCount": match_count,
        "reportedMatchCount": len(matches),
        "truncated": match_count > len(matches),
        "summary": kind_summary,
        "severitySummary": severity_summary,
        "patternSummary": pattern_summary,
        "diagnostics": diagnostics,
        "matches": matches,
        "findings": findings,
    }


def normalize_patterns(policy: Mapping[str, Any]) -> tuple[list[SourcePattern], list[dict[str, Any]]]:
    """Normalize policy rows without hard-coding project terms."""

    raw_patterns = policy.get("patterns", [])
    if not isinstance(raw_patterns, list):
        return [], [invalid_policy("patterns", "patterns must be a list")]
    patterns: list[SourcePattern] = []
    diagnostics: list[dict[str, Any]] = []
    for index, row in enumerate(raw_patterns, start=1):
        if not isinstance(row, Mapping):
            diagnostics.append(invalid_policy(f"patterns[{index}]", "pattern row must be an object"))
            continue
        pattern = row.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            diagnostics.append(invalid_policy(pattern_id(row, index), "pattern must be a non-empty string"))
            continue
        regex = bool(row.get("regex", False))
        if regex:
            try:
                compile_pattern(pattern, case_sensitive=bool_value(row, "caseSensitive", True))
            except re.error as exc:
                diagnostics.append(invalid_policy(pattern_id(row, index), f"invalid regex: {exc}"))
                continue
        patterns.append(
            SourcePattern(
                pattern_id=pattern_id(row, index),
                pattern=pattern,
                kind=str(row.get("kind") or "source_pattern"),
                severity=normalize_severity(row.get("severity")),
                regex=regex,
                case_sensitive=bool_value(row, "caseSensitive", True),
                exclude_generated=bool_value(row, "excludeGenerated", False),
                max_matches=max(1, int_value(row.get("maxMatches"), DEFAULT_MAX_MATCHES)),
                message=str(row.get("message") or ""),
            )
        )
    return patterns, diagnostics


def collect_matches(
    documents: tuple[SourceDocument, ...],
    patterns: list[SourcePattern],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Collect bounded pattern matches and per-pattern counts."""

    matches: list[dict[str, Any]] = []
    pattern_summary: list[dict[str, Any]] = []
    for pattern in patterns:
        pattern_matches = list(matches_for_pattern(documents, pattern))
        visible = pattern_matches[: pattern.max_matches]
        matches.extend(visible)
        pattern_summary.append(
            {
                "patternId": pattern.pattern_id,
                "kind": pattern.kind,
                "severity": pattern.severity,
                "matchCount": len(pattern_matches),
                "reportedMatchCount": len(visible),
                "truncated": len(pattern_matches) > len(visible),
                "excludeGenerated": pattern.exclude_generated,
                "regex": pattern.regex,
                "caseSensitive": pattern.case_sensitive,
            }
        )
    return sorted(matches, key=match_sort_key), pattern_summary


def summary_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    """Summarize total matches by a pattern-summary field."""

    counts: Counter[str] = Counter()
    for row in rows:
        counts[str(row[key])] += int(row["matchCount"])
    return dict(sorted(counts.items()))


def matches_for_pattern(
    documents: tuple[SourceDocument, ...],
    pattern: SourcePattern,
) -> Iterable[dict[str, Any]]:
    """Yield source rows matching one normalized pattern."""

    compiled = compile_pattern(pattern.pattern, case_sensitive=pattern.case_sensitive) if pattern.regex else None
    needle = pattern.pattern if pattern.case_sensitive else pattern.pattern.lower()
    for document in documents:
        if pattern.exclude_generated and document.generated:
            continue
        for line_number, line in enumerate(document.text.splitlines(), start=1):
            haystack = line if pattern.case_sensitive else line.lower()
            matched = bool(compiled.search(line)) if compiled else needle in haystack
            if matched:
                yield {
                    "patternId": pattern.pattern_id,
                    "kind": pattern.kind,
                    "severity": pattern.severity,
                    "module": document.module,
                    "path": document.path,
                    "line": line_number,
                    "text": line.strip(),
                    "generated": document.generated,
                    "message": pattern.message,
                }


def compile_pattern(pattern: str, *, case_sensitive: bool) -> re.Pattern[str]:
    """Compile one regular expression with policy-selected case handling."""

    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(pattern, flags)


def match_finding(match: dict[str, Any]) -> dict[str, Any]:
    """Adapt a source-pattern match to Ladon's shared finding shape."""

    detail = match.get("message") or f"{match['patternId']} matched {match['kind']}"
    return {
        "kind": "source_pattern.match",
        "family": "source_pattern",
        "severity": match["severity"],
        "subject": f"{match['path']}:{match['line']}",
        "message": detail,
        "patternId": match["patternId"],
        "patternKind": match["kind"],
        "module": match["module"],
        "sourcePath": match["path"],
        "line": match["line"],
        "text": match["text"],
        "generated": match["generated"],
    }


def diagnostic_finding(diagnostic: dict[str, Any]) -> dict[str, Any]:
    """Adapt policy diagnostics to the shared finding shape."""

    return {
        "kind": "source_pattern.invalid_policy",
        "family": "source_pattern",
        "severity": "error",
        "subject": diagnostic["subject"],
        "message": diagnostic["message"],
    }


def invalid_policy(subject: str, message: str) -> dict[str, Any]:
    """Return one policy diagnostic row."""

    return {
        "kind": "source_pattern.invalid_policy",
        "severity": "error",
        "subject": subject,
        "message": message,
    }


def pattern_id(row: Mapping[str, Any], index: int) -> str:
    """Return a stable pattern id for rows that omit one."""

    value = row.get("id") or row.get("patternId")
    return str(value) if value else f"pattern_{index}"


def normalize_severity(value: Any) -> str:
    """Return a supported severity label."""

    severity = str(value or "warning")
    return severity if severity in SEVERITIES else "warning"


def bool_value(row: Mapping[str, Any], key: str, default: bool) -> bool:
    """Return boolean policy values without treating arbitrary strings as true."""

    value = row.get(key, default)
    return value if isinstance(value, bool) else default


def int_value(value: Any, default: int) -> int:
    """Return positive integer policy values."""

    if isinstance(value, int):
        return value
    return default


def match_sort_key(row: dict[str, Any]) -> tuple[str, int, str]:
    """Sort matches by source location and then pattern id."""

    return str(row["path"]), int(row["line"]), str(row["patternId"])
