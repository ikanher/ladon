from __future__ import annotations

from pathlib import Path

from ladon.analysis.benchmark_oracles import (
    evaluate_oracles,
    existing_optional_smoke_roots,
    oracle_schema,
)
from ladon.analysis.architecture_policy import summarize_architecture_policy
from ladon.analysis.claim_authority import audit_claim_authority
from ladon.analysis.declaration_graph import summarize_declaration_graph
from ladon.analysis.findings import summarize_findings
from ladon.analysis.module_dag import summarize_module_dag
from ladon.analysis.proof_family_similarity import proof_family_similarity_candidates
from ladon.analysis.source_patterns import SourceDocument, summarize_source_patterns
from ladon.analysis.witness_packet import summarize_packet_evidence
from ladon.ir import LeanDeclaration, LeanImport, LeanModule


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "benchmark_oracles"


def test_oracles_check_positive_and_negative_declaration_edges() -> None:
    payload = {
        "declaration_graph": summarize_declaration_graph(
            {
                "Bench.root": LeanDeclaration(
                    name="Bench.root",
                    module="Bench",
                    references=("local_helper", "shared"),
                ),
                "Bench.local_helper": LeanDeclaration(name="Bench.local_helper", module="Bench"),
                "A.shared": LeanDeclaration(name="A.shared", module="A"),
                "B.shared": LeanDeclaration(name="B.shared", module="B"),
            },
            chosen_roots=("Bench.root",),
        )
    }

    rows = evaluate_oracles(
        payload,
        [
            {
                "fixture": "duplicate-basename",
                "signal": "resolved_edge",
                "source": "Bench.root",
                "target": "Bench.local_helper",
                "expected": True,
            },
            {
                "fixture": "duplicate-basename",
                "signal": "resolved_edge",
                "source": "Bench.root",
                "target": "A.shared",
                "expected": False,
            },
        ],
    )

    assert [row.passed for row in rows] == [True, True]
    assert "fixture=duplicate-basename" in rows[0].message
    assert "observed=False" in rows[1].message


def test_oracles_check_unresolved_reference_classes() -> None:
    payload = {
        "declaration_graph": summarize_declaration_graph(
            {
                "Bench.root": LeanDeclaration(
                    name="Bench.root",
                    module="Bench",
                    references=("count", "Fin", "MissingTheorem", "KnownImported"),
                )
            },
            known_reference_names=("KnownImported",),
        )
    }

    rows = evaluate_oracles(
        payload,
        [
            {
                "fixture": "reference-noise",
                "signal": "unresolved_class",
                "candidate": "count",
                "expected": "local_or_field_candidate",
            },
            {
                "fixture": "reference-noise",
                "signal": "unresolved_class",
                "candidate": "Fin",
                "expected": "external_candidate",
            },
            {
                "fixture": "reference-noise",
                "signal": "unresolved_class",
                "candidate": "MissingTheorem",
                "expected": "actionable_unknown",
            },
            {
                "fixture": "reference-noise",
                "signal": "unresolved_class",
                "candidate": "KnownImported",
                "expected": "known_inventory_candidate",
            },
        ],
    )

    assert all(row.passed for row in rows)


def test_oracles_check_proof_family_root_scope_and_packet_profiles(tmp_path: Path) -> None:
    declaration_graph = summarize_declaration_graph(
        {
            "Bench.alpha_nonneg": LeanDeclaration(
                name="Bench.alpha_nonneg",
                module="Bench",
                kind="theorem",
                references=("Bench.kernel", "Edge"),
            ),
            "Bench.beta_nonneg": LeanDeclaration(
                name="Bench.beta_nonneg",
                module="Bench",
                kind="theorem",
                references=("Bench.kernel", "Edge"),
            ),
            "Bench.kernel": LeanDeclaration(name="Bench.kernel", module="Bench"),
        }
    )
    modules = {
        "Bench": LeanModule(name="Bench", path="Bench.lean", imports=("Bench.Owner",)),
        "Bench.Owner": LeanModule(
            name="Bench.Owner",
            path="Bench/Owner.lean",
            imports=(),
            declarations=("owner",),
        ),
    }
    modules.update(
        {
            f"Bench.Orphan{i}": LeanModule(
                name=f"Bench.Orphan{i}",
                path=f"Bench/Orphan{i}.lean",
                declarations=(f"orphan{i}",),
            )
            for i in range(20)
        }
    )
    module_dag = summarize_module_dag(modules, chosen_roots=("Bench.Owner",))
    findings = summarize_findings(module_dag, declaration_graph)
    packet = tmp_path / "packet"
    (packet / "tests").mkdir(parents=True)
    (packet / "manifest.json").write_text("{}\n", encoding="utf-8")
    (packet / "tests" / "test_review.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    (packet / "README.md").write_text("Lean theorem owner: Bench.root\n", encoding="utf-8")
    payload = {
        "declaration_graph": declaration_graph,
        "findings": findings,
        "packet_evidence": [summarize_packet_evidence(packet, profile="review_packet")],
    }

    rows = evaluate_oracles(
        payload,
        [
            {
                "fixture": "proof-family",
                "signal": "proof_family_candidate",
                "suffix": "nonneg",
                "expected": True,
            },
            {
                "fixture": "root-scope",
                "signal": "root_scope_classification",
                "expected": "narrow_owner",
            },
            {
                "fixture": "review-packet",
                "signal": "packet_profile_status",
                "profile": "review_packet",
                "expected": "complete",
            },
        ],
    )

    assert proof_family_similarity_candidates(
        {
            "Bench.alpha_nonneg": LeanDeclaration(
                name="Bench.alpha_nonneg",
                module="Bench",
                kind="theorem",
                references=("Bench.kernel", "Edge"),
            ),
            "Bench.beta_nonneg": LeanDeclaration(
                name="Bench.beta_nonneg",
                module="Bench",
                kind="theorem",
                references=("Bench.kernel", "Edge"),
            ),
            "Bench.kernel": LeanDeclaration(name="Bench.kernel", module="Bench"),
        },
        declaration_graph["edges"],
        {
            "Bench.alpha_nonneg": {"local_type_parameter_candidate": 1},
            "Bench.beta_nonneg": {"local_type_parameter_candidate": 1},
            "Bench.kernel": {},
        },
    )
    assert all(row.passed for row in rows)


def test_oracles_check_review_intelligence_signals() -> None:
    module_dag = summarize_module_dag(
        {
            "Pkg.Alpha.Owner": LeanModule(
                name="Pkg.Alpha.Owner",
                path="Pkg/Alpha/Owner.lean",
                imports=("Pkg.Beta.Core", "Pkg.Common.Foundation"),
            ),
            "Pkg.Beta.Owner": LeanModule(
                name="Pkg.Beta.Owner",
                path="Pkg/Beta/Owner.lean",
                imports=("Pkg.Common.Foundation",),
            ),
            "Pkg.GeneratedRoute.All": LeanModule(
                name="Pkg.GeneratedRoute.All",
                path="Pkg/GeneratedRoute/All.lean",
                imports=("Pkg.Common.Foundation", "Pkg.Common.Foundation"),
                tags=("generated",),
                import_sites=(
                    LeanImport(module="Pkg.Common.Foundation", line=1, text="import Pkg.Common.Foundation"),
                    LeanImport(module="Pkg.Common.Foundation", line=2, text="import Pkg.Common.Foundation"),
                ),
            ),
            "Pkg.Mixed": LeanModule(
                name="Pkg.Mixed",
                path="Pkg/Mixed.lean",
                imports=(
                    "Pkg.Common.Foundation",
                    "Pkg.Common.Extra",
                    "Pkg.Common.More",
                    "Pkg.Common.Other",
                    "Pkg.Common.Last",
                ),
                declarations=("mixed",),
            ),
            "Pkg.Beta.Core": LeanModule(name="Pkg.Beta.Core", path="Pkg/Beta/Core.lean"),
            "Pkg.Common.Foundation": LeanModule(name="Pkg.Common.Foundation", path="Pkg/Common/Foundation.lean"),
            "Pkg.Common.Extra": LeanModule(name="Pkg.Common.Extra", path="Pkg/Common/Extra.lean"),
            "Pkg.Common.More": LeanModule(name="Pkg.Common.More", path="Pkg/Common/More.lean"),
            "Pkg.Common.Other": LeanModule(name="Pkg.Common.Other", path="Pkg/Common/Other.lean"),
            "Pkg.Common.Last": LeanModule(name="Pkg.Common.Last", path="Pkg/Common/Last.lean"),
        }
    )
    architecture_policy = summarize_architecture_policy(
        module_dag,
        {
            "groups": {
                "alpha": ["Pkg.Alpha.*"],
                "beta": ["Pkg.Beta.*"],
            },
            "rules": [
                {
                    "id": "peer-boundary",
                    "kind": "forbid_imports",
                    "from": ["alpha", "beta"],
                    "to": ["alpha", "beta"],
                    "suggestCommonDependencies": True,
                    "sharedDependencyMode": "all_multi_group_imports",
                }
            ],
        },
    )
    source_patterns = summarize_source_patterns(
        [SourceDocument(module="Pkg.Alpha.Owner", path="Pkg/Alpha/Owner.lean", text="DeprecatedLocalTerm\n")],
        {"patterns": [{"id": "deprecated-term", "pattern": "DeprecatedLocalTerm"}]},
    )
    claim_authority = audit_claim_authority(
        [
            {
                "claimId": "claim.closed",
                "claimedStatus": "lean_closed",
                "claimedAuthority": "lean_proved",
                "requiredEvidenceAuthorities": {"finiteWindow": "imported_interval_certified"},
            }
        ],
        joins=[],
        surfaces=[],
    )
    payload = {
        "architecture_policy": architecture_policy,
        "source_patterns": source_patterns,
        "claim_authority": claim_authority,
        "module_dag": module_dag,
    }

    rows = evaluate_oracles(
        payload,
        [
            {
                "fixture": "peer-boundary",
                "signal": "architecture_pair_count",
                "sourceGroup": "alpha",
                "targetGroup": "beta",
                "expected": 1,
            },
            {
                "fixture": "common-layer",
                "signal": "shared_dependency_candidate",
                "targetModule": "Pkg.Common.Foundation",
                "expected": True,
            },
            {
                "fixture": "source-pattern",
                "signal": "source_pattern_match_count",
                "patternId": "deprecated-term",
                "expected": 1,
            },
            {
                "fixture": "claim-authority",
                "signal": "claim_authority_diagnostic_present",
                "ruleId": "ladon.claim.closed_with_imported_evidence",
                "expected": True,
            },
            {
                "fixture": "facade-subtype",
                "signal": "facade_subtype_count",
                "subtype": "mixed_barrel_and_theorems",
                "expected": 1,
            },
            {
                "fixture": "generated-duplicate",
                "signal": "generated_duplicate_family",
                "generatorFamily": "GeneratedRoute",
                "target": "Pkg.Common.Foundation",
                "duplicateModuleCount": 1,
            },
        ],
    )

    assert all(row.passed for row in rows)


def test_benchmark_fixture_sources_are_portable() -> None:
    expected = [
        FIXTURE_ROOT / "lean" / "Bench" / "DuplicateBasename.lean",
        FIXTURE_ROOT / "lean" / "Bench" / "ReferenceNoise.lean",
        FIXTURE_ROOT / "lean" / "Bench" / "ProofFamilies.lean",
        FIXTURE_ROOT / "module_dag" / "Bench.lean",
        FIXTURE_ROOT / "packet_evidence" / "review_packet" / "manifest.json",
    ]

    assert all(path.is_file() for path in expected)


def test_oracle_schema_and_optional_smoke_roots_are_explicit(tmp_path: Path) -> None:
    existing = tmp_path / "quux"
    existing.mkdir()
    candidates = {
        "quux": str(existing),
        "matrix-factorization": str(tmp_path / "missing-mf"),
    }

    schema = oracle_schema()
    roots = existing_optional_smoke_roots(candidates)

    assert schema["schema"] == "ladon-benchmark-oracle-v1"
    assert "resolved_edge" in schema["supported_signals"]
    assert "architecture_pair_count" in schema["supported_signals"]
    assert "source_pattern_match_count" in schema["supported_signals"]
    assert roots == {"quux": str(existing)}
