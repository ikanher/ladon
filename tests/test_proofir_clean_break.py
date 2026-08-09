from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon.proofir_catalog import discover_catalog_artifacts
from ladon.proofir_v3 import (
    LEGACY_ARTIFACT_KINDS,
    ProofIRV3Error,
    detached_content_id,
    validate_envelope,
)

ROOT = Path(__file__).parents[1]

RETIRED_PRODUCT_PATHS = (
    "src/ladon/proofir_bridge.py",
    "src/ladon/proofir_bridge_cli.py",
    "src/ladon/proofir_bridge_output.py",
    "src/ladon/proofir_input.py",
    "src/ladon/proofir_surface_store.py",
    "src/ladon/proofir_dag_store.py",
    "src/ladon/proofir_queries.py",
    "src/ladon/proofir_triage.py",
    "src/ladon/proofir_attachments.py",
    "src/ladon/proofir_coverage.py",
    "src/ladon/proof_surface_witness.py",
    "docs/PROOFIR_BRIDGE.md",
    "docs/PROOF_SURFACE_WITNESS.md",
    "tests/fixtures/proofir_bridge",
    "tests/fixtures/proofir_v2_conformance",
    "openspec/changes/proofir-v2-conformance-and-validation-freeze",
    "openspec/changes/proofir-v3-envelope-canonicalization-and-converter",
)

RETIRED_SCHEMA_TOKENS = (
    "proofir_surfaces",
    "proofir_claims",
    "proofir_surface_claims",
    "proofir_replay_runs",
    "proofir_replay_surfaces",
    "proofir_dags",
    "proofir_dag_nodes",
    "proofir_dag_edges",
    "proofir_dag_node_authority",
    "proofir_dag_witnesses",
    "proofir_dag_omissions",
    "proofir_claim_dag_links",
    "proofir_attachment_candidates",
    "proofir_attachments",
)


def legacy_envelope(kind: str) -> dict[str, object]:
    value: dict[str, object] = {
        "proofirVersion": "3.0",
        "artifactKind": kind,
        "artifactId": None,
        "producer": {
            "name": "retired-fixture",
            "version": "1",
            "implementation": "test",
            "buildDigest": "sha256:" + "b" * 64,
        },
        "environmentRef": "sha256:" + "e" * 64,
        "subjectRefs": [],
        "coverage": {
            "status": "unavailable",
            "population": {"kind": "legacy-input", "selector": {}},
            "universeKnown": False,
            "expected": 0,
            "discovered": 0,
            "decoded": 0,
            "valid": 0,
            "projected": 0,
            "queryMatched": 0,
            "omitted": [],
            "bounds": {},
        },
        "payload": {},
        "limitations": [],
        "extensions": {},
    }
    value["artifactId"] = detached_content_id(value)
    return value


@pytest.mark.parametrize("kind", sorted(LEGACY_ARTIFACT_KINDS))
def test_every_legacy_kind_has_one_stable_rejection(kind: str) -> None:
    value = legacy_envelope(kind)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(value)
    assert captured.value.diagnostic.to_dict() == {
        "artifactId": value["artifactId"],
        "stage": "kind-schema-valid",
        "code": "legacy-artifact-kind",
        "pointer": "/artifactKind",
        "message": f"legacy ProofIR artifact kind is unsupported: {kind}",
    }


def test_governance_witness_legacy_kinds_are_explicitly_rejected() -> None:
    assert {
        "proof_surface_witness",
        "ladon_proof_surface_witness",
    } <= LEGACY_ARTIFACT_KINDS


@pytest.mark.parametrize("kind", sorted(LEGACY_ARTIFACT_KINDS))
def test_catalog_uses_the_same_attributable_legacy_diagnostic(
    tmp_path: Path, kind: str
) -> None:
    artifact_path = tmp_path / "legacy.json"
    artifact_path.write_text(json.dumps(legacy_envelope(kind)), encoding="utf-8")
    config_dir = tmp_path / ".ladon"
    config_dir.mkdir()
    (config_dir / "proofir.json").write_text(
        json.dumps({"artifacts": ["legacy.json"]}), encoding="utf-8"
    )
    _, artifacts = discover_catalog_artifacts(tmp_path)
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.state == "unsupported"
    assert artifact.validation_stage == "kind-schema-valid"
    diagnostic = json.loads(artifact.diagnostic or "null")
    assert diagnostic["artifactId"] == legacy_envelope(kind)["artifactId"]
    assert diagnostic["stage"] == "kind-schema-valid"
    assert diagnostic["code"] == "legacy-artifact-kind"
    assert diagnostic["pointer"] == "/artifactKind"


def test_retired_legacy_product_paths_are_absent() -> None:
    assert not [path for path in RETIRED_PRODUCT_PATHS if (ROOT / path).exists()]


def test_distribution_and_release_have_only_the_native_cli() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    release_gate = (ROOT / "scripts/release_gate_distribution.py").read_text(
        encoding="utf-8"
    )
    cli_help = (ROOT / "src/ladon/cli.py").read_text(encoding="utf-8")
    assert "ladon-proofir-bridge" not in pyproject
    assert "LADON_PROOFIR_BRIDGE_CONSOLE" not in release_gate
    assert "Validate, canonicalize, or inspect ProofIR artifacts." in cli_help
    assert "inspect, or convert ProofIR" not in cli_help


def test_proof_search_schema_and_writer_contain_no_legacy_semantic_projection() -> None:
    schema = (ROOT / "src/ladon/proof_search_schema.py").read_text(encoding="utf-8")
    writer = (ROOT / "src/ladon/proof_search_index.py").read_text(encoding="utf-8")
    for token in RETIRED_SCHEMA_TOKENS:
        assert token not in schema
        assert token not in writer
    assert "proofir_surface_store" not in writer
    assert "proofir_dag_store" not in writer
    assert "proofir_attachments" not in writer
    assert "retired_" not in schema
    assert "retired_" not in writer


def test_retired_bridge_report_artifact_kinds_are_not_registered() -> None:
    versions = (ROOT / "src/ladon/artifact_versions.py").read_text(encoding="utf-8")
    assert "ladon_proofir_bridge_report" not in versions
    assert "ladon_proofir_bridge_snapshot" not in versions


def test_no_retired_bridge_adapter_survives_in_product_or_current_docs() -> None:
    scanned_paths = [
        *sorted((ROOT / "src/ladon").glob("*.py")),
        ROOT / "README.md",
        ROOT / "docs/ARCHITECTURE.md",
        ROOT / "docs/CLI.md",
        ROOT / "docs/REPORT_CONTRACT_V2.md",
        ROOT / "docs/LEAN_REVIEW_INTELLIGENCE.md",
        ROOT / "scripts/ladon_atlas_export.py",
        ROOT / "scripts/ladon_atlas_workflow.py",
    ]
    allowed = {
        ROOT / "src/ladon/proofir_v3.py",
        ROOT / "src/ladon/proofir_catalog.py",
    }
    forbidden = (
        "proofir_bridge",
        "ladon-proofir-bridge",
        "ladon_proofir_bridge",
        "--bridge-report",
        "bridge_reports",
        "proof_surface_witness",
        "retired_",
    )
    findings = []
    for path in scanned_paths:
        if path in allowed or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        findings.extend(
            f"{path.relative_to(ROOT)}:{token}" for token in forbidden if token in text
        )
    assert findings == []


def test_native_evidence_cli_has_no_dag_compatibility_arguments() -> None:
    cli = (ROOT / "src/ladon/proof_search_cli.py").read_text(encoding="utf-8")
    assert (
        'choices=("theorem", "artifact", "route", "slice", "alternatives", "triage")'
        in cli
    )
    assert '"dag"' not in cli
    assert '"--dag"' not in cli
    assert '"--reverse"' not in cli
