from __future__ import annotations

import pytest

from ladon.report_contract import ReportModelError
from ladon.report_declaration_compaction import (
    compact_declaration_collections,
    is_compact_declaration_container,
)


CONTAINER_POINTER = "#/sections/declaration_graph"


def test_valid_compact_declaration_container_is_idempotent() -> None:
    raw = {
        "declarations": [
            {
                "declaration": "Fixture.first",
                "authority": "lean_environment",
                "surface": {
                    "confidence": "direct",
                    "nonclaim": "Navigation evidence only.",
                },
                "trust": {
                    "authority": {
                        "declarations": [{"authority": "opaque-evidence-value"}]
                    }
                },
            },
            {"declaration": "Fixture.second"},
        ],
        "edges": [],
    }

    compacted = compact_declaration_collections(
        raw,
        pointer=CONTAINER_POINTER,
    )

    assert is_compact_declaration_container(compacted)
    assert (
        compact_declaration_collections(
            compacted,
            pointer=CONTAINER_POINTER,
        )
        == compacted
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"_declarationEvidence": {}},
        {
            "declarations": [],
            "_declarationEvidence": [],
        },
        {
            "declarations": [
                {
                    "declaration": "Fixture.hybrid",
                    "authority": "forged",
                    "evidenceRef": (
                        f"{CONTAINER_POINTER}/_declarationEvidence/"
                        "evidence:000000000000000000000000"
                    ),
                }
            ],
            "_declarationEvidence": {
                "evidence:000000000000000000000000": {
                    "fields": {"/authority": "lean_environment"}
                }
            },
        },
        {
            "declarations": [
                {
                    "declaration": "Fixture.dangling",
                    "evidenceRef": (
                        f"{CONTAINER_POINTER}/_declarationEvidence/"
                        "evidence:111111111111111111111111"
                    ),
                }
            ],
            "_declarationEvidence": {
                "evidence:000000000000000000000000": {
                    "fields": {"/authority": "lean_environment"}
                }
            },
        },
        {
            "declarations": [{"declaration": "Fixture.orphan"}],
            "_declarationEvidence": {
                "evidence:000000000000000000000000": {
                    "fields": {"/authority": "lean_environment"}
                }
            },
        },
        {
            "declarations": [
                {
                    "declaration": "Fixture.wrongPath",
                    "evidenceRef": (
                        "#/sections/other/_declarationEvidence/"
                        "evidence:000000000000000000000000"
                    ),
                }
            ],
            "_declarationEvidence": {
                "evidence:000000000000000000000000": {
                    "fields": {"/authority": "lean_environment"}
                }
            },
        },
    ],
    ids=[
        "reserved-key-without-declarations",
        "reserved-key-with-wrong-table-shape",
        "hybrid-inline-and-referenced-evidence",
        "dangling-evidence-reference",
        "unreferenced-evidence-entry",
        "evidence-reference-for-another-container",
    ],
)
def test_reserved_declaration_evidence_requires_canonical_container(
    payload: dict[str, object],
) -> None:
    with pytest.raises(
        ReportModelError,
        match="reserved _declarationEvidence key",
    ):
        compact_declaration_collections(
            payload,
            pointer=CONTAINER_POINTER,
        )


def test_nested_reserved_declaration_evidence_is_rejected() -> None:
    payload = {
        "declarations": [
            {
                "declaration": "Fixture.nested",
                "details": {"_declarationEvidence": {}},
            }
        ]
    }

    with pytest.raises(
        ReportModelError,
        match="reserved _declarationEvidence key",
    ):
        compact_declaration_collections(
            payload,
            pointer=CONTAINER_POINTER,
        )
