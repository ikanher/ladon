"""Closed requests and bounded historical records for refinement workflows."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path

from ladon import proof_contract_lift_check as lift_owner
from ladon.proof_contract_lift_goals import plan_nat_rational_lift
from ladon.proof_contract_payloads import closed
from ladon.proof_contract_refinement import _bounded_json, _finding, create_refinement_branch
from ladon.rational_witness import check_witness, validate_goal

SCHEMA = 'ladon-proof-contract-refinement-workflow-v1'
REQUEST_SCHEMA = 'ladon-proof-contract-refinement-request-v1'
MAX_ARTIFACT_BYTES = 16 * 1024**2
POSITIVE = {'spurious-countermodel', 'lifted-counterexample'}
NEGATIVE = {'incomplete', 'unsupported', 'rejected', 'stale-input', 'unresolved'}
REQUEST_KEYS = {'schema', 'originalFinding', 'baseGoal', 'lift',
                'refinementConstraints', 'repairConstraints'}
ARTIFACT_KEYS = {'schema', 'request', 'originalCheck', 'liftPlanId', 'liftResult',
                 'branches', 'status', 'sourceFormulaFidelity', 'originalClaimRefuted', 'artifactId'}


def finite_deadline(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('deadline must be one finite monotonic time')
    return float(value)


def request_inputs(request, source_root):
    request = _bounded_json(request, 'refinement request')
    closed(request, REQUEST_KEYS, 'refinement request')
    if request['schema'] != REQUEST_SCHEMA:
        raise ValueError('unsupported refinement request schema')
    finding = _finding(request['originalFinding'])
    lift = request['lift']
    closed(lift, {'interpretation', 'mode', 'term'}, 'refinement lift')
    plan = plan_nat_rational_lift(request['baseGoal'], finding['witness'],
                                  lift['interpretation'], mode=lift['mode'])
    lift_owner._validate_term(lift['term'], plan)
    root = Path(source_root).resolve(strict=True)
    lift_owner._source(root, lift['interpretation']['source'])
    branches = planned_branches(request, root)
    original_check = check_witness(request['baseGoal'], finding['witness']['assignment'])
    return request, root, plan, branches, original_check


def planned_branches(request, root):
    rows = []
    for field, kind in (('refinementConstraints', 'source-cited-refinement'),
                        ('repairConstraints', 'proposed-repair')):
        constraints = request[field]
        if type(constraints) is not list or len(constraints) > 64:
            raise ValueError('constraint list must have at most 64 entries')
        if constraints:
            rows.append(_planned_branch(request, root, constraints, kind))
    if not rows:
        raise ValueError('at least one constraint list must be nonempty')
    return rows


def _planned_branch(request, root, constraints, kind):
    branch = create_refinement_branch(request['originalFinding'], constraints, source_root=root)
    if branch['branchKind'] != kind:
        raise ValueError('constraint justification is in the wrong branch')
    derived = copy.deepcopy(request['baseGoal'])
    derived['premises'].extend(copy.deepcopy(row['expression']) for row in constraints)
    validate_goal(derived)
    return {'kind': kind, 'branch': branch}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def identity(value):
    return 'sha256:' + hashlib.sha256(canonical(value)).hexdigest()


def seal(record):
    record = {**record, 'artifactId': identity(record)}
    if len(canonical(record)) > MAX_ARTIFACT_BYTES:
        raise ValueError('refinement artifact exceeds 16 MiB')
    return record


def bounded_artifact(value):
    _native_tree(value)
    encoded = canonical(value)
    if len(encoded) > MAX_ARTIFACT_BYTES:
        raise ValueError('refinement artifact exceeds 16 MiB')
    return json.loads(encoded)


def _native_tree(value):
    stack, count = [(value, 0)], 0
    while stack:
        node, depth = stack.pop()
        count += 1
        if count > 500_000 or depth > 128:
            raise ValueError('refinement artifact exceeds node or depth bound')
        _native_node(node, depth, stack)


def _native_node(node, depth, stack):
    if type(node) is dict:
        if any(type(key) is not str for key in node):
            raise ValueError('refinement artifact keys must be strings')
        stack.extend((child, depth + 1) for child in node.values())
    elif type(node) is list:
        stack.extend((child, depth + 1) for child in node)
    elif type(node) not in (str, bool, int, float, type(None)):
        raise ValueError('refinement artifact must contain only JSON-native values')


def saved_lift(value, request, plan):
    """Check historical shape/bindings only; never authenticate imported evidence."""
    witness = request['originalFinding']['witness']
    template = lift_owner._result('incomplete', plan, witness, None)
    closed(value, set(template), 'historical lift result')
    status = value['status']
    if type(status) is not str or status not in POSITIVE | NEGATIVE:
        raise ValueError('unsupported historical lift status')
    if value['witness'] != witness:
        raise ValueError('historical lift witness changed')
    if value['originalClaimRefuted'] is not False or value['sourceFormulaFidelity'] != 'unverified':
        raise ValueError('historical lift exceeds source authority')
    if value['authenticatedExternalCertificate'] is not False:
        raise ValueError('historical lift cannot authenticate an external certificate')
    if value['planId'] not in (None, plan['planId']) or value['mode'] not in (None, plan['mode']):
        raise ValueError('historical lift plan or mode changed')
    if status in POSITIVE:
        _saved_positive(value, request, plan)
    else:
        _saved_negative(value)


def _saved_negative(value):
    if value['formalClaimRefuted'] is not False or value['sourceVerified'] is not False:
        raise ValueError('nonpositive lift carries a positive authority flag')
    for key in ('spuriousnessEvidence', 'realizationEvidence', 'nativeEvidence', 'checkId', 'binding'):
        if value[key] is not None:
            raise ValueError('nonpositive lift carries positive evidence')


def _saved_positive(value, request, plan):
    realized = plan['mode'] == 'realization'
    expected_status = 'lifted-counterexample' if realized else 'spurious-countermodel'
    expected = {'status': expected_status, 'planId': plan['planId'], 'mode': plan['mode'],
                'sourceVerified': True, 'formalClaimRefuted': realized, 'openObligation': None}
    if canonical({key: value[key] for key in expected}) != canonical(expected):
        raise ValueError('historical lift classification is inconsistent')
    _saved_evidence(value, realized)
    _saved_binding(value['binding'], request, plan)


def _saved_evidence(value, realized):
    evidence = 'realizationEvidence' if realized else 'spuriousnessEvidence'
    other = 'spuriousnessEvidence' if realized else 'realizationEvidence'
    if not value['nativeEvidence'] or value[evidence] != value['nativeEvidence'] or value[other] is not None:
        raise ValueError('historical lift evidence is inconsistent')
    if type(value['checkId']) is not str or not value['checkId'].startswith('sha256:'):
        raise ValueError('historical lift check identity is missing')


def _saved_binding(binding, request, plan):
    lift = request['lift']
    expected = {'planId': plan['planId'], 'goal': request['baseGoal'],
                'witness': request['originalFinding']['witness'],
                'interpretation': lift['interpretation'], 'mode': lift['mode'],
                'termDigest': 'sha256:' + hashlib.sha256(lift['term'].encode()).hexdigest(),
                'source': lift['interpretation']['source'],
                'sourceDigest': 'sha256:' + lift['interpretation']['source']['sha256']}
    closed(binding, set(expected) | {'attemptId', 'checkerIdentity', 'root'}, 'historical lift binding')
    if any(binding[key] != val for key, val in expected.items()):
        raise ValueError('historical lift binding changed')
    for key in ('attemptId', 'checkerIdentity', 'root'):
        if type(binding[key]) is not str or not binding[key]:
            raise ValueError('historical lift execution identity is malformed')
