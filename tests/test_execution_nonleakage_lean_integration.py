"""Exercise discarded environment inputs through installed commands and real Lean."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest
from support.execution_nonleakage import (
    assert_clean_files,
    assert_no_discarded_input,
    poison_environment,
)

from ladon.proof_search_cli import _render_text
from ladon.semantic_evidence_registry import SemanticEvidenceRegistry
from ladon.semantic_result_delivery import collect_semantic_artifacts, deliver_semantic_result

FIXTURE = Path(__file__).parent / 'fixtures' / 'lean_integration'


@pytest.fixture(scope='module')
def pinned_tools() -> tuple[Path, Path]:
    """Resolve the fixture pin before injecting caller inputs; never download/build."""
    lake = shutil.which('lake')
    if lake is None:
        if os.environ.get('LADON_REQUIRE_EXECUTION_NONLEAKAGE') == '1':
            pytest.fail('required nonleakage gate needs the fixture Lean toolchain')
        pytest.skip('Lean toolchain unavailable')
    elan = shutil.which('elan')
    if elan:
        result = subprocess.run(
            [elan, 'which', 'lean'], cwd=FIXTURE, capture_output=True,
            text=True, timeout=10, check=False,
        )
        assert result.returncode == 0, result.stderr
        lean = Path(result.stdout.strip())
    else:
        lean = Path(lake).resolve().with_name('lean')
    assert lean.is_file() and lean.with_name('lake').is_file()
    assert (FIXTURE / '.lake/build/lib/lean/LadonFixture.olean').is_file(), (
        'build the pinned fixture explicitly before running the required gate'
    )
    return lean.with_name('lake'), lean


def _command() -> list[str]:
    console = os.environ.get('LADON_CONSOLE')
    return [console] if console else [sys.executable, '-I', '-m', 'ladon.entrypoint']


def _run(args: list[str], directory: Path, label: str, *, exit_code: int = 0) -> str:
    completed = subprocess.run(
        [*_command(), *args], cwd=directory, capture_output=True, text=True,
        timeout=90, check=False,
    )
    (directory / f'{label}.stdout').write_text(completed.stdout)
    (directory / f'{label}.stderr').write_text(completed.stderr)
    assert_no_discarded_input(completed.stdout)
    assert_no_discarded_input(completed.stderr)
    assert completed.returncode == exit_code, completed.stderr
    return completed.stdout


def _selection(tools: tuple[Path, Path], mode: str) -> list[str]:
    args = ['--toolchain-mode', mode]
    if mode == 'explicit':
        args += ['--lake-path', str(tools[0]), '--lean-path', str(tools[1])]
    return args


def _project_captured(payload: dict[str, Any], directory: Path) -> dict[str, Any]:
    """Reuse one observed run across all renderers and retain SQLite/WAL bytes."""
    store = directory / 'evidence.sqlite'
    projected = {}
    SemanticEvidenceRegistry(store)
    # Hold the initial snapshot while production delivery writes real evidence to WAL.
    with closing(sqlite3.connect(store)) as reader:
        reader.execute('BEGIN')
        reader.execute('SELECT count(*) FROM artifacts').fetchone()
        for mode in ('audit', 'llm', 'review'):
            projected[mode] = deliver_semantic_result(
                payload, projection=mode, repo_root=FIXTURE, registry_path=store,
            )
            encoded = json.dumps(projected[mode], sort_keys=True)
            rendered = _render_text(projected[mode])
            assert_no_discarded_input(encoded)
            assert_no_discarded_input(rendered)
            (directory / f'{mode}.json').write_text(encoded)
            (directory / f'{mode}.txt').write_text(rendered)
        assert store.with_name(store.name + '-wal').stat().st_size > 0
        assert_clean_files(directory)
    return projected['llm']


def _expand_check(reference: dict[str, str], directory: Path, label: str) -> None:
    common = [
        'proof-search', 'evidence', 'semantic-check', reference['artifactRef'],
        '--local-id', reference['localId'], '--repo-root', str(FIXTURE),
        '--evidence-store', str(directory / 'evidence.sqlite'),
    ]
    result = json.loads(_run([*common, '--format', 'json'], directory, label))
    assert result['evidenceReceipt']['observationState'] == 'stored'
    _run([*common, '--format', 'text'], directory, label + '-text')


def _assert_recorded_environment(payload: dict[str, Any]) -> None:
    environments = [artifact for artifact in collect_semantic_artifacts(payload)
                    if artifact['artifactKind'] == 'proofir.environment']
    assert environments
    for environment in environments:
        context = json.loads(environment['payload']['options']['toolchainContext'])
        assert context['executionContextVersion'] == 2
        assert 'LEAN_PATH' in context['environmentKeys']
        assert context['libraryRoots']
        assert context['sourceEnumeration']['environmentKeys'] == context['environmentKeys']
        assert_no_discarded_input(context)


@pytest.mark.parametrize(('candidate', 'status'), [
    ('LadonFixture.fixtureTrue', 'accepted'),
    ('LadonFixture.noSuch', 'rejected'),
    ('id', 'applicable-with-residuals'),
])
def test_console_direct_outcomes_do_not_disclose_caller_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned_tools: tuple[Path, Path],
    candidate: str, status: str,
) -> None:
    poison_environment(monkeypatch)
    output = tmp_path / 'captured.json'
    _run([
        'proof-search', 'check', 'candidate', '--repo-root', str(FIXTURE),
        '--module', 'LadonFixture', '--goal', 'True', '--candidate', candidate,
        *_selection(pinned_tools, 'explicit'), '--progress', '--projection', 'audit',
        '--format', 'json', '--output', str(output),
    ], tmp_path, 'live')
    payload = json.loads(output.read_text())
    assert payload['status'] == status
    _assert_recorded_environment(payload)
    kinds = {artifact['artifactKind'] for artifact in payload['artifacts']}
    if status == 'applicable-with-residuals':
        assert 'proofir.attempt-log' in kinds
    card = _project_captured(payload, tmp_path)['candidate']['check']
    assert card['authority']['executionBinding'] == 'explicit-pinned'
    _expand_check(card['checkRunRef'], tmp_path, 'stored')
    assert_clean_files(tmp_path)


@pytest.mark.parametrize('mode', ['explicit', 'ambient'])
def test_console_discovery_and_scratch_do_not_disclose_caller_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned_tools: tuple[Path, Path], mode: str,
) -> None:
    poison_environment(monkeypatch)
    monkeypatch.setenv('PATH', str(pinned_tools[1].parent) + os.pathsep + os.environ.get('PATH', ''))
    captured = _run([
        'proof-search', 'discover', '--repo-root', str(FIXTURE),
        '--module', 'LadonFixture', '--goal', 'True',
        '--candidate', 'LadonFixture.fixtureTrue', '--candidate', 'LadonFixture.noSuch',
        '--candidate', 'id', '--scratch-mode', 'advisory',
        *_selection(pinned_tools, mode), '--progress', '--projection', 'audit', '--format', 'json',
    ], tmp_path, 'live')
    payload = json.loads(captured)
    statuses = {row['name']: row['check']['status'] for row in payload['candidates']}
    assert statuses == {'LadonFixture.fixtureTrue': 'accepted', 'LadonFixture.noSuch': 'rejected',
                        'id': 'applicable-with-residuals'}
    assert payload['coverage']['scratchCompiled'] == 1
    _assert_recorded_environment(payload)
    compact = _project_captured(payload, tmp_path)
    binding = 'explicit-pinned' if mode == 'explicit' else 'ambient-observed'
    for ordinal, row in enumerate(compact['candidates']):
        check = row['check']
        assert check['authority']['executionBinding'] == binding
        _expand_check(check['checkRunRef'], tmp_path, f'stored-{ordinal}')
        scratch = check.get('scratch')
        if scratch:
            assert scratch['authority']['authorityBasis'] == 'process-observation'
            _expand_check(scratch['checkRunRef'], tmp_path, 'stored-scratch')
    assert_clean_files(tmp_path)


def test_console_preflight_failure_does_not_publish_or_disclose_caller_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned_tools: tuple[Path, Path],
) -> None:
    repository = tmp_path / 'repo'
    repository.mkdir()
    (repository / 'lean-toolchain').write_text('leanprover/lean4:v0.0.0\n')
    store = tmp_path / 'unpublished.sqlite'
    poison_environment(monkeypatch)
    result = _run([
        'proof-search', 'check', 'candidate', '--repo-root', str(repository),
        '--module', 'Main', '--goal', 'True', '--candidate', 'True.intro',
        *_selection(pinned_tools, 'explicit'), '--evidence-store', str(store),
        '--format', 'json',
    ], tmp_path, 'preflight', exit_code=1)
    assert result == ''
    diagnostic = json.loads((tmp_path / 'preflight.stderr').read_text())
    assert diagnostic['diagnostic']['code'] == 'toolchain-unavailable'
    assert not store.exists()
    assert_clean_files(tmp_path)
