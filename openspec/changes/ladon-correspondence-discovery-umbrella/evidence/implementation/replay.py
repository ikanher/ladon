"""Record one ordinary Lean observation with Ladon's existing supervisor.

Usage: uv run python replay.py RUN_ID FIXTURE SOURCE EXPECTED_DECLARATION...
An empty expected list records a deliberately failing attempt; it never passes
the declaration policy. No statement/prose correspondence is checked here.
"""
from pathlib import Path
import dataclasses
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

from ladon.process_supervisor import run_bounded_target_process

here = Path(__file__).resolve().parent
run_id, fixture_arg, source_arg, *expected = sys.argv[1:]
fixture = Path(fixture_arg).resolve()
source = Path(source_arg).resolve()
out = here / 'runs' / run_id
out.mkdir(parents=True)  # do not replace a recorded attempt
shutil.copy2(source, out / source.name)
toolchain = (fixture / 'lean-toolchain').read_text().strip()
tool_root = Path.home() / '.elan/toolchains' / toolchain.replace('/', '--').replace(':', '---') / 'bin'
lean = tool_root / 'lean'
lake = tool_root / 'lake'
lean_path = subprocess.check_output([str(lake), 'env', 'printenv', 'LEAN_PATH'], cwd=fixture, text=True).strip()
env = dict(os.environ, LEAN_PATH=lean_path, LEAN_NUM_THREADS='4')
cmd = [str(lean), str(source)]
result = run_bounded_target_process(cmd, cwd=fixture, timeout_seconds=180,
    max_output_bytes=8*1024*1024, max_rss_bytes=32*1024**3, env=env)
(out/'stdout.txt').write_text(result.stdout)
(out/'stderr.txt').write_text(result.stderr)
matches = re.findall(r"'([^']+)' depends on axioms: \[([^\]]*)\]", result.stdout)
allowed = {'propext', 'Classical.choice', 'Quot.sound'}
observed = {name: [a.strip() for a in values.split(',') if a.strip()] for name, values in matches}
policy = bool(expected) and result.succeeded and set(expected) <= set(observed) and all(
    set(observed[name]) <= allowed for name in expected)
record = dataclasses.asdict(result)
record.pop('stdout'); record.pop('stderr')
record.update(command=cmd, cwd=str(fixture), leanToolchain=toolchain,
    sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(), expected=expected,
    observedAxioms=observed, policyAccepted=policy,
    kind='ordinary compiler observation; no correspondence verdict',
    guaranteeScope='only requested declarations elaborated against existing imported libraries',
    memoryMechanism='sampled aggregate process-tree RSS', memoryLimitBytes=32*1024**3,
    timeoutSeconds=180, maxOutputBytes=8*1024*1024,
    executableSha256=hashlib.sha256(lean.read_bytes()).hexdigest(),
    stdoutSha256=hashlib.sha256(result.stdout.encode()).hexdigest())
(out/'record.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps({'run':run_id,'returncode':result.returncode,'policyAccepted':policy,
                  'elapsedSeconds':result.elapsed_seconds}))
sys.exit(0 if (policy if expected else not result.succeeded) else 1)
