"""Record ordinary reader commands with the installed bounded process owner."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import sys

from ladon.process_supervisor import run_bounded_target_process

parser = argparse.ArgumentParser()
parser.add_argument('--record-dir', type=Path, required=True)
parser.add_argument('--label', required=True)
parser.add_argument('--cwd', type=Path, required=True)
parser.add_argument('--timeout', type=float, default=120)
parser.add_argument('--stdin-file', type=Path)
parser.add_argument('command', nargs=argparse.REMAINDER)
args = parser.parse_args()
command = args.command[1:] if args.command and args.command[0] == '--' else args.command
if not command or not args.label.replace('-', '').replace('_', '').isalnum():
    parser.error('a command and a simple unique label are required')
args.record_dir.mkdir(parents=True, exist_ok=True)
base = args.record_dir / args.label
record = base.with_suffix('.command.json')
if record.exists():
    parser.error('label already exists; retain failed attempts under new labels')
result = run_bounded_target_process(
    command, cwd=args.cwd, timeout_seconds=args.timeout,
    max_output_bytes=64 * 1024 * 1024, max_rss_bytes=32 * 1024**3,
    env=dict(os.environ),
    input_bytes=args.stdin_file.read_bytes() if args.stdin_file else None,
)
streams = {}
for name in ('stdout', 'stderr'):
    data = getattr(result, name).encode('utf-8')
    path = base.with_suffix('.' + name)
    path.write_bytes(data)
    streams[name] = {'path': str(path), 'bytes': len(data), 'sha256': 'sha256:' + hashlib.sha256(data).hexdigest()}
record.write_text(json.dumps({
    'recordedAt': datetime.now(timezone.utc).isoformat(), 'argv': command,
    'cwd': str(args.cwd), 'exitCode': result.returncode,
    'elapsedSeconds': result.elapsed_seconds, 'peakRssBytes': result.peak_rss_bytes,
    'timedOut': result.timed_out, 'memoryLimited': result.memory_limited,
    'outputLimited': result.output_limited, 'streams': streams,
    'stdinFile': str(args.stdin_file) if args.stdin_file else None,
    'limits': {'timeoutSeconds': args.timeout, 'rssGiB': 32, 'outputMiB': 64},
}, indent=2) + '\n')
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
print('\nRECORDED ' + str(record), file=sys.stderr)
sys.exit(result.returncode if result.returncode >= 0 else 128 - result.returncode)
