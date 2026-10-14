"""Three serial paired trials through the ordinary public correspondence CLI."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import platform
import statistics
import time
from pathlib import Path

from ladon.correspondence_implementation import implementation_digest
from ladon.entrypoint import main

WORKLOADS = {'cone': 6, 'numeric': 6, 'scoped': 8}
ORDERS = [('ordinary', 'request'), ('request', 'ordinary'), ('ordinary', 'request')]
_HARNESS_PATH = Path(__file__).resolve()
_HARNESS_BYTES = _HARNESS_PATH.read_bytes()
_HARNESS_STAT = _HARNESS_PATH.stat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _harness_identity():
    current = _HARNESS_PATH.stat()
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    if (any(getattr(current, key) != getattr(_HARNESS_STAT, key) for key in fields)
            or _HARNESS_PATH.read_bytes() != _HARNESS_BYTES):
        raise ValueError('benchmark harness changed after loading')
    return {'path': str(_HARNESS_PATH), 'sha256': hashlib.sha256(_HARNESS_BYTES).hexdigest(),
            'fingerprint': {key: getattr(current, key) for key in fields}}


def freeze(inputs, repo, source_root):
    populations = {}
    for name, count in WORKLOADS.items():
        directory = inputs / name
        prepared = json.loads((directory / 'prepared.json').read_bytes())
        plan = prepared['plan']
        source = repo / plan['slice']['selection']['sourceFile']
        populations[name] = {'expectedChecks': count, 'planId': plan['planId'],
            'preparedSha256': sha(directory / 'prepared.json'),
            'termsSha256': sha(directory / 'terms.json'), 'sourceSha256': sha(source),
            'selection': plan['slice']['selection'], 'environment': plan['slice']['environment'],
            'compiledInventory': plan['slice']['compiledInventory'],
            'toolchainPin': (repo / 'lean-toolchain').read_text().strip()}
    return {'implementationDigest': implementation_digest(), 'benchmarkHarness': _harness_identity(),
        'populations': populations,
        'orders': ORDERS, 'trialsPerWorkload': 3,
        'cachePolicy': 'existing compiled checkout and warmed OS caches; no clean/full build',
        'concurrentBuild': False, 'concurrencyDisclosure': 'operator serializes all builds/tests/replays; external activity not mechanically measured',
        'entrypointScope': 'entrypoint.main in one warmed Python process; interpreter startup and harness input freezing excluded',
        'hardware': {'platform': platform.platform(), 'processor': platform.processor()},
        'repo': str(repo), 'sourceRoot': str(source_root),
        'target': {'minimumConeMedianGain': .30, 'maximumOtherMedianRegression': .10}}


def trial(name, index, mode, inputs, output, repo, source_root):
    directory = output / name / f'trial-{index}-{mode}'
    directory.mkdir(parents=True, exist_ok=False)
    command = ['investigation', 'check', '--plan', str(inputs / name / 'prepared.json'),
        '--terms', str(inputs / name / 'terms.json'), '--repo', str(repo),
        '--root', str(source_root), '--preparation', mode, '--output', str(directory / 'checked.json')]
    log = io.StringIO()
    started = time.monotonic()
    with contextlib.redirect_stdout(log):
        code = main(command)
    result = {'workload': name, 'trial': index, 'requestedMode': mode, 'exitCode': code,
              'wallSeconds': time.monotonic() - started,
              'command': ['uv', 'run', '--locked', 'python', '-m', 'ladon.entrypoint', *command]}
    (directory / 'CLI.log').write_text(log.getvalue())
    checked_path = directory / 'checked.json'
    if checked_path.exists():
        checked = json.loads(checked_path.read_bytes())
        result.update(serializedBytes=checked_path.stat().st_size, sha256=sha(checked_path),
            actualMode=checked['preparationMode'], accounting=checked['executionAccounting'],
            checks=[{'obligation': r['obligation'], 'mode': r['mode'], 'goal': r['goal'],
                     'status': r['status'], 'trust': r.get('completion', {}).get('trust')}
                    for r in checked['checks']], parentSupport=checked['parentSupport'],
            residuals=checked['residuals'],
            compiledImportIdentityReuses=checked['compiledImportIdentityReuses'])
        result['qualified'] = _qualified(code, checked, name, mode)
    else:
        result['qualified'] = False
    (directory / 'timing.json').write_text(json.dumps(result, indent=2) + '\n')
    print(name, index, mode, result['wallSeconds'], result['qualified'], flush=True)
    return result


def _qualified(code, checked, name, mode):
    return (code == 0 and len(checked['checks']) == WORKLOADS[name]
            and checked['parentSupport'] == 'supported-for-attributed-interpretation'
            and all(r['status'] == 'supported' for r in checked['checks'])
            and checked['preparationMode'] == mode and not checked['residuals']
            and all(_trusted(r) for r in checked['checks']))


def _trusted(row):
    completion = row.get('completion', {})
    trust = completion.get('trust', {})
    return (completion.get('replay', {}).get('status') == 'accepted'
            and trust.get('accepted') is True and trust.get('coverage') == 'complete'
            and trust.get('policy') == 'lean-standard-no-placeholders-v1'
            and isinstance(trust.get('observedAxioms'), list)
            and 'sorryAx' not in trust['observedAxioms'])


def _equivalent_work(results):
    for name in WORKLOADS:
        populations = [_work_identity(r) for r in results if r['workload'] == name]
        if len(populations) != 6 or any(p != populations[0] for p in populations):
            return False
    return True


def _work_identity(result):
    return sorted((r['obligation'], r['mode'], r['goal'], r['status'],
                   r['trust']['policy'], r['trust']['coverage'],
                   tuple(sorted(r['trust']['observedAxioms']))) for r in result['checks'])


def summarize(results):
    qualified = (all(r['qualified'] for r in results) and _valid_grid(results)
                 and _equivalent_work(results))
    comparisons = _paired_medians(results)
    target = qualified and comparisons['cone']['gain'] >= .30 and all(
        comparisons[name]['gain'] >= -.10 for name in ('numeric', 'scoped'))
    return {'qualifiedEquivalentWork': qualified, 'targetMet': target,
        'comparisons': comparisons, 'trialCount': len(results),
        'nonclaim': 'Operational evidence only; no paper error or better mathematical detection established.'}


def _valid_grid(results):
    expected = {(name, index, mode) for name in WORKLOADS
                for index, modes in enumerate(ORDERS, 1) for mode in modes}
    actual = [(r['workload'], r['trial'], r['requestedMode']) for r in results]
    return (len(actual) == len(expected) and set(actual) == expected
            and all(type(r['trial']) is int for r in results))


def _paired_medians(results):
    comparisons = {}
    for name in WORKLOADS:
        medians = {mode: statistics.median(r['wallSeconds'] for r in results
                   if r['workload'] == name and r['requestedMode'] == mode)
                   for mode in ('ordinary', 'request')}
        comparisons[name] = {**medians, 'gain': 1 - medians['request'] / medians['ordinary']}
    return comparisons


def run(args):
    args.output.mkdir(parents=True, exist_ok=False)
    baseline = freeze(args.inputs, args.repo, args.root)
    (args.output / 'FREEZE.json').write_text(json.dumps(baseline, indent=2) + '\n')
    results = []
    for name in WORKLOADS:
        for index, modes in enumerate(ORDERS, 1):
            for mode in modes:
                if freeze(args.inputs, args.repo, args.root) != baseline:
                    raise ValueError('benchmark source, implementation, environment or terms drifted')
                results.append(trial(name, index, mode, args.inputs, args.output, args.repo, args.root))
    if freeze(args.inputs, args.repo, args.root) != baseline:
        raise ValueError('benchmark source identity changed during final trial')
    summary = summarize(results)
    (args.output / 'SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('inputs', 'output', 'repo', 'root'):
        parser.add_argument('--' + name, type=lambda p: Path(p).resolve(), required=True)
    run(parser.parse_args())
