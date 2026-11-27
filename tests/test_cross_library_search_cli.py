"""Exercise the same normalized query through the public CLI at each freshness boundary."""
import json
import subprocess
import sys
from importlib.resources import files

import jsonschema
import pytest

from ladon.proof_search_index import build_proof_search_index, default_proof_search_index_path


def search(*args):
    return subprocess.run(
        [sys.executable, "-m", "ladon.entrypoint", "proof-search", "search", *map(str, args)],
        capture_output=True, text=True, check=False,
    )


def success_json(*args):
    proc = search(*args, "--format", "json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    path = files("ladon").joinpath("schemas", payload["schema"] + ".schema.json")
    jsonschema.Draft202012Validator(json.loads(path.read_text())).validate(payload)
    return payload


def test_normalized_query_has_parity_across_entry_points(tmp_path):
    query = ["type-text", "--fragment", "a+b", "--fragment", "Nat"]
    queries = tmp_path / "queries.json"
    queries.write_text(json.dumps([query]))
    manifests = []
    expected = []
    for name, mode in [("Mf", "verify"), ("mathlib", "stored"), ("RH", "stored")]:
        root = tmp_path / name
        root.mkdir()
        (root / "Demo.lean").write_text("theorem demo (a b : Nat) : a + b = a + b := rfl\n")
        index = build_proof_search_index(root, index_path=root / "types #1.sqlite").index_path
        entry = {"name": name, "indexPath": str(index.relative_to(tmp_path)), "freshness": mode}
        if mode == "verify":
            entry["repoRoot"] = name
        manifests.append(entry)
        standalone = success_json(*query, "--index", index)
        single = success_json("batch", "--queries", queries, "--index", index,
                              "--freshness", "stored")
        assert [r["candidateName"] for r in standalone["results"]] == ["demo"]
        assert single["queries"][0]["results"] == standalone["results"]
        expected.append(standalone["results"])
    manifest = tmp_path / "libraries.json"
    manifest.write_text(json.dumps(manifests))
    argv = ["batch", "--queries", queries, "--indexes", manifest]
    named = success_json(*argv)
    assert [g["name"] for g in named["groups"]] == ["Mf", "mathlib", "RH"]
    assert [g["batch"]["queries"][0]["results"] for g in named["groups"]] == expected
    verified_batch = named["groups"][0]["batch"]
    schema = files("ladon").joinpath("schemas", verified_batch["schema"] + ".schema.json")
    jsonschema.Draft202012Validator(json.loads(schema.read_text())).validate(verified_batch)
    rendered = search(*argv)
    assert rendered.returncode == 0, rendered.stderr
    assert "conclusion unavailable" in rendered.stdout
    assert all(label in rendered.stdout for label in ["Mf", "mathlib", "RH", "demo", "stored", "verified-fresh"])


def test_named_cli_publishes_partial_json_with_operational_exit(tmp_path):
    repo = tmp_path / "local"
    repo.mkdir()
    (repo / "Main.lean").write_text("theorem found : True := trivial\n")
    build_proof_search_index(repo)
    manifest = tmp_path / "indexes.json"
    manifest.write_text(json.dumps([
        {"name": "missing", "repoRoot": "absent"}, {"name": "local", "repoRoot": "local"},
    ]))
    queries = tmp_path / "queries.json"
    queries.write_text(json.dumps([["name", "--text", "found"]]))
    proc = search("batch", "--queries", queries, "--indexes", manifest, "--format", "json")
    from ladon.cli_execution import EXIT_OPERATIONAL

    assert proc.returncode == EXIT_OPERATIONAL
    payload = json.loads(proc.stdout)
    assert payload["status"] == "partial"
    missing, local = payload["groups"]
    assert missing["error"]["message"]
    assert local["batch"]["queries"][0]["results"][0]["candidateName"] == "found"


@pytest.mark.parametrize(("fragment", "expected"), [
    ("xs.head", ["plain"]),
    ("xs.head?", ["optionalHead"]),
    ("xs.head!", ["panicHead"]),
    ("Nat → ∀", ["adjacent"]),
])
def test_cli_fragment_search_preserves_lean_token_boundaries(tmp_path, fragment, expected):
    (tmp_path / "Main.lean").write_text(
        "axiom plain (xs : List Nat) (h : xs ≠ []) : xs.head h = 0\n"
        "axiom optionalHead (xs : List Nat) : xs.head? = none\n"
        "axiom panicHead (xs : List Nat) : xs.head! = 0\n"
        "axiom adjacent : Nat→∀ n : Nat, n = n\n"
    )
    index = build_proof_search_index(tmp_path).index_path
    result = success_json("type-text", "--index", index, "--fragment", fragment)
    assert [row["candidateName"] for row in result["results"]] == expected


@pytest.mark.parametrize("use_default_index", [False, True])
def test_named_cli_preserves_healthy_index_when_path_resolution_fails(tmp_path, use_default_index):
    (tmp_path / "Main.lean").write_text("theorem found : True := trivial\n")
    index = build_proof_search_index(tmp_path).index_path
    manifest = tmp_path / "indexes.json"
    broken_repo = tmp_path / "broken"
    loop = default_proof_search_index_path(broken_repo) if use_default_index else tmp_path / "loop.sqlite"
    loop.parent.mkdir(parents=True, exist_ok=True)
    loop.symlink_to(loop.name)
    selector = {"repoRoot": broken_repo.name} if use_default_index else {"indexPath": loop.name}
    manifest.write_text(json.dumps([
        {"name": "broken", **selector},
        {"name": "healthy", "indexPath": str(index.relative_to(tmp_path))},
    ]))
    queries = tmp_path / "queries.json"
    queries.write_text(json.dumps([["name", "--text", "found"]]))
    proc = search("batch", "--queries", queries, "--indexes", manifest, "--freshness", "stored", "--format", "json")
    from ladon.cli_execution import EXIT_OPERATIONAL

    assert proc.returncode == EXIT_OPERATIONAL, proc.stderr
    assert "Traceback" not in proc.stderr
    result = json.loads(proc.stdout)
    assert result["status"] == "partial"
    broken, healthy = result["groups"]
    assert broken["status"] == "unavailable"
    assert str(loop) in broken["error"]["message"]
    assert healthy["batch"]["queries"][0]["results"][0]["candidateName"] == "found"


@pytest.mark.parametrize(("kind", "option"), [("type-text", "--fragment"), ("name", "--text")])
def test_batch_text_distinguishes_a_missing_scope_from_no_matches(tmp_path, kind, option):
    (tmp_path / "Main.lean").write_text("axiom demo : Nat\n")
    index = build_proof_search_index(tmp_path).index_path
    queries = tmp_path / "queries.json"
    queries.write_text(json.dumps([
        [kind, option, "Int", "--scope", "module", "--root", name]
        for name in ("Main", "Missing")
    ]))
    proc = search("batch", "--queries", queries, "--index", index, "--freshness", "stored")
    assert proc.returncode == 0, proc.stderr
    first, second = proc.stdout.split("query 2:")
    assert "returned: 0" in first and "returned: 0" in second
    assert "root_not_indexed" not in first
    assert "root_not_indexed" in second and "Missing" in second
