import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'src')
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon')
base=root/'.codex/state/application-completion-r58/feasibility'
r=json.loads((base/'synth-closure-receipt.json').read_text())
line=next(x[len('LADON_EXPERIMENT '):] for x in r['stdout'].splitlines() if x.startswith('LADON_EXPERIMENT '))
v=json.loads(line); items=[]
while isinstance(v,list) and len(v)==2:
    items.append(v[0]); v=v[1]
items.append(v)
assert len(items)==7, len(items)
target,proof=items[5],items[6]
source=("import Lean\nopen Lean Elab Command\n\n"+
        "theorem completionFeasibilityReplay : "+target+" :=\n  "+proof+"\n\n"+
        "run_cmd do\n  let axioms ← Lean.collectAxioms `completionFeasibilityReplay\n  let names := String.intercalate \",\" (axioms.toList.map toString)\n  logInfo m!\"LADON_AXIOMS [{names}]\"\n  if axioms.contains ``sorryAx then throwError \"replay depends on sorryAx\"\n")
source_path=base/'OwnerReplay.lean'; source_path.write_text(source)
cmd=['/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin/lean',str(source_path),'-o',str(base/'OwnerReplay.olean')]
r=run_bounded_target_process(cmd,cwd=base,timeout_seconds=30,max_output_bytes=8*1024*1024,max_rss_bytes=32*1024**3)
receipt={'command':cmd,'cwd':str(base),'limits':{'timeoutSeconds':30,'maxOutputBytes':8*1024*1024,'maxRssBytes':32*1024**3},'sourceSha256':hashlib.sha256(source.encode()).hexdigest(),'returncode':r.returncode,'elapsedSeconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes,'timedOut':r.timed_out,'outputLimited':r.output_limited,'memoryLimited':r.memory_limited,'stdout':r.stdout,'stderr':r.stderr}
(base/'compiler-replay-receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({k:receipt[k] for k in ('command','cwd','limits','sourceSha256','returncode','elapsedSeconds','peakRssBytes','timedOut','outputLimited','memoryLimited','stdout','stderr')}))
