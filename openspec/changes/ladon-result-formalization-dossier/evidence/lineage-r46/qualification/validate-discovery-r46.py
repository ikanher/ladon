import copy,json,sys
from pathlib import Path
from ladon.child_acceptance import canonical_digest,content_digest,validate_child_bundle
root=Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s/full-qualification');bundle=root/'integration-bundle-r46';candidate=Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s/candidate')
receipt=json.loads((bundle/'discovery-receipt.json').read_text());inventory=json.loads((candidate/'openspec/changes/ladon-authority-safe-verified-discovery-umbrella/children/discovery-acceptance-inventory.json').read_text())
validate_child_bundle(receipt,bundle_root=bundle,inventory=inventory)
records=[]
for damage in ['missing-observation','host-namespace','nonloopback','reachable-ipv4','missing-ipv6']:
 r=copy.deepcopy(receipt);old=r['resultArtifactRefs'][0];result=json.loads((bundle/'objects'/old[7:]).read_text());observation=result['networkIsolation']
 if damage=='missing-observation':result.pop('networkIsolation')
 elif damage=='host-namespace':observation['namespace']=result['hostNetworkNamespace']
 elif damage=='nonloopback':observation['interfaces']=['lo','eth0']
 elif damage=='reachable-ipv4':observation['connectErrors']['ipv4']=0
 elif damage=='missing-ipv6':observation['connectErrors'].pop('ipv6')
 data=json.dumps(result,sort_keys=True,separators=(',',':')).encode();ref=content_digest(data);(bundle/'objects'/ref[7:]).write_bytes(data) if not (bundle/'objects'/ref[7:]).exists() else None
 r['resultArtifactRefs'][0]=ref;r['commands'][0]['evidenceDigest']=ref;r['evidenceFiles'].append({'digest':ref,'path':'objects/'+ref[7:]});r.pop('receiptIdentity');r['receiptIdentity']=canonical_digest(r)
 try:validate_child_bundle(r,bundle_root=bundle,inventory=inventory)
 except ValueError as error:records.append({'case':damage,'status':'rejected','reason':str(error)})
 else:raise AssertionError(damage)
report={'status':'passed','runtime':sys.argv[1],'receiptIdentity':receipt['receiptIdentity'],'networkMutations':records}
(root/('discovery-validation-r46-'+sys.argv[1]+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
