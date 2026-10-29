"""Exact input references and stable semantic owners for conditional connections."""

from copy import deepcopy

from ladon._bounded_json_graph import canonical
from ladon.proof_contract_payloads import closed
from ladon.proof_contract_worker import _NAME
from ladon.real_bound_native_analysis_bundle import _semantic_owner
from ladon.real_bound_native_production import _verify_production
from ladon.real_prose_inputs import sha
from ladon.real_prose_native_production import _recognition, validate_production

REQUEST_SCHEMA = 'ladon-real-prose-connection-request-v1'


def connection_request(value):
    closed(value, {'schema', 'term', 'premises'}, 'Real prose connection request')
    if value['schema'] != REQUEST_SCHEMA:
        raise ValueError('unsupported Real prose connection request')
    term, premises = value['term'], value['premises']
    if type(term) is not str or not term.strip() or len(term.encode()) > 1024**2:
        raise ValueError('connection requires a bounded nonempty proof term')
    _premises(premises)
    return deepcopy(value)


def input_reference(value):
    return {'snapshotId': value['snapshotId'], 'digest': 'sha256:' + sha(canonical(value))}


def authored_observation(value):
    recognition = _recognition(value['check']['result'])
    return recognition['check']['result']['observation']['check']['result']


def authored_owner(value):
    validate_production(value)
    if value['status'] != 'authored':
        raise ValueError('connection requires an authored Real record')
    inner = value['check']['result']
    recognition = _recognition(inner)
    observation = authored_observation(value)
    record = deepcopy(inner['artifacts'][-1]['payload']['record'])
    for key in ('recognitionId', 'observationId'):
        record['source'].pop(key)
    return {'request': deepcopy(value['request']), 'record': record,
            'features': deepcopy(recognition['check']['result']['features']),
            'propositionExpr': deepcopy(observation['observation']['propositionExpr']),
            'contextSource': deepcopy(observation['contextSource']),
            'generated': deepcopy(observation['generated']), 'environment': observation['environment'],
            'leanVersion': observation['leanVersion'], 'implementationDigest': observation['implementationDigest'],
            'compiledInventory': deepcopy(observation['compiledInventory']['inventory'])}


def formal_owner(value):
    _verify_production(value)
    if value['status'] != 'admitted':
        raise ValueError('connection requires an admitted formal Real record')
    return _semantic_owner(value)


def copy_relation(formal_source, prose_source):
    if type(formal_source) is not bytes or type(prose_source) is not bytes:
        raise TypeError('source association requires exact UTF-8 bytes')
    if not formal_source or not prose_source.startswith(formal_source):
        raise ValueError('prose context is not an exact byte-prefix extension of formal source')
    return {'formalBytes': len(formal_source), 'proseBytes': len(prose_source),
            'formalDigest': 'sha256:' + sha(formal_source), 'proseDigest': 'sha256:' + sha(prose_source),
            'helperImportLineOffset': 1}


def bound_inputs(formal, authored, connection):
    request = connection_request(connection)
    owners = {'formal': formal_owner(formal), 'authored': authored_owner(authored)}
    association = copy_relation(formal['sourceText'].encode(),
                                owners['authored']['contextSource']['text'].encode())
    return {'connection': request, 'inputs': {'formal': input_reference(formal),
                                             'authored': input_reference(authored)},
            'owners': owners, 'association': association}


def _premises(premises):
    if (type(premises) is not list or len(premises) > 16
            or any(type(name) is not str or not _NAME.fullmatch(name) for name in premises)
            or len(set(premises)) != len(premises)):
        raise ValueError('connection requires at most 16 distinct local premise names')
