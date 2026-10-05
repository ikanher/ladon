"""Current owner compilation does not claim historical whole-tree freshness."""
from __future__ import annotations

import test_source_association as fixture

from ladon.lean_toolchain import resolve_toolchain_context


def test_unrelated_source_edit_keeps_exact_compiled_owner_association(tmp_path):
    _, capture = fixture._api()
    previous, _ = fixture._context(tmp_path)
    artifacts = fixture._stored_checked_artifacts(tmp_path, previous)
    (tmp_path / 'Unrelated.lean').write_text('def unrelated := 1\n')
    current = resolve_toolchain_context(tmp_path, lake_path=previous.lake_path,
                                        lean_path=previous.lean_path,
                                        environment=previous.environment)
    assert current.source_tree_identity != previous.source_tree_identity
    result = capture(fixture._request(tmp_path, current, artifacts), artifacts,
                     process_runner=fixture._runner(ilean=fixture._ilean()))
    assert result['status'] == 'associated', result
    assert result['checking'] == 'not-assessed'
