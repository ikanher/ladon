"""Ordinary investigation commands retain native contract evidence end to end."""
import copy
import json
from datetime import UTC, datetime

from test_investigation_contract_findings import _native_attachment
from test_investigation_findings import observation_case

from ladon.entrypoint import main
from ladon.investigation_finalization import validate_progress_receipt


def test_public_contract_observation_review_report_and_finalize(tmp_path, capsys):
    base, plain = observation_case(tmp_path)
    base['startedAt'] = datetime.now(UTC).isoformat()
    record = copy.deepcopy(plain['observations'][0]['record'])
    record.update(schema='ladon-investigation-observation-v2', contractAnalysis=_native_attachment())
    plan_path, record_path = tmp_path / 'plan.json', tmp_path / 'record.json'
    plan_path.write_text(json.dumps(base))
    original = plan_path.read_bytes()
    record_path.write_text(json.dumps(record))
    observed = tmp_path / 'observed.json'
    shared = ['--root', str(tmp_path)]
    assert main(['investigation', 'observe', '--plan', str(plan_path), *shared,
                 '--record', str(record_path), '--output', str(observed)]) == 0
    assert plan_path.read_bytes() == original
    assert main(['investigation', 'inspect-observations', '--plan', str(observed), *shared]) == 0
    inspected = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert inspected['schema'] == 'ladon-investigation-observations-v2'
    assert inspected['observations'][0]['record'] == record
    reviewed = _review(tmp_path, observed, shared)
    _finish(tmp_path, observed, reviewed, shared, record)


def _review(root, observed, shared):
    subject = json.loads(observed.read_bytes())['observations'][0]['observationId']
    packet_path, response_path = root / 'challenge.json', root / 'response.json'
    assert main(['investigation', 'challenge', '--plan', str(observed), *shared,
                 '--claim', subject, '--output', str(packet_path)]) == 0
    packet = json.loads(packet_path.read_bytes())
    assert packet['schema'] == 'ladon-investigation-observation-challenge-v2'
    response = {'reviewer': 'independent-fixture-reviewer', 'subject': subject,
                'challengeDigest': packet['challengeDigest'], 'classification': 'mismatch',
                'method': 'different', 'sourceFidelity': 'faithful',
                'evidence': 'Fixture attribution; this does not prove source fidelity or truth.'}
    response_path.write_text(json.dumps(response))
    reviewed = root / 'reviewed.json'
    assert main(['investigation', 'ingest', '--plan', str(observed), *shared,
                 '--packet', str(packet_path), '--response', str(response_path),
                 '--output', str(reviewed)]) == 0
    return reviewed


def _finish(root, observed, reviewed, shared, record):
    report_path, terminal_path = root / 'report.json', root / 'terminal.json'
    assert main(['investigation', 'report', '--plan', str(reviewed), '--plan', str(observed),
                 *shared, '--output', str(report_path)]) == 0
    report = json.loads(report_path.read_bytes())
    assert report['schema'] == 'ladon-investigation-report-v2'
    finding = report['findings'][0]
    assert finding['contractAnalysis'] == record['contractAnalysis']
    assert finding['pendingPlanIds']
    assert main(['investigation', 'finalize', '--plan', str(reviewed), *shared,
                 '--output', str(terminal_path)]) == 0
    receipt = json.loads(terminal_path.read_bytes())
    assert receipt['schema'] == 'ladon-investigation-progress-v3'
    plan = json.loads(reviewed.read_bytes())
    assert receipt['terminal'] and not plan['claims']
    assert validate_progress_receipt(receipt, plan, root) == receipt
