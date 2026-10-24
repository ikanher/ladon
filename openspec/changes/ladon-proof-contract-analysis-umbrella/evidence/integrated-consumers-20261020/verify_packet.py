"""Read-only verification of the integrated-consumer qualification evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tarfile
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    base = Path(__file__).resolve().parent
    manifest = json.loads((base / 'MANIFEST.json').read_text())
    total = 0
    for row in manifest['files']:
        data = (base / row['path']).read_bytes()
        assert digest(data) == row['sha256'], row['path']
        assert len(data) == row['bytes'], row['path']
        total += len(data)
    assert manifest['entries'] == len(manifest['files'])
    assert manifest['bytes'] == total
    for name, archive_name in [('RUNTIME.json', 'runtime.tar.gz'),
                               ('SUPPLEMENTAL-INPUTS.json', 'supplemental-inputs.tar.gz'),
                               ('EXTERNAL-REGRESSION-INPUTS.json', 'external-regression-inputs.tar.gz'),
                               ('INTERRUPTED-CASE.json', 'interrupted-case.tar.gz')]:
        rows = json.loads((base / name).read_text())['files']
        with tarfile.open(base / archive_name) as archive:
            assert set(archive.getnames()) == {r['path'] for r in rows}
            for row in rows:
                data = archive.extractfile(row['path']).read()
                assert digest(data) == row['sha256'], row['path']
                assert len(data) == row['bytes'], row['path']
    wheel = json.loads((base / 'WHEEL.json').read_text())
    wheel_path = base / wheel['wheel']
    assert digest(wheel_path.read_bytes()) == wheel['sha256']
    expected = {r['path'].removeprefix('src/'): r['sha256']
                for r in json.loads((base / 'RUNTIME.json').read_text())['files']
                if r['path'].startswith('src/ladon/')}
    with zipfile.ZipFile(wheel_path) as archive:
        members = {n for n in archive.namelist() if n.startswith('ladon/') and not n.endswith('/')}
        assert members == set(expected)
        for name in members:
            assert digest(archive.read(name)) == expected[name], name
    print(f"PASS: {manifest['entries']} packet files ({total} bytes), all input archives and wheel verified")


if __name__ == '__main__':
    main()
