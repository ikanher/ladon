"""Run one public CLI operation under the shared MF qualification bounds."""
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

from ladon.process_supervisor import run_bounded_target_process

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
CLI = [sys.executable, '-c', 'import sys; from ladon.entrypoint import main; sys.exit(main(sys.argv[1:]))']

def main():
    name, *args = sys.argv[1:]
    out = BASE / (name + '.process.json')
    assert not out.exists(), 'retain previous attempts'
    policy = json.loads((BASE / 'TIMEOUT-REVISION.json').read_text())
    remaining = policy['deadlineEpoch'] - time.time()
    assert remaining > 0, 'aggregate execution deadline exhausted'
    result = run_bounded_target_process(CLI + args, cwd=ROOT,
        timeout_seconds=min(policy["commandSeconds"], remaining), max_output_bytes=8*1024**2,
        max_rss_bytes=12*1024**3, observe_resources=True)
    with out.open('x') as stream:
        json.dump(asdict(result), stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k,v in asdict(result).items() if k in
        ('returncode','stdout','stderr','elapsed_seconds','timed_out','memory_limited','peak_rss_bytes')}, indent=2))
    sys.exit(0 if result.succeeded else 1)

if __name__ == '__main__':
    main()
