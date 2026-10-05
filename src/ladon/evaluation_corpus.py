"""Validate frozen evaluation subjects before running any discovery method.

Portable fixtures remain independent of optional external checkouts. A changed
ranking input or target source invalidates the registered study; unavailable
external toolchains are observations rather than portable contract failures.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ladon.verified_discovery import DiscoveryRequest


def digest_bytes(data: bytes) -> str:
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def validate_evaluation_plan(plan: dict, ladon_root: Path) -> None:
    """Reject changed registration, reused development goals or unsupported bounds."""
    unsigned = {key: value for key, value in plan.items() if key != 'preregistrationIdentity'}
    identity = digest_bytes(json.dumps(unsigned, sort_keys=True, separators=(',', ':')).encode())
    if identity != plan['preregistrationIdentity'] or plan['schema'] != 'ladon-discovery-evaluation-preregistration-v1':
        raise ValueError('evaluation registration identity or schema changed')
    for path, expected in plan['rankingInputs'].items():
        if digest_bytes(_contained_file(ladon_root, path).read_bytes()) != expected:
            raise ValueError('ranking input changed after registration: ' + path)
    _validate_population(plan, ladon_root)
    for repository in plan['repositories']:
        if not repository['optional']:
            verify_repository_snapshot(repository, ladon_root)


def _validate_population(plan, ladon_root) -> None:
    repositories = _unique_rows(plan['repositories'], 'repository')
    cases = plan['cases']
    _unique_rows(cases, 'case')
    bounds = plan['policy']['bounds']
    if not 0 < bounds['maxRssBytes'] <= 32 * 1024 ** 3:
        raise ValueError('evaluation memory exceeds the registered supported ceiling')
    for case in cases:
        repository = repositories[case['repository']]
        _validate_case(case, repository, bounds, repository_root(repository, ladon_root))
    held_out = {case['repository'] for case in cases if case['split'] == 'held-out'}
    if len(held_out) < plan['policy']['promotion']['minAvailableHeldOutRepositoryFamilies']:
        raise ValueError('registration lacks multiple held-out repository families')


def _unique_rows(rows, label):
    indexed = {row['id']: row for row in rows}
    if not rows or len(indexed) != len(rows):
        raise ValueError('evaluation ' + label + ' population is missing or duplicate')
    return indexed


def _validate_case(case, repository, bounds, root) -> None:
    if case['split'] != repository['split']:
        raise ValueError('case split differs from repository registration')
    if case['split'] == 'held-out' and not repository['optional']:
        raise ValueError('synthetic portable fixtures cannot supply external promotion')
    if not case['expectedAcceptableCandidates'] or not case['labelRationale']:
        raise ValueError('evaluation case lacks labels or rationale')
    if not set(case['expectedAcceptableCandidates']) <= set(case['candidatePool']):
        raise ValueError('expected labels are outside the registered comparator pool')
    DiscoveryRequest(repo_root=root, module=case['module'], goal=case['goal'], scope=case['scope'],
                     roots=tuple(case['roots']), local_context=tuple(case['localContext']),
                     max_candidates=bounds['maxCandidates'], batch_size=bounds['batchSize'],
                     timeout_seconds=bounds['timeoutSeconds'], max_rss_bytes=bounds['maxRssBytes'],
                     max_output_bytes=bounds['maxOutputBytes'])


def repository_root(repository: dict, ladon_root: Path) -> Path:
    root = Path(repository['root'])
    if repository['pathBase'] == 'ladon-repository':
        return (ladon_root / root).resolve()
    if not root.is_absolute():
        raise ValueError('optional repository root must be an explicit absolute path')
    return root.resolve()


def verify_repository_snapshot(repository: dict, ladon_root: Path) -> Path:
    """Require selected source/pin/build metadata bytes before optional execution."""
    root = repository_root(repository, ladon_root)
    for name, expected in repository['files'].items():
        if digest_bytes(_contained_file(root, name).read_bytes()) != expected:
            raise ValueError('registered repository source drift: ' + name)
    if (root / 'lean-toolchain').read_text().strip() != repository['toolchain']:
        raise ValueError('registered repository toolchain drift')
    return root


def _contained_file(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('registered source path must be relative and contained')
    selected = root / path
    if selected.is_symlink() or not selected.resolve().is_relative_to(root.resolve()):
        raise ValueError('registered source path is not a contained regular file')
    return selected
