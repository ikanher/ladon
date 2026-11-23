"""Named index batches keep independently validated results in manifest order."""
import json

import pytest

from ladon.proof_search_index import ProofSearchIndexError, build_proof_search_index


def make_index(root, source):
    root.mkdir()
    (root / "Main.lean").write_text(source)
    build_proof_search_index(root)


def write_manifest(path, entries):
    path.write_text(json.dumps(entries))


def test_named_batch_preserves_order_and_same_name_candidates(tmp_path):
    from ladon.proof_search_named_batch import run_named_batch

    first, second = tmp_path / "first", tmp_path / "second"
    make_index(first, "theorem shared : Nat := 1\n")
    make_index(second, "theorem shared : Nat := 2\n")
    manifest = tmp_path / "indexes.json"
    write_manifest(manifest, [
        {"name": "second", "repoRoot": "second"},
        {"name": "first", "repoRoot": "first"},
    ])
    result = run_named_batch(manifest, [["name", "--text", "shared"]])
    assert result["schema"] == "ladon-proof-search-named-batch-v1"
    assert result["operation"] == "search-batch"
    assert result["status"] == "available"
    assert [g["name"] for g in result["groups"]] == ["second", "first"]
    assert [g["batch"]["queries"][0]["results"][0]["candidateName"]
            for g in result["groups"]] == ["shared", "shared"]
    assert result["groups"][0]["batch"]["generationIdentity"] != result["groups"][1]["batch"]["generationIdentity"]


def test_named_batch_reports_mixed_success_and_unavailable_group(tmp_path):
    from ladon.proof_search_named_batch import run_named_batch

    good = tmp_path / "good"
    make_index(good, "theorem present : Nat := 1\n")
    manifest = tmp_path / "indexes.json"
    write_manifest(manifest, [
        {"name": "missing", "repoRoot": "absent"},
        {"name": "empty", "repoRoot": "good"},
    ])
    result = run_named_batch(manifest, [["name", "--text", "absent"]])
    assert result["status"] == "partial"
    assert result["groups"][0]["status"] == "unavailable"
    assert result["groups"][0]["error"]
    assert result["groups"][1]["status"] == "available"
    assert result["groups"][1]["batch"]["queries"][0]["results"] == []


@pytest.mark.parametrize("entries", [
    [{"name": "x", "repoRoot": "a"}, {"name": "x", "repoRoot": "b"}],
    [{"name": "x", "freshness": "stored"}],
    [{"name": "x", "indexPath": "x.sqlite", "freshness": "verify"}],
    [{"name": "x", "repoRoot": "a", "freshness": "unknown"}],
    [{"name": "x", "repoRoot": "a", "freshness": ["stored"]}],
    [{"name": "x", "repoRoot": "a", "freshness": {"mode": "stored"}}],
])
def test_manifest_is_validated_before_any_index_reads(tmp_path, monkeypatch, entries):
    from ladon import proof_search_batch
    from ladon.proof_search_named_batch import run_named_batch

    manifest = tmp_path / "indexes.json"
    write_manifest(manifest, entries)
    monkeypatch.setattr(proof_search_batch, "run_prepared_batch",
                        lambda *_args, **_kwargs: pytest.fail("index read before validation"), raising=False)
    with pytest.raises((ProofSearchIndexError, ValueError)):
        run_named_batch(manifest, [["name", "--text", "x"]])


def test_relative_index_path_and_stored_entry_work_without_repo(tmp_path):
    from ladon.proof_search_named_batch import run_named_batch

    repo = tmp_path / "repo"
    make_index(repo, "theorem archive_name : Nat := 1\n")
    manifest = tmp_path / "indexes.json"
    write_manifest(manifest, [{"name": "archive", "indexPath": "repo/.ladon/index/proof-search.sqlite",
                               "freshness": "stored"}])
    result = run_named_batch(manifest, [["name", "--text", "archive_name"]])
    assert result["status"] == "available"
    group = result["groups"][0]
    assert group["batch"]["freshness"] == "stored"
    assert group["batch"]["validation"]["captureCount"] == 0


def test_library_failure_does_not_discard_successful_groups(tmp_path, monkeypatch):
    from ladon import proof_search_batch
    from ladon.proof_search_named_batch import run_named_batch

    manifest = tmp_path / "indexes.json"
    write_manifest(manifest, [{"name": "large", "repoRoot": "a"}, {"name": "ok", "repoRoot": "b"}])
    def prepared(root, requests, **kwargs):
        if root.name == "a":
            raise ProofSearchIndexError("batch output exceeds selected byte allowance")
        return {"operation": "search-batch", "status": "available", "queries": []}
    monkeypatch.setattr(proof_search_batch, "run_prepared_batch", prepared, raising=False)
    result = run_named_batch(manifest, [["name", "--text", "x"]])
    assert result["status"] == "partial"
    assert [g["status"] for g in result["groups"]] == ["unavailable", "available"]


def test_verified_source_race_is_scoped_to_its_group(tmp_path, monkeypatch):
    from ladon import proof_search_batch
    from ladon.proof_search_named_batch import run_named_batch

    changing, stable = tmp_path / "changing", tmp_path / "stable"
    make_index(changing, "theorem old_name : Nat := 1\n")
    make_index(stable, "theorem stable_name : Nat := 2\n")
    manifest = tmp_path / "indexes.json"
    write_manifest(manifest, [{"name": "changing", "repoRoot": "changing"},
                              {"name": "stable", "repoRoot": "stable"}])
    original = proof_search_batch._query
    changed = []
    def query(connection, args):
        answer = original(connection, args)
        if not changed:
            (changing / "Main.lean").write_text("theorem new_name : Nat := 2\n")
            changed.append(True)
        return answer
    monkeypatch.setattr(proof_search_batch, "_query", query)
    result = run_named_batch(manifest, [["name", "--text", "name"]])
    assert result["status"] == "partial"
    assert result["groups"][0]["status"] == "unavailable"
    assert result["groups"][0]["freshness"] == "unstable-source"
    assert result["groups"][0]["batch"]["queries"] == []
    assert result["groups"][1]["status"] == "available"
    assert result["groups"][1]["batch"]["queries"][0]["results"][0]["candidateName"] == "stable_name"


def test_all_unavailable_is_unavailable_aggregate(tmp_path):
    from ladon.proof_search_named_batch import run_named_batch

    manifest = tmp_path / "indexes.json"
    write_manifest(manifest, [{"name": "missing-a", "repoRoot": "a"},
                              {"name": "missing-b", "repoRoot": "b"}])
    result = run_named_batch(manifest, [["name", "--text", "x"]])
    assert result["status"] == "unavailable"
    assert [group["status"] for group in result["groups"]] == ["unavailable", "unavailable"]


def test_aggregate_overflow_leaves_existing_output_untouched(tmp_path, monkeypatch, capsys):
    from ladon import proof_search_batch
    from ladon.cli import main

    queries = tmp_path / "queries.json"
    queries.write_text(json.dumps([["name", "--text", "x"]]))
    manifest = tmp_path / "indexes.json"
    write_manifest(manifest, [{"name": "first", "repoRoot": "a"},
                              {"name": "second", "repoRoot": "b"}])
    output = tmp_path / "result.json"
    output.write_text("keep existing file\n")
    monkeypatch.setattr(proof_search_batch, "run_prepared_batch", lambda *_args, **_kwargs: {
        "schema": "test", "operation": "search-batch", "status": "available",
        "generationIdentity": "generation", "queries": [], "padding": "x" * 600_000,
    })
    code = main(["proof-search", "search", "batch", "--queries", str(queries),
                 "--indexes", str(manifest), "--output", str(output), "--format", "json"])
    capsys.readouterr()
    assert code != 0
    assert output.read_text() == "keep existing file\n"



@pytest.mark.parametrize("library_count,query_count", [(9, 1), (8, 17)])
def test_named_request_bounds_precede_index_access(tmp_path, monkeypatch, library_count, query_count):
    from ladon import proof_search_batch
    from ladon.proof_search_named_batch import run_named_batch

    manifest = tmp_path / "indexes.json"
    write_manifest(manifest, [{"name": str(i), "repoRoot": "."} for i in range(library_count)])
    monkeypatch.setattr(proof_search_batch, "run_prepared_batch",
                        lambda *_args, **_kwargs: pytest.fail("index opened"))
    with pytest.raises(ProofSearchIndexError):
        run_named_batch(manifest, [["name", "--text", "test"]] * query_count)


@pytest.mark.parametrize("key", ["repository", "generationIdentity"])
def test_stored_index_missing_provenance_fails_only_its_group(tmp_path, key):
    import sqlite3

    from ladon.proof_search_named_batch import run_named_batch

    for name in ("damaged", "intact"):
        make_index(tmp_path / name, "axiom found : Nat\n")
    with sqlite3.connect(tmp_path / "damaged/.ladon/index/proof-search.sqlite") as db:
        db.execute("DELETE FROM metadata WHERE key=?", (key,))
    manifest = tmp_path / "indexes.json"
    write_manifest(manifest, [{"name": name, "indexPath": f"{name}/.ladon/index/proof-search.sqlite"}
                              for name in ("damaged", "intact")])
    result = run_named_batch(manifest, [["name", "--text", "found"]], freshness="stored")
    assert result["status"] == "partial"
    assert key in result["groups"][0]["error"]["message"]
    assert result["groups"][1]["status"] == "available"
