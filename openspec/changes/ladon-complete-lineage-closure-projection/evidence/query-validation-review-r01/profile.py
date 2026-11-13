from argparse import Namespace
from pathlib import Path
import json,time
import ladon.proof_search_index as idx
import ladon.theorem_lineage_cli as cli
out=Path('/home/codex/projects/ladon/temp/lineage-validation-review-r01')
rows=[]
def timed(fn,label):
 def call(*a,**kw):
  start=time.monotonic()
  try:return fn(*a,**kw)
  finally:rows.append({'stage':label,'seconds':round(time.monotonic()-start,6)})
 return call
idx.capture_repository_snapshot=timed(idx.capture_repository_snapshot,'capture')
cli.capture_repository_snapshot=idx.capture_repository_snapshot
for key in ['_database_counts','_stored_sources','database_storage_accounting','schema_lookup_indexes','schema_index_columns','schema_query_surfaces','schema_foreign_keys']:
 setattr(idx,key,timed(getattr(idx,key),key))
cli.inspect_proof_search_index=timed(idx.inspect_proof_search_index,'full_inspection_inclusive')
cli._closure_status=timed(cli._closure_status,'closure_lookup')
args=Namespace(repo_root='/home/codex/projects/lean/matrix-factorization',index=None,history=None,refresh='never',theorem='Mf.DP.pSamplingOperator_ofDPEventBound_le_classicalSubsamplingEventBoundWitness',view='summary',max_database_mib=1536,max_rss_mib=12288,timeout=120,format='json',output=str(out/'result.json'),max_output_bytes=1048576)
start=time.monotonic()
try:
 code=cli.run_lineage_command(args)
finally:
 report={'elapsedSeconds':round(time.monotonic()-start,6),'stages':rows,'query':vars(args)}
 (out/'profile.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'exit':code,**report},indent=2))
