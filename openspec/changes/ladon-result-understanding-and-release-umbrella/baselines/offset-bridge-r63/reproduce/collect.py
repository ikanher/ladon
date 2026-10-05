from pathlib import Path
import hashlib,json,shutil,re
from ladon.result_assessments import validate_result_assessments
root=Path.cwd();state=root/'.codex/state/offset-bridge-r63';run=Path((state/'run-path').read_text().strip());out=root/'openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/offset-bridge-r63';out.mkdir(exist_ok=True)
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for arm in ['ordinary','augmented']:
 folder=run/'sessions'/arm
 for p in folder.rglob('*'):
  if p.is_file():copy(p,out/'sessions'/arm/p.relative_to(folder))
 summary=json.loads((folder/'summary.json').read_text());before=json.loads((folder/'before.json').read_text());after=json.loads((folder/'after.json').read_text());commands=json.loads((folder/'commands.json').read_text());assert not summary['parseErrors']
 calls=[c for c in commands if re.search(r'\bladon\s',c['command'])];semantic=[c for c in calls if '--help' not in c['command']]
 records.append({**summary,'ladonCommandCount':len(calls),'ladonSemanticCommandCount':len(semantic),'originalTargetSha256':before['source']['Bridge.lean']['sha256'],'finalSourceSha256':after['source']['Bridge.lean']['sha256'],'originalSignatureUnchanged':True,'observedResult':'Checked offset bridge; standard permitted axioms; original conditions intact'})
for name in ['reader-protocol.json','preflight.json','replay-summary.json']:copy(state/name,out/name)
for n in ['manifest.json','guide.json','assessments.json','exposition.tex','IntendedTarget.lean','source-inventory.json','original-claim.txt']:copy(run/'shared'/n,out/'fixture'/n)
for arm in ['ordinary','augmented']:
 for p in (run/'root-replay-v2'/arm).iterdir():
  if p.suffix!='.olean':copy(p,out/'root-replay'/arm/p.name)
# Preserve actual source owners needed to inspect the specialization, not the full population.
for n in ['PoissonFixedEpochAsymptotics','PoissonFixedEpochRate','PoissonFixedEpochVariance','FixedParticipationGaussianCalibrationAsymptotics','FixedParticipationGaussianCalibration','FixedParticipationRate','GaussianCriticalScale']:
 copy(run/'shared/source/Mf/DP'/(n+'.lean'),out/'lean-source/Mf/DP'/(n+'.lean'))
for n in ['lean-toolchain','lakefile.toml','lake-manifest.json']:copy((root/'../lean/matrix-factorization').resolve()/n,out/'lean-source'/n)
for n in ['prepare_bridge.py']:copy(root/'.codex/state/returned-r05-review'/n,out/'reproduce'/n)
for n in ['preflight.py','read_one.py','session_exec.py','replay.py','replay-v1.py','collect.py']:copy(state/n,out/'reproduce'/n)
# A root-authored minimal conventional exposition revision, after both original sessions.
old=(out/'fixture/exposition.tex').read_text();paragraph='The exact profile limit is inverted by bracketing the calibrated noise between\n$\\Delta/(\\sqrt{2\\log T}+s_{E,\\delta}\\pm\\eta)$ for each $\\eta>0$.\nThe general profile limit and this inversion are proved in the appendix.'
assert paragraph in old
addition=''' For $T\\geq E$, the capped schedule has
$q_T=\\min(1,E/T)=E/T$, and its calibrated standard deviation is exactly
$\\sigma_{E,T}$. Specializing the general offset theorem to this schedule and
writing $T=E+k$, $k\\in\\mathbb{N}$, therefore gives the displayed offset limit.'''
new=old.replace(paragraph,paragraph+addition,1);(out/'exposition-offset-r63.tex').write_text(new)
(out/'paragraph-original.txt').write_text(paragraph+'\n');(out/'paragraph-revised.txt').write_text(paragraph+addition+'\n')
manifest=json.loads((out/'fixture/manifest.json').read_text());assessment=json.loads((out/'fixture/assessments.json').read_text());leading=next(v for v in assessment['assessments'] if v['id']=='component-assessment-11');original_leading=json.dumps(leading,sort_keys=True)
row=next(v for v in assessment['assessments'] if v['id']=='component-assessment-10');row['kind']='source-correspondence';row['author']={'id':'OpenAI Codex, root agent r63','kind':'model'}
row['basis']='Attributed correspondence assessment supported by fresh ordinary Lean compilation of the unchanged fixed-E offset target in root-replay/ordinary/Bridge.lean and root-replay/augmented/Bridge.lean. Both source-bound replay receipts report only propext, Classical.choice and Quot.sound. This is not canonical ProofIR resolution or independent human review.'
row['differences']=['The general mapped theorem remains a schedule theorem; the separately checked adapter identifies capped rate and exact calibrated stddev at T=E+extra, translates sqrt/log and the explicit quantile. Prose rendering and strategy correspondence remain attributed. No leading-component promotion.']
row['evidenceRefs']=[sha(out/'root-replay'/a/'receipt.json')+'#OffsetBridge.fixedEpochOffsetBridge' for a in ['ordinary','augmented']]
assert json.dumps(leading,sort_keys=True)==original_leading
validate_result_assessments(assessment,manifest);save(out/'assessments-offset-r63.json',assessment)
save(out/'coverage-change.json',{'claimId':'thm:smallbatch','componentId':'offset','historicalCompanion':'fixture/assessments.json','updatedCompanion':'assessments-offset-r63.json','historicalKind':'reported-implication-without-checked-adapter','newKind':'source-correspondence','originalClaimRevision':row['claimRevision'],'mappedGenericTargetRevisionsUnchanged':row['targetRevisions'],'checkedAdapterSourceDigests':{a:sha(out/'root-replay'/a/'Bridge.lean') for a in ['ordinary','augmented']},'newCanonicalTargetResolution':False,'correspondence':'root model-attributed, not independent certification','leadingAssessmentByteContentUnchanged':True,'wholeClaimCoveragePromoted':False,'expositionOriginalSha256':sha(out/'fixture/exposition.tex'),'expositionRevisedSha256':sha(out/'exposition-offset-r63.tex'),'manuscriptEditedInNeighbor':False})
save(out/'acceptance.json',{'sessions':records,'rootReplay':json.loads((state/'replay-summary.json').read_text()),'mathematicalOutcome':'Both original-signature offset bridges checked without new premises or disallowed axioms','productOutcome':'No concrete Ladon contribution observed. One augmented help command, no semantic operation; both consumed common curation. Consolidate standalone surfaces; no third uptake challenge. Artifact workflow benefit unmeasured.','readerRetries':0,'interventions':[],'rootActionsAfterReaders':'Two independent compiler replays and attributed component assessment/paragraph revision; no proof repairs to reader artifacts','preparationLimits':['Scaffold lacked closing unnamed-section end; both repaired it. Import preflight passed but scaffold was not compiled before sessions.','Prompt mistakenly named proof-search complete instead of proof-search goal complete; no attempt used that erroneous pointer. This limits claims about accessibility and command non-use.','Reader environment supplied compiled roots; ordinary initially shadowed compiled paths with sources and tried a Lake build; all attempts retained.','Recorder inventories declared task/output directories; /tmp inspection copies and nested session operations remain command text, not universal filesystem monitoring.','First root replay failed because source outside cwd violated compiler root; v2 changed cwd only and checked unchanged saved proof sources.','Root authored conventional paragraph revision after readers; not an independent reader or human judgment.'],'umbrellaTasks':{'done':33,'total':50,'task9.1':'open'},'installedAugmentedCandidate':'3806c436fe68e4d5700646b649b6a6525ec14ba0','maintenanceCandidateSeparate':True})
(out/'resources.csv').write_text('session,seconds,peak_tree_rss_bytes,ladon_commands,ladon_semantic_commands\n'+''.join(f"{v['name']},{v['seconds']},{v['peakTreeRssBytes']},{v['ladonCommandCount']},{v['ladonSemanticCommandCount']}\n" for v in records))
print(json.dumps({'output':str(out),'sessions':len(records),'peakGiB':max(v['peakTreeRssBytes'] for v in records)/2**30}))
