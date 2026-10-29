"""One lease around fresh admissions, exact owners and independent conditional replay."""

import sys
import tempfile
from pathlib import Path

from ladon._bounded_json_graph import canonical
from ladon.bounded_json_transport import pack_json, unpack_json
from ladon.proof_contract_payloads import closed
from ladon.proof_slice import pinned_toolchain
from ladon.real_bound_native_production import _current_source, replay_real_bound
from ladon.real_prose_connection_context import check_goal, remaining, verify_imports
from ladon.real_prose_connection_history import validate_inner, validate_snapshot
from ladon.real_prose_connection_inputs import authored_owner, bound_inputs, formal_owner
from ladon.real_prose_connection_resources import stop_on_limits
from ladon.real_prose_inputs import implementation_identity, sha
from ladon.real_prose_native_production import _produce, inspect_real_prose_bound
from ladon.source_association_io import _read_regular


def current_inputs(job,formal,authored):
    remaining(job)
    _current_source(formal,Path(job['formalRoot']))
    inspect_real_prose_bound(authored,Path(job['proseRoot']))
    if implementation_identity() != job['implementationDigest']:
        raise ValueError('connection implementation changed during execution')
    remaining(job)


def _prepare(job):
    closed(job,{'version','formal','authored','formalRoot','proseRoot','connection','workspace',
                'startedMonotonic','timeoutSeconds','deadlineMonotonic','maxRssBytes',
                'maxOutputBytes','implementationDigest','previous'},'connection worker job')
    if (job['version'] != 1 or implementation_identity() != job['implementationDigest']
            or job['deadlineMonotonic'] != job['startedMonotonic']+job['timeoutSeconds']):
        raise ValueError('connection requires one current implementation and deadline')
    workspace = Path(job['workspace']).resolve(strict=True)
    if list(workspace.iterdir()):
        raise ValueError('connection workspace must be request-owned and empty')
    scratch = workspace/'scratch'
    scratch.mkdir()
    tempfile.tempdir = str(scratch)
    bound = bound_inputs(job['formal'],job['authored'],job['connection'])
    _previous(job,bound)
    current_inputs(job,job['formal'],job['authored'])
    a,b = (pinned_toolchain(Path(job[key])) for key in ('formalRoot','proseRoot'))
    if a.lean_release != b.lean_release or a.lean_identity != b.lean_identity:
        raise ValueError('connection source owners use incompatible pinned Lean executables')
    return bound


def compute(job):
    bound = _prepare(job)
    result = {'status':'unresolved','phase':'formal-admission','bound':bound,
              'formal':None,'authored':None,'goal':None}
    formal = replay_real_bound(job['formal'],job['formalRoot'],timeout_seconds=remaining(job))
    result['formal'] = formal
    stop_on_limits([formal['check'].get('processReceipt') or {}],job)
    if formal['status'] != 'admitted':
        return result
    if formal_owner(formal) != bound['owners']['formal']:
        raise ValueError('fresh formal admission changed its semantic owner')
    result['phase'] = 'authored-recognition'
    request = job['authored']['request']
    authored = _produce(job['proseRoot'],request['interpretation'],request['context'],
        request['alternativeId'],request['author'],job['timeoutSeconds'],job['maxRssBytes'],
        job['maxOutputBytes'],job['startedMonotonic'],previous=job['authored'])
    result['authored'] = authored
    stop_on_limits([authored['check'].get('processReceipt') or {}],job)
    if authored['status'] != 'authored':
        return result
    if authored_owner(authored) != bound['owners']['authored']:
        raise ValueError('fresh recognition changed the exact authored owner')
    result['phase'] = 'conditional-goal'
    goal = check_goal(job,formal,authored,bound['connection'],Path(job['proseRoot']))
    result['goal'] = goal
    if goal['status'] == 'checked':
        verify_imports(goal,formal,authored,Path(job['workspace']))
        result.update({'status':'connected','phase':'complete'})
    current_inputs(job,formal,authored)
    validate_inner(result)
    return result


def main():
    try:
        job = unpack_json(sys.stdin.buffer.read(8*1024**2+1))
        result = compute(job)
        body = {'status':'completed','result':result,'diagnostic':None}
        encoded = pack_json(body)
        remaining(job)
        sys.stdout.buffer.write(encoded)
        return 0
    except (ValueError,TypeError,KeyError,IndexError,OSError,TimeoutError) as error:
        sys.stdout.buffer.write(pack_json({'status':'rejected','result':None,'diagnostic':str(error)[:500]}))
        return 2



def _previous(job,bound):
    descriptor = job['previous']
    if descriptor is None:
        return
    closed(descriptor,{'path','digest'},'connection previous-history custody')
    path = Path(descriptor['path'])
    expected = Path(job['workspace']).parent/'previous-wire.json'
    if path != expected:
        raise ValueError('connection previous history escaped its supervisor owner')
    wire = _read_regular(path,8*1024**2)
    if descriptor['digest'] != 'sha256:'+sha(wire):
        raise ValueError('connection previous-history copy changed')
    snapshot = unpack_json(wire)
    if len(canonical(snapshot))+len(canonical(job)) > 32*1024**2:
        raise ValueError('connection aggregate replay inputs exceed 32 MiB')
    validate_snapshot(snapshot)
    previous = snapshot['check']['result']
    if previous is None or previous['bound'] != bound:
        raise ValueError('connection replay requires exact original records, owners and request')
    remaining(job)


if __name__ == '__main__':
    raise SystemExit(main())
