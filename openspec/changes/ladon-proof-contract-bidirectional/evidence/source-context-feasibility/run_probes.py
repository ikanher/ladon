"""Tiny isolated source-prefix and alias feasibility probes (Lean 4.32.1)."""
from __future__ import annotations

import json
from pathlib import Path

from ladon.process_supervisor import run_bounded_target_process

LEAN = Path('/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin/lean')
LEAN_LIB = Path('/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/lib/lean')
ROOT = Path(__file__).resolve().parent
LIMITS = {'timeout_seconds': 60, 'max_output_bytes': 8 * 1024**2,
          'max_rss_bytes': 12 * 1024**3}


def run(label: str, args: list[str], env=None):
    result = run_bounded_target_process(args, cwd=ROOT, env=env, **LIMITS)
    return {
        'label': label,
        'command': result.command,
        'returncode': result.returncode,
        'timedOut': result.timed_out,
        'memoryLimited': result.memory_limited,
        'outputLimited': result.output_limited,
        'elapsedSeconds': result.elapsed_seconds,
        'peakRssBytes': result.peak_rss_bytes,
        'stdout': result.stdout,
        'stderr': result.stderr,
    }


def main():
    source_env = {'LEAN_PATH': str(LEAN_LIB)}
    alias_env = {'LEAN_PATH': f'{ROOT}:{LEAN_LIB}'}
    receipts = [
        run('positive-exact-prefix-and-parent-absence-guard',
            [str(LEAN), str(ROOT / 'GeneratedPrefixExact.lean')], source_env),
        run('negative-exact-prefix-omitted-parent-reference',
            [str(LEAN), str(ROOT / 'GeneratedPrefixExact_bad.lean')], source_env),
        run('compile-source-module-with-parent',
            [str(LEAN), '-o', str(ROOT / 'ObligationsRedOriginal.olean'),
             str(ROOT / 'ObligationsRed.original.lean')], source_env),
        run('imported-alias-can-use-parent',
            [str(LEAN), str(ROOT / 'ImportedAlias.lean')], alias_env),
    ]
    (ROOT / 'probe_receipts.json').write_text(json.dumps({
        'schema': 'source-bridge-feasibility-probes-v1',
        'limits': LIMITS,
        'receipts': receipts,
    }, indent=2) + '\n')
    for receipt in receipts:
        print(json.dumps({key: receipt[key] for key in (
            'label', 'returncode', 'timedOut', 'memoryLimited', 'outputLimited',
            'elapsedSeconds', 'peakRssBytes', 'stdout', 'stderr')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
