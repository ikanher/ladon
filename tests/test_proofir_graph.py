from __future__ import annotations

from itertools import permutations

from ladon.bounded_graph import (
    cyclic_components,
    strongly_connected_components_from_adjacency,
)


def test_sccs_are_deterministic_across_input_orders() -> None:
    edges = (("A", "B"), ("B", "A"), ("B", "C"), ("C", "D"), ("D", "C"))
    observed = set()
    for ordering in permutations(edges):
        adjacency: dict[str, list[str]] = {}
        for source, target in ordering:
            adjacency.setdefault(source, []).append(target)
        observed.add(str(cyclic_components(adjacency)))
    assert observed == {"(('A', 'B'), ('C', 'D'))"}


def test_iterative_scc_handles_graphs_beyond_python_recursion_limit() -> None:
    adjacency = {index: [index + 1] for index in range(2_000)}
    assert len(strongly_connected_components_from_adjacency(adjacency)) == 2_001
    assert cyclic_components(adjacency) == ()
