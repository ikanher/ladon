"""Focused benchmark oracles for promoted Ladon report signals."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping


Oracle = Mapping[str, Any]
Payload = Mapping[str, Any]
ORACLE_SCHEMA_VERSION = "ladon-benchmark-oracle-v1"
SUPPORTED_SIGNALS = (
    "architecture_pair_count",
    "claim_authority_diagnostic_present",
    "facade_subtype_count",
    "generated_duplicate_family",
    "resolved_edge",
    "shared_dependency_candidate",
    "source_pattern_match_count",
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
        "architecture_pair_count": check_architecture_pair_count,
        "claim_authority_diagnostic_present": check_claim_authority_diagnostic_present,
        "facade_subtype_count": check_facade_subtype_count,
        "generated_duplicate_family": check_generated_duplicate_family,
        "resolved_edge": check_resolved_edge,
        "shared_dependency_candidate": check_shared_dependency_candidate,
        "source_pattern_match_count": check_source_pattern_match_count,
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


def check_architecture_pair_count(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check a direct architecture-policy group pair count."""

    source_group = str(oracle["sourceGroup"])
    target_group = str(oracle["targetGroup"])
    row = next(
        (
            item
            for item in payload.get("architecture_policy", {}).get("directPairSummary", [])
            if item.get("sourceGroup") == source_group and item.get("targetGroup") == target_group
        ),
        None,
    )
    observed = int(row.get("uniqueDirectEdgeCount", 0)) if row else 0
    return observed == int(oracle.get("expected", 0)), observed


def check_claim_authority_diagnostic_present(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check whether a claim-authority diagnostic rule is present."""

    diagnostics = claim_authority_diagnostics(payload)
    rule_id = str(oracle["ruleId"])
    observed = any(row.get("ruleId") == rule_id for row in diagnostics)
    return observed == bool(oracle.get("expected", True)), observed


def check_facade_subtype_count(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check a facade subtype count from module-DAG metadata."""

    subtype = str(oracle["subtype"])
    observed = int(payload.get("module_dag", {}).get("facade_subtype_summary", {}).get(subtype, 0))
    return observed == int(oracle.get("expected", 0)), observed


def check_generated_duplicate_family(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check generated duplicate-import family summary rows."""

    family = str(oracle["generatorFamily"])
    target = str(oracle["target"])
    row = next(
        (
            item
            for item in payload.get("module_dag", {}).get("duplicate_import_family_summary", [])
            if item.get("generatorFamily") == family and item.get("target") == target
        ),
        None,
    )
    if "duplicateModuleCount" in oracle:
        observed: Any = int(row.get("duplicateModuleCount", 0)) if row else 0
        return observed == int(oracle["duplicateModuleCount"]), observed
    observed = row is not None
    return observed == bool(oracle.get("expected", True)), observed


def check_resolved_edge(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check whether a declaration graph edge is present or absent."""

    source = str(oracle["source"])
    target = str(oracle["target"])
    edges = graph_edges(payload)
    observed = target in edges.get(source, [])
    return observed == bool(oracle.get("expected", True)), observed


def check_shared_dependency_candidate(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check whether a common-layer candidate target appears."""

    target = str(oracle["targetModule"])
    observed = any(
        row.get("targetModule") == target
        for row in payload.get("architecture_policy", {}).get("sharedDependencySummary", [])
    )
    return observed == bool(oracle.get("expected", True)), observed


def check_source_pattern_match_count(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check total source-pattern matches for one pattern id."""

    pattern_id = str(oracle["patternId"])
    row = find_by_key(
        payload.get("source_patterns", {}).get("patternSummary", []),
        "patternId",
        pattern_id,
    )
    observed = int(row.get("matchCount", 0)) if row else 0
    return observed == int(oracle.get("expected", 0)), observed


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


def claim_authority_diagnostics(payload: Payload) -> list[dict[str, Any]]:
    """Return claim-authority diagnostic rows from supported report namespaces."""

    diagnostics: list[dict[str, Any]] = []
    for key in ("claim_authority", "claimAuthority"):
        rows = payload.get(key, {}).get("diagnostics", [])
        if isinstance(rows, list):
            diagnostics.extend(row for row in rows if isinstance(row, dict))
    bridge = payload.get("proofir_bridge", {})
    if isinstance(bridge, dict):
        rows = bridge.get("routeAuthorityAudit", {}).get("diagnostics", [])
        if isinstance(rows, list):
            diagnostics.extend(row for row in rows if isinstance(row, dict))
    return diagnostics


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
