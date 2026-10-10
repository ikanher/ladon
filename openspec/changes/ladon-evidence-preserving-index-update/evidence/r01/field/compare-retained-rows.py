import sqlite3, json
from pathlib import Path
root=Path('temp/index-history-field/fixture/.ladon/index/proof-search.sqlite.history')
base=sqlite3.connect('temp/index-history-field/pre-row-comparison.sqlite')
def tables(c): return [r[0] for r in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name")]
def rows(c,t):
    cols=[r[1] for r in c.execute(f'pragma table_info("{t}")')]
    if not cols:return []
    q=','.join('"'+x.replace('"','""')+'"' for x in cols)
    return sorted((tuple(r) for r in c.execute(f'SELECT {q} FROM "{t}"')),key=repr)
expected=tables(base)
for archive in sorted(root.glob('*.sqlite')):
    c=sqlite3.connect(archive)
    actual=tables(c)
    mismatches=[]
    for t in sorted(set(expected)|set(actual)):
        if t not in expected or t not in actual or rows(base,t)!=rows(c,t): mismatches.append(t)
    print(json.dumps({'archive':archive.name,'tablesCompared':len(expected),'mismatches':mismatches,'equal':not mismatches}))
    c.close()
base.close()
