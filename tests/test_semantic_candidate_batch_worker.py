from __future__ import annotations

import json
import sys
from pathlib import Path

from ladon.process_supervisor import ProcessResult
from ladon.semantic_candidate_batch_worker import check_semantic_candidates
from ladon.semantic_candidate_worker import SEMANTIC_BATCH_PROTOCOL, SemanticCandidateRequest


def _stream(
    header: dict[str, object], rows: list[dict[str, object]], *, summary: bool = True
) -> str:
    request_id = str(header["requestId"])
    frames = [header]
    frames.extend(
        {
            "protocol": SEMANTIC_BATCH_PROTOCOL,
            "frameVersion": 1,
            "frameKind": "candidate",
            "sequence": index,
            "terminal": False,
            "requestId": request_id,
            "row": row,
        }
        for index, row in enumerate(rows, start=1)
    )
    if summary:
        frames.append(
            {
                "protocol": SEMANTIC_BATCH_PROTOCOL,
                "frameVersion": 1,
                "frameKind": "summary",
                "sequence": len(rows) + 1,
                "terminal": True,
                "requestId": request_id,
                "completed": len(rows),
                "total": len(rows),
            }
        )
    return "\n".join("LADON_FRAME " + json.dumps(frame) for frame in frames)


def test_batch_worker_uses_one_framed_process_and_preserves_row_order(tmp_path: Path) -> None:
    observed: dict[str, object] = {}
    olean = tmp_path / "Main.olean"
    olean.write_bytes(b"compiled")

    def runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        observed["command"] = command
        request_id = command[-4]
        probe_name = command[-5]
        header = {
            "protocol": SEMANTIC_BATCH_PROTOCOL,
            "frameVersion": 1,
            "frameKind": "header",
            "sequence": 0,
            "terminal": False,
            "requestId": request_id,
            "executionContextRef": "unbound",
            "universePolicy": "lean-level-mvar-succ-zero/v1",
            "leanVersion": "4.fixture",
            "leanCommit": "fixture",
            "executablePath": sys.executable,
            "module": "Main",
            "probe": {"name": probe_name, "typeDisplay": "Nat", "typeStructural": "Nat"},
            "importedModules": [{"module": "Main", "oleanPath": str(olean)}],
            "localContext": [],
        }
        rows = [
            {
                "candidate": "Main.good",
                "status": "accepted",
                "candidateSubject": {
                    "name": "Main.good",
                    "typeDisplay": "Nat",
                    "typeStructural": "Nat",
                },
                "applicationTerm": "Main.good",
                "dischargedHypotheses": [],
                "substitutions": [],
                "residualPremises": [],
                "diagnostic": "",
            },
            {
                "candidate": "Main.bad",
                "status": "rejected",
                "candidateSubject": None,
                "applicationTerm": "",
                "dischargedHypotheses": [],
                "substitutions": [],
                "residualPremises": [],
                "diagnostic": "unknown declaration",
            },
        ]
        return ProcessResult(command, 0, _stream(header, rows), "", 0.1)

    result = check_semantic_candidates(
        SemanticCandidateRequest(tmp_path, "Main", "Nat", "Main.good"),
        ["Main.good", "Main.bad"],
        runner=runner,
    )
    assert result.status == "available"
    assert [row["candidate"] for row in result.rows] == ["Main.good", "Main.bad"]
    assert all(row["evidenceReceipt"]["checkRunRef"] == row["checkRunRef"] for row in result.rows)
    assert [artifact["artifactKind"] for artifact in result.rows[0]["artifacts"]] == [
        "proofir.environment",
        "proofir.check-run",
        "proofir.derivation",
    ]
    assert "--batch" in observed["command"]  # type: ignore[operator]


def test_batch_worker_rejects_malformed_accepted_row_fields(tmp_path: Path) -> None:
    def runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        header = {
            "protocol": SEMANTIC_BATCH_PROTOCOL,
            "frameVersion": 1,
            "frameKind": "header",
            "sequence": 0,
            "terminal": False,
            "requestId": command[-3],
            "executionContextRef": "unbound",
            "universePolicy": "lean-level-mvar-succ-zero/v1",
            "leanVersion": "4.fixture",
            "leanCommit": "fixture",
            "executablePath": sys.executable,
            "module": "Main",
            "probe": {"name": command[-4], "typeDisplay": "Nat", "typeStructural": "Nat"},
            "importedModules": [{"module": "Main", "oleanPath": str(tmp_path / "Main.olean")}],
            "localContext": [],
        }
        rows = [
            {
                "candidate": "Main.good",
                "status": "accepted",
                "dischargedHypotheses": [],
                "candidateSubject": 7,
                "substitutions": "bad",
                "residualPremises": [{}],
                "diagnostic": [],
            }
        ]
        return ProcessResult(command, 0, _stream(header, rows), "", 0.1)

    result = check_semantic_candidates(
        SemanticCandidateRequest(tmp_path, "Main", "Nat", "Main.good"),
        ["Main.good"],
        runner=runner,
    )
    assert result.status == "invalid-worker-output"


def test_batch_worker_preserves_validated_prefix_after_timeout(tmp_path: Path) -> None:
    olean = tmp_path / "Main.olean"
    olean.write_bytes(b"compiled")

    def runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        header = {
            "protocol": SEMANTIC_BATCH_PROTOCOL,
            "frameVersion": 1,
            "frameKind": "header",
            "sequence": 0,
            "terminal": False,
            "requestId": command[-4],
            "executionContextRef": "unbound",
            "universePolicy": "lean-level-mvar-succ-zero/v1",
            "leanVersion": "4.fixture",
            "leanCommit": "fixture",
            "executablePath": sys.executable,
            "module": "Main",
            "probe": {"name": command[-5], "typeDisplay": "Nat", "typeStructural": "Nat"},
            "importedModules": [{"module": "Main", "oleanPath": str(olean)}],
            "localContext": [],
        }
        row = {
            "candidate": "Main.good",
            "status": "accepted",
            "candidateSubject": {
                "name": "Main.good",
                "typeDisplay": "Nat",
                "typeStructural": "Nat",
            },
            "applicationTerm": "Main.good",
            "dischargedHypotheses": [],
            "substitutions": [],
            "residualPremises": [],
            "diagnostic": "",
        }
        return ProcessResult(
            command, -9, _stream(header, [row], summary=False), "", 1.0, timed_out=True
        )

    result = check_semantic_candidates(
        SemanticCandidateRequest(tmp_path, "Main", "Nat", "Main.good"),
        ["Main.good", "Main.later"],
        runner=runner,
    )
    assert result.status == "partial"
    assert result.terminal is False
    assert [row["candidate"] for row in result.rows] == ["Main.good"]
    assert result.rows[0]["batchTerminal"] is False
    assert result.rows[0]["evidenceReceipt"]["analysisCompleteness"] == "partial"
