from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

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
from ladon.benchmark_contract import (
    BenchmarkContractError,
    load_benchmark_manifest,
    load_benchmark_manifest_schema,
    promotion_readiness,
    validate_manifest_contract,
)
from ladon.benchmark_control_oracles import evaluate_control_labels
from ladon.benchmark_metrics import (
    classification_metrics,
    extraction_coverage,
    known_case_recall,
)
from ladon.ir import LeanDeclaration, LeanImport, LeanModule


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "benchmark_oracles"
HARNESS_ROOT = Path(__file__).parent / "fixtures" / "benchmark_harness"
CLAIM_AUTHORITY_ROOT = Path(__file__).parent / "fixtures" / "claim_authority"


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
                "class": "boundary",
                "signal": "unresolved_class",
                "candidate": "count",
                "expected": "local_or_field_candidate",
            },
            {
                "fixture": "reference-noise",
                "class": "intentional_negative",
                "signal": "unresolved_class",
                "candidate": "Fin",
                "expected": "external_candidate",
            },
            {
                "fixture": "reference-noise",
                "class": "positive",
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
    claim_fixture = json.loads(
        (CLAIM_AUTHORITY_ROOT / "routes.json").read_text(encoding="utf-8")
    )
    claim_authority = audit_claim_authority(
        claim_fixture["claims"],
        joins=claim_fixture["joins"],
        surfaces=claim_fixture["surfaces"],
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
                "class": "positive",
                "signal": "architecture_pair_count",
                "sourceGroup": "alpha",
                "targetGroup": "beta",
                "expected": 1,
            },
            {
                "fixture": "peer-boundary-absent",
                "class": "intentional_negative",
                "signal": "architecture_pair_count",
                "sourceGroup": "beta",
                "targetGroup": "alpha",
                "expected": 0,
            },
            {
                "fixture": "peer-boundary-exact",
                "class": "boundary",
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
                "class": "positive",
                "signal": "source_pattern_match_count",
                "patternId": "deprecated-term",
                "expected": 1,
            },
            {
                "fixture": "source-pattern-absent",
                "class": "intentional_negative",
                "signal": "source_pattern_match_count",
                "patternId": "unconfigured-term",
                "expected": 0,
            },
            {
                "fixture": "source-pattern-exact",
                "class": "boundary",
                "signal": "source_pattern_match_count",
                "patternId": "deprecated-term",
                "expected": 1,
            },
            {
                "fixture": "claim-authority",
                "class": "positive",
                "signal": "claim_authority_diagnostic_present",
                "ruleId": "ladon.claim.closed_with_imported_evidence",
                "expected": True,
            },
            {
                "fixture": "claim-authority-scoped-negative",
                "class": "intentional_negative",
                "signal": "claim_authority_diagnostic_present",
                "ruleId": "ladon.claim.honest_route_overclaim",
                "expected": False,
            },
            {
                "fixture": "claim-authority-scope-boundary",
                "class": "boundary",
                "signal": "claim_authority_diagnostic_present",
                "ruleId": "ladon.claim.endpoint_scope_overclaim",
                "expected": True,
            },
            {
                "fixture": "facade-subtype",
                "class": "positive",
                "signal": "facade_subtype_count",
                "subtype": "mixed_barrel_and_theorems",
                "expected": 1,
            },
            {
                "fixture": "facade-subtype-absent",
                "class": "intentional_negative",
                "signal": "facade_subtype_count",
                "subtype": "public_root_facade",
                "expected": 0,
            },
            {
                "fixture": "facade-subtype-exact",
                "class": "boundary",
                "signal": "facade_subtype_count",
                "subtype": "mixed_barrel_and_theorems",
                "expected": 1,
            },
            {
                "fixture": "generated-duplicate",
                "class": "positive",
                "signal": "generated_duplicate_family",
                "generatorFamily": "GeneratedRoute",
                "target": "Pkg.Common.Foundation",
                "duplicateModuleCount": 1,
            },
            {
                "fixture": "generated-duplicate-absent",
                "class": "intentional_negative",
                "signal": "generated_duplicate_family",
                "generatorFamily": "OtherGenerator",
                "target": "Pkg.Common.Foundation",
                "expected": False,
            },
            {
                "fixture": "generated-duplicate-exact",
                "class": "boundary",
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


def test_versioned_benchmark_manifest_validates_and_uses_ordinary_cli() -> None:
    manifest = load_benchmark_manifest(HARNESS_ROOT / "manifest-v1.json")
    schema = load_benchmark_manifest_schema()

    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(manifest)
    required = [case for case in manifest["cases"] if case["required"]]
    assert required
    assert all(case["command"][0] == "ladon" for case in required)
    assert all(case["reportVersion"] == "ladon-report-v2" for case in required)
    labels = [
        label
        for case in required
        for label in case["labels"]
    ]
    readiness = promotion_readiness([*labels, *manifest["controlLabels"]])
    assert readiness
    assert all(row["ready"] for row in readiness)


def test_elaborated_oracles_keep_parser_and_lean_authorities_separate() -> None:
    payload = {
        "declaration_graph": {
            "declarations": [
                {
                    "declaration": "Pkg.root",
                    "kind": "theorem",
                    "surface": {
                        "status": "complete",
                        "renderedType": "True",
                    },
                    "parserCandidates": {
                        "items": ["ParserOnly"],
                        "authority": "lean_parser",
                    },
                    "typeDependencies": {
                        "items": ["True"],
                        "authority": "lean_environment",
                    },
                    "valueDependencies": {
                        "items": ["Pkg.helper"],
                        "authority": "lean_environment",
                    },
                }
            ]
        }
    }
    rows = evaluate_oracles(
        payload,
        [
            {
                "fixture": "elaborated",
                "signal": "declaration_required_fields",
                "declaration": "Pkg.root",
                "requiredFields": ["surface.renderedType"],
                "expectedFields": {
                    "kind": "theorem",
                    "surface.status": "complete",
                },
                "expected": True,
            },
            {
                "fixture": "elaborated",
                "signal": "direct_dependency",
                "declaration": "Pkg.root",
                "dependencyKind": "value",
                "target": "ParserOnly",
                "authority": "lean_environment",
                "expected": False,
            },
        ],
    )

    assert all(row.passed for row in rows)
    assert rows[1].observed["parserCandidateOnly"] is True


def test_control_labels_evaluate_separate_machine_families() -> None:
    results = {
        "cases": [
            {
                "cache": {"applicable": True, "warmHit": True},
                "process": {"helperLaunchesWarm": 0},
                "stability": {
                    "schemaValid": True,
                    "normalizedBytesEqual": True,
                    "sizeBudgetsPassed": True,
                },
            }
        ],
        "runtimeControls": {
            "cacheInvalidation": [
                {
                    "input": "source",
                    "observedReason": "source_changed",
                }
            ],
            "timeout": {
                "partialReportPresent": True,
                "orphanPresent": False,
                "passed": True,
            },
            "cancellation": {"passed": True},
        },
    }
    labels = [
        {
            "id": "cache.source",
            "class": "boundary",
            "metricFamily": "cache",
            "signalKind": "cache_invalidation",
            "rationale": "fixture",
            "oracle": {
                "signal": "cache_invalidation_reasons",
                "expected": {"source": "source_changed"},
            },
        },
        {
            "id": "process.cleanup",
            "class": "boundary",
            "metricFamily": "process",
            "signalKind": "timeout_control",
            "rationale": "fixture",
            "oracle": {
                "signal": "process_cleanup_passed",
                "expected": True,
            },
        },
    ]

    assert all(row["passed"] for row in evaluate_control_labels(results, labels))


def test_benchmark_script_rejects_missing_candidate_before_measurement() -> None:
    script = Path(__file__).parents[1] / "scripts" / "ladon_benchmarks.py"

    result = subprocess.run(
        [sys.executable, str(script), "--required"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "--candidate" in result.stderr


def test_benchmark_stdout_is_machine_json_when_output_is_omitted(
    capsys,
    monkeypatch,
) -> None:
    module = load_benchmark_script(monkeypatch)
    results = benchmark_summary_fixture()

    module.emit_results(results, None)

    captured = capsys.readouterr()
    assert json.loads(captured.out) == results
    assert captured.err.startswith("benchmark summary:")


def test_benchmark_main_routes_gate_logs_away_from_json_stdout(
    capsys,
    monkeypatch,
) -> None:
    module = load_benchmark_script(monkeypatch)
    results = benchmark_summary_fixture()

    def fake_run_benchmarks(_candidate, *, required):
        assert required is True
        print("gate progress")
        return results

    monkeypatch.setattr(module, "run_benchmarks", fake_run_benchmarks)

    assert module.main(["--candidate", "worktree", "--required"]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == results
    assert "gate progress" in captured.err
    assert "benchmark summary:" in captured.err


def benchmark_summary_fixture() -> dict:
    """Return the smallest result accepted by the compact renderer."""

    return {
        "metricFamilies": {
            "correctness": {"failedOracleCount": 0},
            "coverage": {"hitCount": 1, "expectedCount": 1},
            "runtime": {
                "maxColdWallSeconds": 0.1,
                "maxWarmWallSeconds": 0.05,
            },
            "memory": {"maxPeakRssMiB": 12.5},
            "cache": {"warmHitCount": 1},
            "stability": {"failedCaseCount": 0},
        }
    }


def load_benchmark_script(monkeypatch):
    """Load the script with its sibling helper modules importable."""

    script = Path(__file__).parents[1] / "scripts" / "ladon_benchmarks.py"
    monkeypatch.syspath_prepend(str(script.parent))
    spec = importlib.util.spec_from_file_location("ladon_benchmarks", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_required_manifest_rejects_local_sibling_and_caller_specific_paths() -> None:
    manifest = load_benchmark_manifest(HARNESS_ROOT / "manifest-v1.json")
    broken = {**manifest, "cases": [{**manifest["cases"][0]}]}

    broken["cases"][0]["command"] = [
        "ladon",
        "--repo-root",
        "../quux",
        "--root",
        "Quux",
    ]
    with pytest.raises(BenchmarkContractError, match="nonportable"):
        validate_manifest_contract(broken)

    broken["cases"][0]["command"] = [
        "ladon",
        "--repo-root",
        "{fixture}",
        "--llm",
    ]
    with pytest.raises(BenchmarkContractError, match="caller-specific"):
        validate_manifest_contract(broken)


def test_metrics_keep_per_kind_confusion_and_coverage_families_separate() -> None:
    labels = [
        {
            "signalKind": "missing_import",
            "expectedOutcome": "present",
        },
        {
            "signalKind": "missing_import",
            "expectedOutcome": "absent",
        },
        {
            "signalKind": "facade",
            "expectedOutcome": "present",
        },
    ]

    metrics = classification_metrics(labels, [True, False, False])

    assert metrics["missing_import"] == {
        "truePositive": 1,
        "falsePositive": 1,
        "falseNegative": 0,
        "trueNegative": 0,
        "precision": 0.5,
        "recall": 1.0,
    }
    assert metrics["facade"]["falseNegative"] == 1
    assert known_case_recall(["Pkg.Missing"], ["Pkg.Missing"])["recall"] == 1.0
    coverage = extraction_coverage(
        {"type": ["A.Type"], "value": ["A.value"]},
        {"type": ["A.Type"], "value": []},
    )
    assert coverage["byKind"]["type"]["recall"] == 1.0
    assert coverage["byKind"]["value"]["recall"] == 0.0
    assert coverage["coverage"] == 0.5


def test_promotion_readiness_requires_positive_negative_and_boundary() -> None:
    rows = promotion_readiness(
        [
            {"promotionFamily": "fan_in", "class": "positive"},
            {"promotionFamily": "fan_in", "class": "intentional_negative"},
            {"promotionFamily": "fan_in", "class": "boundary"},
            {"promotionFamily": "namespace", "class": "positive"},
        ]
    )

    assert rows[0]["ready"] is True
    assert rows[1]["ready"] is False
    assert rows[1]["missingClasses"] == ["boundary", "intentional_negative"]
