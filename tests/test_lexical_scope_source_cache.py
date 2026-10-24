"""A no-source-change producer upgrade must re-extract lexical names."""

from ladon import source_index


def test_scope_producer_upgrade_does_not_reuse_v5_module_cache(tmp_path, monkeypatch):
    repository = tmp_path / 'repo'
    repository.mkdir()
    (repository / 'Main.lean').write_text('namespace Real\nsection Work\ntheorem t : True := trivial\n')
    cache = tmp_path / 'cache'
    current = source_index.SOURCE_INDEX_ALGORITHM_VERSION
    monkeypatch.setattr(source_index, 'SOURCE_INDEX_ALGORITHM_VERSION', 5)
    old = source_index.build_source_index(repository, cache_dir=cache)
    monkeypatch.setattr(source_index, 'SOURCE_INDEX_ALGORITHM_VERSION', current)
    new = source_index.build_source_index(repository, cache_dir=cache)
    assert new.index.fingerprint != old.index.fingerprint
    assert new.cache.reused_entries == 0
    assert new.index.entries[0].module.declaration_evidence[0].candidate_name == 'Real.t'
