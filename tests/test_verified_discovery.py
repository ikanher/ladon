from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from ladon.proof_search_cli import build_proof_search_parser
from ladon.proof_search_discovery_cli import _type_text_shortlist
from ladon.proof_search_index import build_proof_search_index
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
    assert result["batch"]["protocol"] == "ladon-verified-discovery-v1"
    assert result["ranking"]["policy"] == "verified-status-priority-v1"


def test_discovery_check_failure_is_unassessed_and_bounded() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat", max_candidates=1)
    result = discover_candidates(request, [{"name": "a"}, {"name": "b"}], lambda _: 1 / 0)
    assert result["coverage"]["submitted"] == 1
    assert result["coverage"]["completed"] == 0
    assert result["coverage"]["truncated"] is True
    assert result["status"] == "failed"
    assert result["candidates"][0]["check"]["status"] == "unassessed"


def test_discovery_cli_contract_accepts_goal_context_and_candidates() -> None:
    args = build_proof_search_parser().parse_args(
        [
            "discover",
            "--repo-root",
            "/repo",
            "--module",
            "Main",
            "--goal",
            "Nat",
            "--candidate",
            "Main.zero",
            "--local",
            "h:Nat",
            "--max-candidates",
            "2",
        ]
    )
    assert args.proof_search_operation == "discover"
    assert args.local == ["h:Nat"]


def test_semantic_request_retains_discovery_local_context() -> None:
    from ladon.proof_search_discovery_cli import request_to_semantic

    request = DiscoveryRequest(
        Path("/repo"),
        "Main",
        "value = value",
        local_context=({"name": "value", "type": "Nat"},),
    )
    semantic = request_to_semantic(request, None)
    assert semantic.local_context == request.local_context


def test_discovery_attaches_independent_scratch_result_for_acceptance() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat")
    result = discover_candidates(
        request,
        [{"candidateName": "Main.zero"}],
        lambda _name: SemanticCandidateCheck("accepted"),
        lambda _name: {"status": "compiled", "sourceDigest": "sha256:scratch"},
    )
    assert result["candidates"][0]["check"]["scratch"]["status"] == "compiled"


def test_discovery_uses_one_batch_checker_when_provided() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat")
    called: list[tuple[str, ...]] = []

    def batch(names: tuple[str, ...]) -> dict[str, dict[str, str]]:
        called.append(names)
        return {name: {"candidate": name, "status": "rejected"} for name in names}

    result = discover_candidates(
        request,
        [{"candidateName": "a"}, {"candidateName": "b"}],
        lambda _: (_ for _ in ()).throw(AssertionError("per-candidate checker must not run")),
        batch_checker=batch,
    )
    assert called == [("a", "b")]
    assert [row["check"]["status"] for row in result["candidates"]] == ["rejected", "rejected"]


def test_discovery_honors_batch_size_and_ranks_verified_outcomes() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat", batch_size=1)
    called: list[tuple[str, ...]] = []

    def batch(names: tuple[str, ...]) -> dict[str, dict[str, str]]:
        called.append(names)
        return {
            name: {"candidate": name, "status": "accepted" if name == "good" else "rejected"}
            for name in names
        }

    result = discover_candidates(
        request,
        [{"candidateName": "bad"}, {"candidateName": "good"}],
        lambda _: SemanticCandidateCheck("unassessed"),
        batch_checker=batch,
    )
    assert called == [("bad",), ("good",)]
    assert [row["name"] for row in result["candidates"]] == ["good", "bad"]
    assert result["candidates"][0]["shortlist"]["shortlistOrdinal"] == 1


def test_discovery_request_identity_does_not_depend_on_checker_outcome() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat")
    shortlist = [{"candidateName": "Main.zero"}]
    accepted = discover_candidates(request, shortlist, lambda _: SemanticCandidateCheck("accepted"))
    rejected = discover_candidates(request, shortlist, lambda _: SemanticCandidateCheck("rejected"))
    assert accepted["requestIdentity"] == rejected["requestIdentity"]
    assert accepted["resultIdentity"] != rejected["resultIdentity"]


def test_discovery_isolates_batch_and_scratch_failures() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat")
    batch_failed = discover_candidates(
        request,
        [{"candidateName": "Main.zero"}],
        lambda _: SemanticCandidateCheck("accepted"),
        batch_checker=lambda _names: (_ for _ in ()).throw(RuntimeError("batch boom")),
    )
    assert batch_failed["status"] == "failed"
    assert batch_failed["candidates"][0]["check"]["status"] == "unassessed"

    scratch_failed = discover_candidates(
        request,
        [{"candidateName": "Main.zero"}],
        lambda _: SemanticCandidateCheck("accepted"),
        scratch_replayer=lambda _name: (_ for _ in ()).throw(RuntimeError("scratch boom")),
    )
    assert scratch_failed["status"] == "available"
    assert scratch_failed["candidates"][0]["check"]["scratch"]["status"] == "failed"


def test_discovery_shortlist_mode_reuses_type_text_scope_and_coverage(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem first : Nat := 1\ntheorem second : Nat := 2\n",
        encoding="utf-8",
    )
    build_proof_search_index(tmp_path)
    args = argparse.Namespace(
        pattern="Nat",
        module="Main",
        scope="module",
        root=["Main"],
        max_candidates=1,
        freshness="stored",
    )
    rows, evidence = _type_text_shortlist(args, tmp_path, None)
    assert len(rows) == 1
    assert evidence["source"] == "type-text-shortlist"
    assert evidence["coverage"]["scope"]["kind"] == "module"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"local_context": tuple({"name": f"h{i}", "type": "Nat"} for i in range(257))},
        {"timeout_seconds": 601},
        {"max_output_bytes": 65 * 1024 * 1024},
        {"max_rss_bytes": 65 * 1024 * 1024 * 1024},
    ],
)
def test_discovery_rejects_unbounded_public_resources(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="cap"):
        DiscoveryRequest(Path("/repo"), "Main", "Nat", **kwargs)  # type: ignore[arg-type]
