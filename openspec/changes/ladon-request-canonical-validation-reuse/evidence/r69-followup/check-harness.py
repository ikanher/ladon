"""Isolated filtered/full aggregation probes; these are not timing samples."""
import importlib.util,json,sys,tempfile
from pathlib import Path
path=Path('.codex/state/canonical-reuse-r68/benchmark.py')
spec=importlib.util.spec_from_file_location('benchmark',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
records=[]
def fake(exe,side,workload,pair,root):
 return {'side':side,'workload':workload,'pair':pair,'wall_seconds':2 if side=='before' else 1,
         'peak_rss_kib':100,'stdout_sha256':'same'}
module.run=fake
for workload in [*module.WORKLOADS,None]:
 with tempfile.TemporaryDirectory() as temporary:
  sys.argv=['benchmark.py','--before','before','--after','after','--output-dir',temporary]
  if workload:sys.argv.extend(['--workload',workload])
  assert module.main()==0
  d=json.loads((Path(temporary)/'results.json').read_text())
  names={workload} if workload else set(module.WORKLOADS)
  assert set(d['workloads'])==set(d['gates'])==set(d['parity'])==names
  assert len(d['runs'])==10*len(names)
  records.append({'selected':sorted(names),'stubCalls':len(d['runs']),'pass':True})
Path('.codex/state/review-followup-r69/harness-probes.json').write_text(json.dumps(records,indent=2)+'\n')
