"""The production witness command parses a single proof term, never commands."""

import json
from pathlib import Path

import pytest
from test_real_prose_exact_goal import DECLARATIONS, goal, request, run
from test_real_prose_exact_goal import project as _project

from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal

project = _project


@pytest.fixture(scope='module')
def witness_root(project):
    name = 'LadonProseConnectionWitness'
    source = Path(__file__).parents[1]/'src/ladon/lean'/f'{name}.lean'
    (project/source.name).write_bytes(source.read_bytes())
    execution = prepare_direct_lean_execution(project,None,pinned_toolchain(project),require_compiled_module=False)
    result = run_bounded_target_process([*execution.command,'-o',f'.lake/build/lib/lean/{name}.olean',source.name],
        cwd=project,env=execution.environment,timeout_seconds=60,max_output_bytes=8*1024**2,max_rss_bytes=12*1024**3)
    assert result.succeeded,result.stdout+result.stderr
    return project


def witness_source(proof):
    encoded = json.dumps(json.dumps(request(),sort_keys=True,separators=(',',':')))
    return ('import LadonProseConnectionWitness\n'+'\n'.join(DECLARATIONS)+'\n'
            +f'#ladon_connection_witness {encoded} {json.dumps(proof)}\n')


def test_isolated_proof_builds_the_exact_conditional_witness(witness_root):
    text = witness_source('by intro original first second; exact second')
    text += 'example : (∀ n : Nat, True) → True → False → False := LadonCheckedConnectionWitness\n'
    (witness_root/'Case.lean').write_text(text)
    result = run(witness_root,'Case.lean')
    assert result.succeeded,result.stdout+result.stderr


@pytest.mark.parametrize('proof', [
    'by intro original first second; exact second)\naxiom Injected : False\n--',
    'by intro original first second; exact second\naxiom Injected : False',
])
def test_source_command_injection_is_rejected_as_a_nonterm(witness_root,proof):
    (witness_root/'Case.lean').write_text(witness_source(proof))
    result = run(witness_root,'Case.lean')
    assert not result.succeeded
    assert 'not an isolated Lean term' in result.stdout+result.stderr


def test_sorry_in_a_parsed_term_is_still_rejected_by_independent_trust(witness_root):
    text = witness_source('by sorry')+f'example : {goal(request())} := by\n  skip\n'
    (witness_root/'Case.lean').write_text(text)
    context = pinned_toolchain(witness_root)
    captured = capture_source_goal(SourceGoalCaptureRequest(witness_root,'Case.lean','Case',len(text.splitlines()),4,context))
    assert captured['status'] == 'captured',captured
    result = complete_source_goal(SourceGoalCompletionRequest(witness_root,captured['capture'],
                                                             'LadonCheckedConnectionWitness',context))
    assert result['status'] != 'completed'
    assert result['trust']['accepted'] is False
