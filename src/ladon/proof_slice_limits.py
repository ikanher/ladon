"""Shared node-budget contract for proof-slice extraction and replay."""

DEFAULT_MAX_NODES = 131_072
MAX_NODE_BUDGET = 1_048_576


def validate_max_nodes(value):
    if type(value) is not int or not 1 <= value <= MAX_NODE_BUDGET:
        raise ValueError(f"node budget must be an integer from 1 to {MAX_NODE_BUDGET}")
    return value


DEFAULT_MAX_DEPTH = 128
MAX_DEPTH_BUDGET = 4096


def validate_max_depth(value):
    if type(value) is not int or not 1 <= value <= MAX_DEPTH_BUDGET:
        raise ValueError(f"depth budget must be an integer from 1 to {MAX_DEPTH_BUDGET}")
    return value
