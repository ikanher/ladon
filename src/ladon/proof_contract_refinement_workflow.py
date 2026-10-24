"""Fresh refinement attempts and explicitly historical saved-evidence inspection."""
from __future__ import annotations

import time

from ladon import proof_contract_lift_check as lift_owner
from ladon import proof_contract_refinement as refinement
from ladon._proof_contract_refinement_workflow import (
    ARTIFACT_KEYS,
    POSITIVE,
    SCHEMA,
    bounded_artifact,
    canonical,
    finite_deadline,
    identity,
    planned_branches,
    request_inputs,
    saved_lift,
    seal,
)
from ladon.proof_contract_payloads import closed
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES


def refine(request, source_root, *, deadline_monotonic, max_rss_bytes=DEFAULT_MAX_RSS_BYTES):
    """Run one fresh lift then check sibling branches without changing the finding."""
    deadline = finite_deadline(deadline_monotonic)
    bounds = lift_owner._resource_bounds({'max_rss_bytes': max_rss_bytes})
    request, root, plan, branches, original = request_inputs(request, source_root)
    if time.monotonic() >= deadline:
        lifted = lift_owner._result('incomplete', plan, plan['witness'],
                                    'Shared refinement deadline expired.', code='timeout')
    else:
        lifted = _fresh_lift(request, root, plan, deadline, bounds)
    result = {'schema': SCHEMA, 'request': request, 'originalCheck': original,
              'liftPlanId': plan['planId'], 'liftResult': lifted, 'branches': [],
              'status': lifted['status'], 'sourceFormulaFidelity': 'unverified',
              'originalClaimRefuted': False}
    if lifted['status'] in POSITIVE:
        _check_branches(result, branches, root, deadline)
    return seal(result)


def _fresh_lift(request, root, plan, deadline, bounds):
    # Fresh source readers at the boundary avoid using prevalidation caches.
    planned_branches(request, root)
    lift = request['lift']
    lift_owner._source(root, lift['interpretation']['source'])
    owned = {'repoRoot': str(root), 'goal': request['baseGoal'],
             'witness': request['originalFinding']['witness'],
             'interpretation': lift['interpretation'], 'mode': lift['mode'],
             'deadlineMonotonic': deadline, 'limits': bounds}
    if time.monotonic() >= deadline:
        return lift_owner._result('incomplete', plan, plan['witness'],
                                   'Shared refinement deadline expired.', code='timeout')
    return lift_owner.check_nat_rational_lift(owned, plan['planId'], lift['term'])


def _check_branches(result, branches, root, deadline):
    result['status'] = 'incomplete'
    request = result['request']
    for row in branches:
        if time.monotonic() >= deadline:
            return
        checked = refinement.check_rational_refinement(
            row['branch'], request['baseGoal'], request['originalFinding']['witness']['assignment'],
            source_root=root)
        result['branches'].append({**row, 'check': checked})
    # Re-read both formal source and all citations after the last check.
    lift_owner._source(root, request['lift']['interpretation']['source'])
    planned_branches(request, root)
    if time.monotonic() < deadline:
        result['status'] = 'completed'


def inspect_refinement(artifact, source_root):
    """Recompute rational/source evidence; imported Lean claims remain unverified."""
    artifact = bounded_artifact(artifact)
    closed(artifact, ARTIFACT_KEYS, 'refinement artifact')
    if artifact['schema'] != SCHEMA:
        raise ValueError('unsupported refinement artifact schema')
    unsigned = {key: value for key, value in artifact.items() if key != 'artifactId'}
    if artifact['artifactId'] != identity(unsigned):
        raise ValueError('refinement artifact identity changed')
    request, root, plan, branches, original = request_inputs(artifact['request'], source_root)
    _inspect_original(artifact, original, plan)
    saved_lift(artifact['liftResult'], request, plan)
    _inspect_branches(artifact, branches, root)
    return {'schema': 'ladon-proof-contract-refinement-inspection-v1',
            'status': 'validated-historical', 'artifact': artifact, 'leanReplayed': False,
            'liftAuthority': 'unverified-saved-result', 'originalClaimRefuted': False,
            'sourceFormulaFidelity': 'unverified'}


def _inspect_original(artifact, original, plan):
    if artifact['originalClaimRefuted'] is not False or artifact['sourceFormulaFidelity'] != 'unverified':
        raise ValueError('refinement artifact exceeds source authority')
    if canonical(artifact['originalCheck']) != canonical(original):
        raise ValueError('original rational check changed')
    if artifact['liftPlanId'] != plan['planId']:
        raise ValueError('refinement lift plan changed')


def _inspect_branches(artifact, planned, root):
    rows = artifact['branches']
    if type(rows) is not list or len(rows) > len(planned):
        raise ValueError('refinement branches exceed requested population')
    lift_status = artifact['liftResult']['status']
    if lift_status not in POSITIVE:
        if rows or artifact['status'] != lift_status:
            raise ValueError('nonpositive lift cannot carry completed branches')
        return
    if artifact['status'] not in {'completed', 'incomplete'}:
        raise ValueError('refinement workflow status is inconsistent')
    if artifact['status'] == 'completed' and len(rows) != len(planned):
        raise ValueError('completed refinement is missing requested branches')
    for row, expected in zip(rows, planned, strict=False):
        _inspect_branch(row, expected, artifact['request'], root)


def _inspect_branch(row, expected, request, root):
    closed(row, {'kind', 'branch', 'check'}, 'refinement branch row')
    if canonical({'kind': row['kind'], 'branch': row['branch']}) != canonical(expected):
        raise ValueError('refinement branch changed its original inputs')
    refinement.verify_rational_refinement_result(
        row['check'], expected['branch'], request['baseGoal'],
        request['originalFinding']['witness']['assignment'], source_root=root)
