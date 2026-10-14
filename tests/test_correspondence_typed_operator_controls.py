"""Signed Int elaboration and an incompatible but reflexive application."""
import json
from pathlib import Path

from ladon._source_goal_helpers import helper_source
from ladon.correspondence_interpretation import lower_formula
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution

FIXTURE = Path(__file__).parent / 'fixtures/correspondence_m1'


def observed(formula, path):
    helper = Path(__file__).parents[1] / 'src/ladon/lean/ladon_typed_subject_helper.lean'
    path.write_bytes(b'import Lean\nimport Init.Data.Rat\n' + helper_source(helper)
                    + f'\n#ladon_typed_subject ({formula})\n'.encode())
    execution = prepare_direct_lean_execution(FIXTURE, None, pinned_toolchain(FIXTURE),
                                              require_compiled_module=False)
    return run_bounded_target_process([*execution.command, str(path)], cwd=FIXTURE,
        env=execution.environment, timeout_seconds=60, max_output_bytes=8*1024**2,
        max_rss_bytes=32*1024**3)


def test_actual_signed_integer_operand_stays_int(tmp_path):
    term = {'tag': 'app', 'symbol': 'neg', 'args': [{'tag': 'const', 'name': '-3'}]}
    symbols = {'neg': {'leanName': 'Neg.neg', 'leanType': 'Int → Int'}}
    formula = lower_formula({'tag': 'eq', 'left': term,
                             'right': {'tag': 'const', 'name': '3'}}, symbols)
    result = observed(formula, tmp_path / 'Signed.lean')
    assert result.succeeded, result.stdout + result.stderr
    frame = next(line.removeprefix('LADON_TYPED_SUBJECT ') for line in result.stdout.splitlines()
                 if line.startswith('LADON_TYPED_SUBJECT '))
    subject = json.loads(frame)
    negations = [row for row in subject['applications']
                 if 'Neg.neg' in row['operator']['display']]
    assert len(negations) == 2
    assert all(row['arguments'][-1]['type']['display'] == 'Int' for row in negations)
    assert subject['type']['display'] == 'Prop'


def test_wrong_operator_cannot_pass_a_reflexive_typing_probe(tmp_path):
    term = {'tag': 'app', 'symbol': 'add', 'args': [{'tag': 'const', 'name': '1'},
                                                  {'tag': 'const', 'name': '2'}]}
    formula = lower_formula({'tag': 'eq', 'left': term, 'right': term},
                             {'add': {'leanName': 'Nat.add', 'leanType': 'Rat → Rat → Rat'}})
    result = observed(formula, tmp_path / 'Mismatch.lean')
    assert not result.succeeded
    assert 'type mismatch' in (result.stdout + result.stderr).lower()
    assert 'LADON_TYPED_SUBJECT ' not in result.stdout
