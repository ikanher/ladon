"""Exercise known, answer-informed records; no fresh discovery or Lean replay."""
import argparse
import copy
import json
from pathlib import Path

from ladon.investigation import load_plan
from ladon.investigation_correspondence import attach_bundle, challenge_packet_v3, ingest_response
from ladon.investigation_finalization import progress_receipt
from ladon.investigation_observations import (
    challenge_observation, ingest_observation_response, record_observation,
)
from ladon.investigation_reporting import aggregate_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    corpus = load_plan(args.corpus)
    run = Path(corpus['auditRoot'])
    old = load_plan(run / 'plan-08-inventory-compact.json', max_bytes=32 * 1024**2)
    base = {key: copy.deepcopy(old[key]) for key in
            ('version', 'startedAt', 'budgetSeconds', 'scope', 'units', 'claims')}
    base.update(version=3, correspondenceBundles=[], responses=[], reconciliations=[])
    branches, checks = [], []
    for case in corpus['cases']:
        if case['kind'] == 'reference-discrepancy':
            plan = observation_branch(base, case, args.root, args.corpus.parent)
        else:
            plan = native_branch(base, case, args.root, run)
        receipt, saved = progress_receipt(plan, args.root, finalize=True)
        assert saved and receipt['mathematicalReview'] == 'complete-attributed'
        branches.append(plan)
        output = args.output / (case['id'] + '-terminal.json')
        output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
        checks.append({'id': case['id'], 'receipt': output.name, 'status': receipt['status'],
                       'formalCorrespondence': receipt['formalCorrespondence'],
                       'limits': case.get('limits', case.get('scope'))})
    report = aggregate_report(branches, args.root)
    assert len(report['observations']) == 2
    observed = [f for f in report['findings'] if f['kind'] == 'observation']
    assert len(observed) == 2 and all(f['statementRelation'] == 'mismatch' for f in observed)
    native = [f for f in report['findings'] if f['kind'] == 'native-correspondence-review']
    assert len(native) == 6 and all(f['statementRelation'] == 'aligned' for f in native)
    assert sorted(f['methodRelation'] for f in native) == ['different'] * 2 + ['same'] * 4
    assert all(f['mathematicalFalsity'] == 'not-established' for f in report['findings'])
    (args.output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    summary = {'authority': 'Answer-informed known-case projection; recorded checks only; no new Lean replay.',
               'startedAt': base['startedAt'], 'budgetSeconds': base['budgetSeconds'],
               'referenceDiscrepanciesRetained': 2, 'localControlsRetained': 6,
               'differentValidControlMethods': 2, 'newLeanChecks': 0, 'freshDiscoveries': 0,
               'qualifications': checks}
    (args.output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def observation_branch(base, case, root, corpus_dir):
    source_rows = (corpus_dir / case['source']).read_text().splitlines()
    start, end = int(source_rows[0].split(':', 1)[0]), int(source_rows[-1].split(':', 1)[0])
    lines = (root / base['scope']['path']).read_text().splitlines()
    record = {'schema': 'ladon-investigation-observation-v1', 'id': case['id'],
              'source': {**base['scope'], 'startLine': start, 'endLine': end,
                         'quote': '\n'.join(lines[start - 1:end])},
              'author': 'answer-informed-curator', 'assertion': case['scope'],
              'comparison': case['expected']['statementRelation'],
              'evidence': case['observedEvidenceQuote'], 'formalSources': [],
              'dependencies': 'Original source assumptions; exact native bridge not established in recorded run.'}
    plan = record_observation(base, record, root)
    subject = plan['observations'][0]['observationId']
    packet = challenge_observation(plan, subject, root)
    response = {'reviewer': 'development-projection-check', 'subject': subject,
                'challengeDigest': packet['challengeDigest'], 'classification': 'mismatch',
                'method': 'different', 'sourceFidelity': 'faithful',
                'evidence': 'Answer-informed transcription of frozen review observation, not a new blind assessment: '
                            + case['observedEvidenceQuote']}
    return ingest_observation_response(plan, packet, response, root)


def native_branch(base, case, root, run):
    bundle = load_plan(run / case['checkedArtifact'], max_bytes=32 * 1024**2)
    plan = attach_bundle(base, bundle, root)
    subject = plan['correspondenceBundles'][0]['subject']
    packet = challenge_packet_v3(plan, subject, root)
    response = load_plan(run / case['review'])
    return ingest_response(plan, packet, response, root)


if __name__ == '__main__':
    main()
