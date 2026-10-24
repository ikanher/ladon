import hashlib,json,shutil,time
from pathlib import Path
from ladon.proof_slice import extract_proof_slice
from ladon.proof_contract_production import produce_formal_contract
from ladon.correspondence_check import prepare_correspondence
from ladon.proof_contract_source_obligations import _runner
root=Path('.codex/state/proof-contract-analysis/context-bridge/probe-repo').resolve();root.mkdir(exist_ok=True)
shutil.copyfile('tests/fixtures/correspondence_m1/lean-toolchain',root/'lean-toolchain')
text='''import Lean
namespace Contexts
theorem both (n m : Nat) (hn : 0 < n) (hm : 0 < m) : 0 < n ∧ 0 < m := And.intro hn hm
theorem bounded (n : Nat) (h : n < 5) : n < 5 := h
theorem dependent (n : Nat) (i : Fin n) : True ∧ True := And.intro True.intro True.intro
theorem ordered (n m : Nat) (hn : 0 < n) (hm : 0 < m) : 0 < n ∧ 0 < m := both n m hn hm
theorem represented (n : Nat) (h : n < 5) : n < 5 := bounded n h
end Contexts
'''
(root/'Contexts.lean').write_text(text)
start=time.monotonic();deadline=start+60
var=lambda i:{'tag':'var','id':i}
pos=lambda i:{'tag':'lt','left':{'tag':'const','name':'0'},'right':var(i)}
formula={'tag':'implies','premise':pos('n'),'conclusion':{'tag':'implies','premise':pos('m'),'conclusion':{'tag':'and','items':[pos('n'),pos('m')]}}}
for i in ('m','n'):formula={'tag':'forall','binder':{'id':i,'name':i,'domain':'Nat'},'body':formula}
record={'id':'ordered-original','source':{'path':'claim.txt','startLine':1,'endLine':1,'quote':'Positive n and m yield both positive.','sha256':hashlib.sha256(b'Positive n and m yield both positive.\n').hexdigest()},'formula':formula,'symbols':{}}
(root/'claim.txt').write_text(record['source']['quote']+'\n')
actual=extract_proof_slice(root,'Contexts.lean','Contexts','Contexts.ordered','Contexts.both',scoped=True)
assert actual['complete'],actual
plan=prepare_correspondence(record,actual,{'n':'n','m':'m'})
observed=produce_formal_contract(root,'Contexts.lean','Contexts','Contexts.ordered',timeout_seconds=30,runner=_runner(deadline))
assert observed['observation']['declarationRange']['startLine']==6,observed
out=Path('.codex/state/proof-contract-analysis/context-bridge')
for name,value in [('feasibility-slice.json',actual),('feasibility-plan.json',plan),('feasibility-observation.json',observed)]:
 (out/name).write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'elapsedSeconds':time.monotonic()-start,'budgetSeconds':60,'premises':[p['occurrence'] for p in actual['nodes'][0]['premises']],'goals':[(g['id'],g['goal']) for g in plan['obligations']],'positionObserved':observed['observation']['declarationRange']},indent=2))
