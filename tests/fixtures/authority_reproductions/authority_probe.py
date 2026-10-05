"""Retrospectively observe two authority defects through an installed public API."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

import ladon
from ladon.lean_toolchain import LeanToolchainError, resolve_toolchain_context
from ladon.proofir_result_dimensions import project_dimensions


def _save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def _preflight(directory: Path) -> dict:
    root = directory / 'repository'
    root.mkdir()
    (root / 'lean-toolchain').write_text('leanprover/lean4:v4.20.0\n')
    for name in ('lake', 'lean'):
        executable = root / name
        executable.write_text(
            '#!/bin/sh\nif [ "$LADON_SYNTHETIC_VERSION_SWITCH" = enabled ]; then\n'
            "  printf 'Lean version 4.20.0\\n'\nelse\n"
            "  printf 'Lean version 0.0.0\\n'\nfi\n"
        )
        executable.chmod(0o755)
    supplied = {'PATH': str(root), 'HOME': str(root), 'LADON_SYNTHETIC_VERSION_SWITCH': 'enabled'}
    try:
        context = resolve_toolchain_context(root, lake_path=root / 'lake', lean_path=root / 'lean',
                                            environment=supplied, selection_mode='explicit')
    except LeanToolchainError as error:
        if 'pin mismatch' not in str(error):
            raise
        return {'family': 'preflight-environment', 'classification': 'repaired',
                'preflight': 'rejected', 'diagnostic': str(error), 'workerLaunched': False}
    worker = subprocess.run([str(context.lean_path), '--version'], cwd=root,
                            env=dict(context.environment), capture_output=True, text=True,
                            timeout=10, check=True)
    (directory / 'worker.stdout').write_text(worker.stdout)
    (directory / 'worker.stderr').write_text(worker.stderr)
    _save(directory / 'captured-context.json', context.to_dict())
    assert 'LADON_SYNTHETIC_VERSION_SWITCH' not in context.environment
    return {'family': 'preflight-environment', 'classification':
            'defect-observed' if '0.0.0' in worker.stdout else 'unexpected',
            'preflight': 'accepted', 'workerVersion': worker.stdout.strip(),
            'expectedPin': '4.20.0', 'workerLaunched': True,
            'scope': 'Selected executable version observed under the returned worker environment; no Lean proof check.'}


def _promotion() -> dict:
    rows = []
    for parent in ('ambient-selected-application-check', 'not-assessed'):
        try:
            observed = project_dimensions('explicit-pinned-application-check', 'partial',
                                          parent_authority=parent, parent_completeness='partial')
        except ValueError as error:
            if 'authority' not in str(error):
                raise
            rows.append({'parent': parent, 'classification': 'repaired', 'diagnostic': str(error)})
        else:
            rows.append({'parent': parent, 'classification': 'defect-observed' if observed ==
                         ('explicit-pinned-application-check', 'partial') else 'unexpected',
                         'observed': list(observed)})
    classifications = {row['classification'] for row in rows}
    return {'family': 'ambient-or-absent-promotion', 'cases': rows,
            'classification': next(iter(classifications)) if len(classifications) == 1 else 'unexpected'}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--expect', choices=('historical', 'current'), required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = {'schema': 'ladon-retrospective-authority-probe-v1', 'retrospective': True,
              'expectation': args.expect, 'python': sys.version, 'executable': sys.executable,
              'installedVersion': importlib.metadata.version('ladon'),
              'packagePath': str(Path(ladon.__file__).resolve()),
              'probeDigest': 'sha256:' + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    try:
        report['results'] = [_preflight(args.output_dir), _promotion()]
        expected = 'defect-observed' if args.expect == 'historical' else 'repaired'
        report['status'] = 'matched' if all(row['classification'] == expected
                                           for row in report['results']) else 'unexpected'
        code = 0 if report['status'] == 'matched' else 1
    except Exception as error:
        report.update(status='setup-failed', errorType=type(error).__name__, error=str(error))
        code = 2
    _save(args.output_dir / 'result.json', report)
    print(json.dumps({'status': report['status'], 'expectation': args.expect,
                      'result': str(args.output_dir / 'result.json')}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
