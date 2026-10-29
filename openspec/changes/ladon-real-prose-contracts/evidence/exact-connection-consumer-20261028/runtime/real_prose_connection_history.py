"""Saved conditional checks are consistency evidence, never checking authority."""

import math

from ladon._proof_contract_lift_evidence import _validate_native_evidence
from ladon.bounded_json_transport import pack_json
from ladon.proof_contract_payloads import closed
from ladon.proofir_v3 import _digest
from ladon.real_bound_native_evidence import _receipts
from ladon.real_prose_connection_context import (
    MODULE,
    WITNESS,
    generated_goal_source,
    owner_request,
)
from ladon.real_prose_connection_inputs import (
    authored_owner,
    connection_request,
    copy_relation,
    formal_owner,
)
from ladon.real_prose_inputs import observation_identity, sha
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.semantic_candidate_limits import validate_semantic_bounds

LEGACY_SCHEMA = 'ladon-real-prose-connection-v1'
SCHEMA = 'ladon-real-prose-connection-v2'
FRESH = 'fresh-conditional-lean-check'
QUALIFICATIONS = {'admission':'unresolved','fidelity':'attributed-unreviewed',
                  'sourceTheoremProof':'not-checked','mathematicalFalsity':'not-established'}


def validate_bound(bound):
    closed(bound,{'connection','inputs','owners','association'},'connection input binding')
    connection_request(bound['connection'])
    for key in ('inputs','owners'):
        closed(bound[key],{'formal','authored'},'ordered connection owners')
    for ref in bound['inputs'].values():
        closed(ref,{'snapshotId','digest'},'connection input reference')
        if any(not _digest(value) for value in ref.values()):
            raise ValueError('connection input reference is not a digest')


def validate_inner(inner,*,legacy=False):
    closed(inner,{'status','phase','bound','formal','authored','goal'},'connection worker result')
    validate_bound(inner['bound'])
    if inner['status'] not in {'connected','unresolved'}:
        raise ValueError('invalid connection worker status')
    owners = inner['bound']['owners']
    if (inner['formal'] is not None and inner['formal']['status'] == 'admitted'
            and formal_owner(inner['formal']) != owners['formal']):
        raise ValueError('fresh formal check substituted a semantic owner')
    if (inner['authored'] is not None and inner['authored']['status'] == 'authored'
            and authored_owner(inner['authored']) != owners['authored']):
        raise ValueError('fresh authored check substituted a semantic owner')
    if inner['status'] == 'connected':
        _connected(inner,legacy=legacy)


def _connected(inner,*,legacy=False):
    if (inner['phase'] != 'complete' or inner['formal'] is None or inner['authored'] is None
            or inner['formal']['status'] != 'admitted' or inner['authored']['status'] != 'authored'):
        raise ValueError('connected result lacks both fresh owner checks')
    formal, authored = inner['formal'], inner['authored']
    owner = inner['bound']['owners']['authored']
    relation = copy_relation(formal['sourceText'].encode(),owner['contextSource']['text'].encode())
    if relation != inner['bound']['association']:
        raise ValueError('connection changed exact copied-source association')
    _goal(inner['goal'],formal,authored,inner['bound']['connection'],legacy=legacy)


def _goal(goal,formal,authored,connection,*,legacy=False):
    closed(goal,{'status','request','sourceText','premiseObservations','compilations','capture',
                 'completion','completionTerm'} | (set() if legacy else {'commitment'}),'connection goal evidence')
    if goal['status'] != 'checked' or goal['completionTerm'] != WITNESS:
        raise ValueError('connection goal is not independently completed')
    names = [row['target'] for row in goal['premiseObservations']]
    if names != connection['premises']:
        raise ValueError('connection changed ordered conditional premises')
    expected = owner_request(formal,authored,goal['premiseObservations'])
    source = generated_goal_source(authored,expected,connection)
    if goal['request'] != expected or goal['sourceText'] != source:
        raise ValueError('connection source/goal differs from its exact semantic owners')
    _receipts(goal['compilations'])
    _capture_completion(goal,source)
    if not legacy:
        from ladon.real_prose_connection_commitment import validate_commitment

        validate_commitment(goal['commitment'],expected,connection['term'],source,
                            goal['capture']['capture']['goal']['typeStructural'],
                            environment=goal['capture']['capture']['environment'])


def _capture_completion(goal,source):
    capture_run = goal['capture']
    if capture_run['status'] != 'captured':
        raise ValueError('connection has no original source-goal capture')
    capture = capture_run['capture']
    identity = capture['source']
    if (identity['digest'] != 'sha256:'+sha(source.encode()) or identity['byteLength'] != len(source.encode())
            or identity['module'] != MODULE or identity['position']['line'] != len(source.splitlines())
            or identity['position']['column'] != 4):
        raise ValueError('connection captured a different source or selected goal')
    environment = capture['environment']
    subject = capture['goal']['typeStructural']
    _validate_native_evidence({'nativeEvidence':{'capture':capture,'completion':goal['completion'],
        'canonicalTypedSubject':subject,'actualTypedSubject':subject,
        'compiledInventory':environment['compiledInventory'],'environmentRef':environment['executionContextRef'],
        'executableIdentity':environment['executableDigest']}},{'term':WITNESS})
    _receipts(capture_run['processReceipts'])
    _receipts(goal['completion']['processReceipts'])


def validate_snapshot(snapshot):
    closed(snapshot,{'schema','status','authority','admission','fidelity','sourceTheoremProof',
                     'mathematicalFalsity','check','snapshotId'},'conditional connection snapshot')
    if snapshot['schema'] not in {SCHEMA,LEGACY_SCHEMA} or snapshot['snapshotId'] != observation_identity(snapshot):
        raise ValueError('invalid or altered conditional connection snapshot')
    if any(snapshot[key] != value for key,value in QUALIFICATIONS.items()):
        raise ValueError('conditional connection promoted its qualifications')
    check = snapshot['check']
    closed(check,{'status','result','diagnostic','bounds','processReceipt','workerInputDigest',
                  'implementationDigest'},'connection supervision')
    expected = _check_status(check,legacy=snapshot['schema'] == LEGACY_SCHEMA)
    if snapshot['status'] != expected or snapshot['authority'] != (FRESH if expected == 'connected' else 'none'):
        raise ValueError('connection status/authority differs from recorded evidence')


def _check_status(check,*,legacy=False):
    if check['status'] == 'completed':
        _supervision(check)
        _receipts([check['processReceipt']])
        validate_inner(check['result'],legacy=legacy)
        return check['result']['status']
    else:
        if check['status'] not in {'rejected','incomplete'} or check['result'] is not None:
            raise ValueError('stopped connection retained check authority')
        return 'unavailable'


def _supervision(check):
    bounds = _recorded_bounds(check['bounds'])
    if not _digest(check['workerInputDigest']) or not _digest(check['implementationDigest']):
        raise ValueError('recorded connection lacks exact worker/implementation digests')
    receipt = check['processReceipt']
    if (receipt['command'][-2:] != ['-m','ladon.real_prose_connection_worker']
            or receipt['peak_rss_bytes'] > bounds['max_rss_bytes']
            or receipt['elapsed_seconds'] > bounds['timeout_seconds']):
        raise ValueError('connection process receipt differs from resource or worker owner')
    wire = pack_json({'status':'completed','result':check['result'],'diagnostic':None})
    if receipt['stdoutDigest'] != 'sha256:'+sha(wire) or len(wire) > bounds['max_output_bytes']:
        raise ValueError('connection worker output digest/length differs from full retained evidence')


def _recorded_bounds(bounds):
    closed(bounds,{'timeout_seconds','max_rss_bytes','max_output_bytes','deadlineMonotonic'},'connection bounds')
    validate_semantic_bounds(bounds['timeout_seconds'],bounds['max_output_bytes'],bounds['max_rss_bytes'])
    if (bounds['timeout_seconds'] > 600 or bounds['max_output_bytes'] > 8*1024**2
            or bounds['max_rss_bytes'] > DEFAULT_MAX_RSS_BYTES
            or not _deadline(bounds['deadlineMonotonic'])):
        raise ValueError('recorded connection resource profile changed')
    return bounds


def _deadline(value):
    return type(value) in (int,float) and math.isfinite(value) and value > 0
