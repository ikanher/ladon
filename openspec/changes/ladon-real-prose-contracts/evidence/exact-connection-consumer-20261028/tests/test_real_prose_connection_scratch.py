"""Explicit scratch parents preserve source environments through capture/replay."""

import os
from pathlib import Path

from ladon import source_goal_capture as capture_api
from ladon.proof_slice import pinned_toolchain
from ladon.source_goal_capture import SourceGoalCaptureRequest
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal


def test_nested_capture_and_completion_use_owned_parent_without_changing_environment(tmp_path,monkeypatch):
    root, parent = tmp_path/'project', tmp_path/'owned-scratch'
    root.mkdir()
    parent.mkdir()
    pin = Path(__file__).parent/'fixtures/real_prose_recognition/lean-toolchain'
    (root/'lean-toolchain').write_bytes(pin.read_bytes())
    (root/'Case.lean').write_text('example : True := by\n  skip\n')
    context = pinned_toolchain(root)
    seen = []
    original = capture_api.tempfile.TemporaryDirectory
    def owned(*args,**kwargs):
        if kwargs.get('prefix','').startswith(('ladon-source-goal-','ladon-source-completion-')):
            assert Path(kwargs['dir']) == parent
            seen.append(kwargs['prefix'])
        return original(*args,**kwargs)
    monkeypatch.setattr(capture_api.tempfile,'TemporaryDirectory',owned)
    environment = os.environ.get('TMPDIR')
    captured = capture_api.capture_source_goal(SourceGoalCaptureRequest(root,'Case.lean','Case',2,4,context),
                                                workspace_parent=parent)
    assert captured['status'] == 'captured',captured
    completed = complete_source_goal(SourceGoalCompletionRequest(root,captured['capture'],'True.intro',context),
                                     workspace_parent=parent)
    assert completed['status'] == 'completed',completed
    assert 'ladon-source-completion-' in seen and seen.count('ladon-source-goal-') >= 2
    assert os.environ.get('TMPDIR') == environment
    assert pinned_toolchain(root).context_identity == context.context_identity
    assert list(parent.iterdir()) == []
