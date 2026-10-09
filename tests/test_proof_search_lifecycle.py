from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ladon.cli import main
from ladon.proof_search_index import build_proof_search_index
from ladon.proof_search_lifecycle import apply_prune, list_indexes, preview_prune
from ladon.sqlite_publication import acquire_publication_lock, release_publication_lock


def _repo(root: Path) -> Path:
    root.mkdir()
    (root / "Main.lean").write_text("theorem named : True := True.intro\n", encoding="utf-8")
    return root


def test_preview_and_apply_reclaim_only_selected_private_index(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "repo")
    default = build_proof_search_index(repo).index_path
    private = build_proof_search_index(
        repo, index_path=default.with_name("proof-search.session.sqlite")
    ).index_path
    inventory = list_indexes(repo)
    rows = {row["name"]: row for row in inventory["rows"]}
    assert rows[default.name]["reason"] == "default-index"
    assert rows[private.name]["classification"] == "disposable-private"

    preview = preview_prune(repo, selected=(private.name, default.name))
    assert default.exists() and private.exists()
    assert preview["eligibleBytes"] == private.stat().st_size
    path = tmp_path / "preview.json"
    path.write_text(json.dumps(preview), encoding="utf-8")
    applied = apply_prune(repo, path)
    assert applied["reclaimedBytes"] == preview["eligibleBytes"]
    assert default.exists() and not private.exists()
    assert private.with_name(private.name + ".lock").exists()
    again = apply_prune(repo, path)
    assert again["reclaimedBytes"] == 0


def test_apply_rechecks_replaced_file_and_active_publisher(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "repo")
    private = build_proof_search_index(
        repo, index_path=repo / ".ladon/index/proof-search.agent.sqlite"
    ).index_path
    preview = preview_prune(repo, selected=(private.name,))
    path = tmp_path / "preview.json"
    path.write_text(json.dumps(preview), encoding="utf-8")

    lock = acquire_publication_lock(private)
    try:
        blocked = apply_prune(repo, path)
        assert blocked["rows"][0]["reason"] == "active-publisher"
        assert private.exists()
    finally:
        release_publication_lock(lock)

    replacement = private.with_suffix(".replacement")
    replacement.write_bytes(private.read_bytes())
    replacement.replace(private)
    blocked = apply_prune(repo, path)
    assert blocked["rows"][0]["reason"] == "identity-or-ownership-changed"
    assert private.exists()


def test_uncertain_sidecar_is_protected(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "repo")
    private = build_proof_search_index(
        repo, index_path=repo / ".ladon/index/proof-search.session.sqlite"
    ).index_path
    Path(str(private) + "-journal").write_text("uncertain", encoding="utf-8")
    preview = preview_prune(repo, selected=(private.name,))
    assert preview["rows"][0]["reason"] == "active-or-uncertain-sidecar"
    assert preview["eligibleBytes"] == 0


@pytest.mark.parametrize("retained_kind,expected_table", [
    ("binder", "binders"),
    ("diagnostic", "proofir_diagnostics"),
    ("v3-environment", "proofir_v3_environments"),
    ("future-proofir", "proofir_future"),
])
def test_retained_evidence_private_index_is_protected(
    tmp_path: Path, retained_kind: str, expected_table: str
) -> None:
    repo = _repo(tmp_path / "repo")
    private = build_proof_search_index(
        repo, index_path=repo / ".ladon/index/proof-search.evidence.sqlite"
    ).index_path
    with sqlite3.connect(private) as connection:
        if retained_kind == "binder":
            declaration = connection.execute("SELECT id FROM declarations LIMIT 1").fetchone()[0]
            connection.execute(
                "INSERT INTO binders VALUES (?,?,?,?,?,?,?,?)",
                (declaration, 0, "h", "explicit", "True", 1, "lexical", "True"),
            )
        elif retained_kind == "diagnostic":
            generation = connection.execute(
                "SELECT generation_id FROM proofir_generations LIMIT 1"
            ).fetchone()[0]
            connection.execute(
                "INSERT INTO proofir_diagnostics VALUES (?,?,?,?,?,?,?)",
                ("diagnostic", generation, None, "configuration", "catalog", "missing", "{}"),
            )
        elif retained_kind == "v3-environment":
            connection.execute(
                "INSERT INTO proofir_v3_environments VALUES (?,?,?,?)",
                ("sha256:environment", None, None, "unresolved"),
            )
        else:
            connection.execute("CREATE TABLE proofir_future (payload TEXT NOT NULL)")
            connection.execute("INSERT INTO proofir_future VALUES ('retained')")
    preview = preview_prune(repo, selected=(private.name,))
    assert preview["rows"][0]["reason"] == f"retained-evidence:{expected_table}"
    assert preview["eligibleBytes"] == 0
    assert private.exists()


def test_cli_list_preview_apply_and_keep(tmp_path: Path, capsys) -> None:
    repo = _repo(tmp_path / "repo")
    private = build_proof_search_index(
        repo, index_path=repo / ".ladon/index/proof-search.private.sqlite"
    ).index_path
    assert main([
        "proof-search", "index", "list", "--repo-root", str(repo), "--format", "text"
    ]) == 0
    listed = capsys.readouterr().out
    assert private.name in listed
    assert "disposable-private" in listed

    preview_path = tmp_path / "preview.json"
    assert main([
        "proof-search", "index", "prune", "--repo-root", str(repo),
        "--select", private.name, "--keep", private.name,
        "--format", "json", "--output", str(preview_path),
    ]) == 0
    capsys.readouterr()
    assert json.loads(preview_path.read_text())["eligibleBytes"] == 0
    assert main([
        "proof-search", "index", "prune", "--repo-root", str(repo),
        "--apply", "--preview-file", str(preview_path), "--format", "json"
    ]) == 0
    applied = json.loads(capsys.readouterr().out)
    assert applied["rows"][0]["reason"] == "explicit-keep"
    assert private.exists()


def test_inventory_protects_foreign_symlink_and_uncertain_temp(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "repo")
    other = _repo(tmp_path / "other")
    folder = repo / ".ladon/index"
    foreign = build_proof_search_index(
        other, index_path=folder / "proof-search.foreign.sqlite"
    ).index_path
    (folder / "proof-search.link.sqlite").symlink_to(foreign)
    (folder / "proof-search.broken.sqlite").write_bytes(b"not-sqlite")
    (folder / ".proof-search.orphan.sqlite.123.tmp").write_text(
        "unknown", encoding="utf-8"
    )
    rows = {row["name"]: row for row in list_indexes(repo)["rows"]}
    assert rows[foreign.name]["reason"] == "foreign-repository"
    assert rows["proof-search.link.sqlite"]["reason"] == "symlink-or-nonregular"
    assert rows["proof-search.broken.sqlite"]["reason"].startswith("unreadable-index:")
    assert rows[".proof-search.orphan.sqlite.123.tmp"]["reason"] == "temporary-or-sidecar-ownership-unknown"


def test_list_bounds_inspection_and_reports_partial_byte_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ladon.proof_search_lifecycle as lifecycle

    repo = _repo(tmp_path / "repo")
    folder = repo / ".ladon/index"
    folder.mkdir(parents=True)
    for number in range(5):
        (folder / f"unknown-{number}").write_bytes(b"abc")
    inspected = []
    original = lifecycle._inspect

    def inspect(root, path, **kwargs):
        inspected.append(path.name)
        return original(root, path, **kwargs)

    monkeypatch.setattr(lifecycle, "_inspect", inspect)
    listing = list_indexes(repo, limit=2)
    assert listing["total"] == 5
    assert listing["returned"] == 2
    assert listing["truncated"] is True
    assert listing["totalBytes"] == 6
    assert listing["totalBytesScope"] == "returned-rows"
    assert inspected == ["unknown-0", "unknown-1"]


def test_age_filter_preview_keeps_private_index_when_named(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "repo")
    private = build_proof_search_index(
        repo, index_path=repo / ".ladon/index/proof-search.private.sqlite"
    ).index_path
    preview = preview_prune(repo, older_than_days=0, keep=(private.name,))
    assert any(row["name"] == private.name for row in preview["rows"])
    assert preview["eligibleBytes"] == 0
    assert private.exists()


def test_partial_delete_reports_failure_and_keeps_persistent_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    repo = _repo(tmp_path / "repo")
    private = build_proof_search_index(
        repo, index_path=repo / ".ladon/index/proof-search.private.sqlite"
    ).index_path
    preview_file = tmp_path / "preview.json"
    preview_file.write_text(
        json.dumps(preview_prune(repo, selected=(private.name,))), encoding="utf-8"
    )
    original_unlink = Path.unlink

    def fail_selected(path: Path, *args, **kwargs):
        if path == private:
            raise PermissionError("simulated denied deletion")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_selected)
    exit_code = main([
        "proof-search", "index", "prune", "--repo-root", str(repo),
        "--apply", "--preview-file", str(preview_file), "--format", "json",
    ])
    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "partial"
    assert output["reclaimedBytes"] == 0
    assert private.exists()
    assert private.with_name(private.name + ".lock").exists()
