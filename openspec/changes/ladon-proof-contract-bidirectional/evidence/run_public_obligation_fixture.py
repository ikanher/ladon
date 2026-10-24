"""Exercise ordinary public planning, inspection and source checking serially."""
import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from time import monotonic

from support.proof_contract_planned_source import build_plan_request
from test_proof_contract_planned_source import FIXTURE

from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.proof_contract_obligation_artifacts import request_payload
from ladon.proof_contract_source_obligations import _runner
from ladon.process_supervisor import run_bounded_target_process


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


def command(output, stem, arguments, deadline):
    argv = [sys.executable, '-m', 'ladon.entrypoint', 'investigation', 'contract', *arguments]
    process = run_bounded_target_process(argv, cwd=Path.cwd(), env=os.environ,
        timeout_seconds=max(0.001, deadline - monotonic()), max_output_bytes=8 * 1024**2,
        max_rss_bytes=12 * 1024**3)
    (output / (stem + '.stdout')).write_text(process.stdout)
    (output / (stem + '.stderr')).write_text(process.stderr)
    save(output / (stem + '-receipt.json'), {
        'command': argv, 'returnCode': process.returncode,
        'elapsedSeconds': process.elapsed_seconds, 'peakRssBytes': process.peak_rss_bytes,
        'memoryLimited': process.memory_limited, 'timedOut': process.timed_out,
        'outputLimited': process.output_limited})
    if process.returncode or process.memory_limited or process.timed_out or process.output_limited:
        raise RuntimeError('Public command stopped: ' + stem + '; inspect its saved receipt')
    return json.loads(process.stdout) if process.stdout.strip() else None


def prepare(output, root, deadline):
    snapshots = {}
    for name in ('firstBound', 'secondBound', 'thirdBound', 'alternateBound', 'endpoint'):
        snapshot = produce_formal_snapshot(root, 'ThreeSteps.lean', 'ThreeSteps',
            'ThreeSteps.' + name, runner=_runner(deadline), timeout_seconds=30)
        save(output / (name + '-snapshot.json'), snapshot)
        if snapshot['status'] != 'extracted':
            raise RuntimeError('Fresh observation unavailable: ' + name)
        snapshots[name] = snapshot
    request = build_plan_request(snapshots)
    save(output / 'graph.json', request.derivation_artifact)
    save(output / 'request.json', request_payload(request))
    artifacts = {a['artifactId']: a for s in snapshots.values() for a in s['artifacts']}
    artifacts[request.derivation_artifact['artifactId']] = request.derivation_artifact
    save(output / 'context.json', {'artifacts': list(artifacts.values())})
    providers, contracts = [], []
    for index, name in enumerate(('firstBound', 'secondBound', 'thirdBound', 'alternateBound')):
        snapshot = snapshots[name]
        contract = next(a for a in snapshot['artifacts'] if a['artifactKind'] == 'proofir.contract')
        path = output / ('contract-' + str(index) + '.json')
        save(path, contract)
        contracts.append(path)
        providers.append({'contractRef': {'artifactRef': contract['artifactId'],
            'kind': 'contract', 'localId': contract['payload']['contractId']},
            'providerSnapshot': snapshot, 'providerReadingId': 'reading:' + name,
            'terms': ['by exact ThreeSteps.' + name]})
    save(output / 'sources.json', {'parentSnapshot': snapshots['endpoint'],
        'parentReadingId': request.desired_reading_identity['readingId'], 'providers': providers})
    return contracts


def run(output):
    started = monotonic()
    deadline = started + 180
    output.mkdir(parents=True, exist_ok=False)
    root = output / 'repo'
    root.mkdir()
    for name in ('ThreeSteps.lean', 'lean-toolchain'):
        shutil.copyfile(FIXTURE / name, root / name)
    source = (root / 'ThreeSteps.lean').read_bytes()
    contracts = prepare(output, root, deadline)
    args = ['obligations', '--derivation', str(output / 'graph.json'),
        '--request', str(output / 'request.json'), '--analysis-id', 'analysis:public-source-fixture',
        '--timeout-seconds', str(min(30, deadline - monotonic())),
        '--output', str(output / 'obligations.json')]
    for path in contracts:
        args.extend(['--contract', str(path)])
    command(output, 'plan', args, deadline)
    command(output, 'inspect', ['inspect', '--input', str(output / 'obligations.json'),
        '--context', str(output / 'context.json')], deadline)
    report = command(output, 'check', ['check-obligations', '--input', str(output / 'obligations.json'),
        '--context', str(output / 'context.json'), '--sources', str(output / 'sources.json'),
        '--root', str(root), '--output-dir', str(output / 'checked'),
        '--timeout-seconds', str(deadline - monotonic())], deadline)
    if (root / 'ThreeSteps.lean').read_bytes() != source:
        raise RuntimeError('Original fixture changed')
    summary = {'schema': 'ladon-public-obligation-fixture-v1',
        'scope': 'constructed-development-control', 'elapsedSeconds': monotonic() - started,
        'budgetSeconds': 180, 'sourceUnchanged': True,
        'sourceDigest': 'sha256:' + hashlib.sha256(source).hexdigest(),
        'sourceChecks': {r['providerDeclaration']: r['status'] for r in report['sourceChecks']},
        'routes': report['routes'], 'wholeMethodAuthority': report['wholeMethodAuthority'],
        'mathematicalFalsity': report['mathematicalFalsity']}
    save(output / 'SUMMARY.json', summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output.resolve())
