"""Independent facade and CLI contracts for the core result-bundle profile."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from support.result_bundle_assertions import assert_integrity_report, parse_text

from ladon.entrypoint import main
from ladon.result_bundles import export_result_bundle, verify_result_bundle
from ladon.result_manifest_io import ResultManifestError

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "result_manifest"
MANIFEST = FIXTURE_DIR / "finite-map.json"
GUIDE = FIXTURE_DIR / "finite-map.guide.json"


def _selection(path: Path, *, entries: list[dict] | None = None) -> Path:
    payload = {
        "schema": "ladon-result-bundle-selection-v1",
        "supplier": {"identity": "bundle contract fixture", "kind": "human"},
        "entries": entries if entries is not None else [
            {"id": "guide-main", "role": "guide", "disclosure": "supplied",
             "permission": "include", "path": str(GUIDE)},
            {"id": "private-note", "role": "attachment", "disclosure": "redacted",
             "permission": "omit", "path": str(path.parent / "private-secret-unreadable.bin"),
             "reason": "not authorized for disclosure"},
        ],
        "lineageBindings": [],
        "identifiers": [],
        "externalDependencies": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _export(tmp_path: Path, *, entries: list[dict] | None = None) -> Path:
    selection = _selection(tmp_path / "selection.json", entries=entries)
    output = tmp_path / "result.zip"
    export_result_bundle(MANIFEST, selection, output)
    return output


def _index(archive: Path) -> dict:
    with zipfile.ZipFile(archive) as stream:
        return json.loads(stream.read("bundle.json"))


def _inventory(index: dict) -> list[dict]:
    rows = index.get("inventory", index.get("payloadInventory"))
    assert isinstance(rows, list), "bundle index must expose its payload inventory"
    assert all({"id", "role", "path", "bytes", "sha256"} <= row.keys() for row in rows)
    return rows


def test_export_verify_preserves_identity_and_reports_integrity_without_replay(tmp_path: Path) -> None:
    archive = _export(tmp_path)
    result = verify_result_bundle(archive)
    assert_integrity_report(result)
    index = _index(archive)
    assert index["schema"] == "ladon-result-bundle-v1"
    assert index["profile"] == "core-v1"
    assert index["resultId"] == "finite-map-example"
    assert index["revision"] == json.loads(MANIFEST.read_text())["revision"]


def test_inventory_is_exact_and_hashes_original_payload_bytes(tmp_path: Path) -> None:
    archive = _export(tmp_path)
    index = _index(archive)
    rows = _inventory(index)
    with zipfile.ZipFile(archive) as stream:
        actual = set(stream.namelist()) - {"bundle.json"}
        declared = {row["path"] for row in rows}
        assert declared == actual
        for row in rows:
            data = stream.read(row["path"])
            assert row["bytes"] == len(data)
            assert row["sha256"] == "sha256:" + hashlib.sha256(data).hexdigest()
    assert not any("private-secret" in row["path"] for row in rows)


def test_tampered_payload_is_rejected(tmp_path: Path) -> None:
    archive = _export(tmp_path)
    with zipfile.ZipFile(archive) as source:
        members = {name: source.read(name) for name in source.namelist()}
    victim = next(row["path"] for row in _inventory(json.loads(members["bundle.json"]))
                  if row["role"] == "guide")
    members[victim] += b" altered"
    changed = tmp_path / "tampered.zip"
    with zipfile.ZipFile(changed, "w", compression=zipfile.ZIP_STORED) as output:
        for name, data in members.items():
            output.writestr(name, data)
    with pytest.raises(ResultManifestError):
        verify_result_bundle(changed)


def test_omitted_unreadable_redacted_path_is_not_opened_or_disclosed(tmp_path: Path) -> None:
    archive = _export(tmp_path)
    raw = archive.read_bytes()
    assert b"private-secret-unreadable.bin" not in raw
    assert b"not authorized for disclosure" in raw
    result = verify_result_bundle(archive)
    assert "private-secret-unreadable.bin" not in json.dumps(result)


def test_export_failure_preserves_prior_archive_and_removes_staging(tmp_path: Path) -> None:
    selection = _selection(tmp_path / "selection.json")
    destination = tmp_path / "result.zip"
    destination.write_bytes(b"previous published result")
    with pytest.raises(ResultManifestError):
        export_result_bundle(MANIFEST, selection, destination, max_bytes=1)
    assert destination.read_bytes() == b"previous published result"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["result.zip", "selection.json"]


@pytest.mark.parametrize("mutate", [
    lambda value: value.update(schema="unknown-selection-v9"),
    lambda value: value["entries"].append(dict(value["entries"][0])),
])
def test_unknown_selection_schema_and_duplicate_entry_ids_fail_closed(tmp_path: Path, mutate) -> None:
    selection = _selection(tmp_path / "selection.json")
    payload = json.loads(selection.read_text())
    mutate(payload)
    selection.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ResultManifestError):
        export_result_bundle(MANIFEST, selection, tmp_path / "result.zip")
    assert not (tmp_path / "result.zip").exists()


def test_cli_export_and_verify_json_text_parity_and_outside_checkout(tmp_path: Path, capsys) -> None:
    selection = _selection(tmp_path / "selection.json")
    bundle = tmp_path / "result.zip"
    argv = ["result", "export", str(MANIFEST), "--selection", str(selection), "--output", str(bundle)]
    assert main(argv) == 0
    json_result = json.loads(capsys.readouterr().out)
    assert main(argv + ["--format", "text"]) == 0
    text_result = parse_text(capsys.readouterr().out)
    assert text_result == json_result

    verify_args = ["result", "verify", str(bundle)]
    assert main(verify_args) == 0
    verify_json = json.loads(capsys.readouterr().out)
    assert main(verify_args + ["--format", "text"]) == 0
    verify_text = parse_text(capsys.readouterr().out)
    assert verify_text == verify_json

    console = os.environ.get("LADON_CONSOLE", str(Path(sys.executable).with_name("ladon")))
    if Path(console).exists():
        child = subprocess.run([console, "result", "verify", str(bundle)], cwd=tmp_path,
                               capture_output=True, text=True, check=False, timeout=10)
        assert child.returncode == 0, child.stderr
        assert json.loads(child.stdout)["resultId"] == "finite-map-example"


def test_review_attachment_keeps_author_subject_revision_and_scope(tmp_path: Path) -> None:
    review_path = tmp_path / "review.json"
    review_path.write_text('{"comment":"historical assessment"}', encoding="utf-8")
    metadata = {
        "author": {"identity": "Reviewer A", "kind": "human"},
        "subjectRevision": json.loads(MANIFEST.read_text())["revision"],
        "scope": "paper-theorem-1",
    }
    entries = [{"id": "review-old", "role": "review", "disclosure": "supplied",
                "permission": "include", "path": str(review_path), "review": metadata}]
    archive = _export(tmp_path, entries=entries)
    row = next(item for item in _inventory(_index(archive)) if item["id"] == "review-old")
    assert row["review"] == metadata


def test_dangling_lineage_and_predecessor_references_are_rejected(tmp_path: Path) -> None:
    selection = _selection(tmp_path / "selection.json")
    value = json.loads(selection.read_text())
    value["lineageBindings"] = [{"entryId": "missing-lineage", "databaseId": "missing-store"}]
    selection.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ResultManifestError):
        export_result_bundle(MANIFEST, selection, tmp_path / "lineage.zip")

    predecessor_selection = _selection(
        tmp_path / "predecessor-selection.json",
        entries=[{"id": "orphan-predecessor", "role": "predecessor",
                  "disclosure": "supplied", "permission": "include", "path": str(MANIFEST)}],
    )
    with pytest.raises(ResultManifestError):
        export_result_bundle(MANIFEST, predecessor_selection, tmp_path / "history.zip")
