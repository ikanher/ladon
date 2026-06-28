from __future__ import annotations

from ladon.analysis.architecture_policy import summarize_architecture_policy


DIRECT_MODULE_DAG = {
    "edges": {
        "Pkg.Alpha.Owner": ["Pkg.Beta.Core", "Pkg.Common.Base"],
        "Pkg.Beta.Core": ["Pkg.Common.Base"],
        "Pkg.Common.Base": [],
    },
    "import_sites": {
        "Pkg.Alpha.Owner": {
            "Pkg.Beta.Core": {
                "sourcePath": "Pkg/Alpha/Owner.lean",
                "line": 7,
                "importText": "import Pkg.Beta.Core",
            }
        }
    },
}

PEER_POLICY = {
    "id": "peer-boundaries",
    "groups": {
        "alpha": ["Pkg.Alpha.*"],
        "beta": ["Pkg.Beta.*"],
    },
    "rules": [
        {
            "id": "peers-do-not-import-each-other",
            "kind": "forbid_imports",
            "from": ["alpha", "beta"],
            "to": ["alpha", "beta"],
        }
    ],
}


def test_architecture_policy_flags_direct_peer_imports_from_globs() -> None:
    report = summarize_architecture_policy(DIRECT_MODULE_DAG, PEER_POLICY)

    assert report["policyId"] == "peer-boundaries"
    assert report["groupMembershipCounts"] == {"alpha": 1, "beta": 1}
    assert [row["kind"] for row in report["findings"]] == [
        "architecture_policy.direct_forbidden_import"
    ]


def test_architecture_policy_records_direct_group_pair() -> None:
    report = summarize_architecture_policy(DIRECT_MODULE_DAG, PEER_POLICY)
    finding = report["findings"][0]

    assert finding["sourceGroup"] == "alpha"
    assert finding["targetGroup"] == "beta"
    assert finding["sourceModule"] == "Pkg.Alpha.Owner"
    assert finding["targetModule"] == "Pkg.Beta.Core"


def test_architecture_policy_records_import_source_location() -> None:
    report = summarize_architecture_policy(DIRECT_MODULE_DAG, PEER_POLICY)
    finding = report["findings"][0]

    assert finding["sourcePath"] == "Pkg/Alpha/Owner.lean"
    assert finding["line"] == 7
    assert finding["importText"] == "import Pkg.Beta.Core"


def test_architecture_policy_reports_direct_pair_summary() -> None:
    report = summarize_architecture_policy(DIRECT_MODULE_DAG, PEER_POLICY)

    assert report["directPairSummary"] == [
        {
            "sourceGroup": "alpha",
            "targetGroup": "beta",
            "uniqueDirectEdgeCount": 1,
            "sampleEdges": [
                {
                    "sourceModule": "Pkg.Alpha.Owner",
                    "targetModule": "Pkg.Beta.Core",
                }
            ],
        }
    ]


def test_architecture_policy_classifies_direct_findings_with_context_tokens() -> None:
    module_dag = {
        "edges": {
            "Pkg.Alpha.Owner": ["Pkg.Beta.Core"],
            "Pkg.Alpha.OwnerBridge": ["Pkg.Beta.Core"],
            "Pkg.Beta.Core": [],
        },
        "module_metadata": {
            "Pkg.Alpha.Owner": {"roles": []},
            "Pkg.Alpha.OwnerBridge": {"roles": []},
            "Pkg.Beta.Core": {"roles": []},
        },
    }

    report = summarize_architecture_policy(module_dag, PEER_POLICY)
    by_subject = {row["subject"]: row for row in report["findings"]}

    assert by_subject["Pkg.Alpha.Owner -> Pkg.Beta.Core"]["policyContext"] == "core-looking"
    assert by_subject["Pkg.Alpha.OwnerBridge -> Pkg.Beta.Core"]["policyContext"] == "bridge-ish"
    assert report["directContextSummary"] == [
        {"policyContext": "bridge-ish", "count": 1, "triageSeverities": ["warning"]},
        {"policyContext": "core-looking", "count": 1, "triageSeverities": ["warning"]},
    ]


def test_architecture_policy_classifies_facade_context_from_module_metadata() -> None:
    module_dag = {
        "edges": {
            "Pkg.Alpha.Facade": ["Pkg.Beta.Core"],
            "Pkg.Beta.Core": [],
        },
        "module_metadata": {
            "Pkg.Alpha.Facade": {"roles": ["facade", "pure_barrel"]},
            "Pkg.Beta.Core": {"roles": []},
        },
    }

    report = summarize_architecture_policy(module_dag, PEER_POLICY)
    finding = report["findings"][0]

    assert finding["policyContext"] == "facade-ish"
    assert finding["triageSeverity"] == "warning"
    assert "public aggregation" in finding["suggestedAction"]


def test_architecture_policy_reports_top_offending_files() -> None:
    report = summarize_architecture_policy(DIRECT_MODULE_DAG, PEER_POLICY)

    assert report["directOffendingFileSummary"] == [
        {
            "sourcePath": "Pkg/Alpha/Owner.lean",
            "sourceModule": "Pkg.Alpha.Owner",
            "uniqueDirectEdgeCount": 1,
            "groupPairs": [
                {"sourceGroup": "alpha", "targetGroup": "beta"}
            ],
            "sampleImports": [
                {
                    "line": 7,
                    "importText": "import Pkg.Beta.Core",
                    "targetModule": "Pkg.Beta.Core",
                    "sourceGroup": "alpha",
                    "targetGroup": "beta",
                    "policyContext": "core-looking",
                }
            ],
            "summaryKey": "Pkg/Alpha/Owner.lean",
        }
    ]


def test_architecture_policy_flags_transitive_paths_when_requested() -> None:
    module_dag = {
        "edges": {
            "Pkg.Alpha.Owner": ["Pkg.Common.Adapter"],
            "Pkg.Common.Adapter": ["Pkg.Beta.Core"],
            "Pkg.Beta.Core": [],
        }
    }
    policy = {
        "groups": {
            "alpha": {"patterns": ["Pkg.Alpha.*"]},
            "beta": {"patterns": ["Pkg.Beta.*"]},
        },
        "rules": [
            {
                "id": "no-alpha-to-beta-reachability",
                "kind": "forbid_imports",
                "fromGroups": ["alpha"],
                "toGroups": ["beta"],
                "includeTransitive": True,
            }
        ],
    }

    report = summarize_architecture_policy(module_dag, policy)

    assert [row["kind"] for row in report["findings"]] == [
        "architecture_policy.transitive_forbidden_import"
    ]
    assert report["findings"][0]["path"] == [
        "Pkg.Alpha.Owner",
        "Pkg.Common.Adapter",
        "Pkg.Beta.Core",
    ]


def test_architecture_policy_transitive_rule_does_not_duplicate_direct_findings() -> None:
    module_dag = {
        "edges": {
            "Pkg.Alpha.Owner": ["Pkg.Beta.Core"],
            "Pkg.Beta.Core": [],
        }
    }
    policy = {
        "groups": {
            "alpha": ["Pkg.Alpha.*"],
            "beta": ["Pkg.Beta.*"],
        },
        "rules": [
            {
                "id": "direct-rule",
                "kind": "forbid_direct_imports",
                "from": ["alpha"],
                "to": ["beta"],
            },
            {
                "id": "transitive-rule",
                "kind": "forbid_transitive_imports",
                "from": ["alpha"],
                "to": ["beta"],
            },
        ],
    }

    report = summarize_architecture_policy(module_dag, policy)

    assert [row["kind"] for row in report["findings"]] == [
        "architecture_policy.direct_forbidden_import"
    ]


def test_architecture_policy_rule_ignores_configured_sources_and_targets() -> None:
    module_dag = {
        "edges": {
            "Pkg.Alpha.Owner": ["Pkg.Beta.Core"],
            "Pkg.Alpha.IntegrationBridge": ["Pkg.Beta.Core"],
            "Pkg.Beta.Core": [],
        }
    }
    policy = {
        "groups": {
            "alpha": ["Pkg.Alpha.*"],
            "beta": ["Pkg.Beta.*"],
        },
        "rules": [
            {
                "id": "peer-rule",
                "kind": "forbid_direct_imports",
                "from": ["alpha"],
                "to": ["beta"],
                "ignoreSource": ["Pkg.Alpha.*Bridge"],
            }
        ],
    }

    report = summarize_architecture_policy(module_dag, policy)

    assert len(report["findings"]) == 1
    assert report["findings"][0]["sourceModule"] == "Pkg.Alpha.Owner"


def test_architecture_policy_can_suggest_shared_dependency_candidates() -> None:
    module_dag = {
        "edges": {
            "Pkg.Alpha.Owner": ["Pkg.Beta.Shared"],
            "Pkg.Alpha.Other": ["Pkg.Beta.Shared"],
            "Pkg.Gamma.Owner": ["Pkg.Beta.Shared"],
            "Pkg.Beta.Shared": [],
        }
    }
    policy = {
        "groups": {
            "alpha": ["Pkg.Alpha.*"],
            "beta": ["Pkg.Beta.*"],
            "gamma": ["Pkg.Gamma.*"],
        },
        "rules": [
            {
                "id": "peer-rule",
                "kind": "forbid_imports",
                "from": ["alpha", "beta", "gamma"],
                "to": ["alpha", "beta", "gamma"],
                "suggestCommonDependencies": True,
            }
        ],
    }

    report = summarize_architecture_policy(module_dag, policy)
    by_kind = {row["kind"]: row for row in report["findings"]}

    assert by_kind["architecture_policy.shared_dependency_candidate"]["targetModule"] == "Pkg.Beta.Shared"
    assert by_kind["architecture_policy.shared_dependency_candidate"]["sourceGroups"] == [
        "alpha",
        "gamma",
    ]
    assert by_kind["architecture_policy.shared_dependency_candidate"]["importerCount"] == 3
    assert by_kind["architecture_policy.shared_dependency_candidate"]["confidence"] == "medium"
    assert report["sharedDependencySummary"][0]["targetModule"] == "Pkg.Beta.Shared"
    assert report["sharedDependencySummary"][0]["confidence"] == "medium"
    assert report["sharedDependencySummary"][0]["dependencyScope"] == "policy_targets"


def test_architecture_policy_can_scan_all_multi_group_imports_for_common_layers() -> None:
    module_dag = {
        "edges": {
            "Pkg.Alpha.Owner": ["Pkg.Common.Kernel", "Pkg.Beta.Shared"],
            "Pkg.Beta.Owner": ["Pkg.Common.Kernel"],
            "Pkg.Gamma.Owner": ["Pkg.Common.Kernel"],
            "Pkg.Common.Kernel": [],
            "Pkg.Beta.Shared": [],
        }
    }
    policy = {
        "groups": {
            "alpha": ["Pkg.Alpha.*"],
            "beta": ["Pkg.Beta.*"],
            "gamma": ["Pkg.Gamma.*"],
        },
        "rules": [
            {
                "id": "all-common-layer-candidates",
                "kind": "forbid_imports",
                "from": ["alpha", "beta", "gamma"],
                "to": ["alpha", "beta", "gamma"],
                "suggestCommonDependencies": True,
                "sharedDependencyMode": "all_multi_group_imports",
            }
        ],
    }

    report = summarize_architecture_policy(module_dag, policy)
    common = report["sharedDependencySummary"][0]

    assert common["targetModule"] == "Pkg.Common.Kernel"
    assert common["sourceGroups"] == ["alpha", "beta", "gamma"]
    assert common["dependencyScope"] == "all_multi_group_imports"
    assert common["confidence"] == "high"


def test_architecture_policy_common_layer_scan_respects_ignored_foundations() -> None:
    module_dag = {
        "edges": {
            "Pkg.Alpha.Owner": ["Pkg.Common.Foundation"],
            "Pkg.Beta.Owner": ["Pkg.Common.Foundation"],
            "Pkg.Common.Foundation": [],
        }
    }
    policy = {
        "groups": {
            "alpha": ["Pkg.Alpha.*"],
            "beta": ["Pkg.Beta.*"],
        },
        "rules": [
            {
                "id": "common-layer-candidates",
                "kind": "forbid_imports",
                "from": ["alpha", "beta"],
                "to": ["alpha", "beta"],
                "suggestCommonDependencies": True,
                "sharedDependencyMode": "all_multi_group_imports",
                "ignoreTarget": ["Pkg.Common.*"],
            }
        ],
    }

    report = summarize_architecture_policy(module_dag, policy)

    assert report["sharedDependencySummary"] == []
    assert not any(
        row["kind"] == "architecture_policy.shared_dependency_candidate"
        for row in report["findings"]
    )


def test_architecture_policy_skipped_report_suggests_draft_prefix_policy() -> None:
    from ladon.analysis.architecture_policy import skipped_architecture_policy_report

    module_dag = {
        "edges": {
            "Pkg.AlphaCoreOne": ["Pkg.BetaCoreOne"],
            "Pkg.AlphaCoreTwo": ["Pkg.Common"],
            "Pkg.AlphaCoreThree": [],
            "Pkg.BetaCoreOne": [],
            "Pkg.BetaCoreTwo": [],
            "Pkg.BetaCoreThree": [],
            "Pkg.Common": [],
        }
    }

    report = skipped_architecture_policy_report(module_dag, searched_paths=["/repo/.ladon/architecture-policy.json"])

    assert report["status"] == "skipped_no_policy"
    assert report["findings"][0]["kind"] == "architecture_policy.skipped_no_policy"
    assert report["draftPolicySuggestions"]
