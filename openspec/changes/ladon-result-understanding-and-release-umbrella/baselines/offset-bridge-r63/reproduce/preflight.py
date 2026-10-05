from pathlib import Path
from dataclasses import asdict
import json,os
from ladon.process_supervisor import run_bounded_target_process
from ladon.lean_toolchain import compiled_library_roots
state=Path('.codex/state/offset-bridge-r63');run=Path((state/'run-path').read_text().strip());cwd=run/'ordinary'
p=cwd/'Preflight.lean';p.write_text('import Mf.DP.PoissonFixedEpochAsymptotics\n#check Mf.DP.tendsto_fixedParticipationCalibratedStddev_offset\n#check Mf.DP.PoissonFixedEpochPoint.ofExtra\n#print axioms Mf.DP.tendsto_fixedParticipationCalibratedStddev_offset\n')
env=dict(os.environ);env['LEAN_PATH']=os.pathsep.join(str(p) for p in compiled_library_roots(cwd));env['PATH']='/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin:'+env['PATH']
r=run_bounded_target_process(['lean',str(p)],cwd=cwd,env=env,timeout_seconds=180,max_output_bytes=8388608,max_rss_bytes=34359738368)
(state/'preflight.json').write_text(json.dumps(asdict(r),indent=2)+'\n');print(r.stdout);assert r.returncode==0 and not r.timed_out and not r.memory_limited
assert 'sorryAx' not in r.stdout
p.unlink()
