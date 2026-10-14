"""Validate identity, immutable first attempts and score arithmetic, not mathematics."""
from pathlib import Path
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    frozen = json.loads((HERE / 'freeze.json').read_text())
    for path, sha in frozen['files'].items():
        assert digest(HERE / path) == sha, path
    config = json.loads((HERE / 'configuration.json').read_text())
    scores = json.loads((HERE / 'scores.json').read_text())
    inventory = {r['case']: r for r in json.loads((HERE / 'reference-inventory.json').read_text())['cases']}
    expected = {(c, a) for c in config['caseOrder'] for a in config['arms']}
    assert {(r['case'], r['arm']) for r in scores['rows']} == expected
    assert len(scores['rows']) == len(expected) == 28
    for row in scores['rows']:
        run = HERE / 'runs' / (row['case'] + '-' + row['arm'])
        record = json.loads((run / 'record.json').read_text())
        assert record['status'] == 'completed' and record['exitCode'] == 0
        assert not any(record[k] for k in ['timedOut', 'outputLimited', 'memoryLimited', 'tokenOverrun'])
        assert record['configurationSha256'] == digest(HERE / 'configuration.json')
        assert record['inputSha256'] == row['sourceSha256'] == digest(HERE / 'cases' / row['case'] / 'INPUT.md')
        assert row['reportSha256'] == record['reportSha256'] == digest(HERE / row['report'])
        for channel in ['stdout', 'stderr']:
            artifact = record[channel + 'Artifact']
            assert artifact['digest'] == 'sha256:' + digest(run / ('first-attempt.' + channel))
        events = [json.loads(line) for line in (run / 'first-attempt.stdout').read_text().splitlines()]
        usage = [e['usage'] for e in events if e.get('type') == 'turn.completed']
        assert len(usage) == 1 and usage == record['tokenUsage']
        assert sum(u['input_tokens'] + u['output_tokens'] for u in usage) == record['accountedTokens'] == row['accountedTokens']
        assert record['accountedTokens'] <= config['tokenAllowance']
        assert row['runtimeSeconds'] == record['runtimeSeconds']
        assert row['completedToolItems'] == record['completedToolItems']
        assert row['coverageReferenceClaims'] == len(inventory[row['case']]['claims'])
        assert 0 <= row['coverageExaminedClaims'] <= row['coverageReferenceClaims']
        assert not row['interventions'] and not record['interventions']
        assert not any(e.get('item', {}).get('type') == 'web_search' for e in events)
    for arm in config['arms']:
        rows = [r for r in scores['rows'] if r['arm'] == arm]
        aggregate = scores['aggregate'][arm]
        assert aggregate['runs'] == len(rows) == 14
        for key in ['accountedTokens', 'completedToolItems', 'abstentions', 'missedReferenceFindings']:
            source = 'abstention' if key == 'abstentions' else key
            assert aggregate[key] == sum(r[source] for r in rows)
        assert math.isclose(aggregate['runtimeSeconds'], sum(r['runtimeSeconds'] for r in rows))
        assert aggregate['excerptSupportedFindings'] == sum(r['supportedReferenceFinding'] for r in rows if r['class'] == 'excerpt')
        assert aggregate['longSupportedFindings'] == sum(r['supportedReferenceFinding'] for r in rows if r['class'] == 'long-selection')
        assert aggregate['longCoverageExamined'] == sum(r['coverageExaminedClaims'] for r in rows if r['class'] == 'long-selection')
        assert aggregate['longCoverageReference'] == sum(r['coverageReferenceClaims'] for r in rows if r['class'] == 'long-selection')
        assert aggregate['falseAlarmsOnControls'] == sum(r['falseAlarms'] for r in rows if not r['referenceDiscrepancy'])
    return {'status': 'passed', 'firstAttempts': len(expected), 'referenceClaimsLongSelections': 11,
            'scope': 'identity, accounting and attributed-score arithmetic; not correspondence truth'}


if __name__ == '__main__':
    print(json.dumps(verify()))
