"""Verify a child acceptance receipt against a separately selected test inventory.

This checks local evidence bytes and recorded coverage, not producer authenticity
or public release authority. Integration still requires both child receipts.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shlex
import stat
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

MAX_EVIDENCE_FILES = 10_000
MAX_EVIDENCE_BYTES = 64 * 1024 * 1024
MAX_BUNDLE_BYTES = 512 * 1024 * 1024


def content_digest(data: bytes) -> str:
    """Name exact bytes without interpreting their contents."""
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def canonical_digest(value: Any) -> str:
    """Use the receipt's compact sorted JSON identity encoding."""
    return content_digest(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def validate_child_bundle(
    receipt: Mapping[str, Any], *, bundle_root: Path, inventory: Mapping[str, Any],
) -> None:
    """Reject incomplete coverage, mismatched identities or unavailable evidence."""
    try:
        _validate_inventory(inventory)
        evidence = _read_evidence(receipt['evidenceFiles'], bundle_root)
        _validate_receipt(receipt, inventory, evidence)
        wheel_members = _wheel_members(evidence[receipt['wheelDigest']])
        _validate_source_wheel(receipt, evidence, wheel_members)
        results = [_json_object(evidence[ref]) for ref in receipt['resultArtifactRefs']]
        _validate_results(receipt, inventory, results, evidence, wheel_members)
        _validate_source_checks(receipt, inventory, evidence)
    except (KeyError, TypeError, AttributeError, OSError, RecursionError,
            zipfile.BadZipFile, UnicodeError, SyntaxError) as error:
        raise ValueError('invalid or unavailable child acceptance evidence') from error


def _validate_inventory(inventory: Mapping[str, Any]) -> None:
    if inventory.get('schema') != 'ladon-child-acceptance-inventory-v1':
        raise ValueError('unsupported child acceptance inventory')
    if inventory.get('requiredRuntimes') != ['py311', 'py312']:
        raise ValueError('acceptance inventory must require both supported runtimes')
    suites = inventory.get('suites')
    if not isinstance(suites, list) or not suites:
        raise ValueError('acceptance inventory has no suites')
    identities = [row['suiteId'] for row in suites]
    if len(set(identities)) != len(identities):
        raise ValueError('acceptance inventory has duplicate suites')
    for row in suites:
        _validate_targets(row['testTargets'])


def _validate_targets(targets) -> None:
    if not isinstance(targets, list) or not targets or len(set(targets)) != len(targets):
        raise ValueError('acceptance inventory has invalid test targets')


def _read_evidence(rows: Any, root: Path) -> dict[str, bytes]:
    if not isinstance(rows, list) or not 0 < len(rows) <= MAX_EVIDENCE_FILES:
        raise ValueError('child bundle evidence population is invalid')
    result: dict[str, bytes] = {}
    total = 0
    for row in rows:
        digest, path = _evidence_path(row, root, result)
        data = _bounded_file(path)
        total += len(data)
        if len(data) > MAX_EVIDENCE_BYTES or total > MAX_BUNDLE_BYTES:
            raise ValueError('child bundle evidence exceeds byte bounds')
        if content_digest(data) != digest:
            raise ValueError('child bundle evidence bytes do not match their digest')
        result[digest] = data
    return result


def _evidence_path(row, root, seen) -> tuple[str, Path]:
    digest, relative = row['digest'], row['path']
    if not isinstance(digest, str) or re.fullmatch(r'sha256:[0-9a-f]{64}', digest) is None:
        raise ValueError('child bundle evidence digest is invalid')
    if digest in seen or relative != 'objects/' + digest[7:]:
        raise ValueError('child bundle evidence path or identity is ambiguous')
    path = root / relative
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('child bundle evidence must be contained regular files')
    return digest, path


def _bounded_file(path: Path) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('child bundle evidence must be regular files')
        return stream.read(MAX_EVIDENCE_BYTES + 1)


def _validate_receipt(receipt: Mapping, inventory: Mapping, evidence: Mapping) -> None:
    body = dict(receipt)
    identity = body.pop('receiptIdentity', None)
    if identity != canonical_digest(body):
        raise ValueError('child receipt identity is invalid')
    if receipt.get('schema') != 'ladon-child-exit-receipt-v1' or receipt.get('status') != 'passed':
        raise ValueError('child receipt has no passing exit')
    if receipt.get('exitClass') != inventory['exitClass']:
        raise ValueError('child receipt has the wrong exit class')
    if receipt.get('analysisCompleteness') != 'complete' or receipt.get('omissions') != []:
        raise ValueError('child receipt is partial')
    _validate_provenance(receipt, inventory, evidence)


def _validate_provenance(receipt, inventory, evidence) -> None:
    recorded = _json_object(evidence[receipt['inventoryArtifactRef']])
    if recorded != inventory:
        raise ValueError('child receipt inventory differs from the selected inventory')
    candidate = _json_object(evidence[receipt['candidateArtifactRef']])
    if canonical_digest(candidate) != receipt['candidateIdentity']:
        raise ValueError('child receipt candidate identity is invalid')
    for field in ('sourceTreeIdentity', 'wheelDigest'):
        if candidate[field] != receipt[field]:
            raise ValueError('child receipt candidate scope differs')
    if content_digest(evidence[receipt['sourceTreeIdentity']]) != receipt['sourceTreeIdentity']:
        raise ValueError('child source manifest is unavailable')
    if receipt['producerIdentity'] not in evidence or receipt['environmentRef'] not in evidence:
        raise ValueError('child receipt provenance is unavailable')


def _json_object(data: bytes) -> dict:
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('duplicate evidence JSON key')
            value[key] = item
        return value
    value = json.loads(data, object_pairs_hook=unique, parse_constant=_invalid_constant)
    if not isinstance(value, dict):
        raise TypeError('child evidence must be a JSON object')
    return value


def _invalid_constant(value: str) -> None:
    raise ValueError('nonfinite evidence JSON constant: ' + value)


def _validate_source_wheel(receipt, evidence, members) -> None:
    manifest = _json_object(evidence[receipt['sourceTreeIdentity']])
    expected = {path.removeprefix('src/'): digest
                for path, digest in manifest['files'].items() if path.startswith('src/ladon/')}
    files = {path: digest for path, digest in members.items() if not path.endswith('/')}
    if expected != files:
        raise ValueError('selected source manifest differs from wheel package bytes')


def _wheel_members(data: bytes) -> dict[str, str]:
    with zipfile.ZipFile(io.BytesIO(data)) as wheel:
        members = [info for info in wheel.infolist() if info.filename.startswith('ladon/')]
        if not members or len(members) > MAX_EVIDENCE_FILES:
            raise ValueError('child wheel has invalid package members')
        if sum(info.file_size for info in members) > MAX_BUNDLE_BYTES:
            raise ValueError('child wheel exceeds expanded byte bounds')
        if len({info.filename for info in members}) != len(members):
            raise ValueError('child wheel has duplicate package members')
        return {info.filename: content_digest(wheel.read(info)) for info in members}


def _validate_results(receipt, inventory, results, evidence, wheel_members) -> None:
    required = {(suite['suiteId'], runtime): suite['testTargets']
                for suite in inventory['suites'] for runtime in inventory['requiredRuntimes']}
    observed = set()
    logs = []
    commands = []
    for ref, result in zip(receipt['resultArtifactRefs'], results, strict=True):
        key = (result['suiteId'], result['runtime'])
        if key in observed or key not in required:
            raise ValueError('child result matrix has duplicate or unexpected entries')
        observed.add(key)
        _validate_result_scope(result, receipt, inventory, wheel_members)
        _validate_environment_profile(result, receipt, inventory, evidence)
        _validate_test_population(result, required[key])
        log = result['logArtifactRef']
        if log not in evidence:
            raise ValueError('child result log is unavailable')
        logs.append(log)
        commands.append({'command': result['command'], 'status': 'passed',
                         'evidenceDigest': ref})
    if observed != set(required):
        raise ValueError('child result matrix is incomplete')
    if receipt['logArtifactRefs'] != logs or receipt['commands'] != commands:
        raise ValueError('child command or log references differ from recorded results')


def _validate_environment_profile(result, receipt, inventory, evidence) -> None:
    profile = _json_object(evidence[receipt['environmentRef']])
    if profile.get('schema') != 'ladon-acceptance-environment-v1':
        raise ValueError('child environment profile has an unsupported schema')
    executable = Path(profile['runtimes'][result['runtime']]['python'])
    if str(executable) != result['pythonExecutable'] or str(executable.parent.parent) != (
        result['environmentPrefix']
    ):
        raise ValueError('child result interpreter differs from selected environment profile')
    platform = inventory.get('requiredPlatform')
    if platform and (profile['posture'] != platform['executionPosture'] or
                     profile['procAvailable'] is not True):
        raise ValueError('required child platform posture is unavailable')
    if platform and platform.get('networkDisabled') is True:
        from ladon.acceptance_network import validate_network_isolation

        validate_network_isolation(result.get('networkIsolation'), profile.get('hostNetworkNamespace'))


def _validate_result_scope(result, receipt, inventory, wheel_members) -> None:
    for field in ('candidateIdentity', 'sourceTreeIdentity', 'wheelDigest', 'workingDirectory',
                  'producerIdentity', 'environmentRef'):
        if result[field] != receipt[field]:
            raise ValueError('child result execution scope differs from receipt')
    if result['installedPackageMembers'] != wheel_members:
        raise ValueError('installed package members differ from selected wheel')
    if result['environmentRequirements'] != inventory['requiredEnvironment']:
        raise ValueError('required child execution environment was not established')
    _validate_python_posture(result)
    _validate_invocation(result, receipt, inventory)


def _validate_python_posture(result) -> None:
    if result['isolatedPython'] is not True or result['pythonVersion'][:2] != (
        [3, 11] if result['runtime'] == 'py311' else [3, 12]
    ):
        raise ValueError('child result has the wrong Python execution posture')
    origin, prefix = Path(result['importOrigin']), Path(result['environmentPrefix'])
    if not origin.is_absolute() or not origin.is_relative_to(prefix):
        raise ValueError('child result import origin is outside its installation')
    if origin.is_relative_to(Path(result['workingDirectory'])):
        raise ValueError('child result imported from the candidate checkout')
    command = result['commandVector']
    if not isinstance(command, list) or len(command) < 3 or command[:2] != [result['pythonExecutable'], '-I']:
        raise ValueError('child result has no isolated invocation')


def _validate_invocation(result, receipt, inventory) -> None:
    root = Path(receipt['workingDirectory'])
    runner = inventory['runnerPath']
    command = result['commandVector']
    if command[2] != str(root / runner) or result['command'] != shlex.join(command):
        raise ValueError('child suite did not invoke the approved acceptance producer')
    flags = command[3::2]
    values = command[4::2]
    names = {'--inventory', '--context', '--wheel', '--runtime', '--output'}
    if len(flags) != len(values) or len(flags) != len(names) or set(flags) != names:
        raise ValueError('child suite invocation contains selection overrides')
    arguments = dict(zip(flags, values, strict=True))
    if arguments['--runtime'] != result['runtime'] or arguments['--inventory'] != str(
        root / inventory['inventoryPath']
    ):
        raise ValueError('child suite invocation differs from selected inventory')
    expected = ['-q', '-o', 'addopts=', '--rootdir', str(root), *result['testTargets']]
    if result['pytestArgv'] != expected or result['pytestEnvironment'] != {
        'PYTEST_ADDOPTS': None, 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
    }:
        raise ValueError('child suite has unapproved pytest selection or plugins')


def _validate_test_population(result: Mapping, targets: list[str]) -> None:
    if result['testTargets'] != targets or type(result['exitCode']) is not int or result['exitCode'] != 0:
        raise ValueError('child suite selection or exit differs from inventory')
    collected, passed = result['collected'], result['passed']
    if not collected or len(set(collected)) != len(collected) or sorted(collected) != sorted(passed):
        raise ValueError('child suite has incomplete or duplicate outcomes')
    if result['initialCollection'] != collected:
        raise ValueError('child suite deselected tests from its initial collection')
    if any(result[field] for field in ('failed', 'skipped', 'collectionErrors')):
        raise ValueError('child suite has failures, skips or collection errors')
    _validate_population_selection(collected, targets)


def _validate_population_selection(collected, targets) -> None:
    if any(not any(_selected(node, target) for target in targets) for node in collected):
        raise ValueError('child suite collected unselected tests')
    if any(not any(_selected(node, target) for node in collected) for target in targets):
        raise ValueError('child suite did not collect every selected target')


def _selected(node: str, target: str) -> bool:
    return node == target or node.startswith((target + '::', target + '['))


def _validate_source_checks(receipt: Mapping, inventory: Mapping, evidence: Mapping) -> None:
    required = inventory.get('requiredSourceChecks', [])
    checks = _json_object(evidence[receipt['sourceChecksArtifactRef']])
    if checks.get('requirements') != required or checks.get('status') != 'passed':
        raise ValueError('child source checks are incomplete')
    manifest = _json_object(evidence[receipt['sourceTreeIdentity']])
    required_files = {path for check in required for path in check['files']}
    if set(checks['sourceFileRefs']) != required_files:
        raise ValueError('child source checks did not cover every required owner')
    _validate_source_inputs(checks, manifest, evidence, receipt, inventory)
    from ladon._child_acceptance_sources import validate_source_checks

    validate_source_checks(checks, inventory, evidence, receipt)


def _validate_source_inputs(checks, manifest, evidence, receipt, inventory) -> None:
    for path, ref in checks['sourceFileRefs'].items():
        if manifest['files'].get(path) != ref or ref not in evidence:
            raise ValueError('child source check inputs differ from candidate')
    runner = inventory['runnerPath']
    if manifest['files'].get(runner) != receipt['producerIdentity']:
        raise ValueError('child producer differs from selected source manifest')
    if manifest['files'].get(inventory['inventoryPath']) != receipt['inventoryArtifactRef']:
        raise ValueError('child inventory differs from selected source manifest')
