import copy,hashlib,json,os,shutil,sys
from pathlib import Path
from ladon.child_acceptance import canonical_digest,content_digest
from ladon.integration_acceptance import evaluate_integration_gate
root=Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s/full-qualification');bundle=root/'integration-bundle-r46';candidate=Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s/candidate');runtime=sys.argv[1]
receipts={role:json.loads((bundle/f'{role}-receipt.json').read_text()) for role in ('correctness','authority','integration')};inventories={role:json.loads((candidate/f'openspec/changes/ladon-authority-safe-verified-discovery-umbrella/children/{role}-acceptance-inventory.json').read_text()) for role in receipts}
def evaluate(rs):return evaluate_integration_gate(rs['integration'],rs['correctness'],rs['authority'],bundle_root=bundle,inventories=inventories)
result=evaluate(receipts);assert result['status']=='passed';(root/f'integration-validation-r46-{runtime}.json').write_text(json.dumps(result,indent=2)+'\n')
mutations=['missing-gate','duplicate-gate','failed-exit','changed-command','wrong-candidate','wrong-wheel','wrong-cwd','unknown-record-field','missing-supported-runtime','partial-child']
records=[]
for mutation in mutations:
 rs=copy.deepcopy(receipts);receipt=rs['integration']
 if mutation=='missing-gate':receipt['integrationPrerequisiteArtifactRefs'].pop()
 elif mutation=='duplicate-gate':receipt['integrationPrerequisiteArtifactRefs'][-1]=receipt['integrationPrerequisiteArtifactRefs'][0]
 elif mutation=='missing-supported-runtime':receipt['resultArtifactRefs'].pop()
 elif mutation=='partial-child':
  rs['correctness']['analysisCompleteness']='partial';rs['correctness'].pop('receiptIdentity');rs['correctness']['receiptIdentity']=canonical_digest(rs['correctness'])
 else:
  old=receipt['integrationPrerequisiteArtifactRefs'][0];row=json.loads((bundle/'objects'/old[7:]).read_text())
  if mutation=='failed-exit':row['exitCode']=1
  elif mutation=='changed-command':row['argv'][-1]='HEAD'
  elif mutation=='wrong-candidate':row['candidateCommit']='c'*40
  elif mutation=='wrong-wheel':row['wheelDigest']='sha256:'+'d'*64
  elif mutation=='wrong-cwd':row['workingDirectory']='/other-candidate'
  elif mutation=='unknown-record-field':row['unlock']=True
  data=json.dumps(row,sort_keys=True,separators=(',',':')).encode();ref=content_digest(data);path=bundle/'objects'/ref[7:]
  if not path.exists():path.write_bytes(data)
  else:assert path.read_bytes()==data
  receipt['integrationPrerequisiteArtifactRefs'][0]=ref;receipt['evidenceFiles'].append({'digest':ref,'path':'objects/'+ref[7:]})
 receipt.pop('receiptIdentity');receipt['receiptIdentity']=canonical_digest(receipt)
 try:evaluate(rs)
 except ValueError as error:records.append({'case':mutation,'status':'rejected','reason':str(error)})
 else:raise AssertionError('integration accepted '+mutation)
(root/f'integration-mutations-r46-{runtime}.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps({'status':'passed','runtime':runtime,'actualBundleMutationsRejected':len(records),'qualification':result['candidateCommit']}))
