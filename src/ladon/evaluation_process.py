"""Capture bounded evaluation commands with explicit accounting and immutable logs."""
from __future__ import annotations

import json
from pathlib import Path

from ladon.evaluation_corpus import digest_bytes
from ladon.process_supervisor import run_bounded_target_process


def measure_command(argv, *, cwd, environment, bounds, output: Path, stem: str,
                    remaining_seconds=None) -> dict:
    """Retain observed failures and sampled RSS without treating unavailable data as zero."""
    seconds = bounds['timeoutSeconds'] if remaining_seconds is None else remaining_seconds
    if seconds <= 0:
        return {'status': 'not-run', 'reason': 'registered deadline exhausted', 'runtimeSeconds': 0}
    result = run_bounded_target_process(argv, cwd=cwd, env=environment,
                                        timeout_seconds=seconds, max_output_bytes=bounds['maxOutputBytes'],
                                        max_rss_bytes=bounds['maxRssBytes'])
    record = {'commandVector': list(argv), 'workingDirectory': str(cwd),
              'exitCode': result.returncode, 'status': 'passed' if result.succeeded else 'failed',
              'runtimeSeconds': result.elapsed_seconds, 'peakRssSampledBytes': result.peak_rss_bytes,
              'outputBytes': len(result.stdout.encode()) + len(result.stderr.encode()),
              'timedOut': result.timed_out, 'outputLimited': result.output_limited,
              'memoryLimited': result.memory_limited,
              'nonclaims': ['RSS is sampled process-group accounting; UTF-8 capture volume is not a kernel byte counter.']}
    output.mkdir(parents=True, exist_ok=True)
    for key, data in (('stdout', result.stdout.encode()), ('stderr', result.stderr.encode())):
        path = output / (stem + '.' + key)
        with path.open('xb') as stream:
            stream.write(data)
        record[key + 'Artifact'] = {'path': str(path), 'digest': digest_bytes(data)}
    path = output / (stem + '.command.json')
    with path.open('x') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    return record


def captured_text(record, channel='stdout') -> str:
    artifact = record.get(channel + 'Artifact')
    if artifact is None:
        return ''
    data = Path(artifact['path']).read_bytes()
    if digest_bytes(data) != artifact['digest']:
        raise ValueError('evaluation capture bytes changed')
    return data.decode('utf-8')
