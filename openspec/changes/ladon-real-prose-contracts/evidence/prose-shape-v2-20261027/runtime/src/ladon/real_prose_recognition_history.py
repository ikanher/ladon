"""Reproduce saved recognition data without granting fresh kernel authority."""

from ladon.correspondence_interpretation import validate_interpretation
from ladon.proof_contract_payloads import closed
from ladon.real_prose_expression import parse_worker
from ladon.real_prose_history import _completed_receipt, validate_prose_snapshot
from ladon.real_prose_inputs import generated_source, observation_identity, validate_context
from ladon.real_prose_recognition import SCHEMA
from ladon.real_prose_shape import PROFILE_ID, recognize_shape
from ladon.real_prose_shape_certificates import apply_certificates
from ladon.real_prose_shape_paths import validate_alias_request


def validate_recognition(snapshot):
    closed(snapshot, {'schema', 'channel', 'profileId', 'status', 'authority', 'fidelity',
                      'admission', 'contract', 'request', 'check', 'snapshotId'}, 'prose recognition')
    required = {'schema': SCHEMA, 'channel': 'prose', 'profileId': PROFILE_ID,
                'authority': 'syntax-only', 'fidelity': 'attributed-unreviewed',
                'admission': 'unresolved', 'contract': None}
    if any(snapshot[key] != value for key, value in required.items()):
        raise ValueError('prose recognition cannot promote admission or change profiles')
    if snapshot['snapshotId'] != observation_identity(snapshot):
        raise ValueError('invalid or altered recognition identity')
    request = snapshot['request']
    closed(request, {'interpretation', 'context'}, 'recognition request')
    validate_interpretation(request['interpretation'], None)
    validate_context(request['context'])
    check = snapshot['check']
    closed(check, {'schema', 'status', 'result', 'diagnostic', 'processReceipt',
                  'workerInputDigest', 'bounds'}, 'recognition supervision')
    if check['schema'] != 'ladon-supervised-obligation-planner-v1':
        raise ValueError('recognition requires its supervised operation')
    if check['status'] != 'completed':
        if snapshot['status'] != 'unavailable' or check['result'] is not None:
            raise ValueError('stopped recognition cannot retain dependent success')
        return
    _completed_receipt(check)
    _inner(check['result'], request)
    if snapshot['status'] != check['result']['status']:
        raise ValueError('recognition status differs from its result')


def _inner(result, request):
    closed(result, {'status', 'observation', 'shape', 'normalization', 'features', 'diagnostic'}, 'recognition result')
    observation = result['observation']
    validate_prose_snapshot(observation)
    if observation['request'] != request:
        raise ValueError('recognition must retain its exact authored interpretation/context')
    if observation['status'] != 'observed':
        _missing_observation(result)
        return
    observed = observation['check']['result']
    shape = recognize_shape(observed['observation']['propositionExpr'])
    if result['shape'] != shape:
        raise ValueError('recognition shape differs from the exact typed proposition')
    if shape['candidate'] is None:
        if result['status'] != 'unresolved' or result['features'] is not None or result['normalization'] is not None:
            raise ValueError('unsupported skeleton cannot carry checked normalization')
        return
    _normalization(result, observed, shape, request)


def _normalization(result, observed, shape, request):
    normal = result['normalization']
    closed(normal, {'request', 'generated', 'workerJson', 'worker', 'processReceipt'}, 'prose normalization')
    validate_alias_request(normal['request'], shape)
    _, generated = generated_source(request, observed['contextSource']['text'].encode())
    if normal['generated'] != generated:
        raise ValueError('normalizer selected a different generated source proposition')
    if _normalization_unavailable(result, normal, observed, request, generated):
        return
    features = apply_certificates(shape, observed['observation']['propositionExpr'], normal['worker']['results'])
    if result['features'] != features:
        raise ValueError('recognized features differ from exact normalization evidence')
    expected = 'recognized' if features['normalizationState'] == 'checked' else 'unresolved'
    if result['status'] != expected or normal['worker']['status'] != ('checked' if expected == 'recognized' else 'partial'):
        raise ValueError('recognition status differs from ordered alias checks')


def _worker_owner(worker, observed, context, declaration):
    closed(worker, {'schema', 'helperVersion', 'module', 'file', 'target', 'leanVersion',
                    'status', 'propositionExpr', 'results', 'importedModules',
                    'compiledModulePaths', 'reason'}, 'prose alias worker')
    expected = {'schema': 'ladon-prose-alias-worker-v1', 'helperVersion': 'ladon-prose-alias-helper-v1',
                'module': context['module'], 'file': context['file'], 'target': declaration,
                'leanVersion': observed['leanVersion']}
    if any(worker[k] != v for k, v in expected.items()):
        raise ValueError('normalizer identity differs from the exact source context')
    if worker['status'] == 'unavailable':
        return
    source = observed['observation']
    for key in ('propositionExpr', 'importedModules', 'compiledModulePaths'):
        if worker[key] != source[key]:
            raise ValueError('normalizer changed the original proposition or compiled context')


def _missing_observation(result):
    if result['status'] != 'unavailable' or any(result[k] is not None for k in ('shape', 'normalization', 'features')):
        raise ValueError('missing observation cannot establish recognition')


def _normalization_unavailable(result, normal, observed, request, generated):
    receipt = normal['processReceipt']
    stopped = receipt['returncode'] != 0 or any(receipt[k] for k in ('timed_out', 'memory_limited', 'output_limited'))
    if stopped or normal['worker'] is None:
        _unavailable_features(result)
        return True
    if parse_worker(normal['workerJson']) != normal['worker']:
        raise ValueError('normalization differs from saved helper output')
    _worker_owner(normal['worker'], observed, request['context'], generated['declaration'])
    if normal['worker']['status'] == 'unavailable':
        _unavailable_features(result)
        return True
    return False


def _unavailable_features(result):
    if result['status'] != 'unavailable' or result['features'] is not None:
        raise ValueError('stopped normalization cannot yield recognized features')
