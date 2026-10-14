"""Request reuse preserves exact immutable file identity and rejects mutation."""

import pytest

from ladon.correspondence_preparation import PreparedSourceContext, _identity
from ladon.source_association_io import _file_identity


def owner_for(path):
    owner = object.__new__(PreparedSourceContext)
    owner.imports = {path: _identity(path)}
    owner.import_directories = {path.parent: owner.directory_fingerprint(path.parent)}
    owner.stale = False
    owner.cached_import_reads = 0
    return owner


def test_request_cache_preserves_identity_and_is_removed_on_exit(tmp_path):
    from ladon.correspondence_import_cache import verified_import_cache
    path = tmp_path / 'M.olean'
    path.write_bytes(b'original exact bytes')
    owner = owner_for(path)
    identity = _file_identity(path)
    with verified_import_cache(owner):
        assert _file_identity(path) == identity
        assert _file_identity(path) == identity
    assert owner.cached_import_reads == 2
    assert _file_identity(path) == identity
    assert owner.cached_import_reads == 2


@pytest.mark.parametrize('mutation', ['bytes', 'restored-bytes', 'absent-sidecar'])
def test_cached_import_mutation_cannot_inherit_original_identity(tmp_path, mutation):
    from ladon.correspondence_import_cache import verified_import_cache
    path = tmp_path / 'M.olean'
    path.write_bytes(b'original exact bytes')
    owner = owner_for(path)
    original = path.read_bytes()
    with verified_import_cache(owner):
        if mutation == 'absent-sidecar':
            sidecar = path.with_suffix('.ir')
            sidecar.write_bytes(b'transient foreign bytes')
            sidecar.unlink()
        else:
            path.write_bytes(b'changed bytes')
            if mutation == 'restored-bytes':
                path.write_bytes(original)
        with pytest.raises(ValueError, match='(?i)(stale|changed|mutation)'):
            _file_identity(path)
        assert owner.stale
