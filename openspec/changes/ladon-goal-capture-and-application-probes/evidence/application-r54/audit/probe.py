"""Auditor-only edge probes for semantic text rendering."""
from __future__ import annotations

import copy
import json
import runpy
import tempfile
from pathlib import Path

from ladon.proof_search_cli import _render_text
from ladon.semantic_result_delivery import deliver_semantic_result


def main() -> None:
    helpers = runpy.run_path("tests/test_semantic_residual_text.py")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        candidate = "Main.unicode"
        check = helpers["_check"](
            "unicode",
            candidate,
            "applicable-with-residuals",
            [{"typeDisplay": "λ" * 1000, "typeStructural": "unicode"}],
        )
        payload = {
            "schema": "ladon-semantic-candidate-check-result-v1",
            "operation": "check-candidate",
            "status": "applicable-with-residuals",
            "candidate": candidate,
            **check,
        }
        projected = deliver_semantic_result(
            payload,
            projection="llm",
            repo_root=root,
            registry_path=root / "evidence.sqlite",
        )
        before = copy.deepcopy(projected)
        text = _render_text(projected)
        residual = projected["candidate"]["check"]["residualPremises"][0]["typeDisplay"]
        assert residual.endswith("…")
        assert "remaining goal: " + residual in text
        assert projected == before
        assert any(
            row["reason"] == "projection-text-byte-limit"
            and row["pointer"].endswith("/residualPremises/0/typeDisplay")
            for row in projected["omissions"]
        )
        assert len(json.dumps(projected, ensure_ascii=False).encode()) <= projected[
            "projection"
        ]["limits"]["maxBytes"]

    malformed = {
        "schema": "ladon-semantic-candidate-check-result-v1",
        "operation": "check candidate",
        "status": "partial",
        "candidate": {
            "name": "C",
            "check": {
                "status": "partial",
                "residualPremises": [{}, None],
                "authority": {"analysisCompleteness": "partial"},
            },
        },
    }
    malformed_text = _render_text(malformed)
    assert malformed_text.count(
        "remaining goal: unavailable in this view; expand check evidence"
    ) == 2

    minimal = {
        "schema": "ladon-verified-discovery-result-v1",
        "operation": "discover",
        "status": "available",
        "requiresAuditExpansion": True,
        "omissions": [{"pointer": "/projection", "reason": "projection-byte-limit", "omitted": 1}],
        "coverage": {
            "omissionPopulation": {
                "observedRecords": 4,
                "projectedRecords": 0,
                "omittedRecords": 4,
            }
        },
        "candidates": [
            {
                "nameFingerprint": "sha256:x",
                "check": {
                    "status": "applicable-with-residuals",
                    "authority": {"analysisCompleteness": "partial"},
                    "environmentRef": {"environmentRef": "env:x"},
                    "checkRunRef": {"artifactRef": "a:x", "kind": "check-run", "localId": "c:x"},
                },
            }
        ],
    }
    minimal_text = _render_text(minimal)
    assert "detail unavailable: this projection requires audit evidence expansion" in minimal_text
    assert "remaining goals: unavailable in this view; expand check evidence" in minimal_text
    assert "evidence expansion checkRunRef:" in minimal_text
    assert "analysisCompleteness=partial" in minimal_text
    print("unicode truncation, omissions, JSON immutability, byte cap, unavailable rows, and minimal expansion passed")


if __name__ == "__main__":
    main()
