"""Fresh original-provider observations through ordinary source and expansion CLIs."""
import hashlib
import json
import shutil
import sys
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from time import monotonic

from support.proof_contract_planned_source import build_plan_request

from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.proof_contract_obligation_artifacts import obligations_artifact
from ladon.proof_contract_provider_expansion import expand_obligation_provider
from ladon.proof_contract_source_obligations import _runner


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        stream.write('\n')


def cli(out, name, args, deadline):
    result = run_bounded_target_process([sys.executable,'-m','ladon.entrypoint',
        'investigation','contract',*args],cwd=Path.cwd(),
        env=__import__('os').environ.copy(),timeout_seconds=min(60,deadline-monotonic()),
        max_output_bytes=8388608,max_rss_bytes=12884901888)
    save(out/(name+'-process.json'),asdict(result))
    assert not (result.timed_out or result.memory_limited or result.output_limited),asdict(result)
    return result


def api_case(out,name,request):
    save(out/(name+'-input.json'),request)
    result=expand_obligation_provider(request)
    save(out/(name+'-result.json'),result)
    print(name,result['status'],result['diagnostic'],flush=True)
    return result


def main():
    out=Path(sys.argv[1]).resolve()
    root=Path(sys.argv[2]).resolve()
    root.mkdir(parents=True,exist_ok=False)
    fixture=Path('tests/fixtures/proof_contract_planned_source')
    for name in ('ThreeSteps.lean','lean-toolchain'):
        shutil.copyfile(fixture/name,root/name)
        shutil.copyfile(fixture/name,out/name)
    original=(root/'ThreeSteps.lean').read_bytes()
    started=monotonic();deadline=started+180
    snapshots={}
    for name in ('firstBound','secondBound','thirdBound','alternateBound','endpoint'):
        snapshots[name]=produce_formal_snapshot(root,'ThreeSteps.lean','ThreeSteps',
            'ThreeSteps.'+name,timeout_seconds=30,runner=_runner(deadline))
        assert snapshots[name]['status']=='extracted',snapshots[name]
        save(out/(name+'-snapshot.json'),snapshots[name])
    plan=build_plan_request(snapshots)
    analysis=obligations_artifact(plan,analysis_id='analysis:provider-expansion-acceptance')
    context={'artifacts':[plan.derivation_artifact,*[
        a for snapshot in snapshots.values() for a in snapshot['artifacts']]]}
    save(out/'analysis.json',analysis);save(out/'context.json',context)
    sources={'parentSnapshot':snapshots['endpoint'],
        'parentReadingId':plan.desired_reading_identity['readingId'],'providers':[]}
    save(out/'sources.json',sources)
    process=cli(out,'missing-providers',['check-obligations','--input',str(out/'analysis.json'),
        '--context',str(out/'context.json'),'--sources',str(out/'sources.json'),
        '--root',str(root),'--output-dir',str(out/'missing-source-run'),
        '--timeout-seconds','120'],deadline)
    assert process.returncode==0,process.stdout
    summary=json.loads((out/'missing-source-run/summary.json').read_text())
    requests=summary['providerSliceRequests']
    assert len(requests)==4,len(requests)
    selected=next(r for r in requests if r['sourceSelection']['declaration']=='ThreeSteps.firstBound')
    assert all(r['status']=='not-dispatched' for r in requests)
    save(out/'selected-provider-request.json',selected)
    limits={'timeout_seconds':30,'max_rss_bytes':12884901888,'max_output_bytes':8388608}
    request={'repoRoot':str(root),'analysisArtifact':analysis,'context':context,
        'providerSliceRequest':selected,'application':'Eq.trans','occurrence':0,
        'deadlineMonotonic':deadline,'limits':limits}
    process=cli(out,'positive',['expand-provider','--input',str(out/'analysis.json'),
        '--context',str(out/'context.json'),'--request',str(out/'selected-provider-request.json'),
        '--root',str(root),'--application','Eq.trans','--timeout-seconds','60',
        '--output',str(out/'positive-result.json')],deadline)
    assert process.returncode==0,process.stdout
    positive=json.loads((out/'positive-result.json').read_text())
    assert positive['status']=='observed',positive['diagnostic']
    assert positive['slice']['complete'] is True
    assert positive['slice']['source']['path']=='ThreeSteps.lean'
    assert positive['slice']['selection']['declaration']=='ThreeSteps.firstBound'
    assert positive['slice']['selection']['application']=='Eq.trans'
    missing=deepcopy(request);missing['application']='Nat.le_refl'
    unavailable=api_case(out,'missing-application',missing)
    assert unavailable['status']=='incomplete'
    assert unavailable['slice']['complete'] is False
    stale=original+b'\n-- Deliberate stale-source negative control.\n'
    try:
        (root/'ThreeSteps.lean').write_bytes(stale)
        (out/'stale-source.lean').write_bytes(stale)
        drift=api_case(out,'stale-source',deepcopy(request))
        assert drift['status']=='rejected'
        assert drift['slice'] is None
    finally:
        (root/'ThreeSteps.lean').write_bytes(original)
    forged=deepcopy(request)
    forged['providerSliceRequest']['binding']['desiredReadingIdentity']['readingId']='forged'
    rejected=api_case(out,'forged-reading',forged)
    assert rejected['status']=='rejected' and 'worker' not in rejected
    expired=deepcopy(request);expired['deadlineMonotonic']=monotonic()-1
    stopped=api_case(out,'expired',expired)
    assert stopped['status']=='incomplete' and 'nativeValidation' not in stopped
    low=deepcopy(request);low['limits']['max_rss_bytes']=1024**2
    memory=api_case(out,'memory-stop',low)
    assert memory['status']=='incomplete' and memory['memoryReportBackRequired'] is True
    assert 'Stop progress and report back to user' in memory['diagnostic']['message']
    assert 'worker' not in memory
    for result in (positive,unavailable,drift,rejected,stopped,memory):
        assert result['wholeMethodAuthority']=='none'
        assert result['mathematicalFalsity']=='not-established'
        assert result['demandDischarged'] is False
    assert positive['unresolvedDemand']==selected['binding']['demand']
    assert positive['coverage']['proofBody']=='incomplete'
    assert (root/'ThreeSteps.lean').read_bytes()==original
    save(out/'acceptance.json',{'missingProviderRequests':len(requests),
        'positiveStatus':positive['status'],'absentApplication':unavailable['status'],
        'staleSource':drift['status'],'forgedReading':rejected['status'],
        'expiry':stopped['status'],'actualMemoryStop':memory['status'],
        'elapsedSeconds':monotonic()-started,'budgetSeconds':180,
        'sourceRestoredAndUnchanged':True,'originalSourceSha256':hashlib.sha256(original).hexdigest(),
        'demandDischarged':False,'wholeMethodAuthority':'none','detectionBenefit':'unmeasured'})


if __name__=='__main__':
    main()
