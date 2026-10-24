"""Derived Nat requirements and separate, construction-bound bridge subjects."""
from __future__ import annotations

import copy
import hashlib
import json

from .correspondence_interpretation import lower_formula, validate_interpretation, validate_symbols

_BINDING_KEYS = ('selectedDemand', 'selectedDemandDigest', 'selectedIdentity', 'backwardRequestDigest', 'backwardResultDigest',
    'desiredReadingId', 'parentReadingId', 'providerReadingId', 'freshParentSnapshotId',
    'freshProviderSnapshotId', 'parentSnapshotId', 'providerSnapshotId',
    'generatedSourceDigest', 'prefixDigest', 'selectedRouteId', 'requestDigest')


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()


def bridge_interpretation(selected, provider_symbols, source):
    """Lower the verified selected offset with freshly bound provider symbols."""
    if not isinstance(selected, dict) or set(selected) != {'contractRecord'}:
        raise ValueError('selected requirement must contain exactly contractRecord')
    record = selected['contractRecord']
    offset = _selected_offset(record)
    _validate_telescope(record)
    symbols = _typed_symbols(provider_symbols)
    if not isinstance(source, dict) or set(source) != {'path'}:
        raise ValueError('generated interpretation requires a sidecar path')
    quote = _canonical(record)
    digest = hashlib.sha256(quote).hexdigest()
    return validate_interpretation({'id': 'generated-bridge-' + digest,
        'source': {'path': source['path'], 'startLine': 1, 'endLine': 1,
                   'quote': quote.decode(), 'sha256': digest},
        'formula': _formula(offset), 'symbols': symbols}, None)


def _selected_offset(record):
    if not isinstance(record, dict):
        raise TypeError('selected contract must be an object')
    regularity = record.get('features', {}).get('regularity', {})
    if regularity.get('state', 'known') != 'known':
        raise ValueError('selected requirement needs known regularity')
    offset = regularity.get('offset')
    if type(offset) is not int or not 0 <= offset < 10**20:
        raise ValueError('selected offset is outside the Nat bridge fragment')
    if record.get('assumptions', []) != []:
        raise ValueError('assumptions are outside the Nat bridge fragment')
    if record.get('profileId', 'norm-scale-v1') != 'norm-scale-v1':
        raise ValueError('unsupported selected contract profile')
    return offset


def _validate_telescope(record):
    telescope = record.get('telescope')
    if telescope is None:
        return
    if not isinstance(telescope, list) or len(telescope) != 2:
        raise ValueError('bridge supports exactly two telescope binders')
    for index, binder in enumerate(telescope):
        if (not isinstance(binder, dict) or binder.get('binderId') != f'b{index}'
                or binder.get('quantifier') != 'forall' or not isinstance(binder.get('typeId'), str)):
            raise ValueError('bridge supports ordered universal b0,b1 binders only')


def _typed_symbols(provider):
    roles = {'out': ('leftOperator', 'Nat → Nat → Nat'),
             'input': ('inputScale', 'Nat → Nat → Nat'),
             'map': ('map', 'Nat → Nat'), 'coefficient': ('constantName', 'Nat')}
    symbols = {key: {'leanName': provider[role], 'leanType': type_}
               for key, (role, type_) in roles.items()}
    symbols.update({key: {'leanName': name, 'leanType': 'Nat → Nat → Nat'}
                    for key, name in [('add', 'Nat.add'), ('mul', 'Nat.mul')]})
    validate_symbols(symbols)
    return symbols


def _formula(offset):
    def variable(identity):
        return {'tag': 'var', 'id': identity}

    def application(symbol, *args):
        return {'tag': 'app', 'symbol': symbol, 'args': list(args)}

    scale = application('add', variable('b0'), {'tag': 'const', 'name': str(offset)})
    body = {'tag': 'le',
        'left': application('out', variable('b0'), application('map', variable('b1'))),
        'right': application('mul', {'tag': 'const', 'name': 'coefficient'},
                             application('input', scale, variable('b1')))}
    for identity, name in [('b1', 'x'), ('b0', 's')]:
        body = {'tag': 'forall', 'binder': {'id': identity, 'name': name, 'domain': 'Nat'},
                'body': body}
    return body


def bridge_goals(prepared, construction):
    """Keep source supply, identity domain, typed map and transfer independent."""
    interpretation = prepared['interpretation']
    formula = lower_formula(interpretation['formula'], interpretation['symbols'])
    by_id = _prepared_rows(prepared['obligations'])
    rows = [
        {'id': 'source-requirement', 'kind': 'source-requirement', 'goal': formula},
        {'id': 'domain', 'kind': 'identity-domain-transport',
         'goal': '∀ (s x : Nat), ((fun (n : Nat) => n) s = s) ∧ ((fun (n : Nat) => n) x = x)',
         'transportProfile': 'universal-nat-identity-v1'},
        copy.deepcopy(by_id['object-map']), copy.deepcopy(by_id['conclusion'])]
    binding = {key: copy.deepcopy(construction[key]) for key in _BINDING_KEYS if key in construction}
    if not isinstance(binding.get('selectedIdentity'), dict):
        raise TypeError('construction lacks selected route identity')
    for row in rows:
        row.update(status='open', binding=copy.deepcopy(binding),
                   goalDigest='sha256:' + hashlib.sha256(_canonical(row)).hexdigest())
    return rows


def _prepared_rows(obligations):
    by_id = {}
    for row in obligations:
        if row['id'] in by_id:
            raise ValueError('duplicate prepared obligation')
        by_id[row['id']] = row
    for identity, kind in [('object-map', 'representation-transport'),
                           ('conclusion', 'conclusion-transfer')]:
        row = by_id.get(identity, {})
        if (row.get('kind') != kind or not isinstance(row.get('goal'), str)
                or row.get('status', 'open') != 'open'):
            raise ValueError('missing exact prepared obligation: ' + identity)
    return by_id
