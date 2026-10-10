import sqlite3, json, sys
pairs=[('fixture','clean-fixture'),('adam','clean-adam')]
fields='name candidate_name name_casefold name_segments namespace kind module package path line column_number start_offset end_offset block_sha256 type_text type_text_bytes type_text_truncated type_status authority privacy locality structure_name doc_text rendered_type conclusion_text fingerprint head arity is_proposition semantic_status helper_identity lean_identity'.split()
for left,right in pairs:
    a=sqlite3.connect(f'temp/index-history-field/{left}/.ladon/index/proof-search.sqlite')
    b=sqlite3.connect(f'temp/index-history-field/{right}/.ladon/index/proof-search.sqlite')
    tables={}
    for table,cols in [('modules','name path package generated source_sha256 source_bytes line_count evidence_status'.split()),('declarations',fields),('module_imports','source target line column_number authority'.split())]:
        def read(conn):
            names=','.join('"'+c+'"' for c in cols)
            return conn.execute(f'SELECT {names} FROM {table} ORDER BY '+','.join('"'+c+'"' for c in cols)).fetchall()
        x,y=read(a),read(b)
        tables[table]={'candidateRows':len(x),'cleanRows':len(y),'equal':x==y}
        if x!=y:
            import itertools
            tables[table]['firstDifference']=next(((i,l,r) for i,(l,r) in enumerate(itertools.zip_longest(x,y)) if l!=r),None)
    print(json.dumps({'candidate':left,'clean':right,'tables':tables},default=str))
    if not all(v['equal'] for v in tables.values()): sys.exit(1)
