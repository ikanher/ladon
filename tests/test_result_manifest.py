from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import jsonschema
import pytest

from ladon._result_manifest_shape import manifest_schema, validate_shape
from ladon.result_manifest import validate_result_manifest
from ladon.result_manifest_io import (
    MAX_MANIFEST_BYTES,
    MAX_RESULT_BYTES,
    ResultManifestError,
    canonical_json,
    content_revision,
    load_result_manifest,
    parse_result_manifest,
)
from ladon.result_manifest_summary import manifest_summary

FIXTURE = Path(__file__).parent / "fixtures" / "result_manifest" / "finite-map.json"


@pytest.fixture
def manifest() -> dict:
    return json.loads(FIXTURE.read_text())


def seal(manifest: dict) -> dict:
    for row in manifest["claims"]:
        row["revision"] = content_revision("claim", row)
    for row in manifest["targets"]:
        row["revision"] = content_revision("target", row)
    manifest["revision"] = content_revision("manifest", manifest)
    return manifest


def summary(manifest: dict) -> dict:
    return manifest_summary(validate_result_manifest(manifest))


def test_fixture_validates_but_does_not_resolve_or_check_lean(manifest: dict) -> None:
    result = summary(manifest)
    assert result["status"] == "valid"
    assert result["canonicalResolution"] == {
        "status": "not-assessed", "unresolvedLinks": 1,
        "reason": "canonical-evidence-not-loaded",
    }
    assert result["mapping"]["unmappedComponents"] == 1
    assert result["reviewSummary"]["correspondenceStatuses"] == {"reviewed-with-differences": 1}
    assert result["reviewObservations"][0]["reviewerKind"] == "model"
    assert result["reviewSummary"]["reviewerAuthentication"] == "not-assessed"


def test_revisions_use_exact_utf8_and_distinct_domains() -> None:
    value = {"statement": "∀ n, n = n", "revision": "ignored"}
    raw = b'ladon-result-manifest-v1/claim\0' + '{"statement":"∀ n, n = n"}'.encode()
    expected = "sha256:" + hashlib.sha256(raw).hexdigest()
    assert content_revision("claim", value) == expected
    assert content_revision("target", value) != expected
    with pytest.raises(ResultManifestError, match="kind"):
        content_revision("unsupported", value)


@pytest.mark.parametrize("section,field", [("claims", "statement"), ("targets", "typeText")])
def test_changed_subject_retires_review(manifest: dict, section: str, field: str) -> None:
    manifest[section][0][field] += " changed"
    result = summary(seal(manifest))
    assert result["reviewSummary"]["current"] == 0
    assert result["reviewSummary"]["historical"] == 1
    assert result["reviewSummary"]["correspondenceStatuses"] == {"not-reviewed": 1}


def test_unsealed_statement_edit_is_rejected(manifest: dict) -> None:
    manifest["claims"][0]["statement"] += " changed"
    manifest["revision"] = content_revision("manifest", manifest)
    with pytest.raises(ResultManifestError, match="claim: content revision"):
        validate_result_manifest(manifest)


def test_changed_link_retires_review(manifest: dict) -> None:
    manifest["links"][0]["componentIds"].append("unrestricted-domain")
    result = summary(seal(manifest))
    assert result["reviewSummary"]["historical"] == 1


def test_conflicting_current_reviews_are_preserved(manifest: dict) -> None:
    review = copy.deepcopy(manifest["reviews"][0])
    review.update(id="review-two", status="reviewed-aligned", differences=[])
    review["reviewer"] = {"id": "reviewer-two", "kind": "human"}
    manifest["reviews"].append(review)
    result = summary(seal(manifest))
    assert result["reviewSummary"]["correspondenceStatuses"] == {"disputed": 1}
    assert len(result["reviewObservations"]) == 2


def test_one_to_many_targets_and_shared_targets(manifest: dict) -> None:
    target = copy.deepcopy(manifest["targets"][0])
    target.update(id="different-environment")
    target["environment"]["digest"] = "sha256:" + "b" * 64
    manifest["targets"].append(target)
    manifest["links"][0]["targetIds"].append(target["id"])
    link = copy.deepcopy(manifest["links"][0])
    link.update(id="second-link", componentIds=["unrestricted-domain"])
    manifest["links"].append(link)
    result = summary(seal(manifest))
    assert result["mapping"]["unmappedComponents"] == 0
    assert result["canonicalResolution"]["unresolvedLinks"] == 2
    assert result["reviewSummary"]["historical"] == 1


@pytest.mark.parametrize("collection", ["claims", "targets", "links", "reviews"])
def test_duplicate_ids_rejected(manifest: dict, collection: str) -> None:
    manifest[collection].append(copy.deepcopy(manifest[collection][0]))
    with pytest.raises(ResultManifestError, match="duplicate ID"):
        validate_result_manifest(seal(manifest))


@pytest.mark.parametrize("field,value", [
    ("claimId", "missing"), ("targetIds", ["missing"]),
    ("componentIds", ["missing"]),
])
def test_dangling_links_rejected(manifest: dict, field: str, value: object) -> None:
    manifest["links"][0][field] = value
    with pytest.raises(ResultManifestError, match="reference|component"):
        validate_result_manifest(seal(manifest))


def test_review_target_set_must_match_its_current_link(manifest: dict) -> None:
    manifest["reviews"][0]["targetRevisions"][0]["targetId"] = "missing"
    with pytest.raises(ResultManifestError, match="target set"):
        validate_result_manifest(seal(manifest))


def test_contradictory_target_snapshot_rejected(manifest: dict) -> None:
    target = copy.deepcopy(manifest["targets"][0])
    target.update(id="contradiction", typeText="False")
    manifest["targets"].append(target)
    with pytest.raises(ResultManifestError, match="contradictory"):
        validate_result_manifest(seal(manifest))


@pytest.mark.parametrize("path", ["../outside.lean", "/tmp/outside.lean", "C:\\outside.lean"])
def test_source_paths_are_not_escaping(manifest: dict, path: str) -> None:
    manifest["targets"][0]["source"]["path"] = path
    with pytest.raises(ResultManifestError, match="source path"):
        validate_result_manifest(seal(manifest))


@pytest.mark.parametrize("raw", [
    b'{"schema":"one","schema":"two"}', b'{"x":NaN}', b'{"x":Infinity}',
    b'[]', b'\xff', b'[' * 2000 + b']' * 2000,
])
def test_strict_json_rejections(raw: bytes) -> None:
    with pytest.raises(ResultManifestError):
        parse_result_manifest(raw)


def test_sparse_oversized_input_rejected_before_parsing(tmp_path: Path) -> None:
    path = tmp_path / "oversized.json"
    with path.open("wb") as stream:
        stream.truncate(MAX_MANIFEST_BYTES + 1)
    with pytest.raises(ResultManifestError, match="input limit"):
        load_result_manifest(path)


def test_manifest_returns_detached_snapshot(manifest: dict) -> None:
    validated = validate_result_manifest(manifest)
    manifest["claims"][0]["statement"] = "different"
    assert validated["claims"][0]["statement"] != "different"


@pytest.mark.parametrize("mutation", ["version", "unknown", "type", "id", "empty", "timestamp"])
def test_shape_rejections_agree_with_jsonschema(manifest: dict, mutation: str) -> None:
    changes = {
        "version": lambda: manifest.update(schema="unknown"),
        "unknown": lambda: manifest.update(extra=True),
        "type": lambda: manifest.update(claims=True),
        "id": lambda: manifest.update(resultId="bad id"),
        "empty": lambda: manifest["claims"][0].update(components=[]),
        "timestamp": lambda: manifest["reviews"][0].update(timestamp="2026-10-02"),
    }
    changes[mutation]()
    with pytest.raises(ResultManifestError):
        validate_shape(manifest)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(manifest, manifest_schema(), format_checker=jsonschema.FormatChecker())


def test_packaged_schema_accepts_fixture(manifest: dict) -> None:
    jsonschema.Draft202012Validator.check_schema(manifest_schema())
    jsonschema.validate(manifest, manifest_schema(), format_checker=jsonschema.FormatChecker())


@pytest.mark.parametrize("text", ["\ud800", "∀" * 22000])
def test_unicode_and_byte_bounds(manifest: dict, text: str) -> None:
    manifest["claims"][0]["statement"] = text
    with pytest.raises(ResultManifestError, match="Unicode|byte limit"):
        validate_result_manifest(manifest)


def test_large_review_projection_retains_total_and_omissions(manifest: dict) -> None:
    original = manifest["reviews"][0]
    manifest["reviews"] = [{**copy.deepcopy(original), "id": f"review-{i}"} for i in range(125)]
    result = summary(seal(manifest))
    assert len(canonical_json(result)) + 1 <= MAX_RESULT_BYTES
    assert result["reviewSummary"]["current"] == 125
    assert len(result["reviewObservations"]) + result["omissions"]["reviewObservations"] == 125


@pytest.mark.parametrize("mutation,match", [
    ("link", "reference"), ("duplicate-target", "duplicate target"),
    ("differences", "anchored differences"),
])
def test_invalid_review_bindings(manifest: dict, mutation: str, match: str) -> None:
    review = manifest["reviews"][0]
    if mutation == "link":
        review["linkId"] = "missing"
    elif mutation == "duplicate-target":
        review["targetRevisions"].append(copy.deepcopy(review["targetRevisions"][0]))
    else:
        review["differences"] = []
    with pytest.raises(ResultManifestError, match=match):
        validate_result_manifest(seal(manifest))


def test_collection_cap_rejected_before_duplicate_identity_check(manifest: dict) -> None:
    manifest["claims"] *= 1001
    with pytest.raises(ResultManifestError, match="collection limit"):
        validate_result_manifest(manifest)


def test_aggregate_collection_cap(manifest: dict) -> None:
    original = manifest["claims"][0]
    manifest["claims"] = [
        {**original, "id": f"claim-{i}", "components": [f"part-{j}" for j in range(1000)]}
        for i in range(101)
    ]
    with pytest.raises(ResultManifestError, match="aggregate"):
        validate_result_manifest(manifest)


def test_unresolved_artifact_reference_is_never_dereferenced(manifest: dict) -> None:
    manifest["targets"][0]["subjectRef"] = {
        "artifactId": "sha256:" + "f" * 64, "subjectId": "external-subject",
    }
    result = summary(seal(manifest))
    assert result["canonicalResolution"]["reason"] == "canonical-evidence-not-loaded"
    assert result["reviewSummary"]["historical"] == 1
