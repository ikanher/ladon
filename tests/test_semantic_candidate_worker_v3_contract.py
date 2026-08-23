from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ladon.lean_toolchain import resolve_toolchain_context
from ladon.process_supervisor import ProcessResult
from ladon.proofir_v3 import validate_envelope_batch
from ladon.semantic_candidate_worker import (
    MAX_IMPORTED_MODULES,
    SEMANTIC_PROTOCOL,
    SemanticCandidateCheck,
    SemanticCandidateRequest,
    _environment_artifact,
    check_semantic_candidate,
)


def test_resource_accounting_names_checker_process_scope() -> None:
    accounting = SemanticCandidateCheck(
        "failed-checker",
        elapsed_seconds=1.25,
        peak_rss_bytes=4096,
    ).to_dict()["resourceAccounting"]

    assert accounting == {
        "scope": "checker-process",
        "checkerElapsedSeconds": 1.25,
        "elapsedSeconds": 1.25,
        "peakRssBytes": 4096,
    }


def test_environment_module_limit_diagnostic_reports_observed_and_allowed(
    tmp_path: Path,
) -> None:
    payload = {"importedModules": [{}] * (MAX_IMPORTED_MODULES + 1)}

    with pytest.raises(
        ValueError,
        match=r"10,001 imported modules; evidence limit is 10,000",
    ):
        _environment_artifact(tmp_path, payload)


def _accepted_payload(tmp_path: Path) -> dict[str, Any]:
    olean = tmp_path / "Main.olean"
    olean.write_bytes(b"exact compiled module")
    executable = tmp_path / "lean"
    executable.write_bytes(b"exact lean executable")
    return {
        "protocol": SEMANTIC_PROTOCOL,
        "frameVersion": 1,
        "sequence": 0,
        "terminal": True,
        "universePolicy": "lean-level-mvar-succ-zero/v1",
        "requestId": "fixture-request",
        "goalRequestDigest": "fixture-goal",
        "executionContextRef": "fixture-context",
        "leanVersion": "4.32.2",
        "leanCommit": "commit",
        "executablePath": str(executable),
        "module": "Main",
        "probe": {
            "name": "filled-from-supervisor-command",
            "typeDisplay": "Nat → Nat",
            "typeStructural": "forallE Nat Nat",
        },
        "candidate": {
            "name": "Main.identity",
            "typeDisplay": "Nat → Nat",
            "typeStructural": "forallE Nat Nat",
        },
        "applicationTerm": "Main.identity",
        "dischargedHypotheses": [],
        "importedModules": [{"module": "Main", "oleanPath": str(olean)}],
        "substitutions": [],
        "residualPremises": [],
        "localContext": [],
    }


def _assert_artifact_family(artifacts: tuple[dict[str, Any], ...]) -> None:
    assert [row["artifactKind"] for row in artifacts] == [
        "proofir.environment",
        "proofir.check-run",
        "proofir.derivation",
    ]
    validate_envelope_batch(list(artifacts))


def _assert_exact_links(artifacts: tuple[dict[str, Any], ...]) -> None:
    environment, check, derivation = artifacts
    assert check["environmentRef"] == environment["environmentRef"]
    receipt = check["extensions"]["ladon.process-observation/v1"]["evidenceReceipt"]
    assert receipt["environmentRef"] == environment["environmentRef"]
    assert receipt["checkRunRef"] == check["payload"]["checkRunId"]
    assert receipt["authorityBasis"] == "elaborator-check"
    assert check["payload"]["inputs"]["artifactRefs"] == [environment["artifactId"]]
    step = derivation["payload"]["steps"][0]
    assert step["checkRunRef"]["artifactRef"] == check["artifactId"]
    assert step["checkRunRef"]["localId"] == check["payload"]["checkRunId"]
    _assert_owned_check_run(check)


def _assert_owned_check_run(check: dict[str, Any]) -> None:
    check_run_id = check["payload"]["checkRunId"]
    assert [
        {"kind": row["kind"], "localId": row["localId"]}
        for row in check["subjectRefs"]
        if row["kind"] == "check-run"
    ] == [{"kind": "check-run", "localId": check_run_id}]
    assert {"kind": "check-run", "localId": check_run_id} not in check["payload"]["inputs"][
        "subjectRefs"
    ]


def _assert_exact_semantics(artifacts: tuple[dict[str, Any], ...]) -> None:
    check, derivation = artifacts[1:]
    step = derivation["payload"]["steps"][0]
    assert step["substitutions"] == []
    assert step["premiseRefs"] == []
    assert step["localContextRef"]["kind"] == "local-context"
    assert check["payload"]["results"][0]["result"] == "accepted"


def _assert_process_bounds(artifacts: tuple[dict[str, Any], ...]) -> None:
    check = artifacts[1]
    assert check["payload"]["outputs"]["stdoutDigest"].startswith("sha256:")
    assert check["extensions"]["ladon.process-observation/v1"]["bounds"] == {
        "timeoutMs": 120000,
        "maxOutputBytes": 8 * 1024 * 1024,
        "maxRssBytes": 4 * 1024 * 1024 * 1024,
    }
    assert (
        check["extensions"]["ladon.process-observation/v1"]["evidenceReceipt"]["schema"]
        == "ladon-evidence-receipt-v1"
    )


def test_accepted_worker_result_closes_exact_environment_and_check_references(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    repo.joinpath("lean-toolchain").write_text("leanprover/lean4:v4.32.2\n")
    compiled_module = repo / ".lake" / "build" / "lib" / "lean" / "Main.olean"
    compiled_module.parent.mkdir(parents=True)
    compiled_module.write_bytes(b"compiled fixture")
    payload = _accepted_payload(tmp_path)

    def accepted_runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        payload["probe"]["name"] = command[-4]
        payload["requestId"] = command[-2]
        payload["goalRequestDigest"] = command[-5]
        payload["executionContextRef"] = command[-1]
        return ProcessResult(
            tuple(command), 0, "LADON_FRAME " + json.dumps(payload), "", 0.25, peak_rss_bytes=4096
        )

    result = check_semantic_candidate(
        SemanticCandidateRequest(repo, "Main", "Nat → Nat", "Main.identity"),
        runner=accepted_runner,
    )

    assert result.status == "accepted"
    assert result.to_dict()["authoritySelection"] == "ambient-selected-application-check"
    assert result.to_dict()["analysisCompleteness"] == "complete"
    assert result.to_dict()["evidenceReceipt"]["schema"] == "ladon-evidence-receipt-v1"
    assert any(
        "trusted target code" in limitation
        for limitation in result.to_dict()["evidenceReceipt"]["limitations"]
    )
    assert result.to_dict()["evidenceReceipt"]["executionBinding"] == "ambient-observed"
    assert result.to_dict()["environmentRef"] == result.artifacts[0]["environmentRef"]
    assert result.to_dict()["checkRunId"] == result.artifacts[1]["payload"]["checkRunId"]
    assert result.to_dict()["checkRunRef"] == {
        "artifactRef": result.artifacts[1]["artifactId"],
        "kind": "check-run",
        "localId": result.artifacts[1]["payload"]["checkRunId"],
    }
    assert result.to_dict()["substitutions"] == []
    assert result.to_dict()["residualPremises"] == []
    assert result.to_dict()["failureStage"] is None
    _assert_artifact_family(result.artifacts)
    _assert_exact_links(result.artifacts)
    _assert_exact_semantics(result.artifacts)
    _assert_process_bounds(result.artifacts)

    stale_check = json.loads(json.dumps(result.artifacts[1]))
    stale_check["subjectRefs"][-1]["display"] = "mutated after identity"
    fallback = SemanticCandidateCheck(
        "accepted",
        artifacts=(stale_check,),
        environment_ref=result.artifacts[0]["environmentRef"],
        check_run_id=result.artifacts[1]["payload"]["checkRunId"],
    ).to_dict()
    assert fallback["checkRunRef"] is None
    assert fallback["checkRunId"] == result.artifacts[1]["payload"]["checkRunId"]


def test_rejected_worker_result_owns_and_qualifies_its_check_run(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    repo.joinpath("lean-toolchain").write_text("leanprover/lean4:v4.32.2\n")
    payload = _accepted_payload(tmp_path)
    rejected = {
        key: payload[key]
        for key in (
            "protocol",
            "frameVersion",
            "sequence",
            "terminal",
            "universePolicy",
            "requestId",
            "goalRequestDigest",
            "executionContextRef",
            "leanVersion",
            "leanCommit",
            "executablePath",
            "module",
            "probe",
            "importedModules",
            "localContext",
        )
    }
    rejected.update(
        {
            "candidateName": "Main.missing",
            "status": "rejected",
            "failureStage": "candidate-not-found",
            "diagnostic": "unknown declaration",
        }
    )

    def rejected_runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        rejected["probe"]["name"] = command[-4]
        rejected["requestId"] = command[-2]
        rejected["goalRequestDigest"] = command[-5]
        rejected["executionContextRef"] = command[-1]
        return ProcessResult(
            command,
            0,
            "LADON_FRAME " + json.dumps(rejected),
            "",
            0.1,
        )

    result = check_semantic_candidate(
        SemanticCandidateRequest(repo, "Main", "Nat", "Main.missing"),
        runner=rejected_runner,
    )

    assert result.status == "rejected"
    assert result.to_dict()["failureStage"] == "candidate-not-found"
    assert result.to_dict()["checkRunRef"] == {
        "artifactRef": result.artifacts[1]["artifactId"],
        "kind": "check-run",
        "localId": result.artifacts[1]["payload"]["checkRunId"],
    }
    _assert_owned_check_run(result.artifacts[1])
    validate_envelope_batch(list(result.artifacts))


def test_result_exposes_raw_check_id_when_no_owner_artifact_is_available() -> None:
    check_run_id = "check:" + "a" * 64
    result = SemanticCandidateCheck(
        "unassessed",
        substitutions=({"variable": "x", "termDisplay": "value"},),
        residual_premises=({"typeDisplay": "P"},),
        failure_stage="integration-only",
        environment_ref="sha256:" + "b" * 64,
        check_run_id=check_run_id,
    ).to_dict()

    assert result["checkRunRef"] is None
    assert result["checkRunId"] == check_run_id
    assert result["substitutions"] == [{"variable": "x", "termDisplay": "value"}]
    assert result["residualPremises"] == [{"typeDisplay": "P"}]
    assert result["failureStage"] == "integration-only"


def test_timeout_never_publishes_accepted_artifacts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    def timeout_runner(*_args: object, **_kwargs: object) -> ProcessResult:
        return ProcessResult(("lake", "env", "lean"), -9, "", "deadline", 1.0, timed_out=True)

    result = check_semantic_candidate(
        SemanticCandidateRequest(repo, "Main", "Nat", "Main.value"),
        runner=timeout_runner,
    )

    assert result.status == "timeout"
    assert result.artifacts == ()
    assert result.diagnostic == {"code": "checker-timeout", "message": "deadline"}
    assert result.to_dict()["evidenceReceipt"]["operationOutcome"] == "failed"


def test_unframed_rejection_prose_remains_process_failure(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    def prose_runner(*_args: object, **_kwargs: object) -> ProcessResult:
        return ProcessResult(
            ("lake", "env", "lean"),
            1,
            "",
            "candidate did not unify with the elaborated goal",
            0.1,
        )

    result = check_semantic_candidate(
        SemanticCandidateRequest(repo, "Main", "Nat", "Main.value"),
        runner=prose_runner,
    )

    assert result.status == "failed-checker"
    assert result.artifacts == ()
    assert result.evidence_receipt is not None
    assert result.evidence_receipt["checkRunRef"] is None
    assert result.evidence_receipt["operationOutcome"] == "failed"


def test_worker_process_failure_retains_both_frontend_diagnostic_streams(
    tmp_path: Path,
) -> None:
    result = check_semantic_candidate(
        SemanticCandidateRequest(tmp_path, "Main", "True", "Main.proof"),
        runner=lambda command, **_kwargs: ProcessResult(
            command,
            1,
            "Main.lean:1:0: error: unknown module 'Dependency'",
            "ELABORATION_FAILURE Main.lean",
            0.1,
        ),
    )

    assert result.status == "failed-checker"
    assert result.diagnostic is not None
    message = str(result.diagnostic["message"])
    assert "unknown module 'Dependency'" in message
    assert "ELABORATION_FAILURE Main.lean" in message


@pytest.mark.parametrize(
    "kwargs",
    [
        {"timeout_seconds": True},
        {"timeout_seconds": 601},
        {"max_output_bytes": 1.5},
        {"max_output_bytes": 65 * 1024 * 1024},
        {"max_rss_bytes": 1.5},
        {"max_rss_bytes": 65 * 1024 * 1024 * 1024},
    ],
)
def test_direct_request_uses_shared_typed_resource_caps(
    tmp_path: Path, kwargs: dict[str, object]
) -> None:
    with pytest.raises((TypeError, ValueError), match="semantic check"):
        SemanticCandidateRequest(
            tmp_path,
            "Main",
            "Nat",
            "Main.value",
            **kwargs,  # type: ignore[arg-type]
        )


def test_direct_request_rejects_oversized_candidate_before_process_launch(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="candidate.*transport byte cap"):
        SemanticCandidateRequest(tmp_path, "Main", "Nat", "Main." + ("x" * 100_000))


def test_explicit_toolchain_ignores_path_shadow_and_sanitizes_worker_environment(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    repo.joinpath("lean-toolchain").write_text("leanprover/lean4:v4.32.2\n")
    compiled_module = repo / ".lake" / "build" / "lib" / "lean" / "Main.olean"
    compiled_module.parent.mkdir(parents=True)
    compiled_module.write_bytes(b"compiled fixture")
    lake = repo / "lake"
    lean = repo / "lean"
    for tool in (lake, lean):
        tool.write_text("#!/bin/sh\nprintf 'Lean version 4.32.2\\n'\n")
        tool.chmod(0o755)
    context = resolve_toolchain_context(
        repo,
        lake_path=lake,
        lean_path=lean,
        environment={"PATH": str(tmp_path / "shadow"), "SECRET": "redacted"},
    )
    payload = _accepted_payload(tmp_path)
    payload["executablePath"] = str(lean)
    observed: dict[str, object] = {}

    def runner(command: tuple[str, ...], **kwargs: object) -> ProcessResult:
        observed["command"] = command
        observed["env"] = kwargs.get("env")
        payload["probe"]["name"] = command[-4]
        payload["requestId"] = command[-2]
        payload["goalRequestDigest"] = command[-5]
        payload["executionContextRef"] = command[-1]
        return ProcessResult(tuple(command), 0, "LADON_FRAME " + json.dumps(payload), "", 0.1)

    result = check_semantic_candidate(
        SemanticCandidateRequest(repo, "Main", "Nat → Nat", "Main.identity", toolchain=context),
        runner=runner,
    )
    assert result.status == "accepted"
    assert observed["command"][0] == str(lean)  # type: ignore[index]
    assert "lake" not in observed["command"]  # type: ignore[operator]
    assert "SECRET" not in observed["env"]  # type: ignore[operator]
    assert context.context_identity.startswith("sha256:")


def test_worker_rejects_executable_changed_during_run(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    repo.joinpath("lean-toolchain").write_text("leanprover/lean4:v4.32.2\n")
    compiled_module = repo / ".lake" / "build" / "lib" / "lean" / "Main.olean"
    compiled_module.parent.mkdir(parents=True)
    compiled_module.write_bytes(b"compiled fixture")
    lake = repo / "lake"
    lean = repo / "lean"
    for tool in (lake, lean):
        tool.write_text("#!/bin/sh\nprintf 'Lean version 4.32.2\\n'\n")
        tool.chmod(0o755)
    context = resolve_toolchain_context(repo, lake_path=lake, lean_path=lean)

    def mutating_runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        lean.write_text("#!/bin/sh\nprintf 'Lean version 4.32.2 changed\\n'\n")
        return ProcessResult(command, 0, "", "", 0.1)

    result = check_semantic_candidate(
        SemanticCandidateRequest(repo, "Main", "Nat → Nat", "Main.identity", toolchain=context),
        runner=mutating_runner,
    )

    assert result.status == "invalid-worker-output"
    assert result.diagnostic["code"] == "toolchain-identity-changed"


def test_worker_protocol_rejects_foreign_or_unscoped_semantic_rows(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    payload = _accepted_payload(tmp_path)
    payload["candidate"]["name"] = "Other.foreign"

    def foreign_runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        payload["probe"]["name"] = command[-4]
        return ProcessResult(tuple(command), 0, "LADON_FRAME " + json.dumps(payload), "", 0.1)

    result = check_semantic_candidate(
        SemanticCandidateRequest(repo, "Main", "Nat", "Main.identity"),
        runner=foreign_runner,
    )

    assert result.status == "invalid-worker-output"
    assert result.artifacts == ()
    assert result.diagnostic["code"] == "invalid-worker-output"
