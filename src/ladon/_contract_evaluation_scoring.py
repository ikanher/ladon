"""Strict, deterministic case-level scoring for contract evaluations."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from ladon._contract_evaluation_core import _opaque_identifier

MAX_ROWS = 256
MAX_FINDINGS = 4096
MAX_OUTPUT = 2 * 1024 * 1024


def _fail(message: str) -> None:
    raise ValueError(message)


def _keys(obj: Any, required: set[str], optional: set[str] = frozenset(), where: str = "object") -> None:
    if not isinstance(obj, dict): _fail(f"{where} must be an object")
    if any(not isinstance(key, str) for key in obj): _fail(f"{where} keys must be strings")
    missing = required - obj.keys()
    extra = obj.keys() - required - optional
    if missing: _fail(f"{where} missing fields: {', '.join(sorted(missing))}")
    if extra: _fail(f"{where} has unknown fields: {', '.join(sorted(extra))}")


def _number(value: Any, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
        _fail(f"invalid {name}")


def _counter(value: Any, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 10**9:
        _fail(f"invalid {name}")


def _nullable_int(value: Any, name: str) -> None:
    if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 2**63 - 1):
        _fail(f"invalid {name}")


def canonical_json(value: Any) -> bytes:
    return __import__("json").dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


_STATUSES = ("complete", "timeout", "unsupported", "resource-stop", "checker-failure", "extraction-error")
_JUDGMENTS = ("supported", "refuted", "unsupported", "unresolved")
_CLASSES = {
    "A": {"mismatch", "valid", "unknown"},
    "B": {"matching", "discrepancy", "unsupported"},
    "C": set(),
}
_ROW_FIELDS = {
    "caseId", "track", "status", "checkerAttempts", "failedProbes", "extractionErrors",
    "unsupportedSelections", "elapsedSeconds", "peakRssBytes",
}


def _normalize_aggregation_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict], dict[str, dict]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)) or len(rows) > MAX_ROWS:
        _fail("aggregation rows must be a bounded sequence")
    normalized = []
    by_id: dict[str, dict] = {}
    for value in rows:
        row = dict(value) if isinstance(value, Mapping) else value
        _validate_aggregation_row(row)
        cid = row["caseId"]
        if cid in by_id:
            _fail("duplicate aggregation caseId")
        by_id[cid] = row
        normalized.append(row)
    return normalized, by_id


def _validate_aggregation_row(row: Any) -> None:
    _keys(row, _ROW_FIELDS, {"batch", "observedClass", "findingIds"}, where="aggregation row")
    _opaque_identifier(row["caseId"], r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", "aggregation caseId")
    track = row["track"]
    if not isinstance(track, str) or track not in _CLASSES or row["status"] not in _STATUSES:
        _fail("invalid aggregation track or status")
    _validate_aggregation_class(row, track)
    _validate_aggregation_findings(row)
    _validate_aggregation_measurements(row)


def _validate_aggregation_class(row: dict, track: str) -> None:
    observed = row.get("observedClass")
    if observed is not None and (not isinstance(observed, str) or observed not in _CLASSES[track]):
        _fail("invalid aggregation observedClass")


def _validate_aggregation_findings(row: dict) -> None:
    findings = row.get("findingIds", [])
    valid_findings = isinstance(findings, list) and len(findings) <= MAX_FINDINGS
    if valid_findings:
        for item in findings:
            _opaque_identifier(item, r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", "aggregation findingId")
    if not valid_findings or len(set(findings)) != len(findings):
        _fail("invalid aggregation findingIds")


def _validate_aggregation_measurements(row: dict) -> None:
    for name in ("checkerAttempts", "failedProbes", "extractionErrors", "unsupportedSelections"):
        _counter(row[name], name)
    _number(row["elapsedSeconds"], "elapsedSeconds")
    _nullable_int(row["peakRssBytes"], "peakRssBytes")


def _normalize_case_adjudication(adj: Mapping[str, Any], finding_ids: set[str]) -> tuple[str, dict[str, str]]:
    _keys(dict(adj), {"caseJudgment", "findings"}, where="case adjudication")
    case_judgment = adj["caseJudgment"]
    if not isinstance(case_judgment, str) or case_judgment not in _JUDGMENTS:
        _fail("invalid case judgment")
    judgments = _normalize_finding_judgments(adj["findings"])
    if set(judgments) != finding_ids:
        _fail("adjudication finding IDs mismatch")
    if any(not isinstance(value, str) or value not in _JUDGMENTS for value in judgments.values()):
        _fail("invalid finding judgment")
    return case_judgment, judgments


def _normalize_finding_judgments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, Mapping): return dict(raw)
    if not isinstance(raw, list): _fail("adjudication findings must be a mapping or array")
    judgments = {}
    for item in raw:
        _keys(item, {"findingId", "judgment"}, where="finding adjudication")
        finding_id = item["findingId"]
        if not isinstance(finding_id, str): _fail("finding adjudication ID must be text")
        if finding_id in judgments: _fail("duplicate finding adjudication")
        judgments[finding_id] = item["judgment"]
    return judgments


def _validate_aggregation_maps(by_id: dict[str, dict], adjudications: Mapping[str, Any], key: Mapping[str, Any]) -> None:
    if set(key) != set(by_id):
        _fail("key case IDs do not match aggregation rows")
    for cid, entry in key.items():
        _keys(entry, {"expectedClass"}, where="key entry")
        expected = entry["expectedClass"]
        if not isinstance(expected, str) or expected not in _CLASSES[by_id[cid]["track"]]:
            _fail("key expectedClass does not match track")
    if not set(adjudications).issubset(by_id):
        _fail("adjudication case IDs do not match report rows")
    for cid, adj in adjudications.items():
        _normalize_case_adjudication(adj, set(by_id[cid].get("findingIds", [])))


# Score false accusations per case while retaining every assertion-level judgment.
def _score_case(row: dict, expected: str, adjudications: Mapping[str, Any]) -> dict:
    cid = row["caseId"]
    adj = adjudications.get(cid, {"caseJudgment": "unresolved", "findings": {}})
    case_judgment, judgments = _normalize_case_adjudication(
        adj, set(row.get("findingIds", []))
    )
    observed = row.get("observedClass")
    discrepancy = observed in ("mismatch", "discrepancy")
    accused = _is_false_accusation(expected, discrepancy, case_judgment, judgments)
    fault = expected in ("mismatch", "discrepancy")
    control = expected in ("valid", "matching")
    tp = _is_true_positive(row, fault, accused, discrepancy, case_judgment, judgments)
    justified = _is_justified_control(control, accused, case_judgment, judgments)
    unresolved = _unresolved_count(case_judgment, judgments)
    return {
        "expectedClass": expected,
        "caseJudgment": case_judgment,
        "findingJudgments": dict(sorted(judgments.items())),
        "classificationCorrect": observed == expected if observed is not None else None,
        "falseAccusation": accused,
        "truePositive": tp,
        "missedFault": fault and not tp,
        "justifiedControl": justified,
        "abstention": observed is None or unresolved > 0,
        "unresolvedAdjudications": unresolved,
    }


def _is_false_accusation(expected: str, discrepancy: bool, case_judgment: str,
                         judgments: Mapping[str, str]) -> bool:
    if any(value in ("refuted", "unsupported") for value in judgments.values()): return True
    if discrepancy and case_judgment in ("refuted", "unsupported"): return True
    return expected in ("valid", "matching", "unsupported") and discrepancy


def _supported_findings(judgments: Mapping[str, str]) -> bool:
    return all(value == "supported" for value in judgments.values())


def _is_true_positive(row, fault, accused, discrepancy, case_judgment, judgments) -> bool:
    has_evidence = case_judgment == "supported" and bool(row.get("findingIds"))
    return fault and not accused and discrepancy and has_evidence and _supported_findings(judgments)


def _is_justified_control(control, accused, case_judgment, judgments) -> bool:
    return control and not accused and case_judgment == "supported" and _supported_findings(judgments)


def _unresolved_count(case_judgment: str, judgments: Mapping[str, str]) -> int:
    return int(case_judgment == "unresolved") + sum(
        value == "unresolved" for value in judgments.values()
    )


def _new_track_counts() -> dict[str, Any]:
    return {
        "counts": {status: 0 for status in _STATUSES},
        "truePositives": 0, "falseAccusations": 0, "missedFaults": 0,
        "justifiedControls": 0, "abstentions": 0, "unsupported": 0,
        "errors": 0, "checkerAttempts": 0, "failedProbes": 0,
        "extractionErrors": 0, "unsupportedSelections": 0,
        "elapsedSeconds": 0.0, "peakRssBytes": None,
        "coverageCases": 0, "unresolvedAdjudications": 0,
        "positiveDenominator": 0, "controlDenominator": 0,
        "timeToFirstSupportedFinding": None,
    }


def _accumulate_case(counts: dict[str, Any], row: dict, score: dict, elapsed_before: float) -> None:
    _accumulate_resource_counts(counts, row)
    _accumulate_score_counts(counts, score)
    _accumulate_class_counts(counts, row, score)
    _accumulate_time_to_finding(counts, row, score, elapsed_before)


def _accumulate_resource_counts(counts: dict[str, Any], row: dict) -> None:
    counts["counts"][row["status"]] += 1
    for metric in ("checkerAttempts", "failedProbes", "extractionErrors", "unsupportedSelections"):
        counts[metric] += row[metric]
    counts["elapsedSeconds"] += row["elapsedSeconds"]
    rss = row["peakRssBytes"]
    if rss is not None: counts["peakRssBytes"] = max(counts["peakRssBytes"] or 0, rss)
    counts["coverageCases"] += int(row.get("observedClass") is not None)


def _accumulate_score_counts(counts: dict[str, Any], score: dict) -> None:
    counts["truePositives"] += int(score["truePositive"])
    counts["falseAccusations"] += int(score["falseAccusation"])
    counts["missedFaults"] += int(score["missedFault"])
    counts["justifiedControls"] += int(score["justifiedControl"])
    counts["abstentions"] += int(score["abstention"])
    counts["unresolvedAdjudications"] += score["unresolvedAdjudications"]


def _accumulate_class_counts(counts: dict[str, Any], row: dict, score: dict) -> None:
    expected = score["expectedClass"]
    status = row["status"]
    counts["positiveDenominator"] += int(expected in ("mismatch", "discrepancy"))
    counts["controlDenominator"] += int(expected in ("valid", "matching"))
    if expected in ("unknown", "unsupported") and (
        row.get("observedClass") in ("unknown", "unsupported") or status == "unsupported"
    ):
        counts["unsupported"] += 1
    if status in ("unsupported", "checker-failure", "extraction-error", "timeout", "resource-stop"):
        counts["errors"] += 1


def _accumulate_time_to_finding(counts: dict[str, Any], row: dict, score: dict, elapsed_before: float) -> None:
    has_supported_finding = bool(row.get("findingIds")) and score["caseJudgment"] == "supported"
    if has_supported_finding and counts["timeToFirstSupportedFinding"] is None:
        counts["timeToFirstSupportedFinding"] = elapsed_before + row["elapsedSeconds"]


# Derive all rates from observed denominators and report undefined empty-track rates as null.
def _track_summary(track: str, rows: list[dict], adjudications: Mapping[str, Any], key: Mapping[str, Any]) -> tuple[dict, list[dict]]:
    counts = _new_track_counts()
    cases = []
    elapsed_before = 0.0
    for row in rows:
        score = _score_case(row, key[row["caseId"]]["expectedClass"], adjudications)
        _accumulate_case(counts, row, score, elapsed_before)
        cases.append({**row, **score})
        elapsed_before += row["elapsedSeconds"]
    n = len(rows)
    summary = {
        "n": n, "denominator": n,
        "truePositives": counts["truePositives"],
        "falseAccusations": counts["falseAccusations"],
        "missedFaults": counts["missedFaults"],
        "justifiedControls": counts["justifiedControls"],
        "abstentions": counts["abstentions"], "unsupported": counts["unsupported"],
        "errors": counts["errors"], "checkerAttempts": counts["checkerAttempts"],
        "failedProbes": counts["failedProbes"], "extractionErrors": counts["extractionErrors"],
        "unsupportedSelections": counts["unsupportedSelections"], "statusCounts": counts["counts"],
        "elapsedSeconds": round(counts["elapsedSeconds"], 9), "wallTimeSeconds": None,
        "peakRssBytes": counts["peakRssBytes"], "coverageCases": counts["coverageCases"],
        "coverage": counts["coverageCases"] / n if n else None,
        "timeToFirstSupportedFinding": counts["timeToFirstSupportedFinding"],
        "unresolvedAdjudications": counts["unresolvedAdjudications"],
        "falseAccusationRate": counts["falseAccusations"] / n if n else None,
        "truePositiveRate": counts["truePositives"] / counts["positiveDenominator"] if counts["positiveDenominator"] else None,
        "justifiedControlRate": counts["justifiedControls"] / counts["controlDenominator"] if counts["controlDenominator"] else None,
    }
    return summary, cases


def aggregate_case_metrics(rows: Sequence[Mapping[str, Any]], adjudications: Mapping[str, Any], key: Mapping[str, Any]) -> dict:
    """Strict pure scorer, also usable with miniature synthetic populations."""
    normalized, by_id = _normalize_aggregation_rows(rows)
    if not isinstance(adjudications, Mapping) or not isinstance(key, Mapping):
        _fail("adjudications and key must be mappings")
    _validate_aggregation_maps(by_id, adjudications, key)
    tracks = {}
    case_results = []
    for track in ("A", "B", "C"):
        summary, cases = _track_summary(
            track, [row for row in normalized if row["track"] == track], adjudications, key
        )
        tracks[track] = summary
        case_results.extend(cases)
    case_results.sort(key=lambda row: (row["track"], row["caseId"]))
    out = {"schema": "ladon-contract-evaluation-metrics-v1", "cases": case_results, "tracks": tracks}
    if len(canonical_json(out)) > MAX_OUTPUT:
        _fail("aggregate output exceeds limit")
    return out

