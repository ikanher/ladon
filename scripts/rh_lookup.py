"""Build or use the RH snapshot's source-free module lookup for Ladon searches."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
import zlib
from collections.abc import Iterable
from contextlib import closing
from functools import lru_cache
from itertools import groupby
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

COMMIT = "40e56bab026552e089d7afcfeff08d2defb9c005"
GENERATION = "fcde1db2b08c41dbd3d772d84f10f605fb87642e85615cfabc1345cff3cac67f"
WORDS = re.compile(rb"[a-z0-9_]+")
EXAMPLE = Path(__file__).resolve().parents[1] / "assets/rh/example-modules.json"
PATTERN = "Real.sqrt |S.det|"
MODULE = "GroundTheory.HeightsAndTheta.Heights.HeightKernels.PThetaSummandNorm"


def example_files() -> list[tuple[str, bytes]]:
    return sorted(
        (path, bytes.fromhex(digest)) for path, digest in json.loads(EXAMPLE.read_text()).items()
    )


@lru_cache(maxsize=65536)
def triple(first: bytes, second: bytes, third: bytes) -> int:
    # Collisions only add candidate modules. Ladon checks the literal on the source.
    return zlib.crc32(b" ".join((first, second, third)))


def fingerprints(words: list[bytes]) -> set[int]:
    return {triple(a, b, c) for a, b, c in zip(words, words[1:], words[2:])}


def module_fingerprints(rows: Iterable[tuple]) -> set[int]:
    hashes: set[int] = set()
    for _, _, signature, rendered, conclusion in rows:
        text = signature or ""
        if (rendered or "") != text or (conclusion or "") != text:
            raise ValueError("expected lexical signatures only")
        hashes.update(fingerprints(WORDS.findall(text.encode().lower())))
    return hashes


def build(index: Path, output: Path) -> None:
    with tempfile.TemporaryDirectory() as scratch:
        database = Path(scratch) / "lookup.sqlite"
        with (
            closing(sqlite3.connect(index.resolve().as_uri() + "?mode=ro", uri=True)) as src,
            closing(sqlite3.connect(database)) as dst,
        ):
            if src.execute(
                "SELECT value FROM metadata WHERE key='generationIdentity'"
            ).fetchone() != (GENERATION,):
                raise ValueError("expected the documented RH lexical snapshot")
            dst.executescript("""
                CREATE TABLE modules(id INTEGER PRIMARY KEY, path TEXT UNIQUE, sha256 BLOB);
                CREATE TABLE hits(fingerprint INTEGER, module INTEGER, PRIMARY KEY(fingerprint,module)) WITHOUT ROWID;
            """)
            rows = src.execute("""
                SELECT m.path,m.source_sha256,d.type_text,d.rendered_type,d.conclusion_text
                FROM modules m LEFT JOIN declarations d ON d.module=m.name ORDER BY m.name
            """)
            modules = groupby(rows, key=lambda row: row[:2])
            for module_id, ((path, digest), group) in enumerate(modules, 1):
                hashes = module_fingerprints(group)
                dst.execute(
                    "INSERT INTO modules VALUES(?,?,?)", (module_id, path, bytes.fromhex(digest))
                )
                dst.executemany(
                    "INSERT INTO hits VALUES(?,?)", ((value, module_id) for value in sorted(hashes))
                )
            if select_modules(dst, PATTERN, MODULE) != example_files():
                raise ValueError("example module list differs from checked-in snapshot")
            dst.commit()
        with tempfile.TemporaryDirectory(dir=output.parent) as staging:
            packed = Path(staging) / "lookup.gz"
            with (
                database.open("rb") as source,
                packed.open("wb") as target,
                gzip.GzipFile(fileobj=target, filename="", mode="wb", mtime=0) as compressed,
            ):
                shutil.copyfileobj(source, compressed)
            os.link(packed, output)


def select_modules(db: sqlite3.Connection, pattern: str, module: str) -> list[tuple[str, bytes]]:
    data = pattern.encode().lower()
    # An endpoint word can be only part of a source identifier. Only interior
    # whole words are guaranteed to survive a successful literal substring match.
    words = [m.group() for m in WORDS.finditer(data) if m.start() > 0 and m.end() < len(data)]
    hashes = sorted(fingerprints(words))
    if not hashes:
        raise ValueError(
            "use a type fragment with at least three complete interior ASCII words, or build the full index"
        )
    placeholders = ",".join("?" for _ in hashes)
    matches = db.execute(
        f"""
        SELECT path,sha256 FROM modules WHERE id IN (
            SELECT module FROM hits WHERE fingerprint IN ({placeholders})
            GROUP BY module HAVING count(*)=?
        )
    """,
        (*hashes, len(hashes)),
    )
    selected = dict(matches)
    scoped = db.execute(
        "SELECT path,sha256 FROM modules WHERE path=?", (module.replace(".", "/") + ".lean",)
    ).fetchone()
    if scoped is None:
        raise ValueError(f"module absent from snapshot: {module}")
    selected[scoped[0]] = scoped[1]
    return sorted(selected.items())


def lookup_files(lookup: Path | None, pattern: str, module: str) -> list[tuple[str, bytes]]:
    if lookup is None:
        if (pattern, module) != (PATTERN, MODULE):
            raise ValueError("supply --lookup for a query outside the worked example")
        return example_files()
    with tempfile.TemporaryDirectory() as scratch:
        database = Path(scratch) / "lookup.sqlite"
        with gzip.open(lookup, "rb") as data, database.open("wb") as out:
            shutil.copyfileobj(data, out)
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as db:
            return select_modules(db, pattern, module)


def prepare(
    lookup: Path | None, destination: Path, pattern: str, module: str, source_root: Path | None
) -> None:
    if destination.exists():
        raise ValueError(f"choose a new source directory: {destination}")
    files = lookup_files(lookup, pattern, module)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as scratch:
        tree = Path(scratch) / "src"
        for path, digest in files:
            relative = Path(path)
            if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".lean":
                raise ValueError(f"invalid snapshot path: {path}")
            if source_root is None:
                url = f"https://raw.githubusercontent.com/leanprover-community/riemann-hypothesis/{COMMIT}/src/{quote(path)}"
                with urlopen(url, timeout=60) as response:
                    data = response.read()
            else:
                data = (source_root / relative).read_bytes()
            if hashlib.sha256(data).digest() != digest:
                raise ValueError(f"source checksum mismatch: {path}")
            target = tree / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        tree.rename(destination)
    print(f"Prepared {len(files)} checksum-verified source modules in {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    producer = commands.add_parser("build")
    producer.add_argument("--index", type=Path, required=True)
    producer.add_argument("--output", type=Path, required=True)
    reader = commands.add_parser("prepare")
    reader.add_argument("--lookup", type=Path)
    reader.add_argument("--directory", type=Path, required=True)
    reader.add_argument("--source-root", type=Path)
    reader.add_argument("--type-text", default=PATTERN)
    reader.add_argument("--module", default=MODULE)
    args = parser.parse_args()
    if args.command == "build":
        build(args.index, args.output)
    else:
        prepare(args.lookup, args.directory, args.type_text, args.module, args.source_root)


if __name__ == "__main__":
    main()
