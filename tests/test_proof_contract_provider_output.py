"""Output admission retains resource status without publishing oversized evidence."""
import importlib
import json

from ladon.proof_contract_provider_expansion import _bounded


def test_oversized_worker_result_is_an_incomplete_output_stop():
    worker=importlib.import_module('ladon.proof_contract_provider_worker')
    body=json.loads(worker._response({'large':'x'*(8*1024**2)}))
    assert body['status']=='completed'
    assert body['result']['status']=='output-limit'
    assert len(json.dumps(body)) < 10000


def test_oversized_public_result_preserves_memory_stop_guidance():
    result=_bounded({'padding':'x'*(8*1024**2), 'memoryReportBackRequired':True,
        'diagnostic':{'message':'Stop progress and report back to user: 12 GiB memory limit reached.'}})
    assert result['status']=='incomplete'
    assert result['memoryReportBackRequired'] is True
    assert 'Stop progress and report back to user' in result['diagnostic']['message']
    assert len(json.dumps(result)) < 10000
