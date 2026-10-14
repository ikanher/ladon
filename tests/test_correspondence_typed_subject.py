"""Actual elaboration exposes operand types, including nested overloads."""

import json
from pathlib import Path

import pytest

from ladon._source_goal_helpers import helper_source
from ladon.correspondence_interpretation import UnsupportedInterpretation, lower_formula
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution

FIXTURE = Path(__file__).parent / 'fixtures/correspondence_m1'


def numeral(value):
    return {'tag': 'const', 'name': str(value)}


def app(symbol, *args):
    return {'tag': 'app', 'symbol': symbol, 'args': list(args)}


@pytest.mark.parametrize('domain', ['Rat', 'Int', 'Nat'])
def test_actual_nested_operator_operands_have_declared_domain(tmp_path, domain):
    symbols = {'divide': {'leanName': 'HDiv.hDiv', 'leanType': f'{domain} → {domain} → {domain}'},
               'add': {'leanName': 'HAdd.hAdd', 'leanType': f'{domain} → {domain} → {domain}'}}
    term = app('add', app('divide', numeral(41), numeral(20)), numeral(1))
    formula = lower_formula({'tag': 'eq', 'left': term, 'right': term}, symbols)
    helper = Path(__file__).parents[1] / 'src/ladon/lean/ladon_typed_subject_helper.lean'
    source = tmp_path / 'Typed.lean'
    source.write_bytes(b'import Lean\nimport Init.Data.Rat\n' + helper_source(helper)
                       + f'\n#ladon_typed_subject ({formula})\n'.encode())
    execution = prepare_direct_lean_execution(FIXTURE, None, pinned_toolchain(FIXTURE),
                                              require_compiled_module=False)
    result = run_bounded_target_process([*execution.command, str(source)], cwd=FIXTURE,
                env=execution.environment, timeout_seconds=60, max_output_bytes=8*1024**2,
                max_rss_bytes=32*1024**3)
    assert result.succeeded, result.stdout + result.stderr
    frames = [line.removeprefix('LADON_TYPED_SUBJECT ') for line in result.stdout.splitlines()
              if line.startswith('LADON_TYPED_SUBJECT ')]
    assert len(frames) == 1
    subject = json.loads(frames[0])
    divisions = []
    for row in subject['applications']:
        graph = json.loads(row['operator']['structural'].removeprefix('ladon-expr-dag-v1:'))
        if graph['nodes'][graph['root']][:2] == ['const', '`HDiv.hDiv']:
            divisions.append(row)
    # Actual expression evidence must contain both nested divisions. No proof
    # of this reflexive formula establishes source fidelity or arithmetic truth.
    assert len(divisions) == 2, subject
    for row in divisions:
        assert [arg['type']['display'] for arg in row['arguments'][-2:]] == [domain, domain]


def test_unsupported_dependent_and_unknown_profiles_fail_explicitly():
    formula = app('dependent', numeral(1))
    with pytest.raises(UnsupportedInterpretation, match='dependent operator'):
        lower_formula(formula, {'dependent': {'leanName': 'id',
                      'leanType': '∀ (n : Nat), Nat'}})
    with pytest.raises(ValueError, match='profile'):
        lower_formula(numeral(1), {}, _profile='unrecognized')
