"""Request-size and expression-node stops are distinct bounded failures."""

import json

from test_real_prose_exact_goal import DECLARATIONS, goal, request, run, source
from test_real_prose_exact_goal import project as _project

project = _project


def test_oversized_request_stops_before_parsing_owners(project):
    encoded = json.dumps(request(), sort_keys=True, separators=(',', ':'))
    encoded += ' ' * (8 * 1024**2)
    text = source(request()).replace(goal(request()), 'ladon_prose_exact_goal% ' + json.dumps(encoded))
    (project / 'Case.lean').write_text(text)
    result = run(project, 'Case.lean')
    assert not result.succeeded
    assert 'exact goal request exceeds 8 MiB' in result.stdout + result.stderr


def test_large_balanced_expression_stops_at_node_limit(project):
    value = request()
    declarations = list(DECLARATIONS)
    expression = 'True'
    for _ in range(15):
        expression = f'({expression} ∧ {expression})'
    declarations[1] = 'def Reading : Prop := ' + expression
    text = source(value).replace('\n'.join(DECLARATIONS), '\n'.join(declarations))
    # Permit elaboration of the finite source without changing Ladon's resource caps.
    text = text.replace('import LadonProseExactGoal\n',
                        'import LadonProseExactGoal\nset_option maxHeartbeats 0\n')
    for row in [value['formal'], value['authored'], *value['premises']]:
        for key in row['range']:
            if key.endswith('Line'):
                row['range'][key] += 1
    value['authored']['range']['endColumn'] = len(declarations[1])
    prefix = text.split('example :', 1)[0]
    text = prefix + 'example :' + source(value).split('example :', 1)[1]
    (project / 'Case.lean').write_text(text)
    result = run(project, 'Case.lean')
    assert not result.succeeded
    assert 'expression node count exceeds 100000' in result.stdout + result.stderr


def _arrow_case(depth):
    value = request()
    declarations = list(DECLARATIONS)
    declarations[1] = 'def Reading : Prop := ' + 'True → ' * depth + 'True'
    value['authored']['range']['endColumn'] = len(declarations[1])
    expression = {'const': 'True', 'levels': []}
    for _ in range(depth):
        expression = {'forallE': {'name': '_', 'type': {'const': 'True', 'levels': []},
                                 'body': expression, 'binderInfo': 'explicit'}}
    value['authored']['expression'] = expression
    value['premises'] = []
    text = 'import LadonProseExactGoal\n' + '\n'.join(declarations) + '\n'
    text += f'example : {goal(value)} := by\n  intros\n  exact True.intro\n'
    return text


def test_exact_total_depth_ceiling_is_accepted(project):
    (project / 'Case.lean').write_text(_arrow_case(127))
    result = run(project, 'Case.lean')
    assert result.succeeded, result.stdout + result.stderr


def test_formal_wrapper_counts_toward_the_total_depth_ceiling(project):
    (project / 'Case.lean').write_text(_arrow_case(128))
    result = run(project, 'Case.lean')
    assert not result.succeeded
    assert 'expression depth exceeds 128' in result.stdout + result.stderr
