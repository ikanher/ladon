"""Finite JSON DAG construction, preflight and streaming canonical expansion."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=True, allow_nan=False).encode('ascii')
    except (ValueError, TypeError, RecursionError, OverflowError) as error:
        raise ValueError('transport requires canonical finite JSON') from error


def string_token(value, limits):
    if type(value) is not str:
        raise ValueError('transport keys and strings must be strings')
    try:
        size = len(value.encode('utf-8'))
    except UnicodeError as error:
        raise ValueError('transport strings must be valid UTF-8') from error
    if size > limits.max_string_bytes:
        raise ValueError('transport string exceeds UTF-8 byte limit')
    return canonical(value)


def scalar_token(value, limits):
    if type(value) is str:
        return string_token(value, limits)
    if value is None or type(value) in (bool, int):
        return canonical(value)
    if type(value) is float and math.isfinite(value):
        return canonical(value)
    raise ValueError('transport scalar is nonfinite or not JSON')


@dataclass(frozen=True)
class Footprint:
    size: int
    depth: int
    occurrences: int


def check_footprint(result, limits):
    if (result.size > limits.max_expanded_bytes or result.depth > limits.max_depth
            or result.occurrences > limits.max_expanded_nodes):
        raise ValueError('transport expanded byte/depth/occurrence limit exceeded')
    return result


def children(row):
    if row[0] == 'object':
        return row[2]
    return row[1] if row[0] == 'array' else []


def footprint(row, prior, limits):
    if row[0] == 'scalar':
        return check_footprint(Footprint(len(scalar_token(row[1], limits)), 0, 1), limits)
    refs = children(row)
    size = 2 + max(0, len(refs)-1) + sum(prior[ref].size for ref in refs)
    if row[0] == 'object':
        size += sum(len(string_token(key, limits))+1 for key in row[1])
    depth = max((prior[ref].depth+1 for ref in refs), default=0)
    occurrences = 1 + sum(prior[ref].occurrences for ref in refs)
    return check_footprint(Footprint(size, depth, occurrences), limits)


def _container(value, limits):
    if len(value) > limits.max_edges:
        raise ValueError('transport container exceeds edge limit')
    if type(value) is list:
        return None, value
    for key in value:
        string_token(key, limits)
    keys = sorted(value)
    return keys, [value[key] for key in keys]


class _Builder:
    def __init__(self, limits):
        self.limits = limits
        self.nodes, self.metrics = [], []
        self.signatures, self.memo, self.active = {}, {}, set()
        self.edges = 0

    def intern(self, row):
        metric = footprint(row, self.metrics, self.limits)
        signature = canonical(row)
        if signature in self.signatures:
            return self.signatures[signature]
        edges = self.edges + len(children(row))
        if len(self.nodes) >= self.limits.max_nodes or edges > self.limits.max_edges:
            raise ValueError('transport DAG node/edge limit exceeded')
        index = len(self.nodes)
        self.nodes.append(row)
        self.metrics.append(metric)
        self.signatures[signature] = index
        self.edges = edges
        return index

    def enter(self, value, depth, stack, results):
        if depth > self.limits.max_depth:
            raise ValueError('transport input exceeds depth limit')
        if type(value) not in (dict, list):
            results.append(self.intern(['scalar', value]))
            return
        identity = id(value)
        if identity in self.active:
            raise ValueError('transport input contains a cycle')
        if identity in self.memo:
            results.append(self.memo[identity])
            return
        keys, values = _container(value, self.limits)
        self.active.add(identity)
        stack.append(('exit', value, keys, len(values)))
        stack.extend(('enter', child, depth+1) for child in reversed(values))

    def exit(self, value, keys, count, results):
        refs = results[-count:] if count else []
        if count:
            del results[-count:]
        row = ['array', refs] if keys is None else ['object', keys, refs]
        index = self.intern(row)
        self.memo[id(value)] = index
        self.active.remove(id(value))
        results.append(index)


def build_graph(value, limits):
    builder = _Builder(limits)
    stack, results = [('enter', value, 0)], []
    while stack:
        action, *args = stack.pop()
        if action == 'enter':
            builder.enter(*args, stack, results)
        else:
            builder.exit(*args, results)
    return builder.nodes, results[0], builder.metrics[-1]


def _references(refs, index):
    if type(refs) is not list:
        raise ValueError('transport references require a list')
    if any(type(ref) is not int or not 0 <= ref < index for ref in refs):
        raise ValueError('transport references must be strictly backward integers')


def _row(row, index, limits):
    if type(row) is not list or not row or type(row[0]) is not str:
        raise ValueError('transport node must be a tagged list')
    kind = row[0]
    arity = {'scalar': 2, 'array': 2, 'object': 3}.get(kind)
    if arity is None or len(row) != arity:
        raise ValueError('transport node has an invalid tag/arity')
    if kind == 'scalar':
        scalar_token(row[1], limits)
        return
    refs = row[2] if kind == 'object' else row[1]
    _references(refs, index)
    if kind == 'object':
        _keys(row[1], refs, limits)


def _keys(keys, refs, limits):
    if type(keys) is not list or len(keys) != len(refs):
        raise ValueError('transport object keys/refs differ')
    for key in keys:
        string_token(key, limits)
    if keys != sorted(set(keys)):
        raise ValueError('transport object keys must be sorted and unique')


def _postorder(nodes, root):
    stack, seen, order = [(root, False)], set(), []
    while stack:
        index, exiting = stack.pop()
        if exiting:
            order.append(index)
        elif index not in seen:
            seen.add(index)
            stack.append((index, True))
            stack.extend((child, False) for child in reversed(children(nodes[index])))
    if order != list(range(len(nodes))):
        raise ValueError('transport nodes are unreachable or not canonical postorder')


def preflight(nodes, root, limits):
    if type(nodes) is not list or not 0 < len(nodes) <= limits.max_nodes:
        raise ValueError('transport DAG node limit/shape invalid')
    if type(root) is not int or root != len(nodes)-1:
        raise ValueError('transport root must be final integer node')
    metrics, signatures, edges = [], set(), 0
    for index, row in enumerate(nodes):
        _row(row, index, limits)
        edges += len(children(row))
        if edges > limits.max_edges:
            raise ValueError('transport DAG edge limit exceeded')
        metrics.append(footprint(row, metrics, limits))
        signature = canonical(row)
        if signature in signatures:
            raise ValueError('transport duplicate DAG node')
        signatures.add(signature)
    if nodes[root][0] != 'object':
        raise ValueError('transport root must be an object')
    _postorder(nodes, root)
    return metrics[root]


def _content_tokens(row):
    refs = children(row)
    parts = []
    for index, ref in enumerate(refs):
        if index:
            parts.append(b',')
        if row[0] == 'object':
            parts.append(canonical(row[1][index])+b':')
        parts.append(ref)
    return parts


def expanded_digest(nodes, root):
    digest = hashlib.sha256()
    stack = [root]
    while stack:
        item = stack.pop()
        if type(item) is bytes:
            digest.update(item)
            continue
        row = nodes[item]
        if row[0] == 'scalar':
            digest.update(canonical(row[1]))
        else:
            opening, closing = (b'{', b'}') if row[0] == 'object' else (b'[', b']')
            digest.update(opening)
            stack.append(closing)
            stack.extend(reversed(_content_tokens(row)))
    return 'sha256:' + digest.hexdigest()


def materialize(nodes, root):
    box = [None]
    stack = [(root, box, 0)]
    while stack:
        index, parent, key = stack.pop()
        row = nodes[index]
        if row[0] == 'scalar':
            parent[key] = row[1]
            continue
        refs = children(row)
        value = {} if row[0] == 'object' else [None]*len(refs)
        parent[key] = value
        keys = row[1] if row[0] == 'object' else range(len(refs))
        stack.extend((ref, value, child_key) for child_key, ref in reversed(list(zip(keys, refs, strict=True))))
    return box[0]
