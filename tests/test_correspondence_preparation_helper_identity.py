"""Actual helper bytes are frozen at preparation and ABA mutation stays stale."""
import pytest
from test_correspondence_prepared_context import _case

from ladon import correspondence_preparation as preparation


def test_restored_actual_helper_material_cannot_inherit_prepared_authority(tmp_path, monkeypatch):
    repo, source, _, fresh, toolchain, prepare, _ = _case(tmp_path)
    helper = tmp_path / 'typed-helper.lean'
    helper.write_bytes(preparation.helper_material_paths()[0].read_bytes())
    codec = preparation.helper_material_paths()[1]
    monkeypatch.setattr(preparation, 'helper_material_paths', lambda: [helper, codec])
    original = helper.read_bytes()
    with (pytest.raises(ValueError, match='(?i)(stale|helper|changed)'),
          prepare(repo, fresh, source.read_bytes(), toolchain) as context):
        assert context is not None
        context.verify()
        helper.write_bytes(original + b'\n-- helper mutation probe\n')
        helper.write_bytes(original)
        with pytest.raises(ValueError, match='(?i)(stale|helper|changed)'):
            context.verify()
        assert context.stale
