from pathlib import Path

import pytest

from ladon.proofir_packet import build_packet_manifest, verify_packet_manifest


def test_manifest_records_hash_size_and_source_state(tmp_path: Path) -> None:
    source = tmp_path / "proof-state.md"
    source.write_text("state\n", encoding="utf-8")
    manifest = build_packet_manifest(
        tmp_path, [("proof-state.md", "proof-state", "packet-local")]
    )
    entry = manifest["files"][0]
    assert entry["bytes"] == 6
    assert len(entry["sha256"]) == 64
    assert manifest["sourceState"]["toolchainFiles"] == []
    verify_packet_manifest(tmp_path, manifest)


def test_manifest_fails_closed_for_missing_or_changed_files(tmp_path: Path) -> None:
    source = tmp_path / "proof-state.md"
    source.write_text("state\n", encoding="utf-8")
    manifest = build_packet_manifest(
        tmp_path, [("proof-state.md", "proof-state", "packet-local")]
    )
    source.write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        verify_packet_manifest(tmp_path, manifest)
    source.unlink()
    with pytest.raises(ValueError, match="missing"):
        verify_packet_manifest(tmp_path, manifest)


def test_manifest_rejects_omitted_source_at_build(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="cli.py"):
        build_packet_manifest(tmp_path, [("cli.py", "cli", "packet-local")])


def test_manifest_rejects_vacuous_or_tampered_inventory(tmp_path: Path) -> None:
    source = tmp_path / "proof-state.md"
    source.write_text("state\n", encoding="utf-8")
    manifest = build_packet_manifest(
        tmp_path, [("proof-state.md", "proof-state", "packet-local")]
    )
    with pytest.raises(ValueError, match="non-empty"):
        verify_packet_manifest(tmp_path, {**manifest, "files": []})
    tampered = dict(manifest)
    tampered["inventoryDigest"] = "0" * 64
    with pytest.raises(ValueError, match="inventory digest"):
        verify_packet_manifest(tmp_path, tampered)
    with pytest.raises(ValueError, match="legacy"):
        verify_packet_manifest(tmp_path, {"format": "proofir-review-packet-manifest-v1", "files": manifest["files"]})


def test_manifest_rejects_unadvertised_regular_file(tmp_path: Path) -> None:
    source = tmp_path / "proof-state.md"
    source.write_text("state\n", encoding="utf-8")
    manifest = build_packet_manifest(
        tmp_path, [("proof-state.md", "proof-state", "packet-local")]
    )
    (tmp_path / "extra.txt").write_text("unlisted\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unadvertised"):
        verify_packet_manifest(tmp_path, manifest)
