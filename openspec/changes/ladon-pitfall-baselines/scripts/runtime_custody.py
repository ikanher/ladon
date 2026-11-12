#!/usr/bin/env python3
"""Recoverable runtime snapshots. This helper is evaluation tooling, not Ladon runtime."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

SCHEMA = "ladon-runtime-custody-v2"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe(name):
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or not p.parts or str(p) != name:
        raise ValueError(f"unsafe snapshot path: {name}")
    return p


def tree(path, dest, out, ancestors=()):
    real = path.resolve(strict=True)
    if real.is_dir():
        key = (real.stat().st_dev, real.stat().st_ino)
        if key in ancestors:
            raise ValueError(f"cyclic directory: {path}")
        for child in sorted(path.iterdir()):
            if child.name not in {"__pycache__", ".pytest_cache"}:
                tree(child, f"{dest}/{child.name}", out, (*ancestors, key))
    elif real.is_file():
        safe(dest)
        if dest in out:
            raise ValueError(f"duplicate snapshot path: {dest}")
        out[dest] = path.absolute()
    else:
        raise ValueError(f"unsupported runtime entry: {path}")


def command(args, cwd=None):
    return subprocess.check_output(
        args, cwd=cwd, text=True, stderr=subprocess.PIPE
    ).strip()


def python_files(out):
    prefix = Path(sys.base_prefix)
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    out["python/bin/python3"] = Path(sys.executable).resolve()
    std = prefix / "lib" / version
    for p in sorted(std.iterdir()):
        if p.name not in {"site-packages", "__pycache__"}:
            tree(p, f"python/lib/{version}/{p.name}", out)
    # Capture interpreter and extension shared-library dependencies, including loader.
    known = {p.resolve() for p in out.values()}
    pending = [
        out["python/bin/python3"],
        *[
            p
            for n, p in out.items()
            if ("/lib-dynload/" in n and p.suffix == ".so")
            or n.endswith(
                (
                    "/bin/lean",
                    "/bin/lake",
                    "/bin/git",
                    "/bin/sh",
                    "/bin/bash",
                    "/bin/env",
                )
            )
        ],
    ]
    seen = set()
    while pending:
        p = pending.pop()
        if p in seen:
            continue
        seen.add(p)
        r = subprocess.run(["ldd", str(p)], text=True, capture_output=True, timeout=30)
        if r.returncode:
            if (
                "statically linked" in r.stdout + r.stderr
                or "not a dynamic executable" in r.stdout + r.stderr
            ):
                continue
            raise ValueError(f"cannot inspect dynamic dependencies of {p}: {r.stderr}")
        if "not found" in r.stdout:
            raise ValueError(f"unresolved Python dependency: {r.stdout}")
        for line in r.stdout.splitlines():
            m = re.search(r"(?:=>\s*)?(/\S+)\s+\(", line)
            if not m:
                continue
            dep = Path(m[1])
            real = dep.resolve()
            if real in known:
                pending.append(real)
                continue
            known.add(real)
            dest = (
                "python/lib/" if real.is_relative_to(prefix) else "hostlib/"
            ) + dep.name
            if dest in out and sha(out[dest]) != sha(real):
                raise ValueError(f"library collision: {dest}")
            out[dest] = dep.absolute()
            pending.append(real)


class ReservedWriter:
    """Keep enough free space for one reconstruction while the archive grows."""

    def __init__(self, raw, directory, reserve):
        self.raw, self.directory, self.reserve = raw, directory, reserve

    def write(self, data):
        if shutil.disk_usage(self.directory).free < self.reserve + len(data):
            raise ValueError(
                "archive capacity reached; reconstruction reserve preserved"
            )
        return self.raw.write(data)

    def tell(self):
        return self.raw.tell()

    def flush(self):
        return self.raw.flush()


def capture(args):
    repo = args.repo.resolve(strict=True)
    bundle = args.bundle.resolve()
    if bundle.exists():
        raise ValueError(f"bundle exists: {bundle}")
    files = {}
    for name in ["src/ladon", "pyproject.toml", "uv.lock", "README.md"]:
        p = repo / name
        if p.exists():
            tree(p, name, files)
    # The executing helper is the frozen launcher implementation itself.
    files["runtime_custody.py"] = Path(__file__).resolve()
    components = {}
    for item in args.component:
        name, source = item.split("=", 1)
        safe(name)
        if "/" in name or name in {"src", "python", "hostlib", "runtime_custody.py"}:
            raise ValueError(f"invalid component: {name}")
        if name in components:
            raise ValueError(f"duplicate component: {name}")
        root = Path(source).resolve(strict=True)
        components[name] = str(root)
        tree(root, name, files)
    python_files(files)
    tracked = command(
        [
            "git",
            "ls-files",
            "-z",
            "--",
            "src/ladon",
            "pyproject.toml",
            "uv.lock",
            "README.md",
        ],
        repo,
    ).split("\0")
    missing = sorted(n for n in tracked if n and not (repo / n).exists())
    entries = []
    for name, p in sorted(files.items()):
        st = p.stat()
        entries.append(
            {
                "path": name,
                "state": "present",
                "sha256": sha(p),
                "bytes": st.st_size,
                "mode": stat.S_IMODE(st.st_mode) & 0o777,
                "mtimeNs": st.st_mtime_ns,
                "sourceSymlink": os.readlink(p) if p.is_symlink() else None,
            }
        )
    entries += [{"path": n, "state": "missing"} for n in missing]
    total = sum(e.get("bytes", 0) for e in entries)
    bundle.parent.mkdir(parents=True, exist_ok=True)
    reserve = total + 512 * 1024**2
    if shutil.disk_usage(bundle.parent).free < reserve + 1024 * 1024:
        raise ValueError("insufficient disk for archive plus one reconstruction")
    with tempfile.TemporaryDirectory(
        prefix=".custody-capture-", dir=bundle.parent
    ) as tmp:
        work = Path(tmp)
        payload = work / "payload.tar.gz"
        with (
            payload.open("wb") as raw,
            gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=ReservedWriter(raw, bundle.parent, reserve),
                compresslevel=1,
                mtime=0,
            ) as gz,
            tarfile.open(fileobj=gz, mode="w|") as tar,
        ):
            for e in entries:
                if e["state"] == "missing":
                    continue
                p = files[e["path"]]
                info = tarfile.TarInfo(e["path"])
                info.size = e["bytes"]
                info.mode = e["mode"]
                info.mtime = e["mtimeNs"] // 1_000_000_000
                with p.open("rb") as f:
                    tar.addfile(info, f)
                if sha(p) != e["sha256"]:
                    raise ValueError(f"source drift during capture: {p}")
        if total > 1024**3 and shutil.disk_usage(work).free < total + 512 * 1024**2:
            raise ValueError("archive leaves insufficient disk for one reconstruction")
        data = {
            "symlinkPolicy": "Effective file bytes materialized as regular files; direct original file-symlink targets retained per entry",
            "schema": SCHEMA,
            "requiredHostLoader": {
                "path": "/lib64/ld-linux-x86-64.so.2",
                "sha256": sha(Path("/lib64/ld-linux-x86-64.so.2")),
            },
            "gitHeadContextOnly": command(["git", "rev-parse", "HEAD"], repo),
            "components": components,
            "pythonVersion": sys.version,
            "entries": entries,
            "payload": "payload.tar.gz",
            "payloadSha256": sha(payload),
            "uncompressedBytes": total,
        }
        if args.profiles:
            data["profiles"] = json.loads(args.profiles.read_text())
            for profile in data["profiles"].values():
                safe(profile["executable"])
                if profile["executable"] not in files:
                    raise ValueError("profile executable absent from snapshot")
                for folder in profile["leanPath"]:
                    safe(folder)
        if args.artifact_pairs:
            pairs = json.loads(args.artifact_pairs.read_text())
            data["artifactPairs"] = pairs
            by = {e["path"]: e for e in entries}
            for pair in pairs:
                for field in ["source", "artifact"]:
                    if by.get(pair[field], {}).get("sha256") != pair[field + "Sha256"]:
                        raise ValueError(f"artifact pair differs: {pair[field]}")
        manifest = work / "manifest.json"
        manifest.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        identity = sha(manifest)
        (work / "manifest.sha256").write_text(identity + "\n")
        os.rename(work, bundle)
    print(
        json.dumps(
            {
                "bundle": str(bundle),
                "identity": identity,
                "files": len(entries),
                "bytes": total,
                "archiveBytes": payload.stat().st_size
                if payload.exists()
                else (bundle / "payload.tar.gz").stat().st_size,
            }
        )
    )


def load(bundle, identity=None):
    data_path = bundle / "manifest.json"
    expected = identity or (bundle / "manifest.sha256").read_text().strip()
    if sha(data_path) != expected:
        raise ValueError("manifest identity mismatch")
    d = json.loads(data_path.read_text())
    if d["schema"] != SCHEMA:
        raise ValueError("unsupported custody schema")
    names = set()
    for e in d["entries"]:
        safe(e["path"])
        if e["path"] in names:
            raise ValueError("duplicate manifest path")
        names.add(e["path"])
        if e["state"] not in {"present", "missing"}:
            raise ValueError("invalid entry state")
        if e["state"] == "present":
            if type(e["bytes"]) is not int or e["bytes"] < 0:
                raise ValueError("invalid file size")
            if not re.fullmatch(r"[0-9a-f]{64}", e["sha256"]):
                raise ValueError("invalid file digest")
            if type(e["mode"]) is not int or not 0 <= e["mode"] <= 0o777:
                raise ValueError("invalid file mode")
    if sum(e.get("bytes", 0) for e in d["entries"]) != d["uncompressedBytes"]:
        raise ValueError("inconsistent reconstruction size")
    if d["payload"] != "payload.tar.gz":
        raise ValueError("invalid payload locator")
    if sha(bundle / d["payload"]) != d["payloadSha256"]:
        raise ValueError("payload integrity mismatch")
    return d


def verify_tree(d, root):
    by = {e["path"]: e for e in d["entries"]}
    actual = set()
    for p in root.rglob("*"):
        if p.is_symlink():
            raise ValueError(f"unexpected symbolic link: {p}")
        if p.is_file():
            actual.add(p.relative_to(root).as_posix())
    expected = {n for n, e in by.items() if e["state"] == "present"}
    if actual != expected:
        raise ValueError(
            f"runtime inventory drift: extra={sorted(actual - expected)[:5]}, missing={sorted(expected - actual)[:5]}"
        )
    for n in sorted(expected):
        p = root / n
        e = by[n]
        if sha(p) != e["sha256"] or stat.S_IMODE(p.stat().st_mode) != e["mode"]:
            raise ValueError(f"runtime bytes/mode drift: {n}")
    for pair in d.get("artifactPairs", []):
        for field in ["source", "artifact"]:
            if sha(root / pair[field]) != pair[field + "Sha256"]:
                raise ValueError(f"source/artifact drift: {pair[field]}")


def restore(args):
    bundle = args.bundle.resolve()
    dest = args.destination.resolve()
    if dest.exists():
        raise ValueError(f"destination exists: {dest}")
    d = load(bundle, args.identity)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(dest.parent).free < d["uncompressedBytes"] + 512 * 1024**2:
        raise ValueError("insufficient destination disk for reconstruction")
    expected = {e["path"]: e for e in d["entries"] if e["state"] == "present"}
    with tempfile.TemporaryDirectory(
        prefix=".custody-restore-", dir=dest.parent
    ) as tmp:
        root = Path(tmp)
        seen = set()
        with tarfile.open(bundle / d["payload"], "r:gz") as tar:
            for member in tar:
                safe(member.name)
                if (
                    not member.isfile()
                    or member.name not in expected
                    or member.name in seen
                ):
                    raise ValueError(f"unsupported archive member: {member.name}")
                e = expected[member.name]
                if member.size != e["bytes"]:
                    raise ValueError(f"archive size mismatch: {member.name}")
                p = root / member.name
                p.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as src, p.open("xb") as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
                p.chmod(e["mode"])
                os.utime(p, ns=(e["mtimeNs"], e["mtimeNs"]))
                seen.add(member.name)
        verify_tree(d, root)
        os.rename(root, dest)
    print(json.dumps({"restored": str(dest)}))


def run(args):
    bundle = args.bundle.resolve()
    root = args.root.resolve(strict=True)
    d = load(bundle, args.identity)
    verify_tree(d, root)
    if sha(Path(__file__)) != sha(root / "runtime_custody.py"):
        raise ValueError("launcher implementation differs from frozen identity")
    env = {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    libs = [str(root / "python/lib"), str(root / "hostlib")]
    if args.profile:
        profile = d["profiles"][args.profile]
        exe = root / profile["executable"]
        libs.insert(0, str(exe.parent.parent / "lib"))
        env["LEAN_PATH"] = os.pathsep.join(str(root / n) for n in profile["leanPath"])
        env["PATH"] = str(exe.parent) + os.pathsep + str(root / "system-tools/bin")
    else:
        env["PATH"] = str(root / "system-tools/bin")
    env["GIT_EXEC_PATH"] = str(root / "system-tools/libexec/git-core")
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["LD_LIBRARY_PATH"] = os.pathsep.join(libs)
    argv = args.arguments
    if argv and argv[0] == "--":
        argv = argv[1:]
    if args.action == "exec":
        if not args.profile:
            raise ValueError("exec requires a frozen profile")
        binary = exe
        command_args = argv
    else:
        binary = root / "python/bin/python3"
        code = 'import sys, pathlib, runpy; sys.path.insert(0, sys.argv.pop(1)); import ladon; assert pathlib.Path(ladon.__file__).resolve().is_relative_to(pathlib.Path(sys.path[0]).resolve()); sys.argv[0]="ladon"; runpy.run_module("ladon.entrypoint", run_name="__main__")'
        command_args = ["-I", "-B", "-c", code, str(root / "src"), *argv]
    loader = root / "hostlib/ld-linux-x86-64.so.2"
    if args.profile:
        host = d["requiredHostLoader"]
        if sha(Path(host["path"])) != host["sha256"] or sha(loader) != host["sha256"]:
            raise ValueError("host loader differs from preserved platform identity")
    # Lean locates its sysroot through /proc/self/exe, so use its own executable.
    # CPython instead locates its stdlib through argv[0] and supports explicit ld.so.
    executable_args = (
        [str(loader), "--library-path", env["LD_LIBRARY_PATH"], str(binary)]
        if loader.exists() and args.action != "exec"
        else [str(binary)]
    )
    cwd = root
    if args.cwd:
        safe(args.cwd)
        cwd = root / args.cwd
    with tempfile.TemporaryDirectory(prefix="custody-execution-", dir="/tmp") as home:
        env["HOME"] = home
        env["TMPDIR"] = home
        proc = subprocess.run([*executable_args, *command_args], env=env, cwd=cwd)
    return proc.returncode


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="action", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("--repo", type=Path, required=True)
    cap.add_argument("--bundle", type=Path, required=True)
    cap.add_argument("--component", action="append", default=[])
    cap.add_argument("--artifact-pairs", type=Path)
    cap.add_argument("--profiles", type=Path)
    for name in ["restore", "verify", "run", "exec"]:
        q = sub.add_parser(name)
        q.add_argument("--bundle", type=Path, required=True)
        q.add_argument("--identity")
        q.add_argument(
            "--destination" if name == "restore" else "--root", type=Path, required=True
        )
        if name in {"run", "exec"}:
            q.add_argument("--profile")
            q.add_argument("--cwd")
            q.add_argument("arguments", nargs=argparse.REMAINDER)
    a = p.parse_args()
    try:
        if a.action == "capture":
            capture(a)
        elif a.action == "restore":
            restore(a)
        elif a.action == "verify":
            verify_tree(
                load(a.bundle.resolve(), a.identity), a.root.resolve(strict=True)
            )
            print("verified")
        else:
            return run(a)
    except (
        OSError,
        ValueError,
        KeyError,
        subprocess.SubprocessError,
        tarfile.TarError,
    ) as exc:
        print(f"custody failure: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
