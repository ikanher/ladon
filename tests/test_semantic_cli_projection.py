from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from support.proofir_v3_native import environment_artifact
from support.semantic_evidence import semantic_evidence

from ladon import proof_search_cli
from ladon.proof_search_cli import _render_text, build_proof_search_parser, proof_search_main
from ladon.proof_search_terminal import semantic_payload_failed
from ladon.semantic_evidence_registry import SemanticEvidenceRegistry


def _canonical_check() -> dict[str, Any]:
    artifacts, _registry, receipt = semantic_evidence(
        "cli", candidate="Main.proof"
    )
    environment, check = artifacts
    check_run_id = check["payload"]["checkRunId"]
    return {
        "schema": "ladon-semantic-candidate-check-result-v1",
        "operation": "check-candidate",
        "status": "accepted",
        "applicationTerm": "Main.proof",
        "substitutions": [],
        "residualPremises": [],
        "dischargedHypotheses": [],
        "environmentRef": environment["environmentRef"],
        "checkRunId": check_run_id,
        "checkRunRef": {
            "artifactRef": check["artifactId"],
            "kind": "check-run",
            "localId": check_run_id,
        },
        "evidenceReceipt": receipt,
        "artifacts": [environment, check],
        "diagnostic": None,
        "resourceAccounting": {},
        "limitations": [],
    }


def _candidate_arguments(tmp_path: Path, evidence_store: Path) -> list[str]:
    return [
        "check",
        "candidate",
        "--repo-root",
        str(tmp_path),
        "--module",
        "Main",
        "--goal",
        "True",
        "--candidate",
        "Main.proof",
        "--evidence-store",
        str(evidence_store),
        "--format",
        "json",
    ]


def test_semantic_cli_defaults_to_compact_registered_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "semantic.sqlite"
    monkeypatch.setattr(
        proof_search_cli,
        "_dispatch_check",
        lambda _args, _repo_root: _canonical_check(),
    )
    args = build_proof_search_parser().parse_args(_candidate_arguments(tmp_path, path))

    payload = proof_search_cli._dispatch(args)

    assert args.projection == "llm"
    assert payload["schema"] == "ladon-semantic-candidate-projection-v1"
    assert "artifacts" not in payload
    reference = payload["candidate"]["check"]["checkRunRef"]
    registry = SemanticEvidenceRegistry(path)
    assert registry.resolve_typed_ref(reference)["reference"] == reference


def test_semantic_audit_projection_preserves_full_payload_without_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "semantic.sqlite"
    canonical = _canonical_check()
    monkeypatch.setattr(
        proof_search_cli,
        "_dispatch_check",
        lambda _args, _repo_root: canonical,
    )
    arguments = [*_candidate_arguments(tmp_path, path), "--projection", "audit"]

    payload = proof_search_cli._dispatch(build_proof_search_parser().parse_args(arguments))

    assert payload == canonical
    assert not path.exists()


def test_semantic_environment_expansion_uses_registry_not_lexical_index(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "semantic.sqlite"
    environment = environment_artifact()
    SemanticEvidenceRegistry(path).register_bundle([environment])

    status = proof_search_main(
        [
            "evidence",
            "semantic-environment",
            environment["environmentRef"],
            "--repo-root",
            str(tmp_path / "no-index"),
            "--evidence-store",
            str(path),
            "--format",
            "json",
        ]
    )

    assert status == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["artifact"] == environment
    assert payload["reference"] == {"environmentRef": environment["environmentRef"]}
    assert payload["registry"]["counts"]["environments"] == 1


def test_missing_semantic_registry_query_is_read_only(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "missing.sqlite"

    status = proof_search_main(
        [
            "evidence",
            "semantic-artifact",
            "sha256:" + "a" * 64,
            "--repo-root",
            str(tmp_path),
            "--evidence-store",
            str(path),
            "--format",
            "json",
        ]
    )

    assert status == 2
    assert not path.exists()
    assert json.loads(capsys.readouterr().err)["exitClass"] == "invocation"


def test_projection_failure_bit_survives_candidate_omission_and_text_rendering() -> None:
    payload = {
        "schema": "ladon-verified-discovery-projection-v1",
        "operation": "discover",
        "status": "partial",
        "candidates": [
            {
                "name": "Main.good",
                "check": {"status": "accepted", "applicationTerm": "Main.good"},
            }
        ],
        "coverage": {
            "operationalFailure": True,
            "candidatePopulation": {"observed": 2, "projected": 1, "omitted": 1},
        },
    }

    assert semantic_payload_failed("discover", payload) is True
    rendered = _render_text(payload)
    assert "Main.good [accepted] application=Main.good" in rendered
    assert "candidates: 1" in rendered
