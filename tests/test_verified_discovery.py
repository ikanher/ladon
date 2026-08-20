from __future__ import annotations

from pathlib import Path

from ladon.proof_search_cli import build_proof_search_parser
from ladon.semantic_candidate_worker import SemanticCandidateCheck
from ladon.verified_discovery import DiscoveryRequest, discover_candidates


def test_discovery_preserves_accepted_rejected_and_failed_candidates() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat", max_candidates=3)

    def checker(name: str) -> SemanticCandidateCheck:
        if name == "good":
            return SemanticCandidateCheck("accepted")
        return SemanticCandidateCheck("rejected", diagnostic={"code": "not-applicable"})

    result = discover_candidates(
        request,
        [{"candidateName": "good"}, {"candidateName": "bad"}, {"candidateName": "missing"}],
        checker,
    )
    assert [row["check"]["status"] for row in result["candidates"]] == [
        "accepted",
        "rejected",
        "rejected",
    ]
    assert result["requestIdentity"].startswith("sha256:")


def test_discovery_check_failure_is_unassessed_and_bounded() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat", max_candidates=1)
    result = discover_candidates(request, [{"name": "a"}, {"name": "b"}], lambda _: 1 / 0)
    assert result["coverage"]["checked"] == 1
    assert result["coverage"]["truncated"] is True
    assert result["candidates"][0]["check"]["status"] == "unassessed"


def test_discovery_cli_contract_accepts_goal_context_and_candidates() -> None:
    args = build_proof_search_parser().parse_args(
        [
            "discover", "--repo-root", "/repo", "--module", "Main", "--goal", "Nat",
            "--candidate", "Main.zero", "--local", "h:Nat", "--max-candidates", "2",
        ]
    )
    assert args.proof_search_operation == "discover"
    assert args.local == ["h:Nat"]
