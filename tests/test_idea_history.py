"""Historical annotations must not acquire proof authority or survive changed statements silently."""

import copy
import hashlib
import json
import sqlite3

import pytest
from test_proof_search_index import sample_repository

from ladon.idea_history import apply_catalogue, historical_projection, rebind_links
from ladon.proof_search_index import build_proof_search_index


def catalogue(db):
    row = db.execute(
        "SELECT package,module,name,type_text FROM declarations ORDER BY id LIMIT 1"
    ).fetchone()
    return {
        "schema": "ladon-ideas-v1",
        "ideas": [
            {
                "id": "sa",
                "title": "Stochastic approximation",
                "statement": "Root finding with noisy observations",
                "scope_note": "test fixture",
            }
        ],
        "sources": [
            {
                "id": "rm",
                "citation": "Robbins and Monro (1951)",
                "version": "original",
                "url": None,
                "artifact_path": None,
                "artifact_sha256": None,
            }
        ],
        "attributions": [
            {
                "id": "a",
                "idea_id": "sa",
                "source_id": "rm",
                "source_locator": "title",
                "year_start": 1951,
                "year_end": 1951,
                "precision": "year",
                "dating_basis": "publication year; test attribution only",
                "review_status": "reviewed",
                "reviewer": "fixture",
                "reviewed_at": "2026-10-31",
                "is_selected": 1,
            }
        ],
        "links": [
            {
                "id": "l",
                "idea_id": "sa",
                "package": row[0],
                "module": row[1],
                "declaration_name": row[2],
                "statement_sha256": hashlib.sha256((row[3] or "").encode()).hexdigest(),
                "relation": "formalizes",
                "review_status": "proposed",
                "evidence_locator": "fixture",
                "note": "test only",
            }
        ],
        "dependencies": [],
    }


@pytest.fixture
def indexed(tmp_path):
    repo = sample_repository(tmp_path)
    result = build_proof_search_index(repo)
    with sqlite3.connect(result.index_path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        yield repo, db


def test_exact_decade_and_unassessed(indexed):
    _, db = indexed
    data = catalogue(db)
    apply_catalogue(db, data, source_path="fixture")
    decl = db.execute("SELECT declaration_id FROM declaration_idea_bindings").fetchone()[0]
    assert historical_projection(db, [decl])[decl][0]["idea_year"] == 1951
    data["attributions"][0].update(year_start=1940, year_end=1949, precision="decade")
    apply_catalogue(db, data, source_path="fixture")
    date = historical_projection(db, [decl])[decl][0]
    assert date["idea_year"] is None and date["guess_of_the_decade"] == 1940
    assert historical_projection(db, ["absent"])["absent"][0]["status"] == "unassessed"


@pytest.mark.parametrize(
    "mutation",
    [
        "cycle",
        "duplicate_selection",
        "exact_without_source",
        "bad_decade",
        "unreviewed_selection",
        "unknown_field",
        "bad_reference",
    ],
)
def test_invalid_catalogue_is_atomic(indexed, mutation):
    _, db = indexed
    data = catalogue(db)
    apply_catalogue(db, data, source_path="fixture")
    before = "\n".join(db.iterdump())
    changed = copy.deepcopy(data)
    a = changed["attributions"][0]
    if mutation == "cycle":
        changed["dependencies"] = [
            {
                "id": "e",
                "parent_idea_id": "sa",
                "child_idea_id": "sa",
                "evidence": "x",
                "review_status": "proposed",
            }
        ]
    elif mutation == "duplicate_selection":
        changed["attributions"].append({**a, "id": "a2"})
    elif mutation == "exact_without_source":
        a["source_id"] = None
    elif mutation == "bad_decade":
        a.update(precision="decade", year_start=1951, year_end=1960)
    elif mutation == "unreviewed_selection":
        a["review_status"] = "proposed"
    elif mutation == "unknown_field":
        a["publication_magic"] = True
    else:
        changed["links"][0]["idea_id"] = "absent"
    with pytest.raises(ValueError):
        apply_catalogue(db, changed, source_path="bad")
    assert "\n".join(db.iterdump()) == before


def test_statement_change_and_delete_retain_authored_link(indexed):
    _, db = indexed
    apply_catalogue(db, catalogue(db), source_path="fixture")
    decl = db.execute("SELECT declaration_id FROM declaration_idea_bindings").fetchone()[0]
    db.execute("UPDATE declarations SET type_text='different' WHERE id=?", (decl,))
    rebind_links(db)
    assert db.execute("SELECT resolution FROM declaration_idea_bindings").fetchone()[0] == "stale"
    db.execute("DELETE FROM declarations WHERE id=?", (decl,))
    rebind_links(db)
    assert db.execute("SELECT resolution FROM declaration_idea_bindings").fetchone()[0] == "missing"
    assert db.execute("SELECT count(*) FROM declaration_ideas").fetchone()[0] == 1


def test_build_sync_query_and_refresh(tmp_path):
    from ladon.idea_migration import read_ideas, sync_ideas
    from ladon.proof_search_index import query_proof_search_index, update_proof_search_index
    from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist

    repo = sample_repository(tmp_path)
    path = build_proof_search_index(repo).index_path
    with sqlite3.connect(path) as db:
        data = catalogue(db)
    (repo / "ladon-ideas.json").write_text(json.dumps(data))
    sync_ideas(repo)
    first = read_ideas(repo)
    assert first["inputStatus"] == "current"
    rows = query_proof_search_index(repo)["results"]
    selected = [row for row in rows if row["historicalIdeas"][0]["idea_year"] == 1951]
    assert len(selected) == 1
    with sqlite3.connect(path) as db:
        result = query_type_shortlist(db, TypeSearchRequest(pattern="Nat"))
        assert all("historicalIdeas" in row for row in result["results"])
    # Complete rebuild reproduces authored rows and current bindings.
    build_proof_search_index(repo)
    assert read_ideas(repo)["tables"] == first["tables"]
    # Ordinary source update preserves authored records but invalidates a changed signature.
    source = repo / selected[0]["path"]
    source.write_text(source.read_text().replace(selected[0]["typeText"], "ChangedSignature"))
    update_proof_search_index(repo)
    assert (
        read_ideas(repo)["tables"]["declaration_idea_bindings"]["rows"][0]["resolution"] == "stale"
    )
    (repo / "ladon-ideas.json").unlink()
    sync_ideas(repo)
    assert read_ideas(repo)["inputStatus"] == "missing-retained"
    assert len(read_ideas(repo)["tables"]["ideas"]["rows"]) == 1


def test_nontrivial_cycle_and_ambiguous_link(indexed):
    _, db = indexed
    data = catalogue(db)
    data["ideas"].append({**data["ideas"][0], "id": "other"})
    data["dependencies"] = [
        {
            "id": "e1",
            "parent_idea_id": "sa",
            "child_idea_id": "other",
            "evidence": "fixture",
            "review_status": "proposed",
        },
        {
            "id": "e2",
            "parent_idea_id": "other",
            "child_idea_id": "sa",
            "evidence": "fixture",
            "review_status": "proposed",
        },
    ]
    with pytest.raises(ValueError, match="cycle"):
        apply_catalogue(db, data, source_path="fixture")
    data["dependencies"].pop()
    apply_catalogue(db, data, source_path="fixture")
    decl = db.execute("SELECT declaration_id FROM declaration_idea_bindings").fetchone()[0]
    names = [row[1] for row in db.execute("PRAGMA table_info(declarations)")]
    row = list(db.execute("SELECT * FROM declarations WHERE id=?", (decl,)).fetchone())
    row[names.index("id")] = "duplicate"
    db.execute(f"INSERT INTO declarations VALUES ({','.join('?' for _ in names)})", row)
    rebind_links(db)
    assert (
        db.execute("SELECT resolution FROM declaration_idea_bindings").fetchone()[0] == "ambiguous"
    )


def test_missing_catalogue_cannot_erase_history_on_rebuild(tmp_path):
    from ladon.idea_migration import sync_ideas
    from ladon.proof_search_index import ProofSearchIndexError

    repo = sample_repository(tmp_path)
    path = build_proof_search_index(repo).index_path
    with sqlite3.connect(path) as db:
        data = catalogue(db)
    authored = repo / "ladon-ideas.json"
    authored.write_text(json.dumps(data))
    sync_ideas(repo)
    authored.unlink()
    before = path.read_bytes()
    with pytest.raises(ProofSearchIndexError, match="catalogue"):
        build_proof_search_index(repo)
    assert path.read_bytes() == before


def test_public_commands_are_executable(tmp_path, capsys):
    from ladon.cli import main

    repo = sample_repository(tmp_path)
    build_proof_search_index(repo)
    for operation in ["migrate", "ideas-sync", "ideas"]:
        assert (
            main(["proof-search", "index", operation, "--repo-root", str(repo), "--format", "json"])
            == 0
        )
        assert json.loads(capsys.readouterr().out)["status"]
