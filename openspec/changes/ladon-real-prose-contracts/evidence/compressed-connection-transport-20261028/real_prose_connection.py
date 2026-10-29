"""Fresh conditional connections and explicitly historical saved inspection."""

import hashlib
import os
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from ladon._proof_contract_goal_scratch import ENV_AUDIT_DELEGATION, ENV_KEYS
from ladon.bounded_json_transport import (
    _COMPRESSED_MAGIC,
    TransportLimits,
    pack_json_with_compression_fallback,
    unpack_json_with_compression_fallback,
)
from ladon.process_supervisor import run_bounded_target_process
from ladon.real_prose_connection_history import (
    COMPRESSED_SCHEMA,
    FRESH,
    QUALIFICATIONS,
    SCHEMA,
    validate_snapshot,
)
from ladon.real_prose_connection_inputs import connection_request
from ladon.real_prose_inputs import implementation_identity, observation_identity
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES, memory_limit_message
from ladon.semantic_candidate_limits import validate_semantic_bounds


def _bounds(timeout,rss,output,started):
    validate_semantic_bounds(timeout,output,rss)
    if timeout > 600 or rss > DEFAULT_MAX_RSS_BYTES or output > 8*1024**2:
        raise ValueError('connection exceeds 600-second/12-GiB/8-MiB profile')
    return {'timeout_seconds':timeout,'max_rss_bytes':rss,'max_output_bytes':output,
            'deadlineMonotonic':started+timeout}


def _run(job,bounds):
    environment = {k:v for k,v in os.environ.items() if k not in (*ENV_KEYS,ENV_AUDIT_DELEGATION)}
    root = Path(__file__).resolve().parents[2]
    environment['PYTHONPATH'] = str(root/'src')
    wire = pack_json_with_compression_fallback(
        job, limits=TransportLimits(max_wire_bytes=bounds['max_output_bytes']))
    remaining = bounds['deadlineMonotonic']-time.monotonic()
    if remaining <= 0:
        return {'status':'incomplete','result':None,
                'diagnostic':'Stop progress and report back to user: the shared connection deadline was exhausted before launch.',
                'bounds':bounds,'processReceipt':None,
                'workerInputDigest':'sha256:'+hashlib.sha256(wire).hexdigest(),
                'implementationDigest':job['implementationDigest']}
    result = run_bounded_target_process([sys.executable,'-m','ladon.real_prose_connection_worker'],
        cwd=root,env=environment,input_bytes=wire,timeout_seconds=remaining,
        max_rss_bytes=bounds['max_rss_bytes'],max_output_bytes=bounds['max_output_bytes'])
    receipt = asdict(result)
    receipt['command'] = list(result.command)
    for key in ('stdout','stderr'):
        receipt[key+'Digest'] = 'sha256:'+hashlib.sha256(receipt.pop(key).encode()).hexdigest()
    check = {'status':'incomplete','result':None,'diagnostic':None,'bounds':bounds,
             'processReceipt':receipt,'workerInputDigest':'sha256:'+hashlib.sha256(wire).hexdigest(),
             'implementationDigest':job['implementationDigest']}
    if result.succeeded:
        output_wire = result.stdout.encode()
        body = unpack_json_with_compression_fallback(output_wire)
        if set(body) != {'status','result','diagnostic'} or body['status'] != 'completed':
            raise ValueError('invalid completed connection worker response')
        check.update(body)
        if output_wire.startswith(_COMPRESSED_MAGIC):
            text = output_wire.decode('ascii')
            check['stdoutWireChunks'] = [text[i:i+256*1024]
                                         for i in range(0,len(text),256*1024)]
    else:
        check['diagnostic'] = _failure(result,bounds)
    return check


def _failure(result,bounds):
    if result.memory_limited:
        return memory_limit_message(bounds['max_rss_bytes'],result.peak_rss_bytes)
    if result.timed_out:
        return 'Stop progress and report back to user: the shared connection deadline was exhausted.'
    if result.output_limited:
        return 'Stop progress and report back to user: the connection output limit was insufficient.'
    try:
        return unpack_json_with_compression_fallback(result.stdout.encode())['diagnostic']
    except (ValueError,TypeError,KeyError):
        return result.stderr[-500:] or 'connection worker failed'


def connect_real_prose_bound(formal,authored,formal_root,prose_root,connection,*,
                             timeout_seconds=600,max_rss_bytes=DEFAULT_MAX_RSS_BYTES,
                             max_output_bytes=8*1024**2,_started=None,_previous=None):
    started = time.monotonic() if _started is None else _started
    bounds = _bounds(timeout_seconds,max_rss_bytes,max_output_bytes,started)
    request = connection_request(connection)
    identity = implementation_identity()
    with tempfile.TemporaryDirectory(prefix='ladon-prose-connection-') as directory:
        workspace = Path(directory)/'worker'
        workspace.mkdir()
        previous = _stage_previous(_previous,Path(directory))
        job = {'version':1,'formal':formal,'authored':authored,'formalRoot':str(Path(formal_root).resolve(strict=True)),
               'proseRoot':str(Path(prose_root).resolve(strict=True)),'connection':request,'workspace':str(workspace),
               'startedMonotonic':started,'timeoutSeconds':timeout_seconds,'deadlineMonotonic':bounds['deadlineMonotonic'],
               'maxRssBytes':max_rss_bytes,'maxOutputBytes':max_output_bytes,
               'implementationDigest':identity,'previous':previous}
        check = _run(job,bounds)
    if implementation_identity() != identity:
        raise ValueError('connection implementation changed before publication')
    if time.monotonic() >= bounds['deadlineMonotonic'] and check['status'] == 'completed':
        check.update({'status':'incomplete','result':None,'diagnostic':'shared connection deadline exhausted'})
    status = check['result']['status'] if check['status'] == 'completed' else 'unavailable'
    schema = COMPRESSED_SCHEMA if 'stdoutWireChunks' in check else SCHEMA
    result = {'schema':schema,'status':status,'authority':FRESH if status == 'connected' else 'none',
              **QUALIFICATIONS,'check':check}
    result['snapshotId'] = observation_identity(result)
    validate_snapshot(result)
    return result


def inspect_real_prose_connection(snapshot):
    validate_snapshot(snapshot)
    inner = snapshot['check']['result']
    return {'schema':'ladon-real-prose-connection-inspection-v1','status':'validated-historical',
            'targetOwnerBinding':('not-established-legacy' if snapshot['schema'].endswith('-v1')
                                  else 'recorded-independent-commitment'),
            'recordedStatus':snapshot['status'],'authority':'none','freshCheck':False,
            'evidenceAuthentication':'not-established','sourceFreshness':'not-checked',
            'externalInputBinding':'requires-original-inputs-for-replay','admission':'unresolved',
            'sourceTheoremProof':'not-checked','mathematicalFalsity':'not-established',
            'inputReferences':inner['bound']['inputs'] if inner else None}


def replay_real_prose_connection(snapshot,formal,authored,formal_root,prose_root,**limits):
    started = time.monotonic()
    try:
        request = snapshot['check']['result']['bound']['connection']
    except (KeyError,TypeError) as error:
        raise ValueError('connection without recorded input owners cannot replay') from error
    return connect_real_prose_bound(formal,authored,formal_root,prose_root,request,
        _started=started,_previous=snapshot,**limits)


def _stage_previous(snapshot,directory):
    if snapshot is None:
        return None
    wire = pack_json_with_compression_fallback(snapshot)
    path = directory/'previous-wire.json'
    path.write_bytes(wire)
    return {'path':str(path),'digest':'sha256:'+hashlib.sha256(wire).hexdigest()}
