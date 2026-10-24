import hashlib, json, shutil, time
from pathlib import Path
from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.correspondence_check import prepare_correspondence
from ladon.proof_contract_bridge import _accepted_check
from ladon.proof_contract_bridge_supervision import run_bridge_job
from ladon.proof_contract_probe_artifacts import application_probe_artifact
from ladon.proof_contract_probes import check_application_probe, plan_application_probe
from ladon.proof_contract_artifacts import source_contract_artifact
from ladon.proofir_correspondence import bind_native_interpretation, correspondence_artifacts, interpretation_artifacts
from ladon.proofir_v3 import validate_envelope_batch

base=Path('.codex/state/proof-contract-analysis/restricted-domain')
p=base/'attempt-04'; p.mkdir(parents=True, exist_ok=False)
repo=(p/'repo').resolve(); repo.mkdir()
shutil.copyfile(base/'lean-toolchain', repo/'lean-toolchain')
source='''import Lean
import Std
namespace DomainProbe
def P (x : Nat) : Prop := x = 0
theorem guarded (_tag : Unit) : ∀ x : Nat, x ≤ 0 → P x := by
  intro x hx
  dsimp [P]
  exact Nat.le_zero.mp hx
theorem use : ∀ x : Nat, x ≤ 0 → P x := guarded ()
end DomainProbe
'''
(repo/'Bridge.lean').write_text(source)
started=time.monotonic(); deadline=started+1800
limits={'timeout_seconds':30,'max_rss_bytes':12*1024**3,'max_output_bytes':8*1024**2}
extraction=run_bridge_job('extract-provider',{'repoRoot':str(repo),'sourcePath':'Bridge.lean','sourceDigest':'sha256:'+hashlib.sha256(source.encode()).hexdigest(),'declaration':'DomainProbe.use','application':'DomainProbe.guarded'},deadline_monotonic=deadline,limits=limits)
(p/'extraction.json').write_text(json.dumps(extraction,sort_keys=True,indent=2))
assert extraction['status']=='completed', extraction.get('diagnostic')
actual=extraction['result']; assert actual['complete'] and actual['localContext']==[] and not actual['nodes'][0]['premises']
(p/'actual.json').write_text(json.dumps(actual,sort_keys=True,indent=2))

symbols={'P':{'leanName':'DomainProbe.P','leanType':'Nat → Prop'}}
def rec(i,restricted):
    quote='For every natural x, if x is at most zero then P(x).' if restricted else 'For every natural x, P(x).'
    raw=(quote+'\n').encode(); path=f'reading-{i}.txt'; (repo/path).write_bytes(raw)
    x={'id':'x','name':'x','domain':'Nat'}
    body={'tag':'app','symbol':'P','args':[{'tag':'var','id':'x'}]}
    if restricted: body={'tag':'implies','premise':{'tag':'le','left':{'tag':'var','id':'x'},'right':{'tag':'const','name':'0'}},'conclusion':body}
    formula={'tag':'forall','binder':x,'body':body}
    record={'id':f'reading-{i}','source':{'path':path,'startLine':1,'endLine':1,'quote':quote,'sha256':hashlib.sha256(raw).hexdigest()},'formula':formula,'symbols':symbols}
    sm,interp=interpretation_artifacts(record,actual['environment'],source_root=repo)
    contract={'profileId':'norm-scale-v1','endpointId':'predicate:P','context':{'objectId':'predicate:DomainProbe.P','domainId':'domain:Nat','scaleId':'scale:unknown','representationId':'representation:original'},'telescope':[{'binderId':'x','typeId':'Nat','quantifier':'forall'}],'assumptions':[],'conclusionId':'predicate:P','features':{'regularity':{'state':'unknown','scaleId':'scale:unknown','offset':None,'reason':'not modeled by restricted-domain profile'},'constantDependencies':{'state':'unknown','allowedBinderIds':None,'reason':'not modeled by restricted-domain profile'},'witnessDependencies':[]}}
    owner=source_contract_artifact(contract,contract_id=f'contract:reading-{i}',environment_ref=actual['environment'],source_map_refs=[{'artifactRef':sm['artifactId'],'kind':'source-map','localId':sm['payload']['sourceMapId']}],residuals=[{'code':'profile-feature-omitted','message':'Other features outside this narrow family.','feature':'restricted-domain-v2'}])
    corr=correspondence_artifacts(bind_native_interpretation(prepare_correspondence(record,actual,{}),[sm,interp],source_root=repo))
    return [sm,interp,owner,corr],{'contractRef':{'artifactRef':owner['artifactId'],'kind':'contract','localId':owner['payload']['contractId']},'correspondenceRef':{'artifactRef':corr['artifactId'],'kind':'correspondence','localId':corr['payload']['correspondenceId']}}

# Left is unrestricted; right exactly matches the extracted closed application.
rows0,side0=rec(0,False); rows1,side1=rec(1,True); context={'artifacts':rows0+rows1}; sides=[side0,side1]
validate_envelope_batch(context['artifacts'])
terms_discrepancy={'formal-reading':'Iff.rfl','probe':'''by
  constructor
  · intro x hx
    exact Nat.le_zero.mp hx
  · intro h
    exact Nat.noConfusion (h 1)'''}
terms_control={'formal-reading':'Iff.rfl','probe':'by\n  intro h x hx\n  exact h x'}
cases=[('discrepancy','counterexample','right-to-left',terms_discrepancy),('control','implication','left-to-right',terms_control)]
summary=[]
for label,kind,direction,terms in cases:
    request={'repoRoot':str(repo),'context':context,'left':side0,'right':side1,'template':{'familyId':'restricted-domain','version':'restricted-domain-v2','kind':kind,'direction':direction},'deadlineMonotonic':deadline,'limits':limits}
    planned=plan_application_probe(request); (p/f'{label}-planned.json').write_text(json.dumps(planned,sort_keys=True,indent=2)); assert planned['status']=='planned',planned
    validate_envelope_batch([*context['artifacts'],planned['artifact']])
    checked=check_application_probe(request,planned['planId'],terms); (p/f'{label}-checked.json').write_text(json.dumps(checked,sort_keys=True,indent=2))
    accepted=[]
    for goal in checked['goals']:
        evidence=goal.get('result')
        if evidence:
            raw=load_goal_evidence(repo,evidence)
            assert _accepted_check(raw) == (goal['status']=='checked-support'),(label,goal['goalId'],goal['status'])
            if _accepted_check(raw): accepted.append(goal['goalId'])
    assert len(accepted)==2,(label,checked.get('diagnostic'),checked['goals'])
    assert checked['artifact']['payload']['checkRunRefs']==[] and all(g['status']=='open' for g in checked['artifact']['payload']['result']['goals'])
    summary.append({'case':label,'acceptedGoals':accepted,'status':checked['status'],'elapsed':time.monotonic()-started})
    print(label,accepted,checked['status'],flush=True)
result={'status':'PASS','elapsedSeconds':time.monotonic()-started,'budgetSeconds':1800,'limits':limits,'summary':summary,'scope':'constructed exact Nat zero-guard source-bound discrepancy and valid unrestricted-to-restricted control; no paper or natural-language detection claim'}
(p/'RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)); print(json.dumps(result,sort_keys=True),flush=True)
