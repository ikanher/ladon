"""Composition guards over independently checked actual Lean proof records."""
import json
from pathlib import Path

import pytest

from ladon._proof_contract_route_context_inputs import compose_requirement

FIXTURE = Path(__file__).parent / 'fixtures/proof_contract_route_context'


def _goals():
    return json.loads((FIXTURE / 'checked-composition.json').read_text())


def test_actual_checked_reading_and_transfer_reproduce_checked_final_term():
    goals = _goals()
    composed = compose_requirement(goals)
    assert composed['goal'] == goals[-1]['goal']
    assert composed['term'] == goals[-1]['term']
    assert composed['goalId'] == 'source-requirement'


@pytest.mark.parametrize('missing', ['completion', 'replay', 'trust', 'status'])
def test_incomplete_evidence_never_composes_a_final_proof(missing):
    goals = _goals()
    row = goals[1]
    if missing == 'completion':
        row['result']['completion']['status'] = 'unresolved'
    elif missing == 'replay':
        row['result']['completion']['replay']['status'] = 'rejected'
    elif missing == 'trust':
        row['result']['completion']['trust']['accepted'] = False
    else:
        row['status'] = 'unresolved'
    assert compose_requirement(goals) is None


def test_an_added_assumption_breaks_exact_transfer_link():
    goals = _goals()
    goals[1]['goal'] = 'False → (' + goals[1]['goal'] + ')'
    assert compose_requirement(goals) is None


def test_missing_checked_term_does_not_supply_a_requirement():
    goals = _goals()
    del goals[0]['term']
    assert compose_requirement(goals) is None


def test_missing_reading_channel_does_not_supply_a_requirement():
    assert compose_requirement(_goals()[1:]) is None
