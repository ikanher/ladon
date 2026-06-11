"""Focused benchmark oracles for promoted Ladon report signals."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping


Oracle = Mapping[str, Any]
Payload = Mapping[str, Any]
ORACLE_SCHEMA_VERSION = "ladon-benchmark-oracle-v1"
SUPPORTED_SIGNALS = (
    "resolved_edge",
    "unresolved_class",
    "proof_family_candidate",
    "root_scope_classification",
    "packet_profile_status",
    "finding_kind_present",
    "finding_kind_absent",
)


@dataclass(frozen=True)
class OracleResult:
    """One focused benchmark-oracle evaluation result."""

    fixture: str
    signal: str
    passed: bool
    expected: Any
    observed: Any
    message: str

    def to_json(self) -> dict[str, Any]:
        """Return the stable machine-readable result row."""

        return {
            "fixture": self.fixture,
            "signal": self.signal,
            "passed": self.passed,
            "expected": self.expected,
            "observed": self.observed,
            "message": self.message,
        }


def evaluate_oracles(payload: Payload, oracles: list[Oracle]) -> list[OracleResult]:
    """Evaluate focused signal oracles against one Ladon-like payload."""

    return [evaluate_oracle(payload, oracle) for oracle in oracles]


def evaluate_oracle(payload: Payload, oracle: Oracle) -> OracleResult:
    """Evaluate one oracle row and return an explanatory result."""

    signal = str(oracle["signal"])
    evaluator = oracle_dispatch().get(signal)
    if evaluator is None:
        return result_row(oracle, False, f"unknown signal: {signal}", None)
    passed, observed = evaluator(payload, oracle)
    expected = oracle.get("expected")
    message = oracle_message(oracle, passed, observed)
    return result_row(oracle, passed, message, observed, expected=expected)


def oracle_dispatch() -> dict[str, Callable[[Payload, Oracle], tuple[bool, Any]]]:
    """Return supported oracle evaluators by signal name."""

    return {
        "resolved_edge": check_resolved_edge,
        "unresolved_class": check_unresolved_class,
        "proof_family_candidate": check_proof_family_candidate,
        "root_scope_classification": check_root_scope_classification,
        "packet_profile_status": check_packet_profile_status,
        "finding_kind_present": check_finding_kind_present,
        "finding_kind_absent": check_finding_kind_absent,
    }


def oracle_schema() -> dict[str, Any]:
    """Return a compact schema description for focused benchmark oracles."""

    return {
        "schema": ORACLE_SCHEMA_VERSION,
        "required": ["fixture", "signal", "expected"],
        "supported_signals": list(SUPPORTED_SIGNALS),
        "non_claims": [
            "Benchmark oracles check Ladon signal behavior, not theorem truth.",
            "Focused oracle pass/fail rows are not full-report golden snapshots.",
        ],
    }


def existing_optional_smoke_roots(candidates: Mapping[str, str]) -> dict[str, str]:
    """Return optional external smoke roots that exist on this machine."""

    return {
        name: path
        for name, path in sorted(candidates.items())
        if Path(path).exists()
    }


def check_resolved_edge(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check whether a declaration graph edge is present or absent."""

    source = str(oracle["source"])
    target = str(oracle["target"])
    edges = graph_edges(payload)
    observed = target in edges.get(source, [])
    return observed == bool(oracle.get("expected", True)), observed


def check_unresolved_class(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check unresolved reference classification for one candidate."""

    candidate = str(oracle["candidate"])
    row = find_by_key(
        payload.get("declaration_graph", {}).get("top_unresolved_references", []),
        "candidate",
        candidate,
    )
    observed = row.get("classification") if row else None
    return observed == oracle.get("expected"), observed


def check_proof_family_candidate(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check whether a proof-family similarity candidate is present."""

    suffix = str(oracle["suffix"])
    rows = payload.get("declaration_graph", {}).get("proof_family_similarity_candidates", [])
    observed = any(row.get("suffix") == suffix for row in rows)
    return observed == bool(oracle.get("expected", True)), observed


def check_root_scope_classification(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check the root-scope classification attached to findings."""

    observed = [
        finding.get("root_scope", {}).get("classification")
        for finding in payload.get("findings", [])
        if finding.get("kind") == "root_scope_pressure"
    ]
    expected = str(oracle["expected"])
    return expected in observed, observed


def check_packet_profile_status(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check packet evidence status for a profile."""

    profile = str(oracle["profile"])
    row = find_by_key(payload.get("packet_evidence", []), "profile", profile)
    observed = row.get("profile_status") if row else None
    return observed == oracle.get("expected"), observed


def check_finding_kind_present(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check that a finding kind is present."""

    kinds = finding_kinds(payload)
    expected = str(oracle["kind"])
    return expected in kinds, kinds


def check_finding_kind_absent(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check that a finding kind is absent."""

    kinds = finding_kinds(payload)
    expected = str(oracle["kind"])
    return expected not in kinds, kinds


def graph_edges(payload: Payload) -> dict[str, list[str]]:
    """Return declaration graph edges with normalized string keys and values."""

    return {
        str(source): [str(target) for target in targets]
        for source, targets in payload.get("declaration_graph", {}).get("edges", {}).items()
    }


def finding_kinds(payload: Payload) -> list[str]:
    """Return finding kinds in report order."""

    return [str(finding.get("kind", "")) for finding in payload.get("findings", [])]


def find_by_key(rows: Any, key: str, value: str) -> dict[str, Any] | None:
    """Return the first dictionary row whose key matches value."""

    if not isinstance(rows, list):
        return None
    return next(
        (row for row in rows if isinstance(row, dict) and row.get(key) == value),
        None,
    )


def result_row(
    oracle: Oracle,
    passed: bool,
    message: str,
    observed: Any,
    *,
    expected: Any | None = None,
) -> OracleResult:
    """Build one oracle result with stable fixture and signal labels."""

    return OracleResult(
        fixture=str(oracle.get("fixture", "unknown")),
        signal=str(oracle.get("signal", "unknown")),
        passed=passed,
        expected=oracle.get("expected") if expected is None else expected,
        observed=observed,
        message=message,
    )


def oracle_message(oracle: Oracle, passed: bool, observed: Any) -> str:
    """Render a human-readable oracle outcome."""

    status = "passed" if passed else "failed"
    return (
        f"{status}: fixture={oracle.get('fixture', 'unknown')} "
        f"signal={oracle.get('signal', 'unknown')} "
        f"expected={oracle.get('expected')} observed={observed}"
    )
