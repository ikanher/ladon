import hashlib,json,shutil,tarfile,xml.etree.ElementTree as ET
from pathlib import Path
p=Path('openspec/changes/ladon-proof-contract-bidirectional/evidence/ROUTE-CONTEXT-20261018')
def load(n):return json.loads((p/n).read_text())
def save(n,v):(p/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
source=load('source-verification.json');status=load('integration-status.json');assert source['status']=='PASS' and status['exitCode']==0
xml=ET.parse(p/'integration.xml').getroot();cases=xml.findall('.//testcase');owners={'.'.join(c.attrib['classname'].split('.')[:2]) for c in cases}
assert not any(xml.findall('.//'+kind) for kind in ('failure','error','skipped'))
files=[x for x in load('integration-command.json')['commandVector'] if x.startswith('tests/')]
assert len(owners)==len(files) and len(cases)>=1015,(len(cases),len(owners),len(files))
assert all(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256'] for row in load('RUNTIME.json')['files'])
assert all(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256'] for row in load('TESTS.json')['files'])
assert 'strict quality: PASS' in (p/'quality.log').read_text() and 'All checks passed!' in (p/'ruff.log').read_text()
assert load('reviews/RAW-CUSTODY.json')['status']=='PASS'
verification={'status':'PASS','tests':len(cases),'testOwnerFiles':len(owners),'baselineTests':964,'baselineOwners':150,'newChecks':len(cases)-964,'newTestFiles':len(owners)-150,'initialRed':30,'additionalRed':8,'remainingNewChecks':'green regressions','failures':0,'errors':0,'skips':0,'regressionSeconds':status['elapsedSeconds'],'runtimeEntries':500,'runtimeLiveAndArchiveHashesMatch':True,'rawEvidenceVerified':True,'sourceControls':'source-verification.json','detectionBenefit':'unmeasured','heldOutCAdmittedCases':0,'beamPolicy':'none','wholeMethodAuthority':'none','taskProgress':{'bidirectional':'8/8','umbrella':'2/12'}}
save('verification.json',verification)
rows=['| Constructed control | Result | Checked / required | Check wall time |','|---|---|---|---|']
for name,v in source['cases'].items():rows.append(f"| {name} | {v['status']} | {v['checked']} / {v['goals']} | {v['elapsedSeconds']:.2f} seconds |")
controls='\n'.join(rows)+f"\n\nThe complete serial source driver passed in **{source['acceptance']['elapsedSeconds']:.2f} / 1,200 seconds**, including fresh native production/extraction, public CLI planning/checking, absent-assumption/excluded-parent/closed-reading controls, changed reading/provider/rule/order/checkpoint rejection, two pre-worker deadline stops and the deliberate last 1 MiB memory stop. All 13 positive goals have accepted independent replay and trust; the middle case checks only its original reading and leaves the transfer and final requirement unresolved. See [acceptance](acceptance.json), [log](acceptance.log) and [source verification](source-verification.json)."
resources=f"The final runtime has **500 files**, all matching the live checkout and frozen archive. Maximum sampled source process-tree RSS was **{source['maximumSampledRssBytes']:,} bytes ({source['maximumSampledRssBytes']/1024**3:.2f} GiB)**. The positive compact response is **{source['cases']['positive']['bytes']:,} bytes**, below 8 MiB. All **{source['rawEvidenceFiles']}** referenced raw evidence files match their hashes, projections and captured subjects. Only the deliberate last memory control has a true resource-limit flag. Source bytes are unchanged."
regression=f"The full relevant suite passed **{len(cases)} tests across {len(owners)} files** in **{status['elapsedSeconds']:.2f} seconds**, with no failures, errors or skips. Every prior 964-test / 150-file owner remains included. This adds {len(cases)-964} checks across {len(owners)-150} files; it is coverage growth, not a detection-benefit measurement. Repository-wide strict quality, no-cache Ruff, frozen-test verification and strict child/umbrella OpenSpec validation pass. See [command](integration-command.json), [log](integration.log), [JUnit](integration.xml), [status](integration-status.json) and [verification](verification.json)."
reviews='Independent source reviews are preserved in [reviews](reviews/FINAL-SOURCE-AUDIT.json), including [timeout follow-up](reviews/FOLLOWUP-597.json), [output-capacity finding](reviews/FOLLOWUP-600.json) and [typed-overflow follow-up](reviews/FOLLOWUP-602.json). The separate [raw custody review](reviews/RAW-CUSTODY.json) verifies final source evidence, runtime identity, bounds and local-only support. The root owns final integration and regression acceptance.'
draft=(p/'REPORT-TEMPLATE.md').read_text()
for key,value in {'@@CONTROLS@@':controls,'@@RESOURCES@@':resources,'@@REGRESSION@@':regression,'@@REVIEWS@@':reviews}.items():assert draft.count(key)==1;draft=draft.replace(key,value)
(p/'REPORT.md').write_text(draft)
print(json.dumps(verification,indent=2))
