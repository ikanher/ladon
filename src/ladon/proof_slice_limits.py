"""Shared node-budget contract for proof-slice extraction and replay."""

DEFAULT_MAX_NODES = 131_072
MAX_NODE_BUDGET = 1_048_576


def validate_max_nodes(value):
    if type(value) is not int or not 1 <= value <= MAX_NODE_BUDGET:
        raise ValueError(f"node budget must be an integer from 1 to {MAX_NODE_BUDGET}")
    return value
