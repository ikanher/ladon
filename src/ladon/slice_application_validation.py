"""Compare exact observed DAG subexpressions without interpreting Lean types."""

import hashlib
import json

from ladon._expr_graph_protocol import _LAYOUTS, PREFIX


def _graph(text):
    if not text.startswith(PREFIX):
        raise ValueError("actual applications require structural expression DAGs")
    graph = json.loads(text[len(PREFIX):])
    fingerprints = []
    for node in graph["nodes"]:
        fields = [fingerprints[value] if kind == "r" else value
                  for kind, value in zip(_LAYOUTS[node[0]], node[1:], strict=True)]
        encoded = json.dumps([node[0], *fields], ensure_ascii=False, separators=(",", ":")).encode()
        fingerprints.append(hashlib.sha256(encoded).hexdigest())
    return graph, fingerprints


def validate_application_arguments(application, head):
    graph, fingerprints = _graph(application["application"]["structural"])
    nodes, cursor, arguments = graph["nodes"], graph["root"], []
    while nodes[cursor][0] == "app":
        arguments.append(fingerprints[nodes[cursor][2]])
        cursor = nodes[cursor][1]
    root = nodes[cursor]
    if root[0] != "const" or root[1] != "`" + head:
        raise ValueError("slice projections disagree with their bound application observation: head")
    observed = []
    for row in application["arguments"]:
        argument_graph, argument_fingerprints = _graph(row["expression"]["structural"])
        observed.append(argument_fingerprints[argument_graph["root"]])
    if observed != list(reversed(arguments)):
        raise ValueError("slice projections disagree with their bound application observation: arguments")
