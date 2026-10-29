"""Repeated source-goal elaboration must not acquire random binder identities."""

import json

from test_real_bound_prefix_lean import FIXTURE, lean, prefix_project

__all__ = ["prefix_project"]


def test_prefix_goal_identity_is_independent_of_generated_module_path(prefix_project):
    root, types = prefix_project
    strong, weak = 'PrefixExamples.wide', 'PrefixExamples.narrow'
    quote = json.dumps
    args = f'{quote(strong)} {quote(types[strong])} {quote(weak)} {quote(types[weak])} 0 4 0'
    source = ('import LadonRealBoundPrefix\n' + FIXTURE.read_text() +
              f'\ndef generatedGoal : Prop := ladon_real_bound_prefix% {args}\n'
              'open Lean Elab Command\n'
              'run_cmd liftTermElabM do\n'
              '  let info ← getConstInfo `generatedGoal\n'
              '  logInfo m!"PREFIX_STRUCTURE:{repr info.value?}"\n')
    observations = []
    for name in ('FirstGoal', 'SecondGoal'):
        (root / (name + '.lean')).write_text(source)
        run = lean(root, name + '.lean')
        assert run.succeeded, run.stdout + run.stderr
        observations.append(run.stdout.split('PREFIX_STRUCTURE:', 1)[1])
    assert observations[0] == observations[1]
