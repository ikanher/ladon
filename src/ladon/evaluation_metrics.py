"""Report labeled recall, verified suggestion outcomes and resources separately."""
from __future__ import annotations


def summarize_method(result, expected_candidates) -> dict:
    """Unavailable/unassessed observations stay null; accepted partials stay separate."""
    if result['status'] == 'unavailable':
        return {'status': 'unavailable', 'reason': result['reason'], 'verifiedCandidateRecall': None,
                'incorrectSuggestionRate': None, 'timeToFirstAcceptedCandidateSeconds': None,
                'scratchReplaySuccessRate': None, 'runtimeSeconds': None,
                'peakRssSampledBytes': None, 'outputBytes': None}
    rows = result['assessments']
    closed = [row for row in rows if row['status'] == 'closed']
    found = {row['candidate'] for row in closed if row['candidate'] is not None}
    expected = set(expected_candidates)
    attempts, compiled = _scratch_counts(result)
    metrics = {'status': 'measured', 'verifiedCandidateRecall': len(found & expected) / len(expected) if expected else None,
               'timeToFirstAcceptedCandidateSeconds': min((row['availableAfterSeconds'] for row in closed), default=None),
               'scratchReplaySuccessRate': compiled / attempts if attempts else None,
               'closedCandidates': sorted(found),
               'scratchAttempts': attempts, 'scratchCompiled': compiled}
    metrics.update(_suggestion_counts(rows))
    metrics.update(_outcome_counts(rows, closed))
    metrics.update(_resource_totals(result))
    return metrics


def _outcome_counts(rows, closed):
    return {'closedProofsWithoutLabeledDeclaration': sum(row['candidate'] is None for row in closed),
            'partialApplications': sum(row['status'] == 'partial' for row in rows),
            'rejectedCandidates': sum(row['status'] == 'rejected' for row in rows),
            'unassessedCandidates': sum(row['status'] == 'unassessed' for row in rows)}


def _suggestion_counts(rows):
    invalid = sum(row['status'] in ('invalid', 'admitted') for row in rows)
    assessed = sum(row['status'] in ('closed', 'partial', 'invalid', 'admitted') for row in rows)
    return {'incorrectSuggestionRate': invalid / assessed if assessed else None,
            'invalidSuggestions': invalid, 'assessedSuggestions': assessed}


def _scratch_counts(result):
    attempted = [row for row in result['assessments'] if isinstance(row.get('measurement'), dict)
                 and row['measurement'].get('status') != 'not-run']
    return len(attempted), sum(row['status'] == 'closed' for row in attempted)


def _resource_totals(result):
    measurements = [result['generation'], *[row['measurement'] for row in result['assessments'] if row.get('measurement')]]
    rss = [row.get('peakRssSampledBytes') for row in measurements if row.get('peakRssSampledBytes') is not None]
    return {'runtimeSeconds': sum(row['runtimeSeconds'] for row in measurements),
            'peakRssSampledBytes': max(rss) if rss else None,
            'outputBytes': sum(row.get('outputBytes', 0) for row in measurements),
            'generationRuntimeSeconds': result['generation']['runtimeSeconds'],
            'verificationRuntimeSeconds': sum(row['runtimeSeconds'] for row in measurements[1:])}
