"""Structural DAG validation keeps all child references and constructor fields."""
from __future__ import annotations

import json

import pytest

from ladon._source_goal_protocol import _validate_goals
from ladon.source_association_io import _AssociationError


def _goal(nodes, root):
    return {'goalId': 'g', 'typeDisplay': 'True', 'localContext': [],
            'typeStructural': 'ladon-expr-dag-v1:' + json.dumps({'root': root, 'nodes': nodes})}


@pytest.mark.parametrize('nodes,root', [
    ([['app', 0, 0]], 0),
    ([['const', 'True', '[]']], 1),
    ([['unknown', 'True']], 0),
    ([['bvar', True]], 0),
    ([['const', 'True', '[]'], ['app', -1, 0]], 1),
])
def test_invalid_expr_graph_cannot_become_goal_evidence(nodes, root):
    with pytest.raises(_AssociationError):
        _validate_goals([_goal(nodes, root)])


def test_valid_shared_graph_and_legacy_opaque_expression_are_accepted():
    _validate_goals([_goal([['const', 'True', '[]'], ['app', 0, 0]], 1)])
    row = _goal([], 0)
    row['typeStructural'] = 'Lean.Expr.const `True []'
    _validate_goals([row])
