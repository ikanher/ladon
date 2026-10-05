from __future__ import annotations

import argparse
from pathlib import Path

import pytest
from support.proofir_v3_native import environment_artifact

from ladon import proof_search_discovery_cli
from ladon.proof_search_cli import build_proof_search_parser, proof_search_main
from ladon.proof_search_discovery_cli import _type_text_shortlist
from ladon.proof_search_index import build_proof_search_index
from ladon.proofir_v3 import validate_envelope_batch
from ladon.semantic_candidate_worker import SemanticCandidateCheck
from ladon.verified_discovery import (
    DiscoveryRequest,
    _scratch_check_artifact,
    discover_candidates,
)


def test_scratch_check_artifact_owns_its_check_run_subject() -> None:
    environment = environment_artifact()
    check_run_id = "check:" + "a" * 64
    artifact = _scratch_check_artifact(
        DiscoveryRequest(Path("/repo"), "Main", "Nat"),
        "Main.value",
        check_run_id,
        environment,
        {
            "status": "compiled",
            "sourceDigest": "sha256:" + "b" * 64,
            "outputDigest": "sha256:" + "c" * 64,
            "applicationTerm": "Main.value",
        },
        {"schema": "fixture-receipt"},
        None,
    )

    assert [
        {"kind": row["kind"], "localId": row["localId"]}
        for row in artifact["subjectRefs"]
        if row["kind"] == "check-run"
    ] == [{"kind": "check-run", "localId": check_run_id}]
    assert {"kind": "check-run", "localId": check_run_id} not in artifact["payload"]["inputs"][
        "subjectRefs"
    ]
    validate_envelope_batch([environment, artifact])


@pytest.mark.parametrize(
    "status", ["timeout", "output-limited", "memory-limited", "process-failed"]
)
def test_scratch_check_artifact_records_exact_supervised_failure_status(
    status: str,
) -> None:
    environment = environment_artifact()
    artifact = _scratch_check_artifact(
        DiscoveryRequest(Path("/repo"), "Main", "Nat"),
        "Main.value",
        "check:" + "d" * 64,
        environment,
        {
            "status": status,
            "sourceDigest": "sha256:" + "b" * 64,
            "outputDigest": "sha256:" + "c" * 64,
            "applicationTerm": "Main.value",
            "diagnostic": "bounded failure",
        },
        {"schema": "fixture-receipt"},
        None,
    )

    diagnostics = artifact["payload"]["results"][0]["diagnostics"]
    assert diagnostics[0]["stage"] == "scratch"
    assert diagnostics[0]["code"] == status


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


def test_discovery_rejects_duplicate_candidates_before_checker_work() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat", batch_size=1)
    checker_calls: list[str] = []
    batch_calls: list[tuple[str, ...]] = []

    with pytest.raises(ValueError, match="candidate names must be unique"):
        discover_candidates(
            request,
            [{"candidateName": "Main.same"}, {"candidateName": "Main.same"}],
            lambda name: checker_calls.append(name) or SemanticCandidateCheck("accepted"),
            batch_checker=lambda names: batch_calls.append(tuple(names)) or {},
        )

    assert checker_calls == []
    assert batch_calls == []


def test_discovery_cli_rejects_duplicates_before_toolchain_or_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence_store = tmp_path / "semantic-evidence.sqlite"

    def unexpected_toolchain(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("toolchain resolution must not run")

    monkeypatch.setattr(
        proof_search_discovery_cli,
        "resolve_toolchain_context",
        unexpected_toolchain,
    )

    status = proof_search_main(
        [
            "discover",
            "--repo-root",
            str(tmp_path),
            "--module",
            "Main",
            "--goal",
            "True",
            "--candidate",
            "Main.same",
            "--candidate",
            "Main.same",
            "--evidence-store",
            str(evidence_store),
            "--format",
            "json",
        ]
    )

    assert status == 2
    assert not evidence_store.exists()
    assert "candidate names must be unique" in capsys.readouterr().err


def test_discovery_check_failure_is_unassessed_and_bounded() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat", max_candidates=1)
    result = discover_candidates(request, [{"name": "a"}, {"name": "b"}], lambda _: 1 / 0)
    assert result["coverage"]["submitted"] == 1
    assert result["coverage"]["completed"] == 0
    assert result["coverage"]["truncated"] is True
    assert result["status"] == "failed"
    assert result["candidates"][0]["check"]["status"] == "unassessed"


def test_discovery_cli_documents_ordered_caller_context() -> None:
    parser = build_proof_search_parser()
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
    assert args.projection == "llm"
    assert args.scratch_mode == "none"
    subparsers = next(
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    )
    help_text = " ".join(subparsers.choices["discover"].format_help().split())
    assert "Ordered caller-local declaration NAME:TYPE" in help_text


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
        lambda _name, _application, _parent: {
            "status": "compiled",
            "sourceDigest": "sha256:scratch",
        },
    )
    assert result["candidates"][0]["check"]["scratch"]["status"] == "compiled"


def test_discovery_attempts_at_most_one_advisory_scratch() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat")
    scratch_calls: list[str] = []

    result = discover_candidates(
        request,
        [{"candidateName": "Main.first"}, {"candidateName": "Main.second"}],
        lambda _name: SemanticCandidateCheck("accepted"),
        lambda name, _application, _parent: scratch_calls.append(name) or {"status": "compiled"},
    )

    assert scratch_calls == ["Main.first"]
    assert result["coverage"]["scratchAttempted"] == 1


def test_discovery_rejects_aggregate_process_budget_before_work() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat", max_candidates=6, timeout_seconds=120)
    called: list[str] = []
    with pytest.raises(ValueError, match="aggregate process budget"):
        discover_candidates(
            request,
            [{"candidateName": f"Main.c{i}"} for i in range(6)],
            lambda name: called.append(name) or SemanticCandidateCheck("accepted"),
            lambda _name, _application, _parent: {"status": "compiled"},
        )
    assert called == []


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


def test_discovery_does_not_promote_or_replay_partial_batch_prefix() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat")
    scratch_calls: list[str] = []

    result = discover_candidates(
        request,
        [{"candidateName": "Main.good"}],
        lambda _: SemanticCandidateCheck("unassessed"),
        scratch_replayer=lambda name, _application, _parent: scratch_calls.append(name) or {},
        batch_checker=lambda names: {
            names[0]: {
                "candidate": names[0],
                "status": "accepted",
                "batchTerminal": False,
                "evidenceReceipt": {
                    "authorityBasis": "process-observation",
                    "analysisCompleteness": "partial",
                },
            }
        },
    )

    candidate = result["candidates"][0]["check"]
    assert result["status"] == "partial"
    assert result["coverage"]["completed"] == 0
    assert result["coverage"]["accepted"] == 0
    assert result["coverage"]["rejected"] == 0
    assert result["coverage"]["scratchAttempted"] == 0
    assert candidate["status"] == "provisional-observation"
    assert candidate["observedStatus"] == "accepted"
    assert scratch_calls == []


def test_discovery_request_identity_does_not_depend_on_checker_outcome() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat")
    shortlist = [{"candidateName": "Main.zero"}]
    accepted = discover_candidates(request, shortlist, lambda _: SemanticCandidateCheck("accepted"))
    rejected = discover_candidates(request, shortlist, lambda _: SemanticCandidateCheck("rejected"))
    assert accepted["requestIdentity"] == rejected["requestIdentity"]
    assert accepted["resultIdentity"] != rejected["resultIdentity"]


def test_discovery_identities_bind_shortlist_evidence_and_scratch_policy() -> None:
    request = DiscoveryRequest(Path("/repo"), "Main", "Nat")
    shortlist = [{"candidateName": "Main.zero"}]

    def checker(_name: str) -> SemanticCandidateCheck:
        return SemanticCandidateCheck("accepted")

    explicit = discover_candidates(
        request,
        shortlist,
        checker,
        shortlist_evidence={"source": "explicit-candidates"},
    )
    lexical = discover_candidates(
        request,
        shortlist,
        checker,
        shortlist_evidence={"source": "type-text-shortlist", "pattern": "Nat"},
    )
    advisory = discover_candidates(
        request,
        shortlist,
        checker,
        lambda _name, _application, _parent: {"status": "compiled"},
        shortlist_evidence={"source": "explicit-candidates"},
    )

    assert explicit["resultIdentity"] != lexical["resultIdentity"]
    assert explicit["requestIdentity"] == lexical["requestIdentity"]
    assert explicit["request"]["scratchMode"] == "none"
    assert advisory["request"]["scratchMode"] == "advisory"
    assert explicit["requestIdentity"] != advisory["requestIdentity"]


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
        scratch_replayer=lambda _name, _application, _parent: (_ for _ in ()).throw(
            RuntimeError("scratch boom")
        ),
    )
    assert scratch_failed["status"] == "available"
    assert scratch_failed["candidates"][0]["check"]["scratch"]["status"] == "failed"


@pytest.mark.parametrize(
    ("scope", "roots", "expected"),
    [
        ("repository", [], {"Main.localFact", "Helpers.useful"}),
        ("project", [], {"Main.localFact", "Helpers.useful"}),
        ("module", ["Helpers"], {"Helpers.useful"}),
        ("namespace", ["Helpers"], {"Helpers.useful"}),
        ("file", ["Helpers.lean"], {"Helpers.useful"}),
        ("imports", ["Main"], {"Main.localFact", "Helpers.useful"}),
        ("closure", ["Main"], {"Main.localFact", "Helpers.useful"}),
        ("neighborhood", ["Helpers"], {"Main.localFact", "Helpers.useful"}),
        ("external", [], set()),
    ],
)
def test_discovery_checking_module_does_not_filter_shortlist_scope(
    tmp_path: Path, scope: str, roots: list[str], expected: set[str]
) -> None:
    (tmp_path / "Helpers.lean").write_text(
        "namespace Helpers\ntheorem useful : True := True.intro\nend Helpers\n",
        encoding="utf-8",
    )
    (tmp_path / "Main.lean").write_text(
        "import Helpers\nnamespace Main\ntheorem localFact : True := True.intro\nend Main\n",
        encoding="utf-8",
    )
    build_proof_search_index(tmp_path)
    args = argparse.Namespace(
        pattern="True", module="Main", scope=scope, root=roots,
        max_candidates=20, freshness="stored",
    )

    rows, evidence = _type_text_shortlist(args, tmp_path, None)

    assert {row["candidateName"] for row in rows} == expected
    assert evidence["coverage"]["scope"]["kind"] == scope


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
        {"timeout_seconds": float("nan")},
        {"max_output_bytes": 65 * 1024 * 1024},
        {"max_rss_bytes": 65 * 1024 * 1024 * 1024},
    ],
)
def test_discovery_rejects_unbounded_public_resources(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="cap"):
        DiscoveryRequest(Path("/repo"), "Main", "Nat", **kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field", ["max_candidates", "batch_size", "max_output_bytes", "max_rss_bytes"]
)
def test_discovery_rejects_non_integer_bounds(field: str) -> None:
    with pytest.raises(TypeError, match="must be integers"):
        DiscoveryRequest(Path("/repo"), "Main", "Nat", **{field: 1.5})  # type: ignore[arg-type]
