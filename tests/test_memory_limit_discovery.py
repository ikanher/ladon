"""Discovery must retain process failure guidance even after every row arrived."""
from ladon.proof_search_discovery_cli import _batch_results
from ladon.semantic_candidate_batch_worker import SemanticCandidateBatchCheck
from ladon.semantic_projection_cards import _failure
from ladon.verified_discovery import DiscoveryRequest, discover_candidates


def test_partial_batch_keeps_memory_guidance_in_discovery_and_llm_projection(tmp_path, monkeypatch):
    message = "Stop progress and report back to user: the 12 GiB memory limit was exceeded."
    batch = SemanticCandidateBatchCheck(
        "partial",
        rows=({"candidate": "Main.fact", "status": "accepted", "batchTerminal": False,
               "diagnostic": "original candidate observation"},),
        diagnostic={"code": "batch-memory-limit", "message": message},
    )
    monkeypatch.setattr("ladon.proof_search_discovery_cli.check_semantic_candidates",
                        lambda *_args: batch)
    request = DiscoveryRequest(tmp_path, "Main", "True")
    rows = _batch_results(request, ("Main.fact",), None)
    result = discover_candidates(
        request, [{"candidateName": "Main.fact"}], lambda _name: None,
        batch_checker=lambda _names: rows,
    )
    check = result["candidates"][0]["check"]
    assert check["status"] == "provisional-observation"
    assert check["diagnostic"]["message"] == message
    assert check["diagnostic"]["candidateDiagnostic"] == "original candidate observation"
    projected = _failure(check, "llm", [], "/check/failure")
    assert projected["diagnostic"]["message"] == message
