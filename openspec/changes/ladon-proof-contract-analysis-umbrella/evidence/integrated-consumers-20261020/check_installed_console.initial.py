"""Exercise the locally built console script on constructed contract inputs."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import UTC, datetime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-copy', type=Path, required=True)
    parser.add_argument('--console', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(exist_ok=False)
    sys.path.insert(0, str(args.source_copy / 'tests'))
    from test_investigation_contract_findings import _native_attachment
    from test_investigation_findings import observation_case
    from test_proof_contract_audit_driver import _fixture_plan
    from ladon.investigation_finalization import validate_progress_receipt
    import ladon
    assert Path(ladon.__file__).resolve().is_relative_to(args.console.parent.parent)
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONHOME', None)
    records = []

    def write(name, value):
        path = args.out / name
        path.write_text(json.dumps(value, indent=2) + '\n')
        return path

    def read(name):
        return json.loads((args.out / name).read_text())

    def run(name, *parts, expected=0):
        command = [str(args.console), *map(str, parts)]
        start = time.monotonic()
        result = subprocess.run(command, cwd=args.source_copy, env=env,
                                capture_output=True, text=True, timeout=60, check=False)
        (args.out / (name + '.stdout')).write_text(result.stdout)
        (args.out / (name + '.stderr')).write_text(result.stderr)
        records.append({'name': name, 'argv': command, 'cwd': str(args.source_copy),
                        'expectedExit': expected, 'exitCode': result.returncode,
                        'elapsedSeconds': time.monotonic() - start})
        write('COMMANDS.json', records)
        assert result.returncode == expected, (name, result.stdout, result.stderr)
        return result

    run('help', 'investigation', 'contract', 'audit', '--help')
    plan = write('audit-plan.json', _fixture_plan())
    run('checkpoint', 'investigation', 'contract', 'audit', '--plan', plan,
        '--output', args.out / 'checkpoint', '--max-stages', '1')
    checkpoint = read('checkpoint/run.json')
    assert checkpoint['status'] == 'partial'
    prefix = (args.out / 'checkpoint/stages/propagate.json').read_bytes()
    run('resume', 'investigation', 'contract', 'audit', '--plan', plan,
        '--output', args.out / 'resumed', '--resume', args.out / 'checkpoint')
    resumed = read('resumed/run.json')
    assert resumed['status'] == 'completed'
    assert resumed['clock'] == checkpoint['clock']
    assert (args.out / 'checkpoint/stages/propagate.json').read_bytes() == prefix
    source = args.out / 'source'
    source.mkdir()
    base, plain = observation_case(source)
    base['startedAt'] = datetime.now(UTC).isoformat()
    record = copy.deepcopy(plain['observations'][0]['record'])
    record.update(schema='ladon-investigation-observation-v2', contractAnalysis=_native_attachment())
    plan = write('plan.json', base)
    original = plan.read_bytes()
    record_path = write('record.json', record)
    observed, reviewed = args.out / 'observed.json', args.out / 'reviewed.json'
    shared = ['--root', source]
    run('observe', 'investigation', 'observe', '--plan', plan, *shared,
        '--record', record_path, '--output', observed)
    inspected = run('inspect', 'investigation', 'inspect-observations', '--plan', observed, *shared)
    assert json.loads(inspected.stdout)['observations'][0]['record'] == record
    subject = read('observed.json')['observations'][0]['observationId']
    packet_path = args.out / 'challenge.json'
    run('challenge', 'investigation', 'challenge', '--plan', observed, *shared,
        '--claim', subject, '--output', packet_path)
    packet = read('challenge.json')
    assert packet['schema'] == 'ladon-investigation-observation-challenge-v2'
    response = write('response.json', {'reviewer': 'constructed-attribution', 'subject': subject,
        'challengeDigest': packet['challengeDigest'], 'classification': 'mismatch',
        'method': 'different', 'sourceFidelity': 'faithful',
        'evidence': 'Constructed fixture attribution; no actual source-fidelity judgment.'})
    run('ingest', 'investigation', 'ingest', '--plan', observed, *shared,
        '--packet', packet_path, '--response', response, '--output', reviewed)
    run('report', 'investigation', 'report', '--plan', reviewed, '--plan', observed,
        *shared, '--output', args.out / 'report.json')
    report = read('report.json')
    assert report['schema'] == 'ladon-investigation-report-v2'
    assert report['findings'][0]['contractAnalysis'] == record['contractAnalysis']
    assert report['findings'][0]['pendingPlanIds']
    run('finalize', 'investigation', 'finalize', '--plan', reviewed, *shared,
        '--output', args.out / 'terminal.json')
    receipt = read('terminal.json')
    assert receipt['schema'] == 'ladon-investigation-progress-v3'
    assert not read('reviewed.json')['claims']
    assert validate_progress_receipt(receipt, read('reviewed.json'), source) == receipt
    observed_bytes = observed.read_bytes()
    run('collision', 'investigation', 'observe', '--plan', plan, *shared,
        '--record', record_path, '--output', observed, expected=2)
    assert observed.read_bytes() == observed_bytes and plan.read_bytes() == original
    write('RESULT.json', {'status': 'passed', 'commands': len(records),
        'origin': ladon.__file__, 'sameClockResume': True, 'emptyClaimsFinalized': True,
        'pendingBranchRetained': True, 'inputBytesUnchanged': True,
        'scope': 'Constructed fixtures only; no source interpretation or discovery claim.'})
    print('PASS:', len(records), 'installed console operations')


if __name__ == '__main__':
    main()
