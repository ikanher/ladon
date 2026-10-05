"""Source capture has an explicit CLI and independent outcome."""

import json
from pathlib import Path

from ladon.proof_search_cli import build_proof_search_parser, proof_search_main
from ladon.proof_search_terminal import semantic_payload_failed


def argv():
    return ['check', 'source', '--repo-root', '.', '--module', 'Owner',
            '--source', 'Owner.lean', '--candidate', 'Owner.target',
            '--subject-artifact', 'sha256:' + '1' * 64,
            '--artifact', 'environment.json', '--artifact', 'check.json',
            '--lake-path', '/toolchain/bin/lake', '--lean-path', '/toolchain/bin/lean',
            '--max-rss-mib', '32768', '--format', 'json']


def test_source_capture_parser_is_explicit_and_preserves_authorized_budget():
    args = build_proof_search_parser().parse_args(argv())
    assert args.check_operation == 'source'
    assert args.toolchain_mode == 'explicit'
    assert args.max_rss_mib == 32768
    assert args.artifact == [Path('environment.json'), Path('check.json')]


def test_source_capture_requires_isolation_before_reading_artifacts(capsys):
    code = proof_search_main([*argv(), '--require-isolation'])
    assert code != 0
    terminal = json.loads(capsys.readouterr().err)
    assert terminal['diagnostic']['code'] == 'target-isolation-unavailable'


def test_source_association_failure_is_not_a_successful_checker_result():
    assert semantic_payload_failed('check.source', {'status': 'stale'})
    assert semantic_payload_failed('check.source', {'status': 'unavailable'})
    assert not semantic_payload_failed('check.source', {'status': 'associated'})
