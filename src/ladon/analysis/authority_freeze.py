"""Validate the frozen authority/discovery dependency graph for backlog gates.

Correctness and security maintenance can stay within the existing children.
Adding a release prerequisite requires a separately reviewed policy change;
ledger prose or a completion flag cannot release this freeze.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROGRAM = "ladon-authority-safe-verified-discovery-umbrella"
MAX_LEDGER_BYTES = 1024 * 1024
LEDGER_FIELDS = frozenset({
    "schemaVersion", "program", "sourceEvidence", "releaseInvariant", "evidenceInvariant",
    "discoveryInvariant", "freezeInvariant", "tddInvariant", "existingOwners", "children",
    "historicalReconstructionPolicy",
})
OWNERS = frozenset({
    "ladon-first-hand-proof-search-hardening-umbrella",
    "ladon-proofir-local-integrity-hardening-umbrella",
    "proofir-observation-authority-and-coverage-core",
    "proofir-derivation-hypergraph-semantics", "ladon-cli-execution-contract",
    "ladon-alpha-hardening-umbrella",
})
CHILDREN = {
    "ladon-proof-discovery-correctness-repairs": (
        "installed-scope-freshness-and-type-evidence-honest-discovery", (),
        ("ladon-first-hand-proof-search-hardening-umbrella", "ladon-cli-execution-contract"),
        ("ladon-authority-safe-release-gate",),
    ),
    "ladon-execution-authority-integrity": (
        "single-context-secret-safe-non-escalating-evidence-receipts", (),
        ("ladon-proofir-local-integrity-hardening-umbrella", "proofir-observation-authority-and-coverage-core",
         "proofir-derivation-hypergraph-semantics", "ladon-cli-execution-contract"),
        ("ladon-authority-safe-release-gate",),
    ),
    "ladon-authority-safe-release-gate": (
        "same-candidate-conjunctive-authority-safe-integration",
        ("ladon-proof-discovery-correctness-repairs", "ladon-execution-authority-integrity"),
        ("ladon-alpha-hardening-umbrella",), ("ladon-verified-discovery-loop",),
    ),
    "ladon-verified-discovery-loop": (
        "installed-bounded-goal-context-to-attributable-compiled-application",
        ("ladon-authority-safe-release-gate",),
        ("ladon-proof-discovery-correctness-repairs", "ladon-execution-authority-integrity"),
        ("ladon-capability-readiness-and-external-evaluation",),
    ),
    "ladon-capability-readiness-and-external-evaluation": (
        "machine-evidenced-held-out-capability-readiness", ("ladon-verified-discovery-loop",),
        ("ladon-authority-safe-release-gate", "ladon-portable-benchmark-fixtures-and-signal-oracles"), (),
    ),
}


def inspect_authority_freeze(openspec_root: Path) -> dict[str, Any]:
    """Return freeze violations and file-backed local plans, without executing code."""
    directory = openspec_root / "changes" / PROGRAM
    if not directory.is_dir():
        return {"state": "not-present", "findings": [], "localChildPlans": []}
    try:
        ledger = _read_ledger(directory / "children/dependency-ledger.json")
        details = _ledger_findings(ledger)
        details.extend(_plan_findings(directory))
    except (OSError, ValueError, TypeError) as exc:
        details = [f"dependency ledger is unavailable or invalid: {exc}"]
    findings = [{"kind": "expansion_freeze_violation", "change_id": PROGRAM, "detail": detail}
                for detail in details]
    return {"state": "frozen", "findings": findings,
            "localChildPlans": sorted(CHILDREN) if not findings else []}


def _read_ledger(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        data = stream.read(MAX_LEDGER_BYTES + 1)
    if len(data) > MAX_LEDGER_BYTES:
        raise ValueError("ledger exceeds the byte limit")
    result = json.loads(data, object_pairs_hook=_unique_keys, parse_constant=_reject_constant)
    if not isinstance(result, dict):
        raise TypeError("ledger must be an object")
    return result


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate ledger key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite ledger constant: {value}")


def _ledger_findings(ledger: dict[str, Any]) -> list[str]:
    if set(ledger) != LEDGER_FIELDS or type(ledger.get("schemaVersion")) is not int or ledger["schemaVersion"] != 1:
        return ["ledger fields or schemaVersion differ from the frozen contract"]
    if ledger["program"] != PROGRAM or not ledger["freezeInvariant"]:
        return ["program or expansion-freeze invariant differs from the frozen contract"]
    return _owner_findings(ledger["existingOwners"]) + _child_findings(ledger["children"])


def _owner_findings(rows: Any) -> list[str]:
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        return ["existing owner registry must be a list of objects"]
    names = [row.get("owner") for row in rows]
    if any(set(row) != {"owner", "concern"} for row in rows):
        return ["existing owner registry has unrecognized dependency fields"]
    if len(names) != len(OWNERS) or set(names) != OWNERS:
        return [f"existing owner registry changed: {names!r}"]
    return []


def _child_findings(rows: Any) -> list[str]:
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        return ["children must be a list of objects"]
    names = [row.get("change") for row in rows]
    if len(names) != len(CHILDREN) or set(names) != set(CHILDREN):
        return [f"frozen child registry changed: {names!r}"]
    return [detail for row in rows for detail in _child_row_findings(row)]


def _child_row_findings(row: dict[str, Any]) -> list[str]:
    name = row["change"]
    fields = {"change", "capabilitySpec", "exitClass", "startAfter", "integrationDependsOn", "enables"}
    if set(row) != fields or row["capabilitySpec"] != f"specs/{name}/spec.md":
        return [f"{name}: unknown child fields or changed capability owner"]
    actual = (row["exitClass"], row["startAfter"], row["integrationDependsOn"], row["enables"])
    expected = CHILDREN[name]
    labels = ("exitClass", "startAfter", "integrationDependsOn", "enables")
    return [f"{name}: frozen {field} changed: {value!r}"
            for field, value, baseline in zip(labels, actual, expected, strict=True)
            if value != (list(baseline) if isinstance(baseline, tuple) else baseline)]


def _plan_findings(directory: Path) -> list[str]:
    required = [directory / "children" / f"{name}.md" for name in CHILDREN]
    required.extend(directory / "specs" / name / "spec.md" for name in CHILDREN)
    return [f"local child plan or capability spec is missing: {path.relative_to(directory)}"
            for path in required if not path.is_file()]


__all__ = ["inspect_authority_freeze"]
