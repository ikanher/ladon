import json,sys,time,dataclasses
from pathlib import Path
from ladon.proof_slice import pinned_toolchain
from ladon.process_supervisor import run_bounded_target_process
from ladon.semantic_lean_execution import prepare_direct_lean_execution
b=Path('.codex/state/navier-pair-integration').resolve();root=b/'project';ctx=pinned_toolchain(root)
deadline=json.loads((b/'lean-budget.json').read_text())['deadlineMonotonic']
def remaining():
 r=deadline-time.monotonic();assert r>0,'original shared deadline expired';return r

def run(label,cmd,env=None,cwd=Path.cwd()):
 r=run_bounded_target_process(cmd,cwd=cwd,env=env,timeout_seconds=remaining(),max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
 (b/(label+'-process.json')).write_text(json.dumps({'command':cmd,**dataclasses.asdict(r)},indent=2)+'\n')
 assert not any((r.timed_out,r.memory_limited,r.output_limited)),'Stop progress and report resource stop to user.'
 print(label,r.returncode,round(r.elapsed_seconds,2),r.peak_rss_bytes,flush=True)
 return r
exe=prepare_direct_lean_execution(root,None,ctx,require_compiled_module=False)
r=run('typed-vocabulary',[*exe.command,'PaperVocabulary.lean'],dict(exe.environment),root)
assert r.returncode==0,(r.stdout,r.stderr)
positions=json.loads((b/'goal-positions.json').read_text());term=(b/'five-term.txt').read_text().strip();summary=[]
for name in ['FiveOrderControl','FourOrderProbe']:
 cap=b/(name+'-capture.json');out=b/(name+'-completion.json')
 common=['--repo-root',str(root),'--lean-path',str(ctx.lean_path),'--lake-path',str(ctx.lean_path.with_name('lake')),'--format','json','--max-rss-mib','12288']
 cmd=[sys.executable,'-m','ladon.entrypoint','proof-search','goal','capture',*common,'--source',name+'.lean','--module',name,'--line',str(positions[name]),'--column','4','--timeout-seconds',str(remaining()),'--output',str(cap)]
 r=run(name+'-capture',cmd);assert r.returncode==0,(r.stdout,r.stderr)
 capture=json.loads(cap.read_text());assert capture['status']=='captured'
 cmd=[sys.executable,'-m','ladon.entrypoint','proof-search','goal','complete',*common,'--capture-file',str(cap),'--term',term,'--timeout-seconds',str(remaining()),'--output',str(out)]
 r=run(name+'-completion',cmd);assert out.exists(),(r.stdout,r.stderr)
 result=json.loads(out.read_text())
 if name=='FiveOrderControl':
  assert result['status']=='completed',result.get('diagnostic')
  assert result['trust']['accepted'] and result['replay']['status']=='accepted'
  assert set(result['trust']['observedAxioms'])<= {'propext','Classical.choice','Quot.sound'}
 else:
  assert result['status']!='completed' and result.get('diagnostic'),result
 summary.append({'case':name,'status':result['status'],'diagnostic':result.get('diagnostic'),'trust':result.get('trust'),'resources':result.get('resourceAccounting')})
(b/'BRIDGE-RESULT.json').write_text(json.dumps({'cases':summary,'nativeFrontier':False,'paperNormEquivalence':'unresolved','negativeIsMathematicalRefutation':False,'sharedDeadlineSeconds':600},indent=2)+'\n')
print(json.dumps(summary,indent=2))
