from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from support.semantic_evidence import semantic_evidence
from support.semantic_execution import with_execution_context

from ladon.proofir_v3 import detached_content_id
from ladon.semantic_evidence_registry import SemanticEvidenceRegistry


@pytest.mark.parametrize("kind", ["semantic-artifact", "semantic-check"])
def test_console_reload_reports_stored_receipt_and_preserves_canonical_bytes(
    tmp_path: Path, kind: str,
) -> None:
    artifacts, _, receipt = semantic_evidence()
    artifacts, receipt = with_execution_context(artifacts)
    registry = SemanticEvidenceRegistry(tmp_path / "evidence.sqlite")
    registry.register_bundle(artifacts)
    payload = _expand(tmp_path, kind, artifacts[1]["artifactId"], receipt["checkRunRef"])
    assert payload.returncode == 0, payload.stderr
    result = json.loads(payload.stdout)
    assert result["artifact"] == artifacts[1]
    assert result["evidenceReceipt"]["observationState"] == "stored"
    for field in ("executionBinding", "authorityBasis", "operationOutcome", "sourceFreshness",
                  "environmentMatch", "analysisCompleteness", "subject", "environmentRef", "checkRunRef"):
        assert result["evidenceReceipt"][field] == receipt[field]
    assert registry.resolve_artifact(artifacts[1]["artifactId"]) == artifacts[1]


def test_console_reload_rejects_receipt_with_another_check_owner(tmp_path: Path) -> None:
    artifacts, _, receipt = semantic_evidence()
    artifacts = copy.deepcopy(artifacts)
    extension = artifacts[1]["extensions"]["ladon.process-observation/v1"]
    extension["evidenceReceipt"]["checkRunRef"] = "check:" + "e" * 64
    artifacts[1]["artifactId"] = detached_content_id(artifacts[1])
    SemanticEvidenceRegistry(tmp_path / "evidence.sqlite").register_bundle(artifacts)
    completed = _expand(tmp_path, "semantic-artifact", artifacts[1]["artifactId"], receipt["checkRunRef"])
    assert completed.returncode == 1
    assert completed.stdout == ""
    assert json.loads(completed.stderr)["diagnostic"]["code"] == "invalid-stored-evidence-receipt"


def _expand(tmp_path: Path, kind: str, artifact_ref: str, check_ref: str) -> subprocess.CompletedProcess[str]:
    console = os.environ.get("LADON_CONSOLE", str(Path(sys.executable).with_name("ladon")))
    command = [console, "proof-search", "evidence", kind, artifact_ref,
               "--repo-root", str(tmp_path), "--evidence-store", str(tmp_path / "evidence.sqlite"),
               "--format", "json"]
    if kind == "semantic-check":
        command.extend(["--local-id", check_ref])
    return subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=10, check=False)
