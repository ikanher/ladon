"""Measure the ordinary installed discovery command on a registered subject."""
from __future__ import annotations

import json
from pathlib import Path

from ladon.evaluation_baselines import _replay_proposals
from ladon.evaluation_process import captured_text, measure_command


def run_ladon(case, context, bounds, output: Path, *, console: Path, index: Path) -> dict:
    """Keep every terminal outcome; partial applications never become closed candidates."""
    argv = [str(console), 'proof-search', 'discover', '--repo-root', str(context.repo_root),
            '--index', str(index), '--module', case['module'], '--goal', case['goal'],
            '--pattern', case['pattern'], '--scope', case['scope'], '--freshness', 'verify',
            '--format', 'json', '--projection', 'review', '--scratch-mode', 'advisory',
            '--toolchain-mode', 'explicit', '--lean-path', str(context.lean_path),
            '--lake-path', str(context.lake_path), '--max-candidates', str(bounds['maxCandidates']),
            '--batch-size', str(bounds['batchSize']), '--timeout-seconds', str(bounds['timeoutSeconds']),
            '--max-rss-mib', str(bounds['maxRssBytes'] // (1024 ** 2)),
            '--max-output-mib', str(bounds['maxOutputBytes'] // (1024 ** 2)),
            '--evidence-store', str(output / 'evidence.sqlite')]
    for root in case['roots']:
        argv.extend(('--root', root))
    for row in case['localContext']:
        argv.extend(('--local', row['name'] + ':' + row['type']))
    generation = measure_command(argv, cwd=output, environment=context.environment, bounds=bounds,
                                 output=output, stem='generation')
    assessments = []
    payload = _terminal_payload(generation)
    if payload is not None:
        _validate_subject(payload['request'], case)
        assessments = [_assessment(row, generation['runtimeSeconds']) for row in payload['candidates']]
        if generation['status'] == 'passed' and payload.get('status') == 'available':
            _verify_offered_candidates(assessments, case, context, bounds, output, generation['runtimeSeconds'])
        else:
            for row in assessments:
                if row['status'] == 'closed':
                    row.update(advertisedOutcome='closed', status='unassessed',
                               failureStage='incomplete-terminal-execution')
    return {'method': 'ladon', 'status': generation['status'], 'generation': generation,
            'assessments': assessments, 'population': 'bounded scoped lexical shortlist',
            'nonclaims': ['Terminal batches expose acceptance only at completion.',
                          'At most one independently recorded advisory scratch replay is requested.']}


def _terminal_payload(generation):
    try:
        payload = json.loads(captured_text(generation))
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict) and payload.get('schema') == 'ladon-verified-discovery-projection-v1':
        return payload
    if generation['status'] == 'passed':
        raise ValueError('successful discovery execution lacks its terminal projection')
    return None


def _validate_subject(request, case) -> None:
    for field in ('module', 'goal', 'localContext', 'scope', 'roots'):
        if request[field] != case[field]:
            raise ValueError('measured Ladon request differs from the registered subject')


def _assessment(row, elapsed):
    check = row['check']
    outcomes = {'accepted': 'closed', 'applicable-with-residuals': 'partial', 'rejected': 'rejected'}
    status = outcomes.get(check['status'], 'unassessed')
    if status == 'closed' and check.get('residualPremises') != []:
        raise ValueError('closed candidate lacks exact zero-residual evidence')
    return {'candidate': row['name'], 'status': status, 'availableAfterSeconds': elapsed,
            'evidenceReceipt': check.get('evidenceReceipt'), 'checkRunRef': check.get('checkRunRef'),
            'failureStage': (check.get('failure') or {}).get('stage'),
            'failureDiagnostic': (check.get('failure') or {}).get('diagnostic'),
            'scratch': check.get('scratch'), 'measurement': None}


def _verify_offered_candidates(rows, case, context, bounds, output, elapsed):
    offered = [row for row in rows if row['status'] == 'closed']
    proposals = [('apply ' + row['candidate'] + '\nall_goals assumption', row['candidate']) for row in offered]
    replays = _replay_proposals(proposals, case, context, bounds, output, elapsed)
    for row, replay in zip(offered, replays, strict=True):
        row['advertisedOutcome'] = row['status']
        outcome = 'invalid' if replay['status'] == 'partial' else replay['status']
        row.update(status=outcome, independentOutcome=replay['status'], measurement=replay['measurement'],
                   availableAfterSeconds=replay['availableAfterSeconds'],
                   independentReplaySourcePath=replay['sourcePath'])
