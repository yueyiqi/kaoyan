"""Drill into the frozen authority: table/column/index/FK metadata and row counts."""
from contextlib import closing
import hashlib
import json
import sqlite3
import zipfile
from remote import BASE

archive=zipfile.ZipFile(BASE/'scratchpad/authority.zip')
raw=archive.read('production.sqlite3')
path=BASE/'scratchpad/metadata.sqlite3';path.write_bytes(raw);path.chmod(0o600)
tables=[]
with closing(sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)) as conn:
    conn.row_factory=sqlite3.Row
    assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    for record in conn.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        name=record['name'];quoted='"'+name.replace('"','""')+'"'
        tables.append({'name':name,'ddl':record['sql'],
            'rows':conn.execute('SELECT COUNT(*) FROM '+quoted).fetchone()[0],
            'columns':[dict(r) for r in conn.execute('PRAGMA table_info('+quoted+')')],
            'foreign_keys':[dict(r) for r in conn.execute('PRAGMA foreign_key_list('+quoted+')')],
            'indexes':[dict(r) for r in conn.execute('PRAGMA index_list('+quoted+')')]})
    violations=[tuple(r) for r in conn.execute('PRAGMA foreign_key_check')]
result={'status':'PASS','scope':'frozen production authority, before W1 cutover','database_bytes':len(raw),
        'sha256':hashlib.sha256(raw).hexdigest(),'table_count':len(tables),
        'column_count':sum(len(t['columns']) for t in tables),'tables':tables,
        'foreign_key_violations':violations,'user_row_values_exported':False}
(BASE/'physical_schema.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='tables'},ensure_ascii=False))
assert not violations,'Foreign key integrity failures require investigation'
