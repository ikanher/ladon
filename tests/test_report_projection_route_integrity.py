from __future__ import annotations

from typing import Any

import pytest

from ladon.finding_evidence import resolve_local_json_pointer
from ladon.report_projection import project_sections
from ladon.report_projection_evidence_closure import EvidenceClosure

GENERATED_BASE = "#/sections/module_dag/generated_family_candidates"


def test_architecture_routes_follow_reordered_finding_owners() -> None:
    findings = [
        _architecture_finding("finding-z", severity="info"),
        _architecture_finding("finding-b", severity="warning"),
        _architecture_finding("finding-a", severity="info"),
    ]
    producers = {
        f"{finding['id']}.review": _architecture_producer(finding, index)
        for index, finding in enumerate(findings)
    }
    signals = [
        {
            **producers[f"{finding['id']}.review"],
            "severity": finding["severity"],
            "status": finding["status"],
            "population": finding["population"],
            "role": finding["role"],
        }
        for finding in findings
    ]
    sections = {
        "findings": findings,
        "module_dag": {
            "architectureProducerRegistrations": {"producers": producers},
        },
        "review_regions": [
            _review_region(
                "architecture-region",
                "architecture_integrity_region",
                signals,
                noun="modules",
            )
        ],
    }

    report, _ = _review_report(sections, limit=1)
    projected_findings = report["sections"]["findings"]
    projected_registry = report["sections"]["module_dag"][
        "architectureProducerRegistrations"
    ]["producers"]
    projected_signals = report["sections"]["review_regions"][0]["signals"]

    assert [row["id"] for row in projected_findings] == [
        "finding-b",
        "finding-a",
    ]
    expected_producers = {"finding-b.review", "finding-a.review"}
    assert set(projected_registry) == expected_producers
    assert {row["id"] for row in projected_signals} == expected_producers
    assert "finding-z.review" not in projected_registry
    _assert_architecture_routes(
        report,
        projected_registry,
        projected_signals,
        owner_ids=("finding-b", "finding-a"),
    )


def test_architecture_route_recovers_owner_after_registration_order_changes() -> None:
    target = _architecture_finding(
        "finding-z-target",
        severity="info",
        stable_key="architecture:target",
    )
    other = _architecture_finding(
        "finding-a-other",
        severity="info",
        stable_key="architecture:other",
    )
    # Registration happened while the target finding occupied index zero.
    producer = _architecture_producer(target, 0)
    # Canonical report assembly subsequently reordered the finding population,
    # leaving the producer's positional references stale before projection.
    sections = {
        "findings": [other, target],
        "module_dag": {
            "architectureProducerRegistrations": {
                "producers": {producer["id"]: producer},
            },
        },
        "review_regions": [
            _review_region(
                "architecture-stable-key-region",
                "architecture_integrity_region",
                [producer],
                noun="modules",
            )
        ],
    }

    report, _ = _review_report(sections, limit=1)
    projected_findings = report["sections"]["findings"]
    projected_producer = report["sections"]["module_dag"][
        "architectureProducerRegistrations"
    ]["producers"][producer["id"]]
    projected_signal = report["sections"]["review_regions"][0]["signals"][0]

    assert [row["stable_key"] for row in projected_findings] == [
        "architecture:target",
    ]
    owner_ref = "#/sections/findings/0"
    expected_refs = [owner_ref, f"{owner_ref}/join"]
    assert projected_producer["evidenceRefs"] == expected_refs
    assert projected_signal["evidenceRefs"] == expected_refs
    assert resolve_local_json_pointer(report, owner_ref)["stable_key"] == (
        "architecture:target"
    )
    assert resolve_local_json_pointer(report, expected_refs[1])["id"] == (
        "architecture:target.join"
    )


def test_same_type_architecture_witnesses_rebase_to_distinct_exact_owners() -> None:
    witnesses = [
        {
            "type": "deterministic-graph-path",
            "pointer": "#/sections/module_dag/edges",
            "path": ["Root", "Pkg.Left"],
            "edgeRefs": [
                {
                    "source": "Root",
                    "target": "Pkg.Left",
                    "pointer": "#/sections/module_dag/edges/Root/0",
                }
            ],
            "authority": "module_import_graph",
        },
        {
            "type": "deterministic-graph-path",
            "pointer": "#/sections/module_dag/edges",
            "path": ["Root", "Pkg.Right"],
            "edgeRefs": [
                {
                    "source": "Root",
                    "target": "Pkg.Right",
                    "pointer": "#/sections/module_dag/edges/Root/1",
                }
            ],
            "authority": "module_import_graph",
        },
    ]
    canonical = {
        "findings": [
            {
                "stable_key": "architecture:target",
                "join": {"witnessRefs": witnesses},
            }
        ]
    }
    projected = {
        "findings": [
            {
                "stable_key": "architecture:target",
                "join": {"witnessRefs": [witnesses[1]]},
            }
        ]
    }
    closure = EvidenceClosure(
        canonical=canonical,
        projected=projected,
        changed={},
        limit=2,
    )
    canonical_refs = [
        "#/sections/findings/0/join/witnessRefs/0",
        "#/sections/findings/0/join/witnessRefs/1",
    ]

    assert closure.can_rebase_all(canonical_refs)
    projected_refs = [closure.rebase(reference) for reference in canonical_refs]
    report = {"sections": projected}

    assert None not in projected_refs
    assert len(set(projected_refs)) == 2
    assert [
        resolve_local_json_pointer(report, reference)["path"]
        for reference in projected_refs
        if reference is not None
    ] == [
        ["Root", "Pkg.Left"],
        ["Root", "Pkg.Right"],
    ]


def test_declaration_collision_routes_follow_reordered_groups() -> None:
    groups = [
        _collision_group("collision-z"),
        _collision_group("collision-a"),
    ]
    producers = {
        f"{group['id']}.co_reachable": _collision_producer(group, index)
        for index, group in enumerate(groups)
    }
    sections = {
        "module_dag": {
            "declaration_integrity": {
                "collisionCandidates": groups,
                "producerRegistrations": {"producers": producers},
            }
        },
        "review_regions": [
            _review_region(
                "collision-region",
                "declaration_collision_region",
                list(producers.values()),
                noun="declarations",
            )
        ],
    }

    report, _ = _review_report(sections, limit=4)
    integrity = report["sections"]["module_dag"]["declaration_integrity"]
    projected_groups = integrity["collisionCandidates"]
    projected_producers = integrity["producerRegistrations"]["producers"]
    projected_signals = report["sections"]["review_regions"][0]["signals"]

    assert [row["id"] for row in projected_groups] == [
        "collision-a",
        "collision-z",
    ]
    assert set(projected_producers) == {
        "collision-a.co_reachable",
        "collision-z.co_reachable",
    }
    assert [row["id"] for row in projected_signals] == [
        "collision-a.co_reachable",
        "collision-z.co_reachable",
    ]
    for index, identity in enumerate(("collision-a", "collision-z")):
        expected_ref = (
            f"#/sections/module_dag/declaration_integrity/collisionCandidates/{index}"
        )
        producer = projected_producers[f"{identity}.co_reachable"]
        signal = projected_signals[index]
        assert producer["evidenceRefs"] == [expected_ref]
        assert signal["evidenceRefs"] == [expected_ref]
        assert resolve_local_json_pointer(report, expected_ref)["id"] == identity


def test_lean_audit_route_follows_reordered_declaration_owner() -> None:
    audit_id = "audit-target"
    audit_pointer = "#/sections/module_dag/audit_surfaces/0/auditCommands/0"
    module_pointer = "#/sections/module_dag/module_metadata/Pkg.Audit"
    lexical_ref = "source-index:declaration:lexical-target"
    canonical_lean_ref = "#/sections/declaration_graph/declarations/1"
    producer = {
        "id": f"{audit_id}.review",
        "kind": "audit_command_navigation",
        "evidenceRefs": [
            audit_pointer,
            module_pointer,
            lexical_ref,
            canonical_lean_ref,
        ],
        "inspectionAction": _exact_action("audits", audit_id),
    }
    sections = {
        "declaration_graph": {
            "declarations": [
                _lean_declaration(
                    "decl-z-other",
                    "Pkg.Other.other",
                    "Pkg.Other",
                ),
                _lean_declaration(
                    "decl-a-target",
                    "Pkg.Owner.target",
                    "Pkg.Owner",
                ),
            ]
        },
        "module_dag": {
            "audit_surfaces": [
                {
                    "module": "Pkg.Audit",
                    "auditCommands": [
                        {
                            "id": audit_id,
                            "kind": "check",
                            "referencedDeclaration": "Pkg.Owner.target",
                            "referencedOwner": "Pkg.Owner",
                            "resultAuthority": "lean_environment",
                        }
                    ],
                }
            ],
            "module_metadata": {
                "Pkg.Audit": {"path": "Pkg/Audit.lean"},
            },
            "auditProducerRegistrations": {
                "producers": {producer["id"]: producer},
            },
        },
        "review_regions": [
            _review_region(
                "audit-region",
                "audit_surface_region",
                [producer],
                noun="audits",
            )
        ],
    }

    report, _ = _review_report(sections, limit=4)
    declarations = report["sections"]["declaration_graph"]["declarations"]
    projected_producer = report["sections"]["module_dag"]["auditProducerRegistrations"][
        "producers"
    ][producer["id"]]
    projected_signal = report["sections"]["review_regions"][0]["signals"][0]

    assert [row["id"] for row in declarations] == [
        "decl-a-target",
        "decl-z-other",
    ]
    expected_lean_ref = "#/sections/declaration_graph/declarations/0"
    for routed in (projected_producer, projected_signal):
        assert routed["evidenceRefs"] == [
            audit_pointer,
            module_pointer,
            lexical_ref,
            expected_lean_ref,
        ]
        resolved = resolve_local_json_pointer(report, expected_lean_ref)
        assert resolved["id"] == "decl-a-target"
        assert resolved["declaration"] == "Pkg.Owner.target"


def test_generated_region_signal_ignores_same_id_generic_registration() -> None:
    expected_refs = [
        f"{GENERATED_BASE}/candidates/0",
        f"{GENERATED_BASE}/partitions/0",
        f"{GENERATED_BASE}/candidates/0/members",
        f"{GENERATED_BASE}/partitions/0/features/0",
        f"{GENERATED_BASE}/partitions/0/features/1",
    ]
    generated_producer = {
        "id": "candidate.review",
        "kind": "generated_family_candidate",
        "evidenceRefs": list(expected_refs),
    }
    generic_producer = {
        "id": generated_producer["id"],
        "kind": "generic_other",
        "evidenceRefs": ["#/sections/module_dag/evidenceRows/0"],
    }
    sections = {
        "module_dag": {
            "evidenceRows": [{"id": "generic-owner"}],
            "producerRegistrations": {
                "producers": {generic_producer["id"]: generic_producer},
            },
            "generated_family_candidates": {
                "candidates": [
                    {
                        "id": "candidate",
                        "partitionId": "partition",
                        "importFeatureId": "import",
                        "lexicalFeatureId": "lexical",
                        "members": [{"id": "member"}],
                    }
                ],
                "partitions": [
                    {
                        "id": "partition",
                        "features": [
                            {
                                "id": "import",
                                "kind": "direct_internal_import",
                            },
                            {
                                "id": "lexical",
                                "kind": "declaration_stem",
                            },
                        ],
                    }
                ],
                "producerRegistry": {
                    "producers": {
                        generated_producer["id"]: generated_producer,
                    },
                },
            },
        },
        "review_regions": [
            _review_region(
                "generated-region",
                "generated_family_candidate_region",
                [generated_producer],
                noun="modules",
            )
        ],
    }

    report, _ = _review_report(sections, limit=5)
    dag = report["sections"]["module_dag"]
    generated_registry = dag["generated_family_candidates"]["producerRegistry"][
        "producers"
    ]
    signal = report["sections"]["review_regions"][0]["signals"][0]

    assert generated_registry[generated_producer["id"]]["evidenceRefs"] == expected_refs
    assert signal["evidenceRefs"] == expected_refs
    assert dag["producerRegistrations"]["producers"] == {}


def test_duplicate_registry_identity_is_removed_with_its_orphan_signal() -> None:
    identity = "duplicate.review"
    declaration_producer = {
        "id": identity,
        "kind": "declaration_other",
        "evidenceRefs": ["#/sections/module_dag/evidenceRows/0"],
    }
    generic_producer = {
        "id": identity,
        "kind": "generic_other",
        "evidenceRefs": ["#/sections/module_dag/evidenceRows/1"],
    }
    sections = {
        "module_dag": {
            "evidenceRows": [
                {"id": "declaration-owner"},
                {"id": "generic-owner"},
            ],
            "declaration_integrity": {
                "producerRegistrations": {
                    "producers": {identity: declaration_producer},
                },
            },
            "producerRegistrations": {
                "producers": {identity: generic_producer},
            },
        },
        "review_regions": [
            _review_region(
                "duplicate-region",
                "generic_region",
                [declaration_producer],
                noun="modules",
            )
        ],
    }

    report, _ = _review_report(sections, limit=4)
    dag = report["sections"]["module_dag"]
    region = report["sections"]["review_regions"][0]

    assert dag["declaration_integrity"]["producerRegistrations"]["producers"] == {}
    assert dag["producerRegistrations"]["producers"] == {}
    assert region["signals"] == []
    assert region["signal_count"] == 0


@pytest.mark.parametrize(
    "reference",
    (
        "#/sections/module_dag/evidenceRows/00",
        "#/section/module_dag/evidenceRows/0",
    ),
)
def test_invalid_local_producer_reference_fails_closed(reference: str) -> None:
    producer = {
        "id": "invalid-route.review",
        "kind": "generic_other",
        "evidenceRefs": [reference],
    }
    sections = {
        "module_dag": {
            "evidenceRows": [{"id": "owner"}],
            "producerRegistrations": {
                "producers": {producer["id"]: producer},
            },
        },
        "review_regions": [
            _review_region(
                "invalid-route-region",
                "generic_region",
                [producer],
                noun="modules",
            )
        ],
    }

    report, _ = _review_report(sections, limit=4)
    dag = report["sections"]["module_dag"]
    region = report["sections"]["review_regions"][0]

    assert dag["producerRegistrations"]["producers"] == {}
    assert region["signals"] == []
    assert region["signal_count"] == 0


def test_unresolved_route_records_projection_evidence_unavailable() -> None:
    producer = {
        "id": "unresolved-route.review",
        "kind": "generic_other",
        "evidenceRefs": ["#/sections/module_dag/missingEvidence/0"],
    }
    sections = {
        "module_dag": {
            "producerRegistrations": {
                "producers": {producer["id"]: producer},
            },
        },
        "review_regions": [
            _review_region(
                "unresolved-route-region",
                "generic_region",
                [producer],
                noun="modules",
            )
        ],
    }

    report, omissions = _review_report(sections, limit=4)
    dag = report["sections"]["module_dag"]
    region = report["sections"]["review_regions"][0]

    assert dag["producerRegistrations"]["producers"] == {}
    assert region["signals"] == []
    assert region["signal_count"] == 0
    assert any(
        omission["reason"] == "projection_evidence_unavailable"
        for omission in omissions
    )


def test_generated_restored_evidence_refs_have_no_stale_omissions() -> None:
    expected_refs = [
        f"{GENERATED_BASE}/candidates/0",
        f"{GENERATED_BASE}/partitions/0",
        f"{GENERATED_BASE}/candidates/0/members",
        f"{GENERATED_BASE}/partitions/0/features/0",
        f"{GENERATED_BASE}/partitions/0/features/1",
    ]
    producer = {
        "id": "candidate.review",
        "kind": "generated_family_candidate",
        "evidenceRefs": list(expected_refs),
    }
    sections = {
        "module_dag": {
            "generated_family_candidates": {
                "candidates": [
                    {
                        "id": "candidate",
                        "partitionId": "partition",
                        "importFeatureId": "import-winner",
                        "lexicalFeatureId": "lexical-winner",
                        "members": [{"id": "member"}],
                        "canonicalRef": expected_refs[0],
                    }
                ],
                "partitions": [
                    {
                        "id": "partition",
                        "features": [
                            {
                                "id": "import-winner",
                                "kind": "direct_internal_import",
                            },
                            {
                                "id": "lexical-winner",
                                "kind": "declaration_stem",
                            },
                        ],
                    }
                ],
                "producerRegistry": {
                    "producers": {producer["id"]: producer},
                },
            }
        },
        "review_regions": [
            _review_region(
                "generated-region",
                "generated_family_candidate_region",
                [
                    {
                        **producer,
                        "evidenceRefCount": len(expected_refs),
                        "omittedEvidenceRefCount": 0,
                    }
                ],
                noun="modules",
            )
        ],
    }

    report, omissions = _review_report(sections, limit=1)
    surface = report["sections"]["module_dag"]["generated_family_candidates"]
    projected_producer = surface["producerRegistry"]["producers"][producer["id"]]
    projected_signal = report["sections"]["review_regions"][0]["signals"][0]

    assert projected_producer["evidenceRefs"] == expected_refs
    assert projected_signal["evidenceRefs"] == expected_refs
    assert projected_signal["evidenceRefCount"] == len(expected_refs)
    assert projected_signal["omittedEvidenceRefCount"] == 0
    restored_owners = (
        (f"{GENERATED_BASE}/producerRegistry/producers/candidate.review/evidenceRefs"),
        "#/sections/review_regions/0/signals/0/evidenceRefs",
    )
    assert not [
        omission
        for omission in omissions
        if any(
            _pointer_is_within(omission["pointer"], owner) for owner in restored_owners
        )
    ]


def test_generated_member_refs_retain_exact_metadata_beyond_mapping_cap() -> None:
    member_id = "Module.100"
    member_ref = f"#/sections/module_dag/module_metadata/{member_id}"
    metadata = {
        f"Module.{index:03d}": {"module": f"Module.{index:03d}"} for index in range(101)
    }
    sections = {
        "module_dag": {
            "module_metadata": metadata,
            "generated_family_candidates": {
                "candidates": [
                    {
                        "id": "candidate",
                        "partitionId": "partition",
                        "importFeatureId": "import",
                        "lexicalFeatureId": "lexical",
                        "members": [{"id": member_id}],
                        "memberIds": [member_id],
                        "memberRefs": [member_ref],
                        "canonicalRef": f"{GENERATED_BASE}/candidates/0",
                    }
                ],
                "partitions": [
                    {
                        "id": "partition",
                        "features": [
                            {"id": "import", "kind": "direct_internal_import"},
                            {"id": "lexical", "kind": "declaration_stem"},
                        ],
                    }
                ],
            },
        }
    }

    report, _ = _review_report(sections, limit=100)
    dag = report["sections"]["module_dag"]
    candidate = dag["generated_family_candidates"]["candidates"][0]

    assert member_id in dag["module_metadata"]
    assert candidate["memberIds"] == [member_id]
    assert candidate["memberRefs"] == [member_ref]
    assert resolve_local_json_pointer(report, member_ref)["module"] == member_id


def test_import_boundary_routes_retain_exact_membership_beyond_list_cap() -> None:
    target = "Dependency.100"
    membership = [
        {
            "module": f"Dependency.{index:03d}",
            "present": index == 100,
            "indexEntryStatus": "available" if index == 100 else "absent",
            "authority": "source_index_manifest",
            "sourceIndexFingerprint": "source-fingerprint",
        }
        for index in range(101)
    ]
    canonical_ref = "#/sections/module_dag/source_index/boundaryMembershipEvidence/100"
    sections = {
        "module_dag": {
            "analysis_scope": {"kind": "inventory"},
            "import_boundaries": [
                {
                    "id": "import-boundary:Root:0:Dependency.100",
                    "targetModule": target,
                    "evidenceRefs": [
                        {
                            "type": "source_index_inventory",
                            "pointer": canonical_ref,
                            "module": target,
                            "fingerprint": "source-fingerprint",
                            "present": True,
                            "indexEntryStatus": "available",
                        }
                    ],
                }
            ],
            "source_index": {
                "boundaryMembershipEvidence": membership,
            },
        }
    }

    report, omissions = _review_report(sections, limit=1)
    dag = report["sections"]["module_dag"]
    boundary = dag["import_boundaries"][0]
    routed_ref = boundary["evidenceRefs"][0]["pointer"]
    projected_membership = dag["source_index"]["boundaryMembershipEvidence"]

    assert routed_ref == (
        "#/sections/module_dag/source_index/boundaryMembershipEvidence/0"
    )
    assert len(projected_membership) == 1
    assert resolve_local_json_pointer(report, routed_ref)["module"] == target
    assert {
        row["pointer"]: row["omitted_count"]
        for row in omissions
        if row["reason"] == "projection_collection_limit"
    }["#/sections/module_dag/source_index/boundaryMembershipEvidence"] == 100


def test_import_boundary_self_routes_follow_stratified_reordering() -> None:
    target = "Shared.Dependency"
    membership_ref = "#/sections/module_dag/source_index/boundaryMembershipEvidence/0"
    membership = {
        "module": target,
        "present": True,
        "indexEntryStatus": "available",
        "authority": "source_index_manifest",
        "sourceIndexFingerprint": "source-fingerprint",
    }

    def boundary(identity: str, index: int, status: str) -> dict[str, Any]:
        return {
            "id": identity,
            "status": status,
            "targetModule": target,
            "evidenceRefs": [
                {
                    "type": "source",
                    "pointer": f"#/sections/module_dag/import_boundaries/{index}",
                },
                {
                    "type": "source_index_inventory",
                    "pointer": membership_ref,
                    "module": target,
                    "fingerprint": "source-fingerprint",
                    "present": True,
                    "indexEntryStatus": "available",
                },
            ],
        }

    sections = {
        "module_dag": {
            "import_boundaries": [
                boundary("boundary-z", 0, "z"),
                boundary("boundary-a", 1, "a"),
            ],
            "source_index": {"boundaryMembershipEvidence": [membership]},
        }
    }

    report, _ = _review_report(sections, limit=2)
    boundaries = report["sections"]["module_dag"]["import_boundaries"]

    assert [row["id"] for row in boundaries] == ["boundary-a", "boundary-z"]
    for index, row in enumerate(boundaries):
        self_ref = row["evidenceRefs"][0]["pointer"]
        assert self_ref == f"#/sections/module_dag/import_boundaries/{index}"
        assert resolve_local_json_pointer(report, self_ref)["id"] == row["id"]


def test_invalid_import_boundary_membership_route_fails_closed() -> None:
    sections = {
        "module_dag": {
            "import_boundaries": [
                {
                    "id": "invalid-boundary",
                    "targetModule": "Expected.Dependency",
                    "evidenceRefs": [
                        {
                            "type": "source",
                            "pointer": "#/sections/module_dag/import_boundaries/0",
                        },
                        {
                            "type": "source_index_inventory",
                            "pointer": (
                                "#/sections/module_dag/source_index/"
                                "boundaryMembershipEvidence/0"
                            ),
                            "module": "Expected.Dependency",
                            "fingerprint": "source-fingerprint",
                            "present": True,
                            "indexEntryStatus": "available",
                        },
                    ],
                }
            ],
            "source_index": {
                "boundaryMembershipEvidence": [
                    {
                        "module": "Different.Dependency",
                        "present": True,
                        "indexEntryStatus": "available",
                        "sourceIndexFingerprint": "source-fingerprint",
                    }
                ]
            },
        }
    }

    report, omissions = _review_report(sections, limit=100)

    assert report["sections"]["module_dag"]["import_boundaries"] == []
    assert {
        (row["pointer"], row["reason"], row["omitted_count"]) for row in omissions
    } >= {
        (
            "#/sections/module_dag/import_boundaries",
            "projection_evidence_unavailable",
            1,
        )
    }


def test_evidence_closure_keeps_limit_and_nested_omissions_truthful() -> None:
    canonical_ref = "#/sections/module_dag/architecture/witnesses/1"
    projected_ref = "#/sections/module_dag/architecture/witnesses/0"
    producer = {
        "id": "architecture-z-target.review",
        "kind": "architecture_witness",
        "evidenceRefs": [canonical_ref],
    }
    members = [
        {
            "id": f"member-{index:02d}",
            "module": f"Pkg.Member{index:02d}",
        }
        for index in range(25)
    ]
    labels = [f"label-{index:02d}" for index in range(25)]
    sections = {
        "module_dag": {
            "architecture": {
                "kind": "architecture_evidence",
                "witnesses": [
                    {
                        "id": "architecture-a-unreferenced",
                        "members": [],
                        "labels": [],
                    },
                    {
                        "id": "architecture-z-target",
                        "members": members,
                        "labels": labels,
                        "sourceRange": {
                            "start": {
                                "line": 17,
                                "column": 3,
                            },
                            "end": {
                                "line": 19,
                                "column": 7,
                            },
                        },
                    },
                ],
                "producerRegistrations": {
                    "producers": {producer["id"]: producer},
                },
            }
        },
        "review_regions": [
            _review_region(
                "architecture-limit-region",
                "generic_region",
                [producer],
                noun="modules",
            )
        ],
    }

    report, omissions = _review_report(sections, limit=1)
    architecture = report["sections"]["module_dag"]["architecture"]
    projected_witnesses = architecture["witnesses"]
    projected_producer = architecture["producerRegistrations"]["producers"][
        producer["id"]
    ]
    projected_signal = report["sections"]["review_regions"][0]["signals"][0]
    omission_by_pointer = {
        omission["pointer"]: omission
        for omission in omissions
        if omission["reason"] == "projection_collection_limit"
    }
    witness_pointer = "#/sections/module_dag/architecture/witnesses"
    member_pointer = f"{projected_ref}/members"
    label_pointer = f"{projected_ref}/labels"

    assert {
        "witnessIds": [row["id"] for row in projected_witnesses],
        "memberCount": len(projected_witnesses[0]["members"]),
        "labels": projected_witnesses[0]["labels"],
        "sourceRange": projected_witnesses[0]["sourceRange"],
        "producerRefs": projected_producer["evidenceRefs"],
        "signalRefs": projected_signal["evidenceRefs"],
        "witnessOmitted": omission_by_pointer[witness_pointer]["omitted_count"],
        "memberOmitted": omission_by_pointer[member_pointer]["omitted_count"],
        "labelOmitted": omission_by_pointer[label_pointer]["omitted_count"],
        "staleOwnerOmissions": [
            omission["pointer"]
            for omission in omissions
            if omission["pointer"].startswith(
                "#/sections/module_dag/architecture/witnesses/1"
            )
        ],
    } == {
        "witnessIds": ["architecture-z-target"],
        "memberCount": 0,
        "labels": ["label-00"],
        "sourceRange": {
            "start": {
                "line": 17,
                "column": 3,
            },
            "end": {
                "line": 19,
                "column": 7,
            },
        },
        "producerRefs": [projected_ref],
        "signalRefs": [projected_ref],
        "witnessOmitted": 1,
        "memberOmitted": 25,
        "labelOmitted": 24,
        "staleOwnerOmissions": [],
    }


def _review_report(
    sections: dict[str, Any],
    *,
    limit: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    projected, omissions, _, _ = project_sections(
        sections,
        projection="review",
        summary_item_limit=limit,
        review_item_limit=limit,
    )
    return {"sections": projected}, omissions


def _architecture_finding(
    identity: str,
    *,
    severity: str,
    stable_key: str | None = None,
) -> dict[str, Any]:
    key = stable_key or identity
    return {
        "id": identity,
        "stable_key": key,
        "kind": "composite_import_pressure",
        "severity": severity,
        "status": "open",
        "population": "target_owned",
        "role": "architecture",
        "subject": identity,
        "join": {"id": f"{key}.join"},
    }


def _architecture_producer(
    finding: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    owner_ref = f"#/sections/findings/{index}"
    return {
        "id": f"{finding['stable_key']}.review",
        "kind": finding["kind"],
        "evidenceRefs": [owner_ref, f"{owner_ref}/join"],
        "inspectionAction": _exact_action("modules", finding["stable_key"]),
    }


def _assert_architecture_routes(
    report: dict[str, Any],
    producers: dict[str, Any],
    signals: list[dict[str, Any]],
    *,
    owner_ids: tuple[str, ...],
) -> None:
    signal_by_id = {row["id"]: row for row in signals}
    for index, owner_id in enumerate(owner_ids):
        owner_ref = f"#/sections/findings/{index}"
        expected_refs = [owner_ref, f"{owner_ref}/join"]
        producer_id = f"{owner_id}.review"
        assert producers[producer_id]["evidenceRefs"] == expected_refs
        assert signal_by_id[producer_id]["evidenceRefs"] == expected_refs
        assert resolve_local_json_pointer(report, owner_ref)["id"] == owner_id
        assert (
            resolve_local_json_pointer(
                report,
                expected_refs[1],
            )["id"]
            == f"{owner_id}.join"
        )


def _collision_group(identity: str) -> dict[str, Any]:
    return {
        "id": identity,
        "evidenceKind": "lexical_candidate_name_collision",
        "candidateStatus": "candidate",
        "representativeMembers": [
            {"canonicalRef": (f"source-index:declaration:{identity}.member")}
        ],
    }


def _collision_producer(
    group: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    return {
        "id": f"{group['id']}.co_reachable",
        "kind": "co_reachable_declaration_collision_candidate",
        "evidenceRefs": [
            (f"#/sections/module_dag/declaration_integrity/collisionCandidates/{index}")
        ],
        "inspectionAction": _exact_action(
            "declarations",
            group["id"],
        ),
    }


def _lean_declaration(
    identity: str,
    declaration: str,
    module: str,
) -> dict[str, str]:
    return {
        "id": identity,
        "kind": "theorem",
        "declaration": declaration,
        "module": module,
    }


def _review_region(
    identity: str,
    kind: str,
    signals: list[dict[str, Any]],
    *,
    noun: str,
) -> dict[str, Any]:
    return {
        "id": identity,
        "kind": kind,
        "signals": signals,
        "signal_count": len(signals),
        "inspectionAction": {
            "command": "ladon",
            "arguments": ["inspect", noun],
        },
    }


def _exact_action(noun: str, identity: str) -> dict[str, Any]:
    return {
        "command": "ladon",
        "arguments": ["inspect", noun, "--id", identity],
    }


def _pointer_is_within(candidate: str, parent: str) -> bool:
    return candidate == parent or candidate.startswith(f"{parent}/")
