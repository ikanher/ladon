"""Separate original readings, semantic transfers and a closed route demand."""
from __future__ import annotations

import copy

from ._proof_contract_bridge_goals import bridge_interpretation
from ._proof_contract_context_preparation import _digest
from .correspondence_interpretation import lower_formula


def route_goals(context, binding, state):
    from ._proof_contract_context_goals import ContextOutputLimit
    from ._proof_contract_source_obligations_inputs import bounded_json_size

    extras, symbols = _extra_goals(context, state)
    # Check the expanded representation before copying the existing rows.
    digest = _digest(binding)
    size = bounded_json_size([context['goals'], extras, binding], 8 * 1024**2)
    if size + (len(context['goals']) + len(extras)) * 128 > 8 * 1024**2:
        raise ContextOutputLimit('route context goals exceed 8 MiB')
    rows = copy.deepcopy(context['goals']) + extras
    for row in rows:
        row['routeBindingDigest'] = digest
        row['goalDigest'] = _digest({key: value for key, value in row.items() if key != 'goalDigest'})
    return rows, symbols


def _extra_goals(context, state):
    from ._proof_contract_source_obligations_formula import _formula_symbols
    from .proof_contract_planned_source import _planned_expected_symbols

    expected = _planned_expected_symbols(state['parentFresh'], state['providerFresh'], state['selected'])
    required = _denotation(state['selected']['contractRecord'], expected)
    parent_symbols = _formula_symbols(state['parentFresh']['observation']['normalizedTypeExpr'])
    parent = _denotation(state['parent']['contract'], parent_symbols)
    leaf = context['binding']['originalInterpretation']
    endpoint = state['parentReading']['payload']['record']
    source_formula = lower_formula(leaf['formula'], leaf['symbols'])
    requirement_formula = lower_formula(required['formula'], required['symbols'])
    formal_parent = lower_formula(parent['formula'], parent['symbols'])
    prose_parent = lower_formula(endpoint['formula'], endpoint['symbols'])
    rows = [_row('source-reading', source_formula),
            _row('contract-transfer', f'({source_formula}) → ({requirement_formula})'),
            _row('endpoint-transfer', f'({formal_parent}) → ({prose_parent})'),
            _row('source-requirement', requirement_formula)]
    rows[1].update(antecedentGoal=source_formula, consequentGoal=requirement_formula)
    symbols = {prefix + key: value for prefix, record in
        [('leaf_', leaf), ('endpoint_', endpoint), ('required_', required), ('parent_', parent)]
        for key, value in record['symbols'].items()}
    return rows, symbols


def _denotation(record, symbols):
    from .proof_contract_source_obligations import SourceIncomplete

    try:
        return bridge_interpretation({'contractRecord': record}, symbols,
                                     {'path': 'generated-route-denotation.txt'})
    except (ValueError, TypeError, KeyError) as error:
        raise SourceIncomplete('unsupported route contract denotation: ' + str(error)) from error


def _row(identity, formula):
    return {'id': identity, 'kind': identity, 'goal': formula, 'status': 'open'}
