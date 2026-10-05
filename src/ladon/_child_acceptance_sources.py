"""Check the bounded derivation owners and their recorded quality executions.

Source assertions are re-evaluated from artifact bytes. Tool outcomes are bound
producer records; this checker does not authenticate the process that made them.
"""
from __future__ import annotations

import ast
import json
from collections.abc import Mapping
from typing import Any


def validate_source_checks(checks, inventory, evidence, receipt) -> None:
    sources = {path: evidence[ref].decode('utf-8')
               for path, ref in checks['sourceFileRefs'].items()}
    for requirement in inventory.get('requiredSourceChecks', []):
        selected = {path: sources[path] for path in requirement['files']}
        identity = requirement['checkId']
        if identity == 'single-iterative-slice-owner':
            _validate_iterative_owner(selected)
        elif identity == 'derivation-owner-quality':
            _validate_quality(selected, checks, inventory, evidence, receipt)
        else:
            raise ValueError('unsupported child source check: ' + identity)


def _validate_iterative_owner(sources: Mapping[str, str]) -> None:
    trees = {path: ast.parse(source) for path, source in sources.items()}
    slicers = [(path, node) for path, tree in trees.items() for node in ast.walk(tree)
               if isinstance(node, ast.ClassDef) and node.name == '_Slicer']
    owner = 'src/ladon/_proofir_derivation_slice.py'
    if len(slicers) != 1 or slicers[0][0] != owner:
        raise ValueError('child source has no single owned iterative slicer')
    _validate_dispatch(slicers[0][1])
    for tree in trees.values():
        for node in ast.walk(tree):
            _reject_legacy_node(node)


def _validate_dispatch(slicer: ast.ClassDef) -> None:
    methods = {node.name: node for node in slicer.body if isinstance(node, ast.FunctionDef)}
    if 'run' not in methods or '_expand_iterative' not in methods:
        raise ValueError('child slicer has no iterative entry point')
    calls = [node.func for node in ast.walk(methods['run']) if isinstance(node, ast.Call)]
    if not any(_iterative_call(call) for call in calls):
        raise ValueError('child slicer run does not dispatch to its iterative owner')


def _iterative_call(call: ast.expr) -> bool:
    return (isinstance(call, ast.Attribute) and call.attr == '_expand_iterative'
            and isinstance(call.value, ast.Name) and call.value.id == 'self')


def _reject_legacy_node(node: ast.AST) -> None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {
        'expand', '_expand_step',
    }:
        raise ValueError('child source retains a legacy recursive traversal')
    if isinstance(node, ast.Attribute) and node.attr == 'setrecursionlimit':
        raise ValueError('child source changes the recursion limit')
    if isinstance(node, ast.Name) and node.id == 'setrecursionlimit':
        raise ValueError('child source changes the recursion limit')
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        _reject_quux(node)


def _reject_quux(node: ast.Import | ast.ImportFrom) -> None:
    names = [alias.name for alias in node.names]
    names.append(getattr(node, 'module', '') or '')
    if any(name.lower().split('.')[0] == 'quux' for name in names):
        raise ValueError('child source imports Quux')


def _validate_quality(sources, checks, inventory, evidence, receipt) -> None:
    if any('reviewed-schema-hotspot' in source for source in sources.values()):
        raise ValueError('child derivation quality is suppressed')
    commands = checks['qualityCommands']
    expected = inventory['sourceQualityArgvTails']
    if len(commands) != len(expected):
        raise ValueError('child derivation quality commands are incomplete')
    for command, tail in zip(commands, expected, strict=True):
        _validate_quality_command(command, tail, evidence, receipt)


def _validate_quality_command(command: Mapping[str, Any], tail, evidence, receipt) -> None:
    profile = json.loads(evidence[receipt['environmentRef']])
    interpreters = {row['python'] for row in profile['runtimes'].values()}
    if command['argv'][0] not in interpreters:
        raise ValueError('child quality interpreter differs from selected environment profile')
    if command['argv'][1:] != tail or command['workingDirectory'] != receipt['workingDirectory']:
        raise ValueError('child derivation quality command differs from inventory')
    if type(command['exitCode']) is not int or command['exitCode'] != 0:
        raise ValueError('child derivation quality command failed')
    if command['status'] != 'passed' or command['logArtifactRef'] not in evidence:
        raise ValueError('child derivation quality output is unavailable')
