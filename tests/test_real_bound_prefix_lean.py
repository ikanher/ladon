"""Actual kernel controls for source-derived prefix implications."""

import json
import os
import shutil
from pathlib import Path

import pytest

from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.semantic_lean_execution import prepare_direct_lean_execution

FIXTURE = Path(__file__).parent / 'fixtures/real_bound_native/PrefixExamples.lean'
SOURCES = Path(__file__).parents[1] / 'src/ladon/lean'


def clean_root(root):
    selected = os.environ.get('LADON_MATHLIB_TEST_ROOT')
    if selected is None:
        pytest.skip('set LADON_MATHLIB_TEST_ROOT to a compiled Mathlib project')
    original = Path(selected).resolve()
    context = pinned_toolchain(original)
    (root / 'lean-toolchain').write_text((original / 'lean-toolchain').read_text())
    (root / '.lake/build/lib/lean').mkdir(parents=True)
    for index, library in enumerate(context.library_roots):
        target = root / f'.lake/packages/import{index}/.lake/build/lib/lean'
        target.parent.mkdir(parents=True)
        target.symlink_to(library, target_is_directory=True)


def lean(root, file, *, output=None):
    execution = prepare_direct_lean_execution(root, None, pinned_toolchain(root), require_compiled_module=False)
    args = [*execution.command]
    if output:
        args += ['-o', output]
    return run_bounded_target_process([*args, file], cwd=root, env=execution.environment,
                                     timeout_seconds=60, max_output_bytes=8 * 1024**2,
                                     max_rss_bytes=DEFAULT_MAX_RSS_BYTES)


@pytest.fixture(scope='module')
def prefix_project(tmp_path_factory):
    root = tmp_path_factory.mktemp('real-prefix-rules')
    clean_root(root)
    for name in ('LadonRealBound', 'LadonRealBoundBinding', 'LadonRealBoundPrefix'):
        shutil.copy2(SOURCES / (name + '.lean'), root / (name + '.lean'))
        run = lean(root, name + '.lean', output=f'.lake/build/lib/lean/{name}.olean')
        assert run.succeeded, run.stdout + run.stderr
    names = ['PrefixExamples.wide', 'PrefixExamples.narrow',
             'PrefixExamples.Alternative.higher', 'PrefixExamples.Alternative.lower']
    query = ('import LadonRealBoundPrefix\n' + FIXTURE.read_text() + '\nopen Lean Elab Command\n'
             'elab "#prefix_type " target:str : command => do\n'
             '  liftTermElabM do\n'
             '    let value ← Ladon.RealBoundBinding.observedTypeJson target.getString.toName\n'
             '    logInfo m!"PREFIX_EXPR:{value.compress}"\n')
    query += '\n'.join('#prefix_type ' + json.dumps(name) for name in names)
    (root / 'Query.lean').write_text(query)
    run = lean(root, 'Query.lean')
    assert run.succeeded, run.stdout + run.stderr
    types = [line.split('PREFIX_EXPR:', 1)[1] for line in run.stdout.splitlines() if 'PREFIX_EXPR:' in line]
    assert len(types) == 4
    return root, dict(zip(names, types, strict=True))


def check(root, types, strong, weak, index, high, low, *, admission=None, stale=False):
    quote = lambda text: json.dumps(text, ensure_ascii=False)
    expected = types[strong].replace('"const":"Nat"', '"const":"Int"', 1) if stale else types[strong]
    args = f'{quote(strong)} {quote(expected)} {quote(weak)} {quote(types[weak])} {index} {high} {low}'
    measure = 'PrefixExamples.Alternative.measure' if index else 'PrefixExamples.measure'
    indices = '0' if index else ''
    law = f'ladon_bound_admission% {quote(weak)} {quote(types[weak])} {quote(measure)} [{indices}]'
    term = admission or 'by intros; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl'
    source = ('import LadonRealBoundPrefix\n' + FIXTURE.read_text() +
              f'\nexample : ladon_real_bound_prefix% {args} := by\n'
              f'  have admitted : ({law}) := ({term})\n'
              f'  exact ladon_real_bound_prefix_proof% {args} admitted\n')
    (root / 'Check.lean').write_text(source)
    return lean(root, 'Check.lean')


@pytest.mark.parametrize('strong,weak,index,high,low', [
    ('PrefixExamples.wide', 'PrefixExamples.narrow', 0, 4, 0),
    ('PrefixExamples.Alternative.higher', 'PrefixExamples.Alternative.lower', 1, 7, 2),
])
def test_checked_prefix_rule_works_in_independent_families(prefix_project, strong, weak, index, high, low):
    root, types = prefix_project
    run = check(root, types, strong, weak, index, high, low)
    assert run.succeeded, run.stdout + run.stderr


def test_reverse_direction_is_not_inferred_from_two_admissions(prefix_project):
    root, types = prefix_project
    run = check(root, types, 'PrefixExamples.narrow', 'PrefixExamples.wide', 0, 0, 4)
    assert not run.succeeded


def test_unproved_admission_is_not_a_rule_premise(prefix_project):
    root, types = prefix_project
    run = check(root, types, 'PrefixExamples.wide', 'PrefixExamples.narrow', 0, 4, 0, admission='by trivial')
    assert not run.succeeded


def test_actual_order_and_source_expression_are_rechecked(prefix_project):
    root, types = prefix_project
    wrong_order = check(root, types, 'PrefixExamples.wide', 'PrefixExamples.narrow', 0, 7, 0)
    assert not wrong_order.succeeded
    stale = check(root, types, 'PrefixExamples.wide', 'PrefixExamples.narrow', 0, 4, 0, stale=True)
    assert not stale.succeeded
