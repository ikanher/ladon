from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon.inspection_adapters import load_inspection_dataset
from ladon.inspection_models import InspectionCompatibilityError
from ladon.source_index import build_source_index
from ladon.source_index_cache import manifest_digest


def cached_source_index(tmp_path: Path) -> Path:
    """Return one canonical cache envelope emitted by the source index."""

    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "Demo.lean").write_text(
        "theorem cached : True := by trivial\n",
        encoding="utf-8",
    )
    built = build_source_index(
        repository,
        cache_dir=tmp_path / "cache",
    )
    assert built.cache.cache_path is not None
    return built.cache.cache_path


def test_canonical_source_index_cache_envelope_is_directly_inspectable(
    tmp_path: Path,
) -> None:
    entry = cached_source_index(tmp_path)

    dataset = load_inspection_dataset(
        entry,
        "modules",
        artifact_kind="source-index",
    )

    assert [row.fields["module"] for row in dataset.rows] == ["Demo"]
    assert dataset.coverage["id"] == "source_index.modules"


def test_source_index_cache_envelope_requires_exact_outer_shape(
    tmp_path: Path,
) -> None:
    entry = cached_source_index(tmp_path)
    envelope = json.loads(entry.read_text(encoding="utf-8"))
    envelope["untrusted"] = True
    entry.write_text(json.dumps(envelope), encoding="utf-8")

    with pytest.raises(
        InspectionCompatibilityError,
        match="unsupported source-index schema",
    ):
        load_inspection_dataset(
            entry,
            "modules",
            artifact_kind="source-index",
        )


def test_source_index_cache_envelope_requires_matching_manifests(
    tmp_path: Path,
) -> None:
    entry = cached_source_index(tmp_path)
    envelope = json.loads(entry.read_text(encoding="utf-8"))
    envelope["fingerprintManifest"]["algorithmVersion"] = -1
    entry.write_text(json.dumps(envelope), encoding="utf-8")

    with pytest.raises(
        InspectionCompatibilityError,
        match="envelope manifest does not match its payload",
    ):
        load_inspection_dataset(
            entry,
            "modules",
            artifact_kind="source-index",
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("fingerprintVersion", "foreign-fingerprint-v999", "fingerprint version"),
        ("indexSchema", "ladon-source-index-v999", "manifest schema"),
        ("algorithmVersion", 999, "algorithm identity"),
    ],
)
def test_self_consistent_foreign_analysis_identity_is_rejected(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    entry = cached_source_index(tmp_path)
    envelope = json.loads(entry.read_text(encoding="utf-8"))
    manifest = envelope["fingerprintManifest"]
    manifest[field] = value
    envelope["payload"]["fingerprintManifest"][field] = value
    envelope["payload"]["fingerprint"] = manifest_digest(manifest)
    entry.write_text(json.dumps(envelope), encoding="utf-8")

    with pytest.raises(InspectionCompatibilityError, match=message):
        load_inspection_dataset(
            entry,
            "modules",
            artifact_kind="source-index",
        )
