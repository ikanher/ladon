"""Frozen source input must share the bounded process lifecycle."""

import hashlib
import sys

from ladon.process_supervisor import run_bounded_target_process


def test_bounded_worker_reads_exact_large_frozen_input_and_eof(tmp_path):
    content = (b'\xce\xb1 source\n' * 200_000) + b'last byte'
    result = run_bounded_target_process(
        [sys.executable, '-c',
         'import sys,hashlib; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())'],
        cwd=tmp_path, timeout_seconds=10, max_output_bytes=1024,
        input_bytes=content,
    )
    assert result.succeeded
    assert result.stdout.strip() == hashlib.sha256(content).hexdigest()


def test_unread_large_input_cannot_block_the_supervisor_deadline(tmp_path):
    result = run_bounded_target_process(
        [sys.executable, '-c', 'import time; time.sleep(30)'],
        cwd=tmp_path, timeout_seconds=0.2, max_output_bytes=1024,
        input_bytes=b'x' * 2_000_000,
    )
    assert result.timed_out
    assert result.elapsed_seconds < 5
