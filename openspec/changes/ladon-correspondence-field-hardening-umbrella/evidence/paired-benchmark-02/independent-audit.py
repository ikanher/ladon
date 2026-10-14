import hashlib, importlib.util, json, statistics, sys
from datetime import datetime, timezone
from pathlib import Path

repo=Path('/home/codex/projects/ladon')
evid=repo/'openspec/changes/ladon-correspondence-field-hardening-umbrella/evidence/paired-benchmark-02'
inputs=repo/'openspec/changes/ladon-correspondence-field-hardening-umbrella/evidence/real-cases-attempt03'
freeze=json.loads((evid/'FREEZE.json').read_text())
summary=json.loads((evid/'SUMMARY.json').read_text())
subject=json.loads((evid/'SUBJECT-EQUIVALENCE.json').read_text())
workloads={'cone':6,'numeric':6,'scoped':8}
orders=[('ordinary','request'),('request','ordinary'),('ordinary','request')]
expected={(w,i,m) for w in workloads for i,modes in enumerate(orders,1) for m in modes}
slots=[]; rows=[]; issues=[]; eq_work={}; perwork_axioms={}
for w,n in workloads.items():
  identities=[]; axsets=[]; eq_count=0; qualifications=[]
  for i in range(1,4):
    for mode in orders[i-1]:
      d=evid/w/f'trial-{i}-{mode}'
      timing=json.loads((d/'timing.json').read_text())
      checked_path=d/'checked.json'; checked=json.loads(checked_path.read_text())
      slot=(timing.get('workload'),timing.get('trial'),timing.get('requestedMode')); slots.append(slot)
      if slot!=(w,i,mode): issues.append(f'slot label {slot} expected {(w,i,mode)}')
      if timing.get('exitCode')!=0 or not timing.get('qualified') or timing.get('actualMode')!=mode: issues.append(f'{w}/{i}/{mode}: timing qualification/mode mismatch')
      if timing.get('serializedBytes')!=checked_path.stat().st_size: issues.append(f'{w}/{i}/{mode}: checked bytes mismatch')
      if timing.get('sha256')!=hashlib.sha256(checked_path.read_bytes()).hexdigest(): issues.append(f'{w}/{i}/{mode}: checked digest mismatch')
      if checked.get('preparationMode')!=mode or checked.get('parentSupport')!='supported-for-attributed-interpretation' or checked.get('residuals')!=[]: issues.append(f'{w}/{i}/{mode}: parent/mode/residual gate')
      if len(checked.get('checks',[]))!=n: issues.append(f'{w}/{i}/{mode}: check count')
      work=[]; oneax=[]
      for r in checked.get('checks',[]):
        comp=r.get('completion',{}); replay=comp.get('replay',{}); trust=comp.get('trust',{})
        axioms=trust.get('observedAxioms')
        if r.get('status')!='supported' or comp.get('status')!='completed': issues.append(f'{w}/{i}/{mode}/{r.get("obligation")}: status')
        if replay.get('status')!='accepted' or replay.get('coverage')!='complete': issues.append(f'{w}/{i}/{mode}/{r.get("obligation")}: replay')
        if trust.get('accepted') is not True or trust.get('coverage')!='complete' or trust.get('policy')!='lean-standard-no-placeholders-v1': issues.append(f'{w}/{i}/{mode}/{r.get("obligation")}: trust')
        if not isinstance(axioms,list) or 'sorryAx' in axioms or not set(axioms)<=set(trust.get('allowedAxioms',[])): issues.append(f'{w}/{i}/{mode}/{r.get("obligation")}: axioms')
        oneax.append(tuple(sorted(axioms or [])))
        typed=r.get('typedSubject',{}).get('subject',{}).get('structural')
        cap=r.get('capture',{}).get('capture',{}).get('goal',{}).get('localContext',[])
        observed=cap[0].get('typeStructural') if cap else None
        if not typed or typed!=observed: issues.append(f'{w}/{i}/{mode}/{r.get("obligation")}: typed subject/capture mismatch')
        else: eq_count+=1
        work.append((r.get('obligation'),r.get('mode'),r.get('goal'),r.get('status'),typed,tuple(sorted(axioms or []))))
      identities.append(tuple(sorted(work))); axsets.append(tuple(sorted(oneax)))
      rows.append(timing)
  eq_work[w]=len(set(identities))==1
  perwork_axioms[w]=len(set(axsets))==1
  if not eq_work[w]: issues.append(f'{w}: cross-trial/mode semantic work differs')
  if not perwork_axioms[w]: issues.append(f'{w}: per-check axiom sets differ')
if len(rows)!=18 or len(set(slots))!=18 or set(slots)!=expected: issues.append('exact 18-slot grid mismatch')
comparisons={}
for w in workloads:
  meds={m:statistics.median(r['wallSeconds'] for r in rows if r['workload']==w and r['requestedMode']==m) for m in ('ordinary','request')}
  comparisons[w]={**meds,'gain':1-meds['request']/meds['ordinary']}
if comparisons!=summary['comparisons']: issues.append('reported medians differ from recomputation')
if not summary.get('qualifiedEquivalentWork') or not summary.get('targetMet') or summary.get('trialCount')!=18: issues.append('SUMMARY gate fields disagree')
if comparisons['cone']['gain']<.30 or any(comparisons[w]['gain']<-.10 for w in ('numeric','scoped')): issues.append('threshold miss')
# Verify current frozen input/checker/harness identities from exact declared paths.
for w in workloads:
  fz=freeze['populations'][w]
  prep=inputs/w/'prepared.json'; terms=inputs/w/'terms.json'
  if hashlib.sha256(prep.read_bytes()).hexdigest()!=fz['preparedSha256']: issues.append(f'{w}: prepared hash drift')
  if hashlib.sha256(terms.read_bytes()).hexdigest()!=fz['termsSha256']: issues.append(f'{w}: terms hash drift')
  source=Path(freeze['repo'])/fz['selection']['sourceFile']
  if hashlib.sha256(source.read_bytes()).hexdigest()!=fz['sourceSha256']: issues.append(f'{w}: source hash drift')
  tool=(Path(freeze['repo'])/'lean-toolchain').read_text().strip()
  if tool!=fz['toolchainPin']: issues.append(f'{w}: toolchain drift')
  # All checked plans bind the exact population environment and compiled identities.
  c=json.loads((evid/w/'trial-1-ordinary/checked.json').read_text())
  sl=c['plan']['slice']
  if sl['environment']!=fz['environment'] or sl['compiledInventory']!=fz['compiledInventory']: issues.append(f'{w}: checked plan freeze mismatch')
# Checker and harness source identities.
spec=importlib.util.spec_from_file_location('impl',Path(freeze['repo']).parent/'ladon/src/ladon/correspondence_implementation.py')
# Prefer repository module import path, avoiding any checked-in output mutation.
sys.path.insert(0,str(Path(freeze['repo']).parent/'ladon/src'))
from ladon.correspondence_implementation import implementation_digest
if implementation_digest()!=freeze['implementationDigest']: issues.append('implementation digest drift')
harness=repo/'scripts/benchmark_correspondence_field.py'
if hashlib.sha256(harness.read_bytes()).hexdigest()!=freeze['benchmarkHarness']['sha256']: issues.append('benchmark harness hash drift')
# Per-trial measured scope, process/memory telemetry presence and output accounting.
scopes=set(); mem_scopes=set(); stage_scopes=set(); proc_counts=[]; rsses=[]
for r in rows:
  w,i,m=r['workload'],r['trial'],r['requestedMode']; c=json.loads((evid/w/f'trial-{i}-{m}'/'checked.json').read_text()); a=c['executionAccounting']
  scopes.add(a.get('concurrency')); mem_scopes.add(a.get('memoryMeasurementScope')); stage_scopes.add(a.get('stageMeasurementScope'))
  proc_counts.append(a.get('processCount')); rsses.append(a.get('peakRssBytes'))
  if not isinstance(a.get('stages'),dict) or not a.get('processes'): issues.append(f'{w}/{i}/{m}: missing stage/process accounting')
# Check explicit comparison artifact agrees with independent relations.
if subject.get('workloads') is None: issues.append('subject equivalence summary lacks workloads')
for w in workloads:
  sr=subject['workloads'][w]
  if sr.get('trials')!=6 or sr.get('checksPerTrial')!=workloads[w] or not sr.get('allClosedSubjectsEqual') or not sr.get('allObservedSubjectsMatchCapture'): issues.append(f'{w}: subject equivalence evidence fields')
print(json.dumps({'issues':issues,'slots':len(slots),'uniqueSlots':len(set(slots)),'eq_work':eq_work,'axiom_sets_stable':perwork_axioms,'typed_subject_capture_equalities':sum(1 for r in rows for x in json.loads((evid/r['workload']/f'trial-{r["trial"]}-{r["requestedMode"]}'/'checked.json').read_text())['checks'] if x['typedSubject']['subject']['structural']==x['capture']['capture']['goal']['localContext'][0]['typeStructural']),'recomputed':comparisons,'summary':summary,'accounting':{'processCountMinMax':[min(proc_counts),max(proc_counts)],'peakRssNonNull':sum(x is not None for x in rsses),'concurrencyValues':list(scopes),'memoryScopeValues':list(mem_scopes),'stageScopeValues':list(stage_scopes)}},indent=2))
