"""An imported goal cannot replace the closed subject observed in original source."""
from __future__ import annotations

from test_correspondence_local_environment import _case

from ladon.correspondence_check import _check_goal
from ladon.correspondence_preparation import PreparedSourceContext


def test_actual_prepared_capture_cannot_support_a_different_original_subject(tmp_path):
    root, source, toolchain, fresh = _case(tmp_path, 'local instance : ScopeProbe := ⟨1⟩')
    # Deliberately bypass finite admission to exercise the independent per-goal
    # authority boundary: ordinary source makes this proposition false, while
    # the imported module has lost the local instance and can prove it by rfl.
    context = PreparedSourceContext(root, fresh, source, toolchain,
                                    root / '.lake/build/lib/lean')
    try:
        context.compile(source)
        checked = _check_goal('ScopeProbe.value = 0', 'by rfl', root, source, {}, toolchain,
                              prepared=context)
        assert checked['status'] == 'unresolved', checked
        assert checked['diagnostic']['code'] == 'prepared-goal-subject-mismatch'
        assert 'completion' not in checked, 'different subject must stop before proof completion'
        assert checked['typedSubject']['subject']['structural'] != checked['capture']['capture']['goal']['typeStructural']
    finally:
        context.cleanup()
    assert not list((root / '.lake/build/lib/lean').glob('LadonPrepared*'))
