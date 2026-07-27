from __future__ import annotations

from typing import cast

import pytest

from ladon.snapshot import (
    AnalysisSnapshot,
    SnapshotEntry,
    SnapshotError,
    SnapshotMismatch,
    snapshot_from_source_index_manifest,
)


def snapshot() -> AnalysisSnapshot:
    return AnalysisSnapshot(
        source_index_fingerprint="sha256:index",
        entries={
            "Fixture.lean": SnapshotEntry.present(
                path="Fixture.lean",
                kind="lean_source",
                content=b"theorem fixture : True := by trivial\n",
                collection_refs=("source_index.declarations",),
            )
        },
        configuration={"backend": "text", "schema": "ladon-report-v2"},
    )


def test_snapshot_identity_and_round_trip_are_deterministic() -> None:
    first = snapshot()
    second = AnalysisSnapshot.from_mapping(first.to_dict())

    assert first.identity == second.identity
    assert second.to_dict() == first.to_dict()


def test_snapshot_registry_accepts_idempotent_later_inputs() -> None:
    captured = snapshot()
    registered = captured.register_bytes(
        path=".ladon/source-patterns.json",
        kind="policy",
        content=b'{"patterns":[]}',
        collection_refs=("analysis.source_patterns",),
    )
    same = registered.register(
        registered.entries[".ladon/source-patterns.json"]
    )

    assert same.identity == registered.identity
    assert ".ladon/source-patterns.json" in registered.entries
    with pytest.raises(SnapshotError, match="different state"):
        registered.register_bytes(
            path=".ladon/source-patterns.json",
            kind="policy",
            content=b'{"patterns":[1]}',
        )


def test_snapshot_configuration_is_deeply_immutable() -> None:
    captured = AnalysisSnapshot(
        source_index_fingerprint="sha256:index",
        entries={},
        configuration={"nested": {"values": [1, 2]}},
    )
    nested = cast(dict[str, object], captured.configuration["nested"])

    with pytest.raises(TypeError):
        nested["values"] = []
    assert captured.to_dict()["configuration"] == {
        "nested": {"values": [1, 2]}
    }


def test_snapshot_decoder_rejects_malformed_entry_rows() -> None:
    with pytest.raises(SnapshotError, match="rows must be objects"):
        AnalysisSnapshot.from_mapping(
            {
                "schema": "ladon-analysis-snapshot-v1",
                "sourceIndexFingerprint": "sha256:index",
                "entries": {"Fixture.lean": []},
            }
        )


def test_consumed_bytes_must_match_captured_manifest() -> None:
    captured = snapshot()
    captured.verify_bytes(
        "Fixture.lean",
        b"theorem fixture : True := by trivial\n",
    )

    with pytest.raises(
        SnapshotMismatch,
        match="source_changed_during_analysis",
    ):
        captured.verify_bytes(
            "Fixture.lean",
            b"theorem fixture : False := by trivial\n",
        )


def test_final_comparison_reports_changed_added_and_removed_paths() -> None:
    captured = snapshot()
    changed = SnapshotEntry.present(
        path="Fixture.lean",
        kind="lean_source",
        content=b"changed",
        collection_refs=("source_index.declarations",),
    )
    added = SnapshotEntry.present(
        path="Added.lean",
        kind="lean_source",
        content=b"added",
        collection_refs=("source_index.modules",),
    )

    decision = captured.compare(
        {"Fixture.lean": changed, "Added.lean": added}
    )

    assert decision.status == "changed"
    assert decision.to_dict()["diagnostic"] == "source_changed_during_analysis"
    assert [row["path"] for row in decision.mismatches] == [
        "Added.lean",
        "Fixture.lean",
    ]


def test_byte_stable_dirty_state_is_not_part_of_snapshot_identity() -> None:
    captured = snapshot()

    assert captured.compare(dict(captured.entries)).status == "stable"
    assert "Git" not in captured.to_dict()["configuration"]


def test_source_index_manifest_is_adopted_without_rereading_files() -> None:
    manifest = {
        "sources": [
            {
                "module": "Fixture",
                "path": "Fixture.lean",
                "status": "present",
                "bytes": 3,
                "sha256": "a" * 64,
            }
        ],
        "layout": {
            "stateFiles": [
                {
                    "name": "lakefile.toml",
                    "path": "lakefile.toml",
                    "status": "absent",
                    "bytes": 0,
                    "sha256": None,
                }
            ]
        },
    }

    captured = snapshot_from_source_index_manifest(
        source_index_fingerprint="sha256:index",
        manifest=manifest,
        configuration={"backend": "text"},
    )

    assert captured.entries["Fixture.lean"].sha256 == f"sha256:{'a' * 64}"
    assert captured.entries["lakefile.toml"].status == "absent"


def test_snapshot_rejects_absolute_or_parent_paths() -> None:
    with pytest.raises(SnapshotError, match="repository-relative"):
        SnapshotEntry.present(
            path="../outside",
            kind="policy",
            content=b"{}",
        )
