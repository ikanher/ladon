#!/usr/bin/env python3
"""Generate Ladon's supported-feature matrix from executable pytest gates."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from ladon.readiness import assess_readiness

FEATURES: tuple[dict[str, Any], ...] = (
    {
        "id": "architecture-review",
        "profile": "secondary",
        "summary": "Installed analysis, architecture policy, and bounded report output.",
        "tests": (
            "tests/test_installed_cli_contract.py::test_installed_analyzer_process_contract",
            "tests/test_architecture_policy.py::test_architecture_policy_flags_direct_peer_imports_from_globs",
        ),
    },
    {
        "id": "type-text-declaration-search",
        "profile": "primary",
        "summary": "Bounded lexical and type-text shortlists with no Lean applicability claim.",
        "tests": (
            "tests/test_proof_search_type.py::test_type_search_returns_lexical_shortlist_and_diagnostics",
            "tests/test_discovery_correctness_contract.py::test_type_text_result_has_explicit_lexical_schema_and_zero_diagnostic_cap",
            "tests/test_discovery_correctness_contract.py::test_exact_owner_disambiguates_candidate_and_retains_all_type_evidence",
            "tests/test_semantic_build_mode.py::test_installed_cli_rejects_removed_semantic_mode_without_invoking_lean",
        ),
    },
    {
        "id": "verified-proposition-discovery",
        "profile": "primary",
        "summary": "Bounded terminal Lean proposition checks in trusted repositories; partial prefixes are provisional; ordered typed caller locals are supported.",
        "tests": (
            "tests/test_semantic_candidate_lean_integration.py::test_installed_cli_emits_batch_closed_semantic_evidence",
            "tests/test_semantic_candidate_lean_integration.py::test_installed_cli_accepts_caller_local_context",
            "tests/test_semantic_candidate_lean_integration.py::test_real_lean_closing_profile_covers_terminal_outcomes_and_replay",
            "tests/test_verified_discovery.py::test_discovery_does_not_promote_or_replay_partial_batch_prefix",
        ),
    },
    {
        "id": "evidence-and-lineage-inspection",
        "profile": "audit",
        "summary": "Stored ProofIR dossiers and exact compiled theorem-lineage persistence.",
        "tests": (
            "tests/test_proofir_v3_installed_workflow_contract.py::test_installed_dossier_reports_coverage_and_limitations",
            "tests/test_theorem_lineage_store.py::test_ingestion_is_constrained_and_status_is_fresh",
        ),
    },
    {
        "id": "report-atlas",
        "profile": "extra",
        "summary": "Multi-report atlas and SQLite review projections.",
        "tests": (
            "tests/test_atlas_sqlite.py::test_write_atlas_sqlite_creates_query_tables",
        ),
    },
    {
        "id": "theorem-capsules",
        "profile": "extra",
        "summary": "Pinned module-prefix materialization and replay packaging.",
        "tests": (
            "tests/test_installed_theorem_cli_contract.py::test_installed_theorem_capsule_help_is_caller_neutral",
        ),
    },
    {
        "id": "runsets-and-reportsets",
        "profile": "extra",
        "summary": "Versioned batch execution and independent report publication.",
        "tests": (
            "tests/test_runset_cli.py::test_runset_cli_publishes_clean_independent_reports",
        ),
    },
)


RESOURCE_NODE = "tests/test_resource_watchdog.py::test_supported_rss_limit_cancels_an_active_process_group"
SEMANTIC_REQUIREMENTS = {
    "architecture-review": (FEATURES[0]["tests"][0], FEATURES[0]["tests"][1], RESOURCE_NODE),
    "type-text-declaration-search": (FEATURES[1]["tests"][0], FEATURES[1]["tests"][2], RESOURCE_NODE),
    "verified-proposition-discovery": (
        "tests/test_discovery_vertical_pipeline.py::test_installed_pipeline_finds_explains_compiles_and_rejects",
        "tests/test_discovery_local_context.py::test_invalid_local_context_is_rejected_before_toolchain_probe",
        "tests/test_semantic_candidate_batch_worker.py::test_batch_worker_preserves_validated_prefix_after_timeout",
    ),
    "evidence-and-lineage-inspection": (FEATURES[3]["tests"][0], FEATURES[3]["tests"][1], RESOURCE_NODE),
}


def feature_readiness(feature, registry):
    evidence = registry.get("features", {}).get(feature["id"], {}) if registry else {}
    if not evidence or feature["id"] not in SEMANTIC_REQUIREMENTS:
        return assess_readiness({})
    try:
        inventory = json.loads(Path(registry["inventoryPath"]).read_text())
        names = ("installedSmoke", "adversarialContract", "resourceGate")
        tests = dict(zip(names, ((node,) for node in SEMANTIC_REQUIREMENTS[feature["id"]]), strict=True))
        return assess_readiness(evidence, evidence_root=Path(registry["bundleRoot"]),
                                inventories=dict.fromkeys(names, inventory), test_requirements=tests)
    except (OSError, ValueError, TypeError, KeyError) as error:
        result = assess_readiness({})
        result["reasons"].append("selected evidence unavailable: " + str(error))
        return result


def feature_row(feature, registry):
    readiness = feature_readiness(feature, registry)
    records = readiness["evidence"]
    return {**feature, "tests": list(feature["tests"]), "readiness": readiness["level"],
            "candidateCommit": records.get("installedSmoke", {}).get("candidateCommit"),
            "sourceTreeIdentity": records.get("installedSmoke", {}).get("sourceTreeIdentity"),
            "environmentRef": records.get("installedSmoke", {}).get("environmentRef"),
            "evidenceTimestamp": records.get("installedSmoke", {}).get("timestamp"),
            "evidence": records, "readinessReasons": readiness["reasons"],
            "validationIssues": readiness["validationIssues"],
            "verificationCommand": "uv run --locked pytest -q " + " ".join(feature["tests"])}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def matrix_payload(registry=None) -> dict[str, Any]:
    return {
        "schemaVersion": 3,
        "artifactKind": "ladon_supported_feature_matrix",
        "source": "repository-owned semantic requirements and resolved candidate execution evidence",
        "readinessLadder": ["experimental", "contract-supported", "externally-evaluated", "release-qualified"],
        "scope": "Qualification applies to named candidates only. Missing or stale evidence demotes; implementation and help coverage cannot promote.",
        "features": [feature_row(feature, registry) for feature in FEATURES],
    }


def render_json(registry=None) -> str:
    return json.dumps(matrix_payload(registry), indent=2, sort_keys=True) + "\n"


def render_markdown(registry=None) -> str:
    lines = [
        "# Supported feature matrix",
        "",
        "This file is generated by `scripts/generate_supported_feature_matrix.py`.",
        "Missing execution evidence keeps a capability experimental. Use an explicit candidate evidence registry to generate a qualified matrix.",
        "",
        "| Workflow | Product role | Readiness | Qualified candidate | Contract | Executable gates |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    features = matrix_payload(registry)["features"]
    for feature in features:
        tests = "<br>".join(f"`{node}`" for node in feature["tests"])
        lines.append(
            f"| `{feature['id']}` | {feature['profile']} | {feature['readiness']} | {feature['candidateCommit'] or 'none'} | {feature['summary']} | {tests} |"
        )
    for feature in features:
        if feature['evidence']:
            lines.extend(('', '## Candidate evidence: ' + feature['id'], '',
                          '```json', json.dumps(feature['evidence'], indent=2, sort_keys=True), '```'))
    lines.extend(
        [
            "",
            "The matrix records maintained support ownership, not a theorem-proof claim.",
            "`--verify-tests` executes listed gates but does not itself issue an installed qualification receipt. Optional evidence registries do not control required portable CI.",
            "",
        ]
    )
    return "\n".join(lines)


def verify_tests(root: Path) -> None:
    nodes = [node for feature in FEATURES for node in feature["tests"]]
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *nodes],
        cwd=root,
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)


def write_or_check(path: Path, expected: str, *, check: bool) -> None:
    if check:
        actual = path.read_text(encoding="utf-8") if path.is_file() else ""
        if actual != expected:
            raise SystemExit(f"generated feature matrix is stale: {path}")
        return
    path.write_text(expected, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--verify-tests", action="store_true")
    parser.add_argument("--evidence-registry", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args(argv)
    registry = json.loads(args.evidence_registry.read_text()) if args.evidence_registry else None
    root = project_root()
    if args.verify_tests:
        verify_tests(root)
    write_or_check((args.json_output or root / "docs/SUPPORTED_FEATURE_MATRIX.json"), render_json(registry), check=args.check)
    write_or_check((args.markdown_output or root / "docs/SUPPORTED_FEATURE_MATRIX.md"), render_markdown(registry), check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
