"""Requalify witness-dependence-v2 against final runtime code."""
import hashlib
import json
import time
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.proof_contract_bridge import _accepted_check
from ladon.proof_contract_probes import check_application_probe, plan_application_probe

base = Path('.codex/state/proof-contract-analysis/witness-feasibility')
prior = json.loads((base / 'START.json').read_text())
p = base / 'attempt-07'
p.mkdir()
repo = (base / 'attempt-04' / 'repo').resolve()
context = json.loads((base / 'attempt-04' / 'context.json').read_text())
sides = json.loads((base / 'attempt-04' / 'actual-sides.json').read_text())
started = time.monotonic()
deadline = started + 1800
limits = {'timeout_seconds': 30, 'max_rss_bytes': 12 * 1024**3, 'max_output_bytes': 8 * 1024**2}
(p / 'START.json').write_text(json.dumps({'startedMonotonic': started,
    'deadlineMonotonic': deadline, 'budgetSeconds': 1800, 'limits': limits,
    'scope': 'final-code requalification using the previously source-extracted closed application and identical native interpretations'}, sort_keys=True, indent=2))
source_actual = json.loads((base / 'attempt-04' / 'actual.json').read_text())
(p / 'source-link.json').write_text(json.dumps({'sourceDigest': source_actual['source']['sha256'],
    'environment': source_actual['environment'], 'source': source_actual['source'],
    'selection': source_actual['selection'], 'sourceExtractionAttempt': 'attempt-04'}, sort_keys=True, indent=2))

cases = [
    ('discrepancy', sides[0], sides[1], 'counterexample', 'right-to-left', {
        'formal-reading': 'Iff.rfl',
        'probe': '''by
  constructor
  · exact WitnessProbe.weak ()
  · intro h
    obtain ⟨w, hw⟩ := h
    have bad : Nat.succ w ≤ w := by
      simpa [WitnessProbe.P] using hw (Nat.succ w)
    exact Nat.not_succ_le_self w bad'''}),
    ('strong-to-weak-control', sides[0], sides[1], 'implication', 'left-to-right', {
        'formal-reading': 'Iff.rfl',
        'probe': '''by
  intro h
  obtain ⟨w, hw⟩ := h
  intro x
  exact ⟨w, hw x⟩'''}),
]
summary = []
for label, left, right, kind, direction, terms in cases:
    request = {'repoRoot': str(repo), 'context': context, 'left': left, 'right': right,
        'template': {'familyId': 'witness-dependence', 'version': 'witness-dependence-v2',
                     'kind': kind, 'direction': direction},
        'deadlineMonotonic': deadline, 'limits': limits}
    (p / f'{label}-request.json').write_text(json.dumps(request, sort_keys=True, indent=2))
    planned = plan_application_probe(request)
    (p / f'{label}-planned.json').write_text(json.dumps(planned, sort_keys=True, indent=2))
    assert planned['status'] == 'planned', planned
    (p / f'{label}-terms.json').write_text(json.dumps(terms, sort_keys=True, indent=2))
    before = time.monotonic()
    checked = check_application_probe(request, planned['planId'], terms)
    (p / f'{label}-checked.json').write_text(json.dumps(checked, sort_keys=True, indent=2))
    accepted = []
    for goal in checked['goals']:
        raw = load_goal_evidence(repo, goal['result'])
        assert _accepted_check(raw) and goal['status'] == 'checked-support'
        accepted.append(goal['goalId'])
    assert checked['status'] == ('checked-local-nonimplication' if kind == 'counterexample'
                                 else 'checked-local-implication')
    assert checked['artifact']['payload']['checkRunRefs'] == []
    assert all(goal['status'] == 'open' for goal in checked['artifact']['payload']['result']['goals'])
    summary.append({'case': label, 'acceptedGoals': accepted, 'elapsedSeconds': time.monotonic()-before})
    print(label, 'PASS', accepted, flush=True)
result = {'status': 'PASS', 'elapsedSeconds': time.monotonic()-started,
    'budgetSeconds': 1800, 'checkerAttempts': 4, 'acceptedGoals': 4,
    'scope': 'constructed authored source-bound discrepancy and cross-order implication control; no natural-language fidelity or target-paper detection claim',
    'cases': summary}
(p / 'RESULT.json').write_text(json.dumps(result, sort_keys=True, indent=2))
print('RESULT', json.dumps(result, sort_keys=True), flush=True)
