"""Shared node-budget contract for proof-slice extraction and replay."""

from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES

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


def validate_resource_limits(seconds, rss_bytes):
    if type(seconds) is not int or seconds <= 0:
        raise ValueError("slice resource timeout must be a positive integer in seconds")
    if type(rss_bytes) is not int or rss_bytes <= 0:
        raise ValueError("slice resource RSS allowance must be a positive integer in bytes")


def replay_resource_limits(value):
    limits = value["limits"]
    seconds, rss = limits["secondsPerProcess"], limits["rssBytes"]
    validate_resource_limits(seconds, rss)
    return {"timeout_seconds": seconds, "max_rss_bytes": rss}


def authorize_slice_replay(value, seconds=60, rss_bytes=DEFAULT_MAX_RSS_BYTES):
    validate_resource_limits(seconds, rss_bytes)
    requested = replay_resource_limits(value)
    if requested["timeout_seconds"] > seconds or requested["max_rss_bytes"] > rss_bytes:
        raise ValueError("saved bounds require an explicit slice replay allowance: --slice-timeout-seconds / --slice-max-rss-mib")
    return requested
