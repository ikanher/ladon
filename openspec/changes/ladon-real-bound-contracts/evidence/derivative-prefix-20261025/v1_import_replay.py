"""Fresh checks must inspect changed compiled definitions, not replay old receipts."""
from pathlib import Path
from dataclasses import asdict
import hashlib,json,shutil,sys
from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.real_bound_observation import observe_bound_snapshot
from ladon.real_bound_binding import plan_bound_prefix
from ladon.real_bound_binding_check import verify_binding_source
from ladon.proof_slice import pinned_toolchain
from ladon.process_supervisor import run_bounded_target_process
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
BASE=Path('.codex/state/derivative-prefix').resolve();OUT=BASE/'v1-import-replay';OUT.mkdir(exist_ok=False)
ORIGINAL=BASE.parent/'real-bound-admission/consumer-project'

def save(name,value):
 with (OUT/name).open('x') as f: json.dump(value,f,indent=2)

def project(name):
 p=OUT/name;p.mkdir();shutil.copy2(ORIGINAL/'lean-toolchain',p/'lean-toolchain')
 (p/'.lake/build/lib/lean').mkdir(parents=True);(p/'.lake/packages').symlink_to(ORIGINAL/'.lake/packages',target_is_directory=True)
 return p

root=project('project');builder=project('builder')
original=Path('tests/fixtures/real_bound_binding/ImportedMeaning.lean').read_text()
(root/'ImportedMeaning.lean').write_text(original)
text=Path('tests/fixtures/real_bound_binding/DependentBounds.lean').read_text().replace('DependentBounds','ImportedBounds').replace('sample f p y j ≤ C','ImportedMeaning.interpret (sample f p y j) ≤ C')
(root/'Case.lean').write_text('import ImportedMeaning\n'+text)
module=root/'.lake/build/lib/lean/ImportedMeaning.olean'

def build(name,text):
 (builder/'ImportedMeaning.lean').write_text(text)
 ex=prepare_direct_lean_execution(builder,None,pinned_toolchain(builder),require_compiled_module=False)
 run=run_bounded_target_process([*ex.command,'-o',str(module),'ImportedMeaning.lean'],cwd=builder,env=ex.environment,
   timeout_seconds=60,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
 save(name+'-compile.json',asdict(run));assert run.succeeded,run.stdout

build('original',original)
formal=produce_formal_snapshot(root,'Case.lean','Case','ImportedBounds.estimate')
obs=observe_bound_snapshot(formal,root);assert obs['status']=='observed'
plan=plan_bound_prefix(obs,{'declaration':'ImportedBounds.sample','arguments':['b0','b1']})
save('plan.json',plan);save('observation.json',obs)
save('proof.json',{'term':'by intro P inst; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl'})

def check(name,expected):
 output=OUT/(name+'-result.json')
 cmd=[sys.executable,'-m','ladon.entrypoint','investigation','contract','check-bound-prefix','--root',str(root),
   '--input',str(OUT/'plan.json'),'--proof',str(OUT/'proof.json'),'--timeout-seconds','600','--output',str(output)]
 run=run_bounded_target_process(cmd,cwd=Path.cwd(),timeout_seconds=660,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
 save(name+'-command.json',asdict(run));assert output.exists(),run.stdout+run.stderr
 result=json.loads(output.read_text());assert result['status']==expected,(name,result['status'])
 assert run.returncode==(0 if expected=='checked-binding' else 2)
 print(name,expected,round(run.elapsed_seconds,2),flush=True)
 return result

positive=check('original','checked-binding')
context=pinned_toolchain(root).context_identity
source_hash=hashlib.sha256((root/'Case.lean').read_bytes()).hexdigest()
before=hashlib.sha256(module.read_bytes()).hexdigest()
build('mutated',original.replace(':= value',':= value + 1'))
after=hashlib.sha256(module.read_bytes()).hexdigest()
assert before!=after
assert context==pinned_toolchain(root).context_identity
assert source_hash==hashlib.sha256((root/'Case.lean').read_bytes()).hexdigest()
verify_binding_source(root,plan)
negative=check('mutated','unresolved')
assert negative['supervision']['result']['check']['evidence']['completion']['status']!='completed'
save('RESULTS.json',{'sourceUnchanged':True,'pinnedContextUnchanged':True,'compiledModuleChanged':True,
 'before':before,'after':after,'original':'checked-binding','mutated':'unresolved'})
