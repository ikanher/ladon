"""Capture shared expressions without expanding repeated subtrees."""
from __future__ import annotations

import json

from test_source_goal_completion_lean import _capture


def test_capture_retains_a_shared_local_value_in_bounded_structural_output(tmp_path):
    source = (
        'import Lean\nopen Lean\n'
        'macro "replicateTerm " n:num : term => do\n'
        '  let rec expand (n : Nat) : MacroM (TSyntax `term) := do\n'
        '    if n == 0 then `(term| (1 : Nat))\n'
        '    else\n'
        '      let child ← expand (n - 1)\n'
        '      `(($child, $child))\n'
        '  expand n.getNat\n'
        'example : True := by\n'
        '  have repeated := replicateTerm 9\n'
        '  skip\n'
    )
    _, _, capture = _capture(tmp_path, source, 12, 6)
    local = next(row for row in capture['goal']['localContext'] if row['userName'] == 'repeated')
    structural = local['valueStructural']
    assert structural.startswith('ladon-expr-dag-v1:')
    graph = json.loads(structural.split(':', 1)[1])
    assert len(graph['nodes']) < 1000
    assert graph['root'] == len(graph['nodes']) - 1
    assert len(structural.encode()) < 50000
    assert local['valueDisplay']
