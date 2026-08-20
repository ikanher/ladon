from __future__ import annotations

from typing import Any

from ladon.coverage import CollectionCoverage, CoverageCause
from ladon.finding_evidence import resolve_local_json_pointer
from ladon.report_projection import project_sections

BASE = "#/sections/module_dag/generated_family_candidates"


def test_review_projection_preserves_candidate_witness_array_indices() -> None:
    candidates = [
        _candidate("candidate-z", 0, "partition-z", "import-z", "feature-z"),
        _candidate("candidate-a", 1, "partition-a", "import-a", "feature-a"),
    ]
    partitions = [
        _partition("partition-z", "import-z", "feature-z"),
        _partition("partition-a", "import-a", "feature-a"),
    ]
    producers = {
        f"{candidate['id']}.review": {
            "id": f"{candidate['id']}.review",
            "kind": "generated_family_candidate",
            "evidenceRefs": [
                candidate["canonicalRef"],
                f"{BASE}/partitions/{index}",
                f"{candidate['canonicalRef']}/members",
                f"{BASE}/partitions/{index}/features/0",
                f"{BASE}/partitions/{index}/features/1",
            ],
        }
        for index, candidate in enumerate(candidates)
    }
    sections = {
        "module_dag": {
            "generated_family_candidates": {
                "candidates": candidates,
                "partitions": partitions,
                "producerRegistry": {"producers": producers},
            }
        }
    }

    projected, _, _, _ = project_sections(
        sections,
        projection="review",
        summary_item_limit=20,
        review_item_limit=100,
    )
    report = {"sections": projected}
    surface = projected["module_dag"]["generated_family_candidates"]

    assert [row["id"] for row in surface["candidates"]] == [
        "candidate-z",
        "candidate-a",
    ]
    assert [
        row["features"][1]["id"]
        for row in surface["partitions"]
    ] == ["feature-z", "feature-a"]
    _assert_exact_candidate_routes(report, surface)


def test_review_projection_reindexes_over_cap_candidate_routes() -> None:
    report, surface, generated_region = _project_over_cap_candidates(101)
    retained_ids = [row["id"] for row in surface["candidates"]]

    _assert_over_cap_selection(surface, retained_ids)
    _assert_exact_candidate_routes(report, surface)
    _assert_projected_region_routes(
        report,
        generated_region,
        expected_ids=set(surface["producerRegistry"]["producers"]),
    )


def _project_over_cap_candidates(
    count: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Project one over-cap surface and return its canonical owners."""

    candidates = _over_cap_candidates(count)
    partitions = _over_cap_partitions(count)
    producers = _candidate_producers(candidates, partitions)
    sections = _over_cap_sections(candidates, partitions, producers)
    projected, _, _, _ = project_sections(
        sections,
        projection="review",
        summary_item_limit=20,
        review_item_limit=100,
    )
    report = {"sections": projected}
    surface = projected["module_dag"]["generated_family_candidates"]
    return report, surface, projected["review_regions"][0]


def _over_cap_candidates(count: int) -> list[dict[str, Any]]:
    """Return candidates in the reverse order exercised by projection."""

    return [
        _candidate(
            f"candidate-{count - index:03d}",
            index,
            f"partition-{count - index - 1:03d}",
            f"import-{count - index - 1:03d}",
            f"lexical-{count - index - 1:03d}",
        )
        for index in range(count)
    ]


def _over_cap_partitions(count: int) -> list[dict[str, Any]]:
    """Return the complete partition population for an over-cap surface."""

    return [
        _partition(
            f"partition-{index:03d}",
            f"import-{index:03d}",
            f"lexical-{index:03d}",
        )
        for index in range(count)
    ]


def _candidate_producers(
    candidates: list[dict[str, Any]],
    partitions: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Return producer rows joined to their original partition indices."""

    partition_indexes = _rows_by_id(partitions)
    return {
        f"{candidate['id']}.review": _producer(
            candidate,
            partition_index=partition_indexes[candidate["partitionId"]],
        )
        for candidate in candidates
    }


def _rows_by_id(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Index fixture rows by identifier without embedding that branch in tests."""

    return {row["id"]: index for index, row in enumerate(rows)}


def _over_cap_sections(
    candidates: list[dict[str, Any]],
    partitions: list[dict[str, Any]],
    producers: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Return the raw candidate and review-region owners before projection."""

    signals = [
        {
            **producer,
            "subject": identity,
            "evidenceRefCount": len(producer["evidenceRefs"]),
            "omittedEvidenceRefCount": 0,
        }
        for identity, producer in producers.items()
    ]
    return {
        "module_dag": {
            "generated_family_candidates": {
                "candidates": candidates,
                "partitions": partitions,
                "producerRegistry": {"producers": producers},
            }
        },
        "review_regions": [
            {
                "id": "generated-region",
                "kind": "generated_family_candidate_region",
                "signals": signals,
            }
        ],
    }


def _assert_over_cap_selection(
    surface: dict[str, Any],
    retained_ids: list[str],
) -> None:
    """Assert the cap removes only the joined lowest-ranked candidate."""

    assert len(retained_ids) == 100
    assert "candidate-001" not in retained_ids
    assert "partition-000" not in {
        row["id"] for row in surface["partitions"]
    }
    assert set(surface["producerRegistry"]["producers"]) == {
        f"{identity}.review" for identity in retained_ids
    }


def _assert_projected_region_routes(
    report: dict[str, Any],
    generated_region: dict[str, Any],
    *,
    expected_ids: set[str],
) -> None:
    """Assert retained review signals resolve all of their evidence routes."""

    assert {signal["id"] for signal in generated_region["signals"]} == expected_ids
    for signal in generated_region["signals"]:
        for reference in signal["evidenceRefs"]:
            assert resolve_local_json_pointer(report, reference) is not None


def test_review_projection_rebases_inline_candidate_coverage() -> None:
    members = [
        {"id": f"member-{index}", "population": "target_owned"}
        for index in range(5)
    ]
    candidate = {
        "id": "candidate",
        "status": "advisory",
        "members": members,
        "memberCoverage": _coverage("candidate.members", "candidates/0/members"),
        "representatives": members,
        "representativeCoverage": _coverage(
            "candidate.representatives",
            "candidates/0/representatives",
        ),
    }
    partition = {
        "id": "partition",
        "members": members,
        "memberCoverage": _coverage("partition.members", "partitions/0/members"),
        "features": [],
    }
    sections = {
        "module_dag": {
            "generated_family_candidates": {
                "candidates": [candidate],
                "partitions": [partition],
            }
        }
    }

    projected, _, _, _ = project_sections(
        sections,
        projection="review",
        summary_item_limit=20,
        review_item_limit=2,
    )
    report = {"sections": projected}
    surface = projected["module_dag"]["generated_family_candidates"]

    _assert_inline_coverage(report, surface["candidates"][0], "members")
    _assert_inline_coverage(
        report,
        surface["candidates"][0],
        "representatives",
    )
    _assert_inline_coverage(report, surface["partitions"][0], "members")


def test_review_projection_keeps_detector_bounded_partition_features() -> None:
    report, surface = _project_detector_bounded_features()
    partition = surface["partitions"][0]
    features = partition["features"]
    producer = surface["producerRegistry"]["producers"]["candidate.review"]

    assert [row["id"] for row in features] == _bounded_feature_ids()
    assert partition["featureCoverage"]["visible"] == 12
    assert partition["featureCoverage"]["total"] == 30
    assert partition["featureCoverage"]["omitted"] == 18
    assert [
        resolve_local_json_pointer(report, reference)["id"]
        for reference in producer["evidenceRefs"][-2:]
    ] == ["import-winner", "lexical-winner"]
    _assert_exact_candidate_routes(report, surface)


def _project_detector_bounded_features() -> tuple[dict[str, Any], dict[str, Any]]:
    """Project a detector-bounded feature set through a smaller review limit."""

    candidate = _candidate(
        "candidate",
        0,
        "partition",
        "import-winner",
        "lexical-winner",
    )
    partition = _detector_bounded_partition()
    producer = _producer(candidate, partition_index=0)
    sections = {
        "module_dag": {
            "generated_family_candidates": {
                "candidates": [candidate],
                "partitions": [partition],
                "producerRegistry": {
                    "producers": {"candidate.review": producer}
                },
            }
        }
    }
    projected, _, _, _ = project_sections(
        sections,
        projection="review",
        summary_item_limit=1,
        review_item_limit=2,
    )
    return (
        {"sections": projected},
        projected["module_dag"]["generated_family_candidates"],
    )


def _detector_bounded_partition() -> dict[str, Any]:
    """Return twelve retained keys from a larger detector feature population."""

    features = [
        {
            "id": identity,
            "kind": "direct_internal_import",
            "memberCount": 5,
        }
        for identity in _bounded_feature_ids()[:6]
    ]
    features.extend(
        {
            "id": identity,
            "kind": "declaration_stem",
            "memberCount": 5,
        }
        for identity in _bounded_feature_ids()[6:]
    )
    return {
        "id": "partition",
        "features": features,
        "featureCoverage": CollectionCoverage.exact(
            identity="partition.features",
            pointer=f"{BASE}/partitions/0/features",
            visible=12,
            total=30,
            population="candidate_partition_features",
            scope="partition",
            authority="ladon_derived_heuristic",
            causes=(
                CoverageCause(
                    kind="analysis",
                    identifier="candidate.feature_key_limit",
                    detail="detector retained twelve strongest feature keys",
                    controlling_cap=12,
                ),
            ),
        ).to_dict(),
    }


def _bounded_feature_ids() -> list[str]:
    """Return stable keys with exact winners at the end of each feature kind."""

    return [
        "import-00",
        "import-01",
        "import-02",
        "import-03",
        "import-04",
        "import-winner",
        "lexical-00",
        "lexical-01",
        "lexical-02",
        "lexical-03",
        "lexical-04",
        "lexical-winner",
    ]


def _candidate(
    identity: str,
    index: int,
    partition_id: str,
    import_feature_id: str,
    lexical_feature_id: str,
) -> dict[str, Any]:
    return {
        "id": identity,
        "status": "advisory",
        "partitionId": partition_id,
        "importFeatureId": import_feature_id,
        "lexicalFeatureId": lexical_feature_id,
        "members": [{"id": f"{identity}.member"}],
        "canonicalRef": f"{BASE}/candidates/{index}",
    }


def _partition(
    identity: str,
    import_feature_id: str,
    lexical_feature_id: str,
) -> dict[str, Any]:
    return {
        "id": identity,
        "features": [
            {
                "id": import_feature_id,
                "kind": "direct_internal_import",
                "memberCount": 5,
            },
            {
                "id": lexical_feature_id,
                "kind": "declaration_stem",
                "memberCount": 5,
            }
        ],
    }


def _producer(
    candidate: dict[str, Any],
    *,
    partition_index: int,
) -> dict[str, Any]:
    candidate_index = int(
        str(candidate["canonicalRef"]).rsplit("/", maxsplit=1)[-1]
    )
    return {
        "id": f"{candidate['id']}.review",
        "kind": "generated_family_candidate",
        "evidenceRefs": [
            candidate["canonicalRef"],
            f"{BASE}/partitions/{partition_index}",
            f"{BASE}/candidates/{candidate_index}/members",
            f"{BASE}/partitions/{partition_index}/features/0",
            f"{BASE}/partitions/{partition_index}/features/1",
        ],
    }


def _assert_exact_candidate_routes(
    report: dict[str, Any],
    surface: dict[str, Any],
) -> None:
    candidates = _row_values_by_id(surface["candidates"])
    partitions = _row_values_by_id(surface["partitions"])
    for producer_id, producer in surface["producerRegistry"]["producers"].items():
        candidate_id = producer_id.removesuffix(".review")
        candidate = candidates[candidate_id]
        partition = partitions[candidate["partitionId"]]
        _assert_exact_candidate_route(
            report,
            producer,
            candidate_id=candidate_id,
            candidate=candidate,
            partition=partition,
        )


def _row_values_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index retained report rows by their canonical identifier."""

    return {row["id"]: row for row in rows}


def _assert_exact_candidate_route(
    report: dict[str, Any],
    producer: dict[str, Any],
    *,
    candidate_id: str,
    candidate: dict[str, Any],
    partition: dict[str, Any],
) -> None:
    """Assert one producer's canonical route set after projection."""

    resolved = [
        resolve_local_json_pointer(report, reference)
        for reference in producer["evidenceRefs"]
    ]
    for row in resolved:
        assert row is not None
    assert resolved[0]["id"] == candidate_id
    assert resolved[1]["id"] == candidate["partitionId"]
    assert resolved[2] == candidate["members"]
    assert resolved[3]["id"] == candidate["importFeatureId"]
    assert resolved[4]["id"] == candidate["lexicalFeatureId"]
    assert partition["canonicalRef"] == producer["evidenceRefs"][1]


def _coverage(identity: str, suffix: str) -> dict[str, Any]:
    return CollectionCoverage.exact(
        identity=identity,
        pointer=f"{BASE}/{suffix}",
        visible=5,
        total=5,
        observed_lower_bound=5,
        population="candidate_members",
        scope=identity,
        authority="ladon_derived_projection",
    ).to_dict()


def _assert_inline_coverage(
    report: dict[str, Any],
    owner: dict[str, Any],
    collection: str,
) -> None:
    coverage = owner[f"{collection[:-1]}Coverage"]
    assert coverage["visible"] == len(owner[collection]) == 2
    assert coverage["observedLowerBound"] == 5
    assert coverage["total"] == 5
    assert coverage["omitted"] == 3
    assert coverage["completeness"] == "partial"
    assert coverage["causes"][-1]["id"] == (
        "projection.review_inline_collection_limit"
    )
    assert resolve_local_json_pointer(report, coverage["pointer"]) == (
        owner[collection]
    )
