#!/usr/bin/env python3
"""One-off canonical-reuse r68 benchmark; no instrumentation in the measured CLI."""
from __future__ import annotations
import argparse, hashlib, json, resource, statistics, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REAL = Path('/home/codex/.cache/ladon-reader-loop-r49/shared/result.zip')
SMALL = HERE / 'small-complete/result.zip'
WORKLOADS = {
    'real-inspect': [str(REAL), '--claim', 'cor:fixed-epoch-all-horizon', '--component', 'transcript', '--format', 'json'],
    'real-guide': [str(REAL), '--section', 'checking', '--claim', 'cor:fixed-epoch-all-horizon', '--format', 'json'],
    'small-inspect': [str(SMALL), '--section', 'checking', '--claim', 'paper-theorem-1', '--format', 'json'],
    'small-guide': [str(SMALL), '--section', 'checking', '--claim', 'paper-theorem-1', '--format', 'json'],
}
SUBCOMMAND = {'real-inspect': 'inspect', 'real-guide': 'guide', 'small-inspect': 'inspect', 'small-guide': 'guide'}

def _limit_address_space() -> None:
    cap = 32 * 1024 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))

def run(executable: str, side: str, workload: str, pair: int, root: Path) -> dict:
    out = root / 'outputs' / f'{workload}-pair{pair:02d}-{side}.stdout'
    timing = root / 'timing' / f'{workload}-pair{pair:02d}-{side}.txt'
    out.parent.mkdir(parents=True, exist_ok=True); timing.parent.mkdir(parents=True, exist_ok=True)
    command = [executable, 'result', SUBCOMMAND[workload], *WORKLOADS[workload]]
    fmt = '%e\t%U\t%S\t%M\t%x'
    with out.open('wb') as stdout, timing.open('w', encoding='ascii') as timing_file:
        proc = subprocess.run(['/usr/bin/time', '-f', fmt, '-o', str(timing), '--', *command],
                              stdout=stdout, stderr=subprocess.PIPE, check=False, preexec_fn=_limit_address_space)
    fields = timing.read_text().strip().split('\t')
    stderr = proc.stderr.decode('utf-8', 'replace')
    record = {
        'side': side, 'workload': workload, 'pair': pair, 'command': command,
        'wall_seconds': float(fields[0]), 'user_cpu_seconds': float(fields[1]),
        'system_cpu_seconds': float(fields[2]), 'peak_rss_kib': int(fields[3]),
        'exit_status': int(fields[4]), 'stdout_bytes': out.stat().st_size,
        'stdout_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
        'stdout_path': str(out.relative_to(root)), 'stderr': stderr,
    }
    if record['exit_status'] != 0:
        raise RuntimeError(f'{side} {workload} pair {pair} failed: {stderr}')
    return record

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--before', required=True)
    parser.add_argument('--after')
    parser.add_argument('--baseline-only', action='store_true')
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--pairs', type=int, default=5)
    parser.add_argument('--workload', action='append', choices=tuple(WORKLOADS),
                        help='Limit capture to named workload; repeatable. Default: all.')
    args = parser.parse_args()
    if args.pairs != 5:
        parser.error('r68 cost gate is frozen at exactly five pairs')
    root = Path(args.output_dir).resolve(); root.mkdir(parents=True, exist_ok=True)
    sides = [('before', args.before)] if args.baseline_only else [('before', args.before), ('after', args.after)]
    if not args.baseline_only and not args.after:
        parser.error('--after is required unless --baseline-only is set')
    runs = []
    selected_workloads = args.workload or list(WORKLOADS)
    for workload in selected_workloads:
        for pair in range(1, args.pairs + 1):
            ordered = sides if pair % 2 else list(reversed(sides))
            for side, executable in ordered:
                runs.append(run(executable, side, workload, pair, root))
    by_key = {(row['workload'], row['pair'], row['side']): row for row in runs}
    parity, gates = {}, {}
    if not args.baseline_only:
        for workload in selected_workloads:
            hashes = []
            for pair in range(1, args.pairs + 1):
                a = by_key[(workload, pair, 'before')]['stdout_sha256']
                b = by_key[(workload, pair, 'after')]['stdout_sha256']
                hashes.append(a == b)
            before_rows = [by_key[(workload, pair, 'before')] for pair in range(1, args.pairs + 1)]
            after_rows = [by_key[(workload, pair, 'after')] for pair in range(1, args.pairs + 1)]
            before_wall = statistics.median(r['wall_seconds'] for r in before_rows)
            after_wall = statistics.median(r['wall_seconds'] for r in after_rows)
            before_rss = statistics.median(r['peak_rss_kib'] for r in before_rows)
            after_rss = statistics.median(r['peak_rss_kib'] for r in after_rows)
            faster = sum(a['wall_seconds'] < b['wall_seconds'] for a, b in zip(after_rows, before_rows))
            parity[workload] = {'all_pair_stdout_identical': all(hashes), 'pairs_identical': hashes}
            if workload.startswith('real-'):
                gates[workload] = {
                    'median_wall_improvement_fraction': (before_wall - after_wall) / before_wall,
                    'after_faster_pairs': faster,
                    'pass': (all(hashes) and (before_wall - after_wall) / before_wall >= 0.20 and faster >= 4),
                }
            else:
                wall_regression = after_wall - before_wall
                rss_regression = after_rss - before_rss
                gates[workload] = {
                    'median_wall_delta_seconds': wall_regression,
                    'median_peak_rss_delta_kib': rss_regression,
                    'material_wall_regression': wall_regression > 0.20 * before_wall and wall_regression > 0.050,
                    'material_memory_regression': rss_regression > 0.10 * before_rss and rss_regression > 32 * 1024,
                    'pass': all(hashes) and not (wall_regression > 0.20 * before_wall and wall_regression > 0.050)
                           and not (rss_regression > 0.10 * before_rss and rss_regression > 32 * 1024),
                }
    report = {'schema': 'canonical-reuse-r68-benchmark-v1', 'same_host': True,
              'baseline_only': args.baseline_only, 'pairs': args.pairs,
              'executables': {'before': args.before, 'after': args.after},
              'workloads': {name: WORKLOADS[name] for name in selected_workloads}, 'runs': runs, 'parity': parity, 'gates': gates}
    (root / 'results.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'results': str(root / 'results.json'), 'runs': len(runs), 'parity': parity, 'gates': gates}, sort_keys=True))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
