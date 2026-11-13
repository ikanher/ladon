from pathlib import Path
import json,time,sqlite3
from ladon.proof_search_history import history_status
from ladon.proof_search_history_store import read_history
p=Path('/home/codex/projects/lean/matrix-factorization/.ladon/index/proof-search.sqlite')
with sqlite3.connect(f'{p.as_uri()}?mode=ro',uri=True) as c: rows=read_history(c)
start=time.monotonic(); result=history_status(p,rows); elapsed=time.monotonic()-start
body={'stage':'history_status','seconds':elapsed,'registeredSnapshots':len(rows),'registeredBytes':sum(r['bytes'] for r in rows),'result':result}
Path('/home/codex/projects/ladon/temp/lineage-validation-review-r01/history-profile.json').write_text(json.dumps(body,indent=2)+'\n')
print(json.dumps(body))
