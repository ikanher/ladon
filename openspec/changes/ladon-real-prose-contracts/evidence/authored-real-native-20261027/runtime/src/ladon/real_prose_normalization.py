"""Fresh source-scoped alias equality checks under the parent's absolute deadline."""

import json
import time
from dataclasses import asdict
from pathlib import Path

from ladon._source_goal_inventory import capture_inventory, verify_inventory
from ladon.lean_toolchain import verify_toolchain_identities
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.real_prose_expression import parse_worker
from ladon.real_prose_inputs import context_source, generated_source, reading_request
from ladon.real_prose_shape_paths import alias_request
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.source_association_io import _read_regular

ALIAS_HELPER = Path(__file__).parent / 'lean/ladon_prose_alias.lean'


def normalize_aliases(job, observation, shape):
    root = Path(job['root'])
    request = reading_request(root, **job['request'])
    source = context_source(root, request['context'])
    context = pinned_toolchain(root)
    execution = prepare_direct_lean_execution(root, None, context, require_compiled_module=False)
    inner = observation['check']['result']
    if source.decode() != inner['contextSource']['text'] or context.context_identity != inner['environment']:
        raise ValueError('alias source/context differs from the exact proposition observation')
    files, environment, inventory = capture_inventory(context, inner['observation'])
    if inventory != inner['compiledInventory']['inventory']:
        raise ValueError('compiled context changed before alias normalization')
    result = _run(job, request, source, execution, alias_request(shape))
    verify_inventory(files, environment, inventory)
    verify_toolchain_identities(context)
    if context_source(root, request['context']) != source:
        raise ValueError('source changed during alias normalization')
    return result


def _run(job, request, source, execution, aliases):
    workspace = Path(job['workspace'])
    content, generated = generated_source(request, source)
    paths = [workspace / name for name in ('alias-source.lean', 'alias-helper.lean', 'alias-request.json', 'aliases.json')]
    snapshot, helper, input_, output = paths
    snapshot.write_bytes(content)
    helper.write_bytes(ALIAS_HELPER.read_bytes())
    input_.write_text(json.dumps(aliases))
    ctx = request['context']
    command = [*execution.command, '--run', str(helper), ctx['module'], ctx['file'],
               str(snapshot), generated['declaration'], str(input_), str(output)]
    remaining = job['deadlineMonotonic'] - time.monotonic()
    if remaining <= 0:
        raise ValueError('shared recognition deadline expired before aliases')
    process = run_bounded_target_process(command, cwd=job['root'], env=execution.environment,
        timeout_seconds=remaining, max_rss_bytes=job['maxRssBytes'], max_output_bytes=job['maxOutputBytes'])
    encoded = _read_regular(output, job['maxOutputBytes']).decode() if output.exists() else None
    return {'request': aliases, 'generated': generated, 'workerJson': encoded,
            'worker': parse_worker(encoded) if process.succeeded and encoded is not None else None,
            'processReceipt': asdict(process)}
