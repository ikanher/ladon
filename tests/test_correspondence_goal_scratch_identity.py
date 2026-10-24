"""The generated-goal writer is part of the correspondence implementation."""
import shutil
from pathlib import Path

from ladon import correspondence_implementation as implementation


def test_goal_scratch_helper_change_invalidates_checker_implementation(tmp_path, monkeypatch):
    package = tmp_path / 'ladon'
    shutil.copytree(Path(implementation.__file__).parent, package,
                    ignore=shutil.ignore_patterns('__pycache__'))
    monkeypatch.setattr(implementation, '__file__', str(package / 'correspondence_implementation.py'))
    before = implementation.implementation_digest()
    helper = package / '_proof_contract_goal_scratch.py'
    original = helper.read_bytes()
    helper.write_bytes(original + b'\n# changed generated-goal writer\n')
    assert implementation.implementation_digest() != before
    helper.write_bytes(original)
    assert implementation.implementation_digest() == before
