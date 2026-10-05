"""A small dependent application must retain mathematics in compact transport."""
from ladon.semantic_projection_cards import candidate_card
from ladon.semantic_projection_core import semantic_projection_bytes
from ladon.semantic_projection_fit import finalize_projection


def local(i, origin='goal-introduced'):
    return {'localId': f'local:{i}', 'userName': f'x{i}', 'binderInfo': 'BinderInfo.implicit',
            'typeDisplay': 'Inhabited α' if i == 2 else 'α', 'typeStructural': 'structural-type',
            'valueDisplay': '', 'valueStructural': '', 'dependencies': ['local:0'] if i else [],
            'origin': origin}


def test_compact_dependent_application_keeps_residual_context_and_selected_type():
    selected = {'name': 'Main.step', 'typeDisplay': '∀ {α β : Type} [Inhabited α] (x : α) (y : β), x = x → y = y → x = x ∧ y = y',
                'typeStructural': 'structural-declaration-type', 'binders': [local(i, 'declaration-parameter') for i in range(7)]}
    check = {'status': 'applicable-with-residuals', 'applicationTerm': 'Main.step x y ?h ?k',
             'substitutions': [{'variable': f'v{i}', 'termDisplay': 'x', 'termStructural': 'fvar x'} for i in range(4)],
             'dischargedHypotheses': [], 'residualPremises': [{'typeDisplay': p, 'typeStructural': 'expr'} for p in ['x = x', 'y = y']],
             'applicationObservationVersion': 4, 'semanticProtocol': 'ladon-lean-semantic-v4/check-candidate',
             'residualContexts': [{'goalId': f'_uniq.{i}', 'localContext': [local(j) for j in range(5)]} for i in range(2)],
             'selectedDeclaration': selected}
    omissions = []
    card = candidate_card('Main.step', check, {}, 'llm', {}, omissions, pointer='/candidate')
    payload = {'schema': 'ladon-semantic-candidate-projection-v1', 'operation': 'check-candidate',
               'status': 'applicable-with-residuals', 'candidate': card, 'request': {},
               'coverage': {}, 'omissions': omissions, 'limitations': [],
               'projection': {'name': 'llm', 'canonicalSchema': 'ladon-semantic-candidate-check-result-v1',
                              'canonicalPayloadIdentity': 'sha256:' + 'a' * 64,
                              'limits': {'maxBytes': 8192, 'measurement': 'pretty-json-utf8-v1'}}}
    result = finalize_projection(payload, 8192)
    projected = result['candidate']['check']
    assert projected['selectedDeclaration']['typeDisplay'] == selected['typeDisplay']
    assert [r['typeDisplay'] for r in projected['residualPremises']] == ['x = x', 'y = y']
    assert [r['residualOrdinal'] for r in projected['residualContexts']] == [0, 1]
    assert projected['residualContexts'][0]['localContext'][0]['userName'] == 'x0'
    assert len(semantic_projection_bytes(result)) <= 8192
    assert result['omissions']
