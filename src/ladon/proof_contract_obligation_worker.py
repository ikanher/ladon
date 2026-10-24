"""Finite JSON worker for supervised planner computation; starts no Lean process."""
from __future__ import annotations

import json
import sys

from .proof_contract_io import _decode
from .proof_contract_obligation_planner import ContractObligationPlanRequest
from .proof_contract_payloads import closed

MAX_BYTES = 8 * 1024**2


def _compute(job):
    closed(job, {'version', 'operation', 'request', 'analysisId', 'deadlineObservation'}, 'worker job')
    if job['version'] != 1 or not isinstance(job['request'], dict):
        raise ValueError('unsupported worker job')
    if job['operation'] == 'validate-native':
        return _validate_native(job['request'])
    request = ContractObligationPlanRequest(**job['request'])
    return _operation(job, request)


def _validate_native(request):
    from .proofir_v3 import validate_envelope_batch

    closed(request, {'artifact', 'context'}, 'native validation request')
    context = request['context']
    closed(context, {'artifacts'}, 'native context')
    artifacts = context['artifacts']
    if not isinstance(artifacts, list) or len(artifacts) > 4096:
        raise ValueError('native context exceeds its artifact count bound')
    artifact = request['artifact']
    if (not isinstance(artifact, dict) or artifact.get('artifactKind') != 'proofir.contract-analysis'
            or artifact.get('payload', {}).get('stage') != 'obligations'):
        raise ValueError('native validation requires an obligations artifact')
    validate_envelope_batch([*artifacts, artifact])
    return artifact


def _operation(job, request):
    from .proof_contract_obligation_planner import (
        _plan_contract_obligation_bundles,
        plan_contract_obligation_bundles,
        plan_contract_obligations,
    )

    operation = job['operation']
    if operation == 'plan-v1':
        return plan_contract_obligations(request)
    if operation == 'plan-v2':
        return plan_contract_obligation_bundles(request)
    if operation == 'replay-v2':
        return _plan_contract_obligation_bundles(request, _deadline_replay=job['deadlineObservation'])
    if operation == 'artifact-v2':
        from .proof_contract_obligation_artifacts import obligations_artifact

        return obligations_artifact(request, analysis_id=job['analysisId'])
    raise ValueError('unsupported worker operation')


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('worker input exceeds 8 MiB')
        result = _compute(_decode(raw))
        body = {'status': 'completed', 'result': result, 'diagnostic': None}
        output = json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        if len(output.encode()) > MAX_BYTES:
            raise ValueError('worker output exceeds 8 MiB')
        sys.stdout.write(output)
        return 0
    except (ValueError, TypeError, KeyError, OSError, OverflowError, RecursionError) as error:
        sys.stdout.write(json.dumps({'status': 'rejected', 'result': None,
                                     'diagnostic': str(error)[:500]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
