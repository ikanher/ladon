"""Exact-owner construction preserves conditional targets before proof replay."""

import copy
import json
from pathlib import Path

import pytest

from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal

HELPER = Path(__file__).parents[1] / 'src/ladon/lean/LadonProseExactGoal.lean'
FIXTURE = Path(__file__).parent / 'fixtures/real_prose_recognition/lean-toolchain'
DECLARATIONS = [
    'theorem Seed (n : Nat) : True := True.intro',
    'def Reading : Prop := False',
    'def First : Prop := True',
    'def Second : Prop := False',
]


def const(name):
    return {'const': name, 'levels': []}


def owner(index, name, kind, expression):
    line = DECLARATIONS[index]
    column = len('theorem ' if kind == 'theorem-type' else 'def ')
    return {'name': name, 'kind': kind, 'expression': expression,
            'range': {'startLine': index + 2, 'startColumn': 0,
                      'endLine': index + 2, 'endColumn': len(line),
                      'selectionStartLine': index + 2, 'selectionStartColumn': column,
                      'selectionEndLine': index + 2, 'selectionEndColumn': column + len(name)}}


def request():
    formal = {'forallE': {'name': '_', 'type': const('Nat'),
                         'body': const('True'), 'binderInfo': 'explicit'}}
    return {'schema': 'ladon-prose-exact-goal-v1', 'module': 'Case',
            'formal': owner(0, 'Seed', 'theorem-type', formal),
            'authored': owner(1, 'Reading', 'proposition-value', const('False')),
            'premises': [owner(2, 'First', 'proposition-value', const('True')),
                         owner(3, 'Second', 'proposition-value', const('False'))]}


@pytest.fixture(scope='module')
def project(tmp_path_factory):
    root = tmp_path_factory.mktemp('exact-goal')
    (root / 'lean-toolchain').write_bytes(FIXTURE.read_bytes())
    assert HELPER.is_file(), 'missing exact source-owner constructor'
    (root / 'LadonProseExactGoal.lean').write_bytes(HELPER.read_bytes())
    (root / '.lake/build/lib/lean').mkdir(parents=True)
    result = run(root, 'LadonProseExactGoal.lean', compile_module=True)
    assert result.succeeded, result.stdout + result.stderr
    return root


def run(root, filename, *, compile_module=False):
    execution = prepare_direct_lean_execution(root, None, pinned_toolchain(root),
                                              require_compiled_module=False)
    command = [*execution.command]
    if compile_module:
        command += ['-o', '.lake/build/lib/lean/LadonProseExactGoal.olean']
    return run_bounded_target_process(command + [filename], cwd=root,
                                      env=execution.environment, timeout_seconds=60,
                                      max_output_bytes=8 * 1024**2,
                                      max_rss_bytes=DEFAULT_MAX_RSS_BYTES)


def goal(value):
    return 'ladon_prose_exact_goal% ' + json.dumps(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')))


def source(value):
    return 'import LadonProseExactGoal\n' + '\n'.join(DECLARATIONS) + '\n' + (
        f'example : {goal(value)} := by\n  intro original first second\n  exact second\n')


def test_exact_goal_retains_formal_type_authored_value_and_ordered_premises(project):
    text = source(request())
    text += f'example : ({goal(request())}) = ((∀ n : Nat, True) → True → False → False) := rfl\n'
    (project / 'Case.lean').write_text(text)
    result = run(project, 'Case.lean')
    assert result.succeeded, result.stdout + result.stderr


def _owner_row(value, mutation):
    return value['premises'][0] if mutation.startswith('premise') else value[mutation.split('-')[0]]


def _mutate_owner(value, mutation):
    row = _owner_row(value, mutation)
    if mutation.endswith('-expression'):
        row['expression'] = const('True' if mutation.startswith('authored') else 'False')
    elif mutation.endswith('-range'):
        row['range']['endColumn'] += 1
    else:
        row['kind'] = 'proposition-value' if mutation.startswith('formal') else 'theorem-type'


def _mutate_request(value, mutation):
    if mutation.endswith(('-expression', '-range', '-kind')):
        _mutate_owner(value, mutation)
    elif mutation == 'module':
        value['module'] = 'Other'
    elif mutation == 'duplicate':
        value['premises'].append(copy.deepcopy(value['premises'][0]))
    elif mutation == 'unknown-key':
        value['admission'] = 'accepted'
    elif mutation == 'too-many-premises':
        value['premises'] *= 9
    else:
        value['formal']['name'] = 'True.intro'
        value['formal']['expression'] = const('True')


@pytest.mark.parametrize('mutation', [
    'module', 'formal-expression', 'authored-expression', 'formal-range', 'authored-range',
    'formal-kind', 'authored-kind', 'duplicate', 'premise-expression', 'premise-range',
    'unknown-key', 'too-many-premises', 'imported-formal',
])
def test_owner_substitution_fails_closed(project, mutation):
    value = copy.deepcopy(request())
    _mutate_request(value, mutation)
    (project / 'Case.lean').write_text(source(value))
    result = run(project, 'Case.lean')
    assert not result.succeeded, mutation
    assert 'error:' in result.stdout + result.stderr


def test_original_target_capture_completion_and_replay(project):
    text = 'import LadonProseExactGoal\n' + '\n'.join(DECLARATIONS) + '\n'
    text += f'theorem Witness : {goal(request())} := by\n  intro original first second\n  exact second\n'
    text += f'example : {goal(request())} := by\n  skip\n'
    (project / 'Case.lean').write_text(text)
    context = pinned_toolchain(project)
    captured = capture_source_goal(SourceGoalCaptureRequest(
        project, 'Case.lean', 'Case', len(text.splitlines()), 4, context))
    assert captured['status'] == 'captured', captured
    completed = complete_source_goal(SourceGoalCompletionRequest(
        project, captured['capture'], 'Witness', context))
    assert completed['status'] == 'completed', completed
    assert completed['replay']['status'] == 'accepted'
    assert completed['trust']['accepted'] is True
    assert completed['trust']['coverage'] == 'complete'
    assert not set(completed['trust']['observedAxioms']) - {'propext', 'Classical.choice', 'Quot.sound'}
