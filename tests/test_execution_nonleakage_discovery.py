"""Discarded caller inputs stay absent across mocked worker/process boundaries.

These fixtures exercise production evidence construction, delivery and stored
readers. Framed outcomes and scratch process exits are synthetic observations,
not new Lean verification or an isolation guarantee.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest
from support.execution_nonleakage import (
    assert_clean_files,
    assert_no_discarded_input,
    poison_environment,
)

from ladon import verified_discovery
from ladon.lean_toolchain import LeanToolchainContext, resolve_toolchain_context
from ladon.process_supervisor import ProcessResult
from ladon.proof_search_cli import _write_payload, proof_search_main
from ladon.proofir_v3 import canonical_bytes
from ladon.scratch_replay import replay_scratch
from ladon.semantic_candidate_batch_worker import check_semantic_candidates
from ladon.semantic_candidate_worker import (
    SEMANTIC_BATCH_PROTOCOL,
    UNIVERSE_POLICY,
    SemanticCandidateRequest,
)
from ladon.semantic_evidence_registry import SemanticEvidenceRegistry
from ladon.semantic_result_delivery import collect_semantic_artifacts, deliver_semantic_result
from ladon.verified_discovery import (
    DiscoveryRequest,
    discover_candidates,
    semantic_scratch_replayer,
)


def _toolchain(root: Path, environment: Mapping[str, str]) -> LeanToolchainContext:
    root.mkdir()
    (root / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n")
    (root / "Main.lean").write_text("theorem good : True := True.intro\n")
    compiled = root / ".lake" / "build" / "lib" / "lean" / "Main.olean"
    compiled.parent.mkdir(parents=True)
    compiled.write_bytes(b"mocked compiled module identity")
    for name in ("lake", "lean"):
        tool = root / name
        tool.write_text("#!/bin/sh\nprintf 'Lean version 4.20.0 commit abcdef1\\n'\n")
        tool.chmod(0o755)
    return resolve_toolchain_context(
        root, lake_path=root / "lake", lean_path=root / "lean",
        environment={**environment, "PATH": str(root)},
    )


def _candidate_rows() -> list[dict[str, Any]]:
    rows = []
    for name, status in (
        ("Main.good", "accepted"),
        ("Main.bad", "rejected"),
        ("Main.residual", "applicable-with-residuals"),
    ):
        rejected = status == "rejected"
        rows.append({
            "candidate": name,
            "status": status,
            "candidateSubject": None if rejected else {
                "name": name, "typeDisplay": "True", "typeStructural": "True",
            },
            "applicationTerm": "" if rejected else name,
            "dischargedHypotheses": [],
            "substitutions": [],
            "residualPremises": (
                [{"typeDisplay": "False", "typeStructural": "False"}]
                if status == "applicable-with-residuals" else []
            ),
            "failureStage": "candidate-not-found" if rejected else "",
            "diagnostic": "unknown declaration" if rejected else "",
        })
    return rows


def _batch_frames(command: tuple[str, ...], context: LeanToolchainContext) -> str:
    module, _probe_path, _goal, goal_digest, probe, request_id, context_ref = command[4:11]
    rows = _candidate_rows()
    assert list(command[11:]) == [row["candidate"] for row in rows]
    common = {"protocol": SEMANTIC_BATCH_PROTOCOL, "frameVersion": 1, "requestId": request_id}
    frames = [{
        **common,
        "frameKind": "header", "sequence": 0, "terminal": False,
        "goalRequestDigest": goal_digest, "executionContextRef": context_ref,
        "universePolicy": UNIVERSE_POLICY,
        "leanVersion": context.lean_release, "leanCommit": context.lean_commit,
        "executablePath": str(context.lean_path), "module": module,
        "probe": {"name": probe, "typeDisplay": "True", "typeStructural": "True"},
        "importedModules": [{
            "module": module, "oleanPath": str(context.library_roots[0] / "Main.olean"),
        }],
        "localContext": [],
    }]
    frames.extend({
        **common, "frameKind": "candidate", "sequence": number, "terminal": False, "row": row,
    } for number, row in enumerate(rows, start=1))
    frames.append({
        **common, "frameKind": "summary", "sequence": len(rows) + 1, "terminal": True,
        "completed": len(rows), "total": len(rows),
    })
    return "\n".join("LADON_FRAME " + json.dumps(frame) for frame in frames)


def _scratch_process(command: tuple[str, ...], status: str) -> ProcessResult:
    return ProcessResult(
        command, 0 if status == "compiled" else 1,
        "compiled" if status == "compiled" else "",
        "" if status == "compiled" else "synthetic bounded scratch failure",
        0.01, timed_out=status == "timeout", output_limited=status == "output-limited",
        memory_limited=status == "memory-limited",
    )


def _discovery(
    context: LeanToolchainContext, monkeypatch: pytest.MonkeyPatch, scratch_status: str,
) -> dict[str, Any]:
    launches: list[str] = []

    def batch_runner(command: tuple[str, ...], **kwargs: Any) -> ProcessResult:
        launches.append("batch")
        assert kwargs["env"] == context.environment
        assert_no_discarded_input(kwargs["env"])
        return ProcessResult(command, 0, _batch_frames(command, context), "", 0.01)

    def scratch_runner(command: tuple[str, ...], **kwargs: Any) -> ProcessResult:
        launches.append("scratch")
        assert kwargs["env"] == context.environment
        assert command[0] == str(context.lean_path)
        assert_no_discarded_input(kwargs["env"])
        assert_no_discarded_input(Path(command[-1]).read_bytes())
        return _scratch_process(command, scratch_status)

    def scratch(**kwargs: Any) -> Any:
        return replay_scratch(**kwargs, runner=scratch_runner)

    monkeypatch.setattr(verified_discovery, "replay_scratch", scratch)
    semantic = SemanticCandidateRequest(
        context.repo_root, "Main", "True", "Main.good", toolchain=context,
    )

    def batch(names: Sequence[str]) -> Mapping[str, Mapping[str, Any]]:
        checked = check_semantic_candidates(semantic, names, runner=batch_runner)
        if checked.status != "available":
            pytest.fail(str(checked.diagnostic))
        assert_no_discarded_input(checked.to_dict())
        return {str(row["candidate"]): row for row in checked.rows}

    def unexpected_single(_name: str) -> Any:
        pytest.fail("discovery must retain the batch boundary")

    request = DiscoveryRequest(
        context.repo_root, "Main", "True", max_candidates=3,
        execution_context_ref=context.context_identity,
    )
    payload = discover_candidates(
        request, [{"candidateName": row["candidate"]} for row in _candidate_rows()],
        unexpected_single, semantic_scratch_replayer(request, context), batch,
    )
    assert launches == ["batch", "scratch"], payload["candidates"]
    _assert_discovery_population(payload, scratch_status)
    return payload


def _assert_discovery_population(payload: Mapping[str, Any], scratch_status: str) -> None:
    expected_counts = {
        "completed": 3, "accepted": 2, "rejected": 1,
        "scratchCompiled": int(scratch_status == "compiled"),
    }
    assert {key: payload["coverage"][key] for key in expected_counts} == expected_counts
    checks = {row["name"]: row["check"] for row in payload["candidates"]}
    assert {name: check["status"] for name, check in checks.items()} == {
        "Main.good": "accepted", "Main.bad": "rejected",
        "Main.residual": "applicable-with-residuals",
    }
    scratch = checks["Main.good"]["scratch"]
    assert scratch["status"] == scratch_status
    assert scratch["evidenceReceipt"]["authorityBasis"] == "process-observation"
    assert "scratch" not in checks["Main.residual"]


def _stored_expansions(
    artifacts: Sequence[Mapping[str, Any]], output: Path, context: LeanToolchainContext,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry = SemanticEvidenceRegistry(output / "evidence.sqlite")
    checks = {str(row["artifactId"]): row for row in artifacts
              if row["artifactKind"] == "proofir.check-run"}
    assert len(checks) == 4
    for artifact_ref, artifact in checks.items():
        assert registry.resolve_artifact(artifact_ref) == artifact
        for output_format in ("json", "text"):
            _expand_and_check(artifact, output, context.repo_root, output_format, capsys)


def _expand_and_check(
    artifact: Mapping[str, Any], output: Path, root: Path, output_format: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact_ref = str(artifact["artifactId"])
    status = proof_search_main([
        "evidence", "semantic-check", artifact_ref,
        "--local-id", artifact["payload"]["checkRunId"],
        "--repo-root", str(root), "--evidence-store", str(output / "evidence.sqlite"),
        "--format", output_format,
    ])
    captured = capsys.readouterr()
    assert status == 0, captured.err
    assert_no_discarded_input(captured.out + captured.err)
    if output_format == "json":
        stored = json.loads(captured.out)
        assert stored["artifact"] == artifact
        assert stored["evidenceReceipt"]["observationState"] == "stored"
        assert stored["evidenceReceipt"]["executionBinding"] == "explicit-pinned"
        recorded = artifact["extensions"]["ladon.process-observation/v1"]["evidenceReceipt"]
        for field in ("operationOutcome", "authorityBasis", "analysisCompleteness"):
            assert stored["evidenceReceipt"][field] == recorded[field]
    (output / f"stored-{artifact_ref[7:]}.{output_format}").write_text(captured.out)


@pytest.mark.parametrize(
    "scratch_status", ["compiled", "process-failed", "timeout", "output-limited", "memory-limited"]
)
def test_discovery_scratch_projections_and_stored_evidence_discard_caller_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    scratch_status: str,
) -> None:
    context = _toolchain(tmp_path / "repo", poison_environment(monkeypatch))
    assert "LEAN_PATH" in context.environment
    assert_no_discarded_input(context.to_dict())
    payload = _discovery(context, monkeypatch, scratch_status)
    assert_no_discarded_input(payload)
    artifacts = collect_semantic_artifacts(payload)
    for artifact in artifacts:
        assert_no_discarded_input(canonical_bytes(artifact))
    output = tmp_path / "observations"
    output.mkdir()
    for projection in ("audit", "llm", "review"):
        projected = deliver_semantic_result(
            payload, projection=projection, repo_root=context.repo_root,
            registry_path=output / "evidence.sqlite",
        )
        assert_no_discarded_input(projected)
        for output_format in ("json", "text"):
            _write_payload(
                projected, output=str(output / f"{projection}.{output_format}"),
                output_format=output_format,
            )
    _stored_expansions(artifacts, output, context, capsys)
    assert_clean_files(output)
