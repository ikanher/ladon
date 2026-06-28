from __future__ import annotations

from ladon.render import render_text


def test_text_report_groups_module_dag_details() -> None:
    payload = {
        "metadata": {"repo_root": "/repo", "analysis_root_module": "A"},
        "warnings": [],
        "module_dag": {
            "module_count": 3,
            "edge_count": 2,
            "acyclic": True,
            "topological_layer_count": 2,
            "facade_module_count": 1,
            "top_fan_in": [{"module": "A.Core", "fan_in": 2}],
            "top_fan_out": [{"module": "A.Root", "fan_out": 2}],
            "top_facade_fan_out": [{"module": "A.Facade", "fan_out": 3}],
            "top_implementation_fan_out": [{"module": "A.Owner", "fan_out": 1}],
            "facade_modules": ["A.Facade"],
            "source_modules_not_reachable_from_chosen_roots": ["A.Orphan"],
            "source_modules_not_reachable_from_chosen_roots_count": 1,
            "root_direct_import_closures": [
                {
                    "root": "A.Root",
                    "direct_import": "A.Core",
                    "reachable_module_count": 4,
                }
            ],
        },
        "findings": [],
        "pipeline": {"timings": {}},
    }

    text = render_text(payload)

    assert "Top Module Fan-In\n- A.Core: 2" in text
    assert "Top Module Fan-Out\n- A.Root: 2" in text
    assert "Top Facade/Barrel Module Fan-Out\n- A.Facade: 3" in text
    assert "Top Implementation Module Fan-Out\n- A.Owner: 1" in text
    assert "Root Direct Import Closures\n- A.Root -> A.Core: 4" in text
    assert "Facade Modules\n- A.Facade" in text
    assert "Modules Not Reachable From Chosen Roots\n- count: 1\n- A.Orphan" in text


def test_text_report_summarizes_policy_details_without_listing_every_policy_finding() -> None:
    payload = {
        "metadata": {"repo_root": "/repo", "analysis_root_module": "A"},
        "warnings": [],
        "module_dag": {
            "module_count": 2,
            "edge_count": 1,
            "acyclic": True,
            "topological_layer_count": 1,
            "facade_module_count": 0,
            "top_fan_in": [],
            "top_fan_out": [],
        },
        "architecture_policy": {
            "policyId": "peer-policy",
            "groupCount": 2,
            "ruleCount": 1,
            "summary": {"architecture_policy.direct_forbidden_import": 1},
            "directPairSummary": [
                {
                    "sourceGroup": "alpha",
                    "targetGroup": "beta",
                    "uniqueDirectEdgeCount": 1,
                }
            ],
            "directOffendingFileSummary": [
                {
                    "sourcePath": "A/Owner.lean",
                    "uniqueDirectEdgeCount": 1,
                    "sampleImports": [
                        {"line": 3, "importText": "import B.Core"}
                    ],
                }
            ],
            "sharedDependencySummary": [
                {
                    "targetModule": "A.Shared",
                    "confidence": "medium",
                    "dependencyScope": "all_multi_group_imports",
                    "sourceGroups": ["alpha", "beta"],
                    "importerCount": 3,
                }
            ],
        },
        "findings": [
            {
                "kind": "architecture_policy.direct_forbidden_import",
                "severity": "warning",
                "subject": "A.Owner -> B.Core",
                "count": 1,
                "message": "detail row should stay in JSON only",
            }
        ],
        "pipeline": {"timings": {}},
    }

    text = render_text(payload)

    assert "- pair alpha -> beta: 1" in text
    assert "- file A/Owner.lean: 1 direct violations sample line:3 import B.Core" in text
    assert (
        "- common-layer candidate A.Shared: confidence=medium "
        "scope=all_multi_group_imports groups=alpha,beta importers=3"
    ) in text
    assert "detail row should stay in JSON only" not in text


def test_text_report_summarizes_source_pattern_details_without_duplicate_findings() -> None:
    payload = {
        "metadata": {"repo_root": "/repo", "analysis_root_module": "A"},
        "warnings": [],
        "module_dag": {
            "module_count": 1,
            "edge_count": 0,
            "acyclic": True,
            "topological_layer_count": 1,
            "facade_module_count": 0,
            "top_fan_in": [],
            "top_fan_out": [],
        },
        "source_patterns": {
            "policyId": "source-policy",
            "patternCount": 1,
            "matchCount": 1,
            "diagnostics": [],
            "patternSummary": [
                {
                    "patternId": "legacy-name",
                    "matchCount": 1,
                    "kind": "stale_term",
                    "severity": "warning",
                }
            ],
            "matches": [
                {
                    "path": "A/Owner.lean",
                    "line": 7,
                    "patternId": "legacy-name",
                    "generated": False,
                }
            ],
        },
        "findings": [
            {
                "kind": "source_pattern.match",
                "severity": "warning",
                "subject": "A/Owner.lean:7",
                "message": "detail row should stay in source pattern section",
            }
        ],
        "pipeline": {"timings": {}},
    }

    text = render_text(payload)

    assert "Source Patterns" in text
    assert "- policy: source-policy" in text
    assert "- pattern legacy-name: 1 kind=stale_term severity=warning" in text
    assert "- A/Owner.lean:7 legacy-name generated=False" in text
    assert "detail row should stay in source pattern section" not in text


def test_text_report_renders_module_naming_smells_and_generated_families() -> None:
    payload = {
        "metadata": {"repo_root": "/repo", "analysis_root_module": "A"},
        "warnings": [],
        "module_dag": {
            "module_count": 1,
            "edge_count": 0,
            "acyclic": True,
            "topological_layer_count": 1,
            "facade_module_count": 0,
            "top_fan_in": [],
            "top_fan_out": [],
            "module_name_smell_summary": {
                "generated_encoded_parameters": 1,
                "long_segment": 1,
            },
            "module_name_smells": [
                {
                    "module": "A.GeneratedScalarBw2Eps0p5Gamma0p8.Base",
                    "generated": True,
                    "reasonKinds": ["generated_encoded_parameters", "long_segment"],
                    "suggestedAction": "move generated parameters into a manifest",
                }
            ],
            "generated_family_summary": [
                {
                    "generatorFamily": "GeneratedScalarBw2Eps0p5Gamma0p8",
                    "moduleCount": 3,
                    "maxPathDepth": 4,
                    "reasonSummary": {"generated_encoded_parameters": 3},
                }
            ],
        },
        "findings": [],
        "pipeline": {"timings": {}},
    }

    text = render_text(payload)

    assert "Module Naming Smells" in text
    assert "- generated_encoded_parameters: 1" in text
    assert "- A.GeneratedScalarBw2Eps0p5Gamma0p8.Base: generated=True" in text
    assert "Generated Families" in text
    assert "- GeneratedScalarBw2Eps0p5Gamma0p8: 3 modules maxDepth=4" in text


def test_text_report_renders_unresolved_reference_classifications() -> None:
    payload = {
        "metadata": {"repo_root": "/repo", "analysis_root_module": "A"},
        "warnings": [],
        "module_dag": {
            "module_count": 1,
            "edge_count": 0,
            "acyclic": True,
            "topological_layer_count": 1,
            "facade_module_count": 0,
            "top_fan_in": [],
            "top_fan_out": [],
        },
        "findings": [],
        "declaration_graph": {
            "declaration_count": 1,
            "edge_count": 0,
            "declarations": [
                {
                    "declaration": "A.x_ge_one",
                    "module": "A",
                    "sourceRange": {"startLine": 1, "endLine": 3},
                    "contentHash": "sha256:a",
                    "confidence": "parser_source_range",
                }
            ],
            "unresolved_reference_count": 2,
            "declaration_name_families": [
                {
                    "suffix": "ge_one",
                    "count": 3,
                    "sample_declarations": ["A.x_ge_one", "A.y_ge_one"],
                }
            ],
            "unresolved_reference_classes": [
                {"classification": "local_or_field_candidate", "count": 9},
                {"classification": "actionable_unknown", "count": 2},
            ],
            "top_unresolved_references": [
                {
                    "candidate": "count",
                    "classification": "local_or_field_candidate",
                    "count": 9,
                }
            ],
            "top_actionable_unresolved_references": [
                {
                    "candidate": "MissingTheorem",
                    "classification": "actionable_unknown",
                    "count": 2,
                }
            ],
        },
        "pipeline": {"timings": {}},
    }

    text = render_text(payload)

    assert "Top Unresolved References\n- count: 9 (local_or_field_candidate)" in text
    assert "Declaration Evidence\n- rows: 1\n- source ranges: 1\n- content hashes: 1" in text
    assert "- trust: source evidence is attachment confidence, not proof truth" in text
    assert "Declaration Name Families\n- ge_one: 3" in text
    assert "Unresolved Reference Classes\n- local_or_field_candidate: 9" in text
    assert "Top Actionable Unresolved References\n- MissingTheorem: 2" in text
