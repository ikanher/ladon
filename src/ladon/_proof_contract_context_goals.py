"""Separate obligations under a freshly rebuilt native original context."""
from __future__ import annotations

import copy
import hashlib

from ._proof_contract_bridge_goals import _canonical
from .correspondence_check import _local_bindings, _parts
from .correspondence_transport import transport_inputs


class ContextOutputLimit(ValueError):
    """Expanded goal evidence cannot fit the fixed output budget."""


def build_context_goals(prepared, binding):
    """Preserve ordered channels and add typed formal-domain witnesses.

    The preparation worker validates and rebuilds the original native plan.
    These witnesses establish domain admissibility of the mapped values;
    semantic transport remains a separate conclusion obligation.
    """
    _validate(prepared, binding)
    occurrences = _occurrences(prepared['slice']['nodes'][0]['premises'])
    rows = _copy_rows(prepared['obligations'], occurrences)
    maps = [i for i, row in enumerate(rows) if row['id'] == 'object-map']
    if not prepared['residuals'] and maps:
        rows.insert(maps[0], {'id': 'domain', 'kind': 'domain-admissibility',
                              'goal': _domain_goal(prepared), 'status': 'open'})
    _admit_bindings(rows, binding)
    for row in rows:
        row['binding'] = copy.deepcopy(binding)
        row['goalDigest'] = 'sha256:' + hashlib.sha256(_canonical(row)).hexdigest()
    return rows


def _admit_bindings(rows, binding):
    from ._proof_contract_planned_source_inputs import _planned_input_size

    # Each row adds a binding key, digest and JSON punctuation. Reserve more
    # than their actual fixed cost before copying any potentially large binding.
    size = _planned_input_size(rows) + len(rows) * (_planned_input_size(binding) + 256)
    if size > 8 * 1024**2:
        raise ContextOutputLimit('expanded context goals exceed the output budget')


def _validate(prepared, binding):
    required = {'interpretation', 'slice', 'objectMap', 'obligations', 'residuals'}
    if not isinstance(prepared, dict) or not required <= set(prepared):
        raise ValueError('context bridge requires a rebuilt native plan')
    if not isinstance(binding, dict) or not binding:
        raise ValueError('owned native checkpoint binding required')
    if not isinstance(prepared['obligations'], list) or len(prepared['obligations']) > 4096:
        raise ValueError('invalid bounded prepared obligations')
    if not isinstance(prepared['residuals'], list):
        raise TypeError('invalid correspondence residuals')


def _occurrences(premises):
    if not isinstance(premises, list) or len(premises) > 4096:
        raise ValueError('invalid bounded original premise occurrences')
    result = {}
    for premise in premises:
        occurrence = premise['occurrence']
        if type(occurrence) is not int or not 0 <= occurrence < 4096:
            raise ValueError('invalid source premise occurrence')
        for prefix in ('premise-', 'provider-'):
            identity = prefix + str(occurrence)
            if identity in result:
                raise ValueError('duplicate original premise occurrence')
            result[identity] = occurrence
    return result


def _copy_rows(obligations, occurrences):
    rows, identities = [], set()
    for original in obligations:
        if not isinstance(original, dict) or original.get('status') != 'open':
            raise ValueError('only freshly rebuilt open obligations may be bridged')
        identity = original['id']
        if not isinstance(identity, str) or identity in identities:
            raise ValueError('duplicate or invalid obligation identity')
        if identity == 'domain':
            raise ValueError('original correspondence cannot supply its own domain goal')
        identities.add(identity)
        row = copy.deepcopy(original)
        if identity in occurrences:
            row['occurrence'] = occurrences[identity]
        rows.append(row)
    return rows


def _domain_goal(prepared):
    linked, mapped = transport_inputs(prepared['slice'], prepared['objectMap'])
    scope, prefix, _assumptions, _conclusion = _parts(prepared['interpretation'],
        [row['name'] for row in linked['localContext']])
    checking = copy.deepcopy(prepared)
    lets, _allowed = _local_bindings(linked, mapped, scope, checking)
    if checking['residuals']:
        raise ValueError('domain goal cannot lower every actual object binding')
    witnesses = [_domain_witness(row) for row in linked['localContext']
                 if row['name'] in mapped]
    return prefix + lets + (' ∧ '.join(witnesses) if witnesses else 'True')


def _domain_witness(local):
    type_display, name = local['type']['display'], local['name']
    if not isinstance(type_display, str) or not type_display or not isinstance(name, str):
        raise ValueError('domain witness requires an exact typed formal local')
    return f'(∃ (ladonDomainWitness : {type_display}), ladonDomainWitness = {name})'
