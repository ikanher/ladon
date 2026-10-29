"""Replay an observed proposition across an exact imported-library inventory."""

import time
from pathlib import Path

from ladon._source_goal_inventory import capture_inventory, verify_inventory
from ladon.process_supervisor import run_bounded_target_process
from ladon.real_prose_expression import parse_worker
from ladon.real_prose_inputs import HELPER, generated_source, sha
from ladon.source_association_io import _read_regular


def _run_lean(job, request, source, execution):
    content, generated = generated_source(request, source)
    workspace = Path(job['workspace'])
    snapshot, helper, output = [workspace / name for name in ('target.lean', 'helper.lean', 'value.json')]
    snapshot.write_bytes(content)
    helper.write_bytes(HELPER.read_bytes())
    output.unlink(missing_ok=True)
    context = request['context']
    command = [*execution.command, '--run', str(helper), context['module'], context['file'],
               str(snapshot), generated['declaration'], str(output)]
    remaining = job['deadlineMonotonic'] - time.monotonic()
    if remaining <= 0:
        raise ValueError('shared prose observation deadline expired')
    process = run_bounded_target_process(command, cwd=job['root'], env=execution.environment,
        timeout_seconds=remaining, max_rss_bytes=job['maxRssBytes'],
        max_output_bytes=job['maxOutputBytes'])
    encoded = (_read_regular(output, job['maxOutputBytes']).decode() if output.exists() else None)
    return process, encoded, generated


def observe_stable(job, request, source, context, execution):
    first, encoded, generated = _run_lean(job, request, source, execution)
    if not first.succeeded or encoded is None or parse_worker(encoded)['status'] != 'observed':
        return [first], encoded, generated, None
    files, environment, inventory = capture_inventory(context, parse_worker(encoded))
    second, replayed, actual_generated = _run_lean(job, request, source, execution)
    verify_inventory(files, environment, inventory)
    if not second.succeeded:
        return [first, second], None, generated, None
    if encoded != replayed or generated != actual_generated:
        raise ValueError('prose proposition changed across compiled-context replay')
    return [first, second], replayed, generated, {
        'inventory': inventory, 'observationDigest': sha(encoded.encode())}
