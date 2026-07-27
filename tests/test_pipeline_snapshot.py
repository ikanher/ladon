from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ladon.analysis.generated_family_candidate_profile import (
    CANDIDATE_PROFILE_SCHEMA,
    COMMAND_SKELETON_VERSION,
    DECLARATION_STEM_VERSION,
    GROUPING_VERSION,
)
from ladon.pipeline import run_pipeline
from ladon.pipeline_extraction import indexed_discovery
from ladon.pipeline_models import RunContext
from ladon.report_v3 import build_report_v3
from ladon.ir import LeanModule


def write_project(root: Path) -> bytes:
    """Create one deterministic indexed project and return its root bytes."""

    (root / "Pkg").mkdir()
    root_bytes = b"import Pkg.Core\n"
    (root / "Pkg.lean").write_bytes(root_bytes)
    (root / "Pkg" / "Core.lean").write_text(
        "def core : Nat := 1\n",
        encoding="utf-8",
    )
    return root_bytes


def test_run_context_snapshot_state_defaults_to_absent(tmp_path: Path) -> None:
    context = RunContext(repo_root=tmp_path)

    assert context.source_index is None
    assert context.analysis_snapshot is None


def test_indexed_discovery_retains_index_and_captures_snapshot(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    root_bytes = write_project(repo)
    context = RunContext(
        repo_root=repo,
        requested_root="Pkg",
        source_cache_enabled=False,
    )

    resolved = indexed_discovery(context)

    assert context.source_index is resolved.source_index.index
    snapshot = context.analysis_snapshot
    assert snapshot is not None
    assert snapshot.source_index_fingerprint == context.source_index.fingerprint
    assert snapshot.entries["Pkg.lean"].sha256 == (
        "sha256:" + hashlib.sha256(root_bytes).hexdigest()
    )
    assert snapshot.entries["Pkg.lean"].collection_refs == (
        "source_index.modules",
        "source_index.imports",
        "source_index.declarations",
    )
    assert snapshot.entries["lake-manifest.json"].status == "absent"
    assert snapshot.configuration["scopeFingerprint"] == (
        resolved.scope_plan.fingerprint
    )
    assert snapshot.configuration["extraction"] == {
        "backend": "text",
        "scope": "root",
        "batchSize": context.lean_batch_size,
        "strict": False,
    }
    assert snapshot.configuration["sourceIndex"]["schema"] == (
        context.source_index.schema
    )


def test_snapshot_identity_ignores_cache_outcome(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    cache = tmp_path / "cache"
    cold = RunContext(
        repo_root=repo,
        requested_root="Pkg",
        source_cache_dir=cache,
    )
    warm = RunContext(
        repo_root=repo,
        requested_root="Pkg",
        source_cache_dir=cache,
    )

    indexed_discovery(cold)
    indexed_discovery(warm)

    assert cold.source_index_cache is not None
    assert warm.source_index_cache is not None
    assert cold.source_index_cache["status"] == "miss"
    assert warm.source_index_cache["status"] == "hit"
    assert cold.analysis_snapshot is not None
    assert warm.analysis_snapshot is not None
    assert cold.analysis_snapshot.identity == warm.analysis_snapshot.identity


@pytest.mark.parametrize(
    ("context_field", "result_field", "first_payload", "second_payload"),
    [
        (
            "module_system_witness",
            "module_readiness",
            {
                "artifactKind": "module_system_witness",
                "schemaVersion": 1,
                "rows": [{"module": "Pkg"}],
            },
            {
                "artifactKind": "module_system_witness",
                "schemaVersion": 1,
                "rows": [{"module": "Pkg.Core"}],
            },
        ),
        (
            "import_diet_witness",
            "import_diet",
            {
                "artifactKind": "import_diet_witness",
                "schemaVersion": 1,
                "rows": [
                    {
                        "module": "Pkg",
                        "minimizedImports": ["Pkg.Core"],
                    }
                ],
            },
            {
                "artifactKind": "import_diet_witness",
                "schemaVersion": 1,
                "rows": [{"module": "Pkg", "minimizedImports": []}],
            },
        ),
        (
            "proof_xray",
            "proof_xray",
            {
                "artifactKind": "proof_xray",
                "schemaVersion": 1,
                "rows": [{"declarationName": "Pkg.first"}],
            },
            {
                "artifactKind": "proof_xray",
                "schemaVersion": 1,
                "rows": [{"declarationName": "Pkg.second"}],
            },
        ),
    ],
)
def test_inline_evidence_changes_stable_snapshot_identity(
    tmp_path: Path,
    context_field: str,
    result_field: str,
    first_payload: dict,
    second_payload: dict,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    results = [
        run_pipeline(
            RunContext(
                repo_root=repo,
                requested_root="Pkg",
                source_cache_enabled=False,
                **{context_field: payload},
            )
        )
        for payload in (first_payload, second_payload)
    ]

    snapshots = [result.context.analysis_snapshot for result in results]
    assert all(snapshot is not None for snapshot in snapshots)
    assert all(
        result.context.snapshot_decision is not None
        and result.context.snapshot_decision.status == "stable"
        for result in results
    )
    assert snapshots[0].identity != snapshots[1].identity
    assert getattr(results[0], result_field) != getattr(results[1], result_field)


def test_inline_evidence_phase_reuses_preanalysis_capture(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    witness = {
        "artifactKind": "module_system_witness",
        "schemaVersion": 1,
        "rows": [{"module": "Pkg"}],
    }

    def mutate_after_discovery(context: RunContext, discovery):
        context.module_system_witness["rows"][0]["module"] = "Pkg.Changed"
        return discovery.modules

    result = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            source_cache_enabled=False,
            extraction_backend="lean",
            lean_extractor=mutate_after_discovery,
            module_system_witness=witness,
        )
    )

    quoted = [
        row
        for row in result.module_readiness["rows"]
        if row["kind"] == "module_system_witness"
    ]
    assert witness["rows"][0]["module"] == "Pkg.Changed"
    assert [row["module"] for row in quoted] == ["Pkg"]
    assert result.context.snapshot_decision is not None
    assert result.context.snapshot_decision.status == "stable"


def test_packet_profile_and_order_change_snapshot_identity(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    first = tmp_path / "first-packet"
    second = tmp_path / "second-packet"
    first.mkdir()
    second.mkdir()
    (first / "metadata.json").write_text("{}", encoding="utf-8")
    (second / "tests.md").write_text("Lean theorem owner", encoding="utf-8")

    generic = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            source_cache_enabled=False,
            packet_dirs=(first, second),
            packet_profile="generic",
        )
    )
    review = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            source_cache_enabled=False,
            packet_dirs=(first, second),
            packet_profile="review_packet",
        )
    )
    reversed_order = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            source_cache_enabled=False,
            packet_dirs=(second, first),
            packet_profile="generic",
        )
    )

    identities = {
        result.context.analysis_snapshot.identity
        for result in (generic, review, reversed_order)
        if result.context.analysis_snapshot is not None
    }
    assert len(identities) == 3
    assert [row["profile"] for row in generic.packet_evidence] == [
        "generic",
        "generic",
    ]
    assert [row["profile"] for row in review.packet_evidence] == [
        "review_packet",
        "review_packet",
    ]


def test_pipeline_finalizes_one_stable_snapshot_decision(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)

    result = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            source_cache_enabled=False,
        )
    )

    decision = result.context.snapshot_decision
    assert decision is not None
    assert decision.status == "stable"
    payload = build_report_v3(result.to_report_model()).to_dict()
    assert payload["snapshot"]["decision"]["status"] == "stable"
    assert payload["snapshot"]["decision"]["mismatches"] == []


def test_pipeline_drift_decision_marks_all_coverage_unstable(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)

    def mutate_source(context: RunContext) -> None:
        (context.repo_root / "Pkg" / "Core.lean").write_text(
            "def core : Nat := 2\n",
            encoding="utf-8",
        )

    result = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            source_cache_enabled=False,
            snapshot_verification_hook=mutate_source,
        )
    )
    model = result.to_report_model()

    assert model.snapshot_decision is not None
    assert model.snapshot_decision.status == "changed"
    assert {
        row.completeness for row in model.coverage.collections.values()
    } == {"unstable"}
    payload = build_report_v3(model).to_dict()
    assert payload["snapshot"]["decision"]["diagnostic"] == (
        "source_changed_during_analysis"
    )
    assert all(
        row["completeness"] == "unstable"
        for row in payload["coverage"]["collections"].values()
    )


def test_unobserved_change_and_revert_keeps_byte_snapshot_stable(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)

    def change_and_revert(context: RunContext) -> None:
        path = context.repo_root / "Pkg" / "Core.lean"
        original = path.read_bytes()
        path.write_text("def core : Nat := 999\n", encoding="utf-8")
        path.write_bytes(original)

    result = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            source_cache_enabled=False,
            snapshot_verification_hook=change_and_revert,
        )
    )

    decision = result.context.snapshot_decision
    assert decision is not None
    assert decision.status == "stable"
    assert "unobserved transient filesystem event" in (
        decision.to_dict()["nonclaim"]
    )


def test_indexed_audit_adaptation_does_not_reopen_changed_source(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    core_path = repo / "Pkg" / "Core.lean"
    original = core_path.read_bytes()
    mutated = False

    def mutate_before_registered_read(
        context: RunContext,
        module: LeanModule,
    ) -> None:
        nonlocal mutated
        if module.name == "Pkg.Core" and not mutated:
            mutated = True
            (context.repo_root / module.path).write_text(
                "def core : Nat := 404\n",
                encoding="utf-8",
            )

    def restore_before_final_check(_context: RunContext) -> None:
        core_path.write_bytes(original)

    result = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            source_cache_enabled=False,
            snapshot_read_hook=mutate_before_registered_read,
            snapshot_verification_hook=restore_before_final_check,
        )
    )

    decision = result.context.snapshot_decision
    assert decision is not None
    assert mutated is True
    assert decision.status == "stable"
    assert decision.mismatches == ()
    assert core_path.read_bytes() == original


def test_optional_source_pattern_mixed_read_cannot_yield_stable_evidence(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    core_path = repo / "Pkg" / "Core.lean"
    original = core_path.read_bytes()
    mutated = False
    core_reads = 0

    def mutate_only_for_optional_source_read(
        _context: RunContext,
        module: LeanModule,
    ) -> None:
        nonlocal core_reads, mutated
        if module.name != "Pkg.Core":
            return
        core_reads += 1
        if core_reads == 2 and not mutated:
            mutated = True
            core_path.write_text(
                "def core : Nat := 404\n",
                encoding="utf-8",
            )

    def restore_before_final_check(_context: RunContext) -> None:
        core_path.write_bytes(original)

    result = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            source_cache_enabled=False,
            source_pattern_policy={
                "patterns": [
                    {
                        "id": "transient",
                        "pattern": "404",
                        "kind": "transient_source",
                    }
                ]
            },
            snapshot_read_hook=mutate_only_for_optional_source_read,
            snapshot_verification_hook=restore_before_final_check,
        )
    )

    assert mutated is True
    assert result.source_patterns is not None
    assert result.source_patterns["matchCount"] == 0
    decision = result.context.snapshot_decision
    assert decision is not None
    assert decision.status == "changed"
    assert decision.mismatches == (
        {
            "path": "Pkg/Core.lean",
            "expected": (
                "sha256:"
                + hashlib.sha256(original).hexdigest()
            ),
            "actual": (
                "sha256:"
                + hashlib.sha256(b"def core : Nat := 404\n").hexdigest()
            ),
            "collectionRefs": [
                "analysis.source_patterns",
                "report.findings",
            ],
        },
    )
    assert core_path.read_bytes() == original


def test_path_policy_is_consumed_from_preanalysis_capture(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    policy_path = repo / "source-patterns.json"
    original_policy = {
        "id": "captured-policy",
        "patterns": [
            {
                "id": "core-definition",
                "pattern": "def core",
                "kind": "captured_source",
            }
        ],
    }
    policy_path.write_text(json.dumps(original_policy), encoding="utf-8")
    mutated = False

    def mutate_policy_after_discovery(
        _context: RunContext,
        _module: LeanModule,
    ) -> None:
        nonlocal mutated
        if mutated:
            return
        mutated = True
        policy_path.write_text(
            json.dumps(
                {
                    "id": "transient-policy",
                    "patterns": [
                        {
                            "id": "transient",
                            "pattern": "404",
                            "kind": "transient_source",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def restore_before_final_check(_context: RunContext) -> None:
        policy_path.write_text(
            json.dumps(original_policy),
            encoding="utf-8",
        )

    result = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            source_cache_enabled=False,
            source_pattern_policy_path=policy_path,
            snapshot_read_hook=mutate_policy_after_discovery,
            snapshot_verification_hook=restore_before_final_check,
        )
    )

    assert mutated is True
    assert result.source_patterns is not None
    assert result.source_patterns["policyId"] == "captured-policy"
    assert result.source_patterns["matchCount"] == 1
    decision = result.context.snapshot_decision
    assert decision is not None
    assert decision.status == "stable"


def test_optional_witness_bytes_participate_in_final_drift(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    witness_path = repo / "module-system-witness.json"
    original = b'{"artifactKind":"module_system_witness","schemaVersion":1}\n'
    changed = (
        b'{"artifactKind":"module_system_witness","schemaVersion":1,'
        b'"rows":[]}\n'
    )
    witness_path.write_bytes(original)
    mutated = False

    def mutate_witness_before_optional_phase(
        _context: RunContext,
        _module: LeanModule,
    ) -> None:
        nonlocal mutated
        if not mutated:
            mutated = True
            witness_path.write_bytes(changed)

    def restore_before_final_check(_context: RunContext) -> None:
        witness_path.write_bytes(original)

    result = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            source_cache_enabled=False,
            module_system_witness_path=witness_path,
            snapshot_read_hook=mutate_witness_before_optional_phase,
            snapshot_verification_hook=restore_before_final_check,
        )
    )

    assert mutated is True
    decision = result.context.snapshot_decision
    assert decision is not None
    assert decision.status == "changed"
    mismatch = next(
        row
        for row in decision.mismatches
        if row["path"] == "module-system-witness.json"
    )
    assert mismatch["expected"]["sha256"] == (
        "sha256:" + hashlib.sha256(changed).hexdigest()
    )
    assert mismatch["actual"]["sha256"] == (
        "sha256:" + hashlib.sha256(original).hexdigest()
    )


def test_packet_text_bytes_participate_in_final_drift(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    packet = repo / "packet"
    packet.mkdir()
    readme = packet / "README.md"
    original = b"Lean theorem owner: Pkg.core\n"
    changed = b"Lean theorem owner: Pkg.transient\n"
    readme.write_bytes(original)
    mutated = False

    def mutate_packet_before_packet_phase(
        _context: RunContext,
        _module: LeanModule,
    ) -> None:
        nonlocal mutated
        if not mutated:
            mutated = True
            readme.write_bytes(changed)

    def restore_before_final_check(_context: RunContext) -> None:
        readme.write_bytes(original)

    result = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            source_cache_enabled=False,
            packet_dirs=(packet,),
            packet_profile="review_packet",
            snapshot_read_hook=mutate_packet_before_packet_phase,
            snapshot_verification_hook=restore_before_final_check,
        )
    )

    assert mutated is True
    decision = result.context.snapshot_decision
    assert decision is not None
    assert decision.status == "changed"
    mismatch = next(
        row
        for row in decision.mismatches
        if row["path"] == "packet/README.md"
    )
    assert mismatch["expected"]["sha256"] == (
        "sha256:" + hashlib.sha256(changed).hexdigest()
    )
    assert mismatch["actual"]["sha256"] == (
        "sha256:" + hashlib.sha256(original).hexdigest()
    )


def test_explicit_candidate_profile_drift_changes_shared_snapshot(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    profile_path = repo / "candidate-profile.json"
    profile = explicit_candidate_profile()
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    def mutate_profile(_context: RunContext) -> None:
        changed = {**profile, "representatives": {"limit": 7}}
        profile_path.write_text(json.dumps(changed), encoding="utf-8")

    result = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            source_cache_enabled=False,
            generated_family_candidate_profile_path=profile_path,
            snapshot_verification_hook=mutate_profile,
        )
    )

    decision = result.context.snapshot_decision
    assert decision is not None
    assert decision.status == "changed"
    assert any(
        row["path"].endswith("generatedFamilyCandidateProfile.json")
        for row in decision.mismatches
    )


def explicit_candidate_profile() -> dict:
    """Return one valid non-built-in candidate profile."""

    return {
        "schema": CANDIDATE_PROFILE_SCHEMA,
        "profileVersion": "snapshot-profile-v2",
        "grouping": {"version": GROUPING_VERSION},
        "clauses": {
            "minimumMembers": 3,
            "minimumDensity": {"numerator": 3, "denominator": 4},
            "directInternalImportMemberCoverage": {
                "numerator": 3,
                "denominator": 5,
            },
            "lexicalMemberCoverage": {
                "numerator": 2,
                "denominator": 3,
            },
            "lexicalFeatures": [
                COMMAND_SKELETON_VERSION,
                DECLARATION_STEM_VERSION,
            ],
        },
        "normalizers": {
            "declarationStem": DECLARATION_STEM_VERSION,
            "commandSkeleton": COMMAND_SKELETON_VERSION,
        },
        "representatives": {"limit": 5},
    }
