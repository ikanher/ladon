"""Independent typed-target construction, outside source term elaborators."""

import json
from dataclasses import asdict
from pathlib import Path

from ladon._source_goal_helpers import stage_helper, verify_helper
from ladon.proof_contract_payloads import closed
from ladon.real_prose_connection_environment import (
    finish_environment,
    prepare_environment,
    validate_environment,
)
from ladon.real_prose_inputs import sha
from ladon.source_association_io import _read_regular

SCHEMA = 'ladon-connection-target-commitment-v1'
HELPER = Path(__file__).parent/'lean/ladon_prose_connection_commitment.lean'


def commit_target(job,root,source,request,term,run_lean,*,capture=None):
    context,binding = prepare_environment(root,capture)
    with_path = Path(job['workspace'])/'commitment'
    with_path.mkdir()
    helper,digest = stage_helper(HELPER,with_path)
    destination = with_path/'result.json'
    payload = {'filename':'LadonConnection.lean','module':'LadonConnection',
               'snapshotPath':str(root/'LadonConnection.lean'),
               'line':len(source.splitlines()),'column':4,
               'ownerRequest':json.dumps(request,sort_keys=True,ensure_ascii=False,separators=(',',':')),
               'requestedTerm':term}
    request_file = with_path/'request.json'
    request_file.write_text(json.dumps(payload))
    result = run_lean(job,root,['--run',str(helper),str(request_file),str(destination)])
    verify_helper(HELPER,digest)
    if (root/'LadonConnection.lean').read_text() != source:
        raise ValueError('connection source changed during independent commitment')
    receipt = asdict(result)
    receipt['command'] = list(result.command)
    certificate = json.loads(_read_regular(destination,job['maxOutputBytes'])) if result.succeeded else None
    environment = finish_environment(context,binding,certificate['environment']) if certificate else None
    return {'certificate':certificate,'processReceipt':receipt,'helperDigest':digest,'environment':environment,
            'sourceDigest':'sha256:'+sha(source.encode())}


def validate_commitment(commitment,request,term,source,subject,*,environment=None):
    closed(commitment,{'certificate','processReceipt','helperDigest','sourceDigest','environment'},'target commitment')
    row = commitment['certificate']
    closed(row,{'schema','expectedStructural','actualStructural','kernelCheck','axioms',
                'ownerRequest','requestedTerm','environment'},'target commitment certificate')
    encoded = json.dumps(request,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    expected = {'schema':SCHEMA,'kernelCheck':'synchronous','ownerRequest':encoded,
                'requestedTerm':term,'expectedStructural':subject,'actualStructural':subject}
    if any(row[key] != value for key,value in expected.items()):
        raise ValueError('connection target commitment differs from exact owners, proof or source')
    _validate_trust(row['axioms'])
    validate_environment(row['environment'],commitment['environment'])
    if environment is not None and commitment['environment'] != environment:
        raise ValueError('commitment environment differs from original capture')
    if commitment['sourceDigest'] != 'sha256:'+sha(source.encode()):
        raise ValueError('connection commitment source differs')
    from ladon.proofir_v3 import _digest
    from ladon.real_bound_native_evidence import _receipts

    if not _digest(commitment['helperDigest']):
        raise ValueError('connection commitment lacks helper identity')
    receipt = commitment['processReceipt']
    command = receipt.get('command',[])
    if len(command) < 4 or command[-4] != '--run' or Path(command[-3]).name != HELPER.name:
        raise ValueError('connection commitment used a different helper process')
    _receipts([receipt])


def _validate_trust(axioms):
    if not isinstance(axioms,list):
        raise TypeError('connection commitment lacks complete axioms')
    if any(name not in {'propext','Classical.choice','Quot.sound'} for name in axioms):
        raise ValueError('connection commitment uses unsupported axioms')
