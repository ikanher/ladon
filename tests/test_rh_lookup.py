from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import rh_lookup


def test_snapshot_replay_with_partial_identifier_and_bad_source(tmp_path, monkeypatch):
    sources = tmp_path / "sources"
    sources.mkdir()
    index = tmp_path / "index.sqlite"
    signature = "LongPrefix.sqrt |S.det|Suffix"
    files = {"Integral.lean": signature, "Scoped.lean": "lemma scoped : True", "Other.lean": "ℝ"}
    digests = {name: hashlib.sha256(body.encode()).hexdigest() for name, body in files.items()}
    for path, data in files.items():
        (sources / path).write_text(data)
    manifest = tmp_path / "example.json"
    manifest.write_text(json.dumps({p: digests[p] for p in ("Integral.lean", "Scoped.lean")}))
    monkeypatch.setattr(rh_lookup, "EXAMPLE", manifest)
    monkeypatch.setattr(rh_lookup, "PATTERN", "Prefix.SQRT |S.det|Suf")
    monkeypatch.setattr(rh_lookup, "MODULE", "Scoped")
    with sqlite3.connect(index) as db:
        db.executescript("""
            CREATE TABLE metadata(key,value);
            CREATE TABLE modules(name,path,source_sha256);
            CREATE TABLE declarations(module,type_text,rendered_type,conclusion_text);
        """)
        db.execute("INSERT INTO metadata VALUES('generationIdentity',?)", (rh_lookup.GENERATION,))
        for path, text in files.items():
            module = Path(path).stem
            db.execute("INSERT INTO modules VALUES(?,?,?)", (module, path, digests[path]))
            db.execute("INSERT INTO declarations VALUES(?,?,?,?)", (module, text, text, text))
    lookup = tmp_path / "lookup.gz"
    rh_lookup.build(index, lookup)
    assert signature.encode() not in gzip.decompress(lookup.read_bytes())
    output = tmp_path / "selected"
    rh_lookup.prepare(lookup, output, rh_lookup.PATTERN, rh_lookup.MODULE, sources)
    assert sorted(file.name for file in output.iterdir()) == ["Integral.lean", "Scoped.lean"]
    assert (output / "Integral.lean").read_text() == signature

    (sources / "Scoped.lean").write_text("changed")
    with pytest.raises(ValueError, match="source checksum mismatch"):
        rh_lookup.prepare(None, tmp_path / "bad", rh_lookup.PATTERN, rh_lookup.MODULE, sources)
    assert not (tmp_path / "bad").exists()
