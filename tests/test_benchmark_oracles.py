from __future__ import annotations

from pathlib import Path

from ladon.analysis.benchmark_oracles import (
    evaluate_oracles,
    existing_optional_smoke_roots,
    oracle_schema,
)
from ladon.analysis.declaration_graph import summarize_declaration_graph
from ladon.analysis.findings import summarize_findings
from ladon.analysis.module_dag import summarize_module_dag
from ladon.analysis.proof_family_similarity import proof_family_similarity_candidates
from ladon.analysis.witness_packet import summarize_packet_evidence
from ladon.ir import LeanDeclaration, LeanModule


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
    assert roots == {"quux": str(existing)}
