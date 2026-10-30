"""One balanced follow-up to the predeclared 1.25 timing review threshold."""
import json
import sqlite3
import statistics
import time
from pathlib import Path
from ladon.idea_migration import OBSERVATIONS

report=json.loads(Path('temp/idea-history-baseline/real-index-final-report.json').read_text())
left=sqlite3.connect(report['backupPath'])
right=sqlite3.connect(report['indexPath'])
results={}
for name,sql in OBSERVATIONS.items():
    plans=[db.execute('EXPLAIN QUERY PLAN '+sql).fetchall() for db in (left,right)]
    for _ in range(5):
        left.execute(sql).fetchall()
        right.execute(sql).fetchall()
    samples=[[],[]]
    for round_no in range(51):
        for index in ((0,1) if round_no%2==0 else (1,0)):
            db=(left,right)[index]
            start=time.perf_counter()
            for _ in range(5):
                db.execute(sql).fetchall()
            samples[index].append((time.perf_counter()-start)/5)
    medians=[statistics.median(row) for row in samples]
    results[name]={'beforeMedianSeconds':medians[0],'afterMedianSeconds':medians[1],
                   'medianRatio':medians[1]/medians[0], 'identicalQueryPlan':plans[0]==plans[1],
                   'samples':samples}
left.close();right.close()
Path('temp/idea-history-baseline/timing-review.json').write_text(json.dumps(results,indent=2))
print(json.dumps({name:{k:v for k,v in row.items() if k!='samples'} for name,row in results.items()},indent=2))
