from pathlib import Path
from dataclasses import asdict
import hashlib,json,os,re,shutil
from ladon.process_supervisor import run_bounded_target_process
from ladon.lean_toolchain import compiled_library_roots
state=Path('.codex/state/offset-bridge-r63');run=Path((state/'run-path').read_text().strip());out=run/'root-replay';out.mkdir()
original=(run/'shared/IntendedTarget.lean').read_text();signature=original.split('theorem fixedEpochOffsetBridge',1)[1].split(':= by',1)[0];records=[]
for arm in ['ordinary','augmented']:
 source=run/arm/'Bridge.lean';raw=source.read_text();assert raw.split('theorem fixedEpochOffsetBridge',1)[1].split(':= by',1)[0]==signature
 assert not re.search(r'\b(sorry|admit|axiom)\b',raw.split('theorem fixedEpochOffsetBridge',1)[1].split('#print',1)[0])
 dest=out/arm;dest.mkdir();proof=dest/'Bridge.lean';shutil.copy2(source,proof)
 env=dict(os.environ);env['LEAN_PATH']=os.pathsep.join(str(p) for p in compiled_library_roots(run/arm));env['PATH']='/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin:'+env['PATH']
 r=run_bounded_target_process(['lean','-o',str(dest/'Bridge.olean'),str(proof)],cwd=run/arm,env=env,timeout_seconds=180,max_output_bytes=8388608,max_rss_bytes=34359738368)
 record=asdict(r);record['sourceSha256']='sha256:'+hashlib.sha256(source.read_bytes()).hexdigest();record['originalSignatureUnchanged']=True;record['LEAN_PATH']=env['LEAN_PATH']
 assert r.returncode==0 and not r.timed_out and not r.memory_limited,(arm,r.stdout,r.stderr)
 match=re.search(r"'OffsetBridge.fixedEpochOffsetBridge' depends on axioms: \[([^]]*)\]",r.stdout);assert match
 axioms={x.strip() for x in match[1].split(',') if x.strip()};assert axioms<={'propext','Classical.choice','Quot.sound'},axioms
 record['observedAxioms']=sorted(axioms);record['compiledArtifactSha256']='sha256:'+hashlib.sha256((dest/'Bridge.olean').read_bytes()).hexdigest();record['policy']='Only propext, Classical.choice and Quot.sound permitted; sorryAx and other axioms reject completion.'
 (dest/'receipt.json').write_text(json.dumps(record,indent=2)+'\n');records.append({'arm':arm,'sourceSha256':record['sourceSha256'],'axioms':sorted(axioms),'seconds':r.elapsed_seconds,'rss':r.peak_rss_bytes,'signatureUnchanged':True})
 print(records[-1],flush=True)
(state/'replay-summary.json').write_text(json.dumps(records,indent=2)+'\n')
