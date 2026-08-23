from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from support.semantic_evidence import semantic_evidence

from ladon.semantic_evidence_registry import SemanticEvidenceRegistry
from ladon.semantic_result_delivery import (
    collect_semantic_artifacts,
    deliver_semantic_result,
)
from ladon.semantic_result_projection import SemanticProjectionError
from ladon.verified_discovery import _attach_scratch


def _canonical_result() -> dict[str, Any]:
    artifacts, _registry, receipt = semantic_evidence(
        "delivery", candidate="Main.proof"
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


def test_compact_delivery_registers_and_reresolves_every_reference(tmp_path: Path) -> None:
    canonical = _canonical_result()
    path = tmp_path / "semantic.sqlite"

    projected = deliver_semantic_result(
        canonical,
        projection="llm",
        repo_root=tmp_path,
        registry_path=path,
        max_registry_bytes=4 * 1024 * 1024,
    )

    assert "artifacts" not in projected
    check = projected["candidate"]["check"]
    registry = SemanticEvidenceRegistry(path, max_database_bytes=4 * 1024 * 1024)
    assert registry.resolve_environment(check["environmentRef"]["environmentRef"])
    assert registry.resolve_typed_ref(check["checkRunRef"])["reference"] == check[
        "checkRunRef"
    ]
    counts = registry.inspect()["counts"]
    assert counts == {"artifacts": 2, "environments": 1, "typedRefs": 4}

    repeated = deliver_semantic_result(
        canonical,
        projection="llm",
        repo_root=tmp_path,
        registry_path=path,
        max_registry_bytes=4 * 1024 * 1024,
    )
    assert repeated == projected
    assert registry.inspect()["counts"] == counts


def test_audit_delivery_is_exact_and_does_not_create_registry(tmp_path: Path) -> None:
    canonical = _canonical_result()
    path = tmp_path / "semantic.sqlite"

    result = deliver_semantic_result(
        canonical,
        projection="audit",
        repo_root=tmp_path,
        registry_path=path,
    )

    assert result == canonical
    assert result is not canonical
    assert not path.exists()


def test_compact_delivery_fails_closed_when_accepted_evidence_is_absent(
    tmp_path: Path,
) -> None:
    canonical = _canonical_result()
    canonical["artifacts"] = []

    path = tmp_path / "semantic.sqlite"
    with pytest.raises(SemanticProjectionError, match="unresolved"):
        deliver_semantic_result(
            canonical,
            projection="llm",
            repo_root=tmp_path,
            registry_path=path,
        )
    assert not path.exists()


def test_operational_result_without_evidence_needs_no_registry(tmp_path: Path) -> None:
    canonical = {
        "schema": "ladon-semantic-candidate-check-result-v1",
        "operation": "check-candidate",
        "status": "failed-checker",
        "substitutions": [],
        "residualPremises": [],
        "dischargedHypotheses": [],
        "diagnostic": {"code": "process-failed", "message": "Lean exited"},
        "failureStage": "checker-process",
        "artifacts": [],
    }
    path = tmp_path / "semantic.sqlite"

    projected = deliver_semantic_result(
        canonical,
        projection="llm",
        repo_root=tmp_path,
        registry_path=path,
    )

    assert projected["candidate"]["check"]["status"] == "failed-checker"
    assert projected["coverage"]["operationalFailure"] is True
    assert not path.exists()


def test_discovery_preserves_nonchecker_scratch_callback_failure(tmp_path: Path) -> None:
    canonical = _canonical_result()

    def raising_replayer(
        _candidate: str, _application: str, _parent: dict[str, Any]
    ) -> dict[str, Any]:
        raise RuntimeError("callback raised")

    canonical = _attach_scratch(
        canonical, "Main.proof", raising_replayer, [1]
    )

    projected = deliver_semantic_result(
        canonical,
        projection="llm",
        repo_root=tmp_path,
        registry_path=tmp_path / "semantic.sqlite",
    )

    scratch = projected["candidate"]["check"]["scratch"]
    assert scratch["status"] == "failed"
    assert scratch["diagnostic"]["code"] == "scratch-replay-failed"


def test_collection_includes_discovery_candidate_and_scratch_artifacts() -> None:
    direct = _canonical_result()
    discovery = {
        "candidates": [
            {
                "check": {
                    "artifacts": direct["artifacts"],
                    "scratch": {"artifacts": direct["artifacts"]},
                }
            }
        ]
    }

    assert collect_semantic_artifacts(discovery) == [
        *direct["artifacts"],
        *direct["artifacts"],
    ]
