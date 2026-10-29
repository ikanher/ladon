"""Public native authoring and replay preserve explicit attribution and no admission."""

import json

import pytest
from test_proof_contract_cli import invoke
from test_real_prose_recognition import context, reading
from test_real_prose_recognition import project as _project_fixture


@pytest.fixture
def project(tmp_path):
    return _project_fixture.__wrapped__(tmp_path)


def inputs(project, **options):
    for name, value in [('reading', reading(project, **options)), ('context', context())]:
        (project / (name + '.json')).write_text(json.dumps(value))
    return ['--root', project, '--interpretation', project / 'reading.json',
            '--context', project / 'context.json', '--alternative-id', 'public:a',
            '--author', 'test-author', '--timeout-seconds', '60']


def _assert_historical_report(report):
    assert report['admission'] == 'unresolved' and report['authority'] == 'none'
    assert report['freshCheck'] is False


def test_public_authoring_report_replay_and_output_collision(project):
    output = project / 'authored.json'
    args = inputs(project, set_indexed=True)
    run = invoke('produce-real-prose-bound', *args, '--output', output)
    assert run.returncode == 0, run.stdout + run.stderr
    saved = json.loads(output.read_text())
    record = saved['check']['result']['artifacts'][-1]['payload']['record']
    assert record['scope']['kind'] == 'set-indexed'
    assert record['alternativeId'] == 'public:a'
    for operation in ('inspect', 'report-real-prose-bound'):
        inspected = invoke(operation, '--input', output, '--root', project)
        assert inspected.returncode == 0, inspected.stdout + inspected.stderr
        report = json.loads(inspected.stdout)
        _assert_historical_report(report)
    replay = invoke('replay-real-prose-bound', '--root', project, '--input', output,
                    '--timeout-seconds', '60', '--output', project / 'replayed.json')
    assert replay.returncode == 0, replay.stdout + replay.stderr
    before = output.read_bytes()
    assert invoke('produce-real-prose-bound', *args, '--output', output).returncode == 2
    assert output.read_bytes() == before


def test_unresolved_alias_creates_no_native_contract(project):
    output = project / 'unresolved.json'
    run = invoke('produce-real-prose-bound', *inputs(project, product='wrongProduct'), '--output', output)
    assert run.returncode == 2
    saved = json.loads(output.read_text())
    assert saved['status'] == 'unresolved'
    assert saved['check']['result']['artifacts'] == []


def test_caller_cannot_supply_admitted_features(project):
    run = invoke('produce-real-prose-bound', *inputs(project), '--admission', 'admitted')
    assert run.returncode == 2
