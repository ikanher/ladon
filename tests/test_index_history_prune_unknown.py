"""Unknown evidence layouts cannot be declared disposable by cleanup."""
from __future__ import annotations

import sqlite3

import pytest

from ladon.proof_search_index import build_proof_search_index
from ladon.proof_search_lifecycle import preview_prune


@pytest.mark.parametrize('extension', ['table', 'column'])
def test_prune_protects_unknown_evidence_extensions(tmp_path, extension):
    repo = tmp_path / 'repo'
    repo.mkdir()
    (repo / 'Main.lean').write_text('theorem initial : True := True.intro\n')
    index = build_proof_search_index(repo, index_path=repo / '.ladon/index/proof-search.unknown.sqlite').index_path
    with sqlite3.connect(index) as connection:
        if extension == 'table':
            connection.execute('CREATE TABLE user_evidence(payload TEXT)')
            connection.execute("INSERT INTO user_evidence VALUES ('must preserve')")
        else:
            connection.execute('ALTER TABLE modules ADD COLUMN user_evidence TEXT')
            connection.execute("UPDATE modules SET user_evidence='must preserve'")
    original = index.read_bytes()
    result = preview_prune(repo, selected=(index.name,))
    assert result['rows'][0]['classification'] == 'protected'
    assert index.read_bytes() == original
