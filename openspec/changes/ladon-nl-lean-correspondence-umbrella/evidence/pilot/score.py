"""Aggregate independently adjudicated rows, without deciding mathematical truth."""
import json
import math
import sys
from collections import Counter
from pathlib import Path

VERDICTS = {'argument-fault', 'faithful', 'method-difference', 'ambiguous', 'unresolved'}
ARMS = {'assisted', 'ordinary'}
FIELDS = {'caseId', 'arm', 'expected', 'verdict', 'evidenceStatus', 'evidenceRefs',
          'elapsedSeconds', 'reviewerSeconds', 'commandCount', 'toolSeconds',
          'interpretationError', 'falseEndpointClaim', 'firstResponseRef', 'correctionRef'}


def _number(value, label):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f'invalid nonnegative finite {label}')


def _validate_row(row, cases):
    if not isinstance(row, dict) or set(row) != FIELDS:
        raise ValueError('normalized row requires exact fields')
    if row['caseId'] not in cases or row['arm'] not in ARMS:
        raise ValueError('row is outside declared population')
    _validate_outcome(row)
    for name in ('elapsedSeconds', 'reviewerSeconds', 'commandCount', 'toolSeconds'):
        _number(row[name], name)
    if type(row['commandCount']) is not int:
        raise ValueError('commandCount must be an integer')
    for name in ('interpretationError', 'falseEndpointClaim'):
        if type(row[name]) is not bool:
            raise ValueError(f'{name} must be boolean')


def _validate_population(cases, rows):
    if len(cases) != 8 or len(set(cases)) != 8 or len(rows) != 16:
        raise ValueError('expected complete eight-case paired population')
    seen, keys = set(), {}
    for row in rows:
        _validate_row(row, set(cases))
        pair = row['caseId'], row['arm']
        if pair in seen:
            raise ValueError('duplicate population row')
        seen.add(pair)
        if row['caseId'] in keys and keys[row['caseId']] != row['expected']:
            raise ValueError('cross-arm expected key disagreement')
        keys[row['caseId']] = row['expected']
    if Counter(keys.values()) != Counter({'argument-fault': 4, 'faithful': 2,
                                          'method-difference': 1, 'ambiguous': 1}):
        raise ValueError('expected key population balance changed')


def _assessed(row):
    within_budget = row['elapsedSeconds'] + row['reviewerSeconds'] <= 900
    valid = (row['evidenceStatus'] != 'unresolved' and bool(row['evidenceRefs'])
             and not row['interpretationError'] and within_budget)
    correct = row['verdict'] == row['expected'] and valid
    return {'justifiedFault': correct and row['expected'] == 'argument-fault',
            'correctControl': correct and row['expected'] != 'argument-fault',
            'falseAlarm': row['verdict'] == 'argument-fault' and row['expected'] != 'argument-fault',
            'abstention': row['verdict'] == 'unresolved',
            'budgetExceeded': not within_budget}


def _arm_summary(rows):
    observations = [_assessed(row) for row in rows]
    result = {'cases': len(rows), 'tokens': None, 'monetaryCost': None}
    metrics = {'justifiedFaults': 'justifiedFault', 'correctControls': 'correctControl',
               'falseAlarms': 'falseAlarm', 'abstentions': 'abstention',
               'budgetExceeded': 'budgetExceeded'}
    result.update({name: sum(row[field] for row in observations)
                   for name, field in metrics.items()})
    fields = {'interpretationErrors': 'interpretationError',
              'falseEndpointClaims': 'falseEndpointClaim', 'commands': 'commandCount',
              'toolSeconds': 'toolSeconds'}
    result.update({name: sum(row[field] for row in rows) for name, field in fields.items()})
    result['allocatedSeconds'] = sum(row['elapsedSeconds'] + row['reviewerSeconds'] for row in rows)
    return result


def aggregate(cases, rows):
    _validate_population(cases, rows)
    selected = {arm: [row for row in rows if row['arm'] == arm] for arm in ARMS}
    summaries = {arm: _arm_summary(data) for arm, data in selected.items()}
    assisted, ordinary = summaries['assisted'], summaries['ordinary']
    detection = (assisted['justifiedFaults'] > ordinary['justifiedFaults']
                 and assisted['falseAlarms'] <= ordinary['falseAlarms'])
    matched = _matched_outcomes(selected)
    cost = _cost_benefit(matched, assisted, ordinary)
    return {'schema': 'ladon-correspondence-pilot-aggregation-v1', 'rowCount': len(rows),
            'arms': summaries, 'detectionBenefit': detection, 'costBenefit': cost,
            'authority': 'mechanical aggregation of separately adjudicated rows only',
            'limitations': ['Constructed pilot only; no historical target-paper result.',
                            'Source fidelity and evidence validity require independent adjudication.',
                            'No token or monetary cost observation is available.']}


def main():
    inputs = json.loads(Path(sys.argv[1]).read_text())
    result = aggregate(inputs['cases'], inputs['rows'])
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2) + '\n')


def _validate_outcome(row):
    if row['expected'] not in VERDICTS - {'unresolved'} or row['verdict'] not in VERDICTS:
        raise ValueError('invalid expected key or verdict')
    if row['evidenceStatus'] not in {'checked-valid', 'attributed-valid', 'unresolved'}:
        raise ValueError('invalid evidence status')
    if not isinstance(row['evidenceRefs'], list) or any(
            not isinstance(ref, str) or not ref for ref in row['evidenceRefs']):
        raise ValueError('invalid evidence references')


def _matched_outcomes(selected):
    pairs = zip(sorted(selected['assisted'], key=lambda r: r['caseId']),
                sorted(selected['ordinary'], key=lambda r: r['caseId']))
    return all(_assessed(a) == _assessed(o) and a['interpretationError'] == o['interpretationError']
               and a['falseEndpointClaim'] == o['falseEndpointClaim'] for a, o in pairs)


def _cost_benefit(matched, assisted, ordinary):
    return (matched and assisted['falseAlarms'] == 0 and ordinary['justifiedFaults'] > 0
            and assisted['allocatedSeconds'] < ordinary['allocatedSeconds'])


if __name__ == '__main__':
    main()
