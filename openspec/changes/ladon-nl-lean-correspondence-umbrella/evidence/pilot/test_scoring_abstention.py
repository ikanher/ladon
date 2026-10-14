"""Faster all-abstention runs cannot establish a useful cost benefit."""
from test_scoring_contract import load, population


def test_cheaper_all_abstention_has_no_cost_benefit():
    cases, rows = population()
    for row in rows:
        row['verdict'] = 'unresolved'
        row['evidenceStatus'] = 'unresolved'
        row['elapsedSeconds'] = 1 if row['arm'] == 'assisted' else 100
    result = load().aggregate(cases, rows)
    assert result['detectionBenefit'] is False
    assert result['costBenefit'] is False
