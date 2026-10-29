"""Historical prose observation validation and explicit current-source checks."""

from ladon.correspondence_interpretation import validate_interpretation
from ladon.proof_contract_payloads import closed
from ladon.proof_contract_worker import _validate_declaration_range
from ladon.proof_slice import pinned_toolchain
from ladon.proofir_v3 import validate_envelope_batch
from ladon.real_prose_expression import parse_worker, validate_expression
from ladon.real_prose_inputs import (
    HELPER_VERSION,
    SCHEMA,
    WORKER_SCHEMA,
    context_source,
    generated_source,
    implementation_identity,
    observation_identity,
    sha,
    validate_context,
)


def validate_prose_snapshot(snapshot):
    closed(snapshot, {'schema', 'channel', 'status', 'authority', 'fidelity', 'admission',
                      'contract', 'request', 'check', 'snapshotId'}, 'prose observation')
    constants = {'schema': SCHEMA, 'channel': 'prose', 'authority': 'syntax-only',
                 'fidelity': 'attributed-unreviewed', 'admission': 'unresolved', 'contract': None}
    if any(snapshot[k] != v for k, v in constants.items()):
        raise ValueError('prose observation cannot promote authority or change profile')
    if snapshot['snapshotId'] != observation_identity(snapshot):
        raise ValueError('invalid or altered prose observation identity')
    request = snapshot['request']
    closed(request, {'interpretation', 'context'}, 'prose observation request')
    validate_interpretation(request['interpretation'], None)
    validate_context(request['context'])
    _check(snapshot['check'], request, snapshot['status'])


def _check(check, request, status):
    closed(check, {'schema', 'status', 'result', 'diagnostic', 'processReceipt',
                  'workerInputDigest', 'bounds'}, 'prose supervision')
    if check['schema'] != 'ladon-supervised-obligation-planner-v1':
        raise ValueError('prose observation requires its supervised execution record')
    if check['status'] != 'completed':
        if check['status'] not in {'rejected', 'incomplete'} or status != 'unavailable':
            raise ValueError('stopped prose observation cannot report success')
        if check['result'] is not None:
            raise ValueError('stopped prose observation cannot retain dependent success')
        return
    _completed_receipt(check)
    result = check['result']
    _inner(result, request)
    if result['status'] != status:
        raise ValueError('prose status differs from observed result')


def _inner(result, request):
    closed(result, {'status', 'contextSource', 'environment', 'leanVersion',
                   'implementationDigest', 'generated', 'artifacts', 'observation',
                   'workerJson', 'processReceipts', 'residuals', 'compiledInventory'}, 'prose worker result')
    if result['status'] not in {'observed', 'unsupported', 'unavailable'}:
        raise ValueError('invalid prose observation status')
    source = result['contextSource']
    closed(source, {'schema', 'file', 'module', 'scope', 'sha256', 'text'}, 'prose context source')
    if {k: source[k] for k in request['context']} != request['context']:
        raise ValueError('prose context source differs from its exact request')
    if not isinstance(source['text'], str) or sha(source['text'].encode()) != source['sha256']:
        raise ValueError('prose context source text differs from digest')
    _artifacts(result, request)
    if result['status'] == 'unsupported':
        _unsupported(result, request)
    else:
        _generated(result, request)


def _artifacts(result, request):
    artifacts = result['artifacts']
    if not isinstance(artifacts, list) or len(artifacts) != 2:
        raise ValueError('prose observation requires exactly its native interpretation owners')
    validate_envelope_batch(artifacts)
    if [a['artifactKind'] for a in artifacts] != ['proofir.source-map', 'proofir.interpretation']:
        raise ValueError('prose observation cannot own an admitted contract')
    interpretation = artifacts[1]['payload']
    if interpretation['record'] != request['interpretation']:
        raise ValueError('prose observation interpretation differs from exact owner')
    if any(a['environmentRef'] != result['environment'] for a in artifacts):
        raise ValueError('prose interpretation environment differs from observation')
    _source_owner(artifacts[0], request['interpretation']['source'])


def _source_owner(artifact, source):
    anchors = artifact['payload']['anchors']
    if (len(anchors) != 1 or anchors[0]['sourcePath'] != source['path']
            or anchors[0]['contentDigest'] != 'sha256:' + source['sha256']):
        raise ValueError('prose source anchor differs from interpretation')


def _unsupported(result, request):
    from ladon.correspondence_interpretation import UnsupportedInterpretation

    try:
        generated_source(request, result['contextSource']['text'].encode())
    except UnsupportedInterpretation:
        if (result['generated'] is not None or result['observation'] is not None
                or result['processReceipts'] or result['workerJson'] is not None):
            raise ValueError('unsupported interpretation cannot have elaboration success')
        return
    raise ValueError('supported formula cannot be relabeled unsupported')


def _generated(result, request):
    content, generated = generated_source(request, result['contextSource']['text'].encode())
    if result['generated'] != generated:
        raise ValueError('generated proposition differs from exact interpretation/context')
    if not isinstance(result['processReceipts'], list) or not 1 <= len(result['processReceipts']) <= 2:
        raise ValueError('prose observation requires one exact Lean process receipt')
    if result['workerJson'] is None:
        if result['status'] == 'observed' or result['observation'] is not None:
            raise ValueError('missing helper output cannot establish an observation')
        return
    worker = parse_worker(result['workerJson'])
    if worker != result['observation']:
        raise ValueError('prose expression differs from saved worker output')
    _worker(worker, request['context'], result, content)


def _worker(worker, context, result, content):
    common = {'schema': WORKER_SCHEMA, 'helperVersion': HELPER_VERSION,
              'module': context['module'], 'file': context['file'],
              'target': result['generated']['declaration'], 'leanVersion': result['leanVersion']}
    if any(worker.get(k) != v for k, v in common.items()):
        raise ValueError('prose helper identity differs from exact generated target')
    if worker['status'] != 'observed':
        closed(worker, set(common) | {'status', 'reason'}, 'prose helper failure')
        if (worker['status'] not in {'elaboration-failed', 'not-a-proposition',
                                    'render-limit', 'not-found'} or result['status'] != 'unavailable'):
            raise ValueError('failed prose helper cannot report observed syntax')
        return
    closed(worker, set(common) | {'status', 'propositionExpr', 'sourceModuleOwned',
                                 'declarationRange', 'importedModules', 'compiledModulePaths'}, 'prose helper observation')
    _observed(worker, result, content)


def _observed(worker, result, content):
    if worker['sourceModuleOwned'] is not True or result['status'] != 'observed':
        raise ValueError('prose proposition must own its generated declaration')
    if not all(_successful_receipt(receipt) for receipt in result['processReceipts']):
        raise ValueError('stopped Lean process cannot report observed syntax')
    _validate_declaration_range(worker['declarationRange'])
    span = worker['declarationRange']
    original_lines = result['contextSource']['text'].count('\n') + 1
    if not original_lines < span['startLine'] <= span['endLine'] <= len(content.decode().splitlines()) + 1:
        raise ValueError('prose observation must select the generated declaration')
    validate_expression(worker['propositionExpr'])
    _inventory_owner(worker, result)


def check_current(snapshot, root):
    request, check = snapshot['request'], snapshot['check']
    validate_interpretation(request['interpretation'], root)
    result = check['result']
    if result is None:
        return
    if context_source(root, request['context']).decode() != result['contextSource']['text']:
        raise ValueError('stale prose context source')
    if implementation_identity() != result['implementationDigest']:
        raise ValueError('stale prose observer implementation')
    context = pinned_toolchain(root)
    if context.context_identity != result['environment']:
        raise ValueError('stale prose observation toolchain/source environment')
    if result['compiledInventory'] is not None:
        from ladon._source_goal_inventory import capture_inventory

        _files, _environment, inventory = capture_inventory(context, result['observation'])
        if inventory != result['compiledInventory']['inventory']:
            raise ValueError('stale prose compiled-library context')


def _inventory_owner(worker, result):
    compiled = result['compiledInventory']
    closed(compiled, {'inventory', 'observationDigest'}, 'prose compiled context')
    if (compiled['observationDigest'] != sha(result['workerJson'].encode())
            or len(result['processReceipts']) != 2):
        raise ValueError('prose observation requires compiled-context replay')
    modules = compiled['inventory']['modules']
    expected = [{'module': row['module'], 'path': row['path']} for row in modules]
    if sorted(worker['compiledModulePaths'], key=lambda row: row['module']) != expected:
        raise ValueError('prose compiled paths differ from inventory')
    if sorted(worker['importedModules']) != [row['module'] for row in modules]:
        raise ValueError('prose imported modules differ from inventory')


def _successful_receipt(receipt):
    return receipt['returncode'] == 0 and not any(
        receipt[key] for key in ('timed_out', 'memory_limited', 'output_limited'))


def _completed_receipt(check):
    receipt = check['processReceipt']
    if not isinstance(receipt, dict):
        raise TypeError('completed prose observation requires an outer process receipt')
    if receipt['returnCode'] != 0 or any(
            receipt[key] for key in ('timedOut', 'memoryLimited', 'outputLimited')):
        raise ValueError('stopped supervised process cannot report observed syntax')
    if receipt['inputDigest'] != check['workerInputDigest']:
        raise ValueError('prose worker input digest differs from process receipt')
    for key, bound in [('requestedMaxRssBytes', 'max_rss_bytes'),
                       ('requestedMaxOutputBytes', 'max_output_bytes')]:
        if receipt[key] != check['bounds'][bound]:
            raise ValueError('prose configured cap differs from process receipt')
