#!/usr/bin/env python3
"""Record one installed child-acceptance run without issuing an exit receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

MAX_JSON_BYTES = 64 * 1024 * 1024
MAX_PACKAGE_MEMBERS = 10_000
MAX_PACKAGE_BYTES = 512 * 1024 * 1024
RUNTIMES = {"py311": [3, 11], "py312": [3, 12]}
SCOPE_FIELDS = (
    "candidateIdentity", "sourceTreeIdentity", "wheelDigest", "workingDirectory",
    "producerIdentity", "environmentRef",
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("inventory", "context", "wheel", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--runtime", choices=RUNTIMES, required=True)
    return parser.parse_args()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _read_object(path: Path) -> tuple[dict[str, Any], bytes]:
    with path.open("rb") as stream:
        data = stream.read(MAX_JSON_BYTES + 1)
    if len(data) > MAX_JSON_BYTES:
        raise ValueError("acceptance JSON exceeds the byte bound")
    value = json.loads(data, object_pairs_hook=_unique_object)
    if not isinstance(value, dict):
        raise TypeError("acceptance input must be a JSON object")
    return value, data


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _file_digest(path: Path) -> str:
    with path.open("rb") as stream:
        return "sha256:" + hashlib.file_digest(stream, "sha256").hexdigest()


def _require_digest(value: Any) -> None:
    if not isinstance(value, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        raise ValueError("acceptance scope contains an invalid content digest")


def _relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value or not path.parts:
        raise ValueError("acceptance source path must be a normalized relative path")
    return path


def _source_file(root: Path, relative: str) -> Path:
    path = root.joinpath(*_relative_path(relative).parts)
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError("acceptance source must be a contained regular file")
    return path


def _validate_manifest(context: dict, inventory_path: Path) -> dict[str, str]:
    manifest, data = _read_object(Path(context["sourceManifestPath"]))
    if _digest(data) != context["sourceTreeIdentity"]:
        raise ValueError("source manifest bytes differ from the selected identity")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("source manifest has no candidate files")
    commit = manifest.get("candidateCommit")
    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError("source manifest has no exact candidate commit")
    root = Path(context["workingDirectory"]).resolve()
    for relative, expected in files.items():
        _require_digest(expected)
        if _file_digest(_source_file(root, relative)) != expected:
            raise ValueError("candidate source bytes differ from the selected manifest: " + relative)
    for owned in (inventory_path.resolve(), Path(__file__).resolve()):
        relative = owned.relative_to(root).as_posix()
        if files.get(relative) != _file_digest(owned):
            raise ValueError("inventory or producer is not owned by the selected source manifest")
    return files


def _validate_scope(args: argparse.Namespace, context: dict) -> Path:
    for field in SCOPE_FIELDS:
        if field != "workingDirectory":
            _require_digest(context[field])
    root = Path(context["workingDirectory"])
    if not root.is_absolute() or root.resolve() != Path.cwd().resolve():
        raise ValueError("actual working directory differs from the selected candidate")
    if _file_digest(Path(__file__)) != context["producerIdentity"]:
        raise ValueError("acceptance producer bytes differ from the selected identity")
    if _file_digest(args.wheel) != context["wheelDigest"]:
        raise ValueError("wheel bytes differ from the selected identity")
    return root.resolve()


def _suite(inventory: dict, runtime: str, files: dict[str, str]) -> dict:
    if inventory.get("schema") != "ladon-child-acceptance-inventory-v1":
        raise ValueError("unsupported child acceptance inventory")
    if inventory.get("schemaVersion") != 1 or runtime not in inventory["requiredRuntimes"]:
        raise ValueError("inventory version or runtime is unsupported")
    suites = inventory["suites"]
    if len(suites) != 1 or suites[0]["suiteId"] not in {"authority-acceptance", "correctness-acceptance", "integration-acceptance", "discovery-acceptance"}:
        raise ValueError("runner requires one approved child acceptance suite")
    suite = suites[0]
    _validate_targets(suite["testTargets"], inventory["pytestTargets"], files)
    return suite


def _validate_targets(targets: Any, union: list[str], files: dict[str, str]) -> None:
    if not isinstance(targets, list) or not targets or len(set(targets)) != len(targets):
        raise ValueError("acceptance suite has missing or duplicate targets")
    if targets != union:
        raise ValueError("acceptance suite differs from the inventory target union")
    for target in targets:
        if target.split("::", 1)[0] not in files:
            raise ValueError("acceptance test is not owned by the source manifest")


def _execution_posture(args: argparse.Namespace, inventory: dict, root: Path) -> dict:
    import ladon

    if not sys.flags.isolated or list(sys.version_info[:2]) != RUNTIMES[args.runtime]:
        raise ValueError("acceptance requires the selected isolated Python runtime")
    required = inventory["requiredEnvironment"]
    if required.get("LADON_REQUIRE_EXECUTION_NONLEAKAGE") != "1":
        raise ValueError("acceptance inventory must require nonleakage qualification")
    observed = {key: os.environ.get(key) for key in required}
    if observed != required:
        raise ValueError("required acceptance environment is unavailable")
    if any(key in os.environ for key in ("PYTHONPATH", "PYTHONHOME")):
        raise ValueError("acceptance must unset Python path/home overrides")
    origin = Path(ladon.__file__).resolve()
    if not origin.is_relative_to(Path(sys.prefix)) or origin.is_relative_to(root):
        raise ValueError("Ladon was not imported from the selected installed environment")
    return {"importOrigin": str(origin), "environmentRequirements": observed}


def _package_members(wheel_path: Path, origin: str) -> dict[str, str]:
    package_root = Path(origin).parent
    result: dict[str, str] = {}
    with zipfile.ZipFile(wheel_path) as wheel:
        members = [info for info in wheel.infolist() if info.filename.startswith("ladon/")]
        if not members or len(members) > MAX_PACKAGE_MEMBERS:
            raise ValueError("wheel package population is invalid")
        if sum(info.file_size for info in members) > MAX_PACKAGE_BYTES:
            raise ValueError("wheel package exceeds its expanded byte bound")
        for info in members:
            if info.filename in result:
                raise ValueError("wheel has duplicate package members")
            result[info.filename] = _installed_member(wheel, info, package_root)
    _reject_extra_package_files(package_root, result)
    return result


def _installed_member(wheel: zipfile.ZipFile, info: zipfile.ZipInfo, root: Path) -> str:
    relative = _relative_path(info.filename.rstrip("/"))
    path = root.parent.joinpath(*relative.parts)
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError("installed package member is not contained")
    if info.is_dir():
        if not path.is_dir():
            raise ValueError("installed package directory is unavailable")
        observed = _digest(b"")
    else:
        observed = _file_digest(path)
    if observed != _digest(wheel.read(info)):
        raise ValueError("installed package bytes differ from the selected wheel")
    return observed


def _reject_extra_package_files(root: Path, expected: dict[str, str]) -> None:
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("installed package contains an unrecorded symlink")
        if path.is_file() and path.suffix != ".pyc":
            relative = "ladon/" + path.relative_to(root).as_posix()
            if relative not in expected:
                raise ValueError("installed package contains files outside the selected wheel")


class _Capture:
    def __init__(self) -> None:
        self.collected: list[str] = []
        self.initial_collection: list[str] = []
        self.failures: set[str] = set()
        self.skips: set[str] = set()
        self.collection_errors: set[str] = set()
        self.phases: dict[str, dict[str, str]] = {}

    def pytest_collection_modifyitems(self, items) -> None:
        self.initial_collection = [item.nodeid for item in items]

    def pytest_collection_finish(self, session) -> None:
        self.collected = [item.nodeid for item in session.items]

    def pytest_collectreport(self, report) -> None:
        if report.failed:
            self.collection_errors.add(report.nodeid)
        if report.skipped:
            self.skips.add(report.nodeid)

    def pytest_runtest_logreport(self, report) -> None:
        self.phases.setdefault(report.nodeid, {})[report.when] = report.outcome
        if report.failed:
            self.failures.add(report.nodeid)
        if report.skipped or hasattr(report, "wasxfail"):
            self.skips.add(report.nodeid)

    def result(self) -> dict[str, list[str]]:
        passed = [
            node for node in self.collected
            if self.phases.get(node) == {"setup": "passed", "call": "passed", "teardown": "passed"}
            and node not in self.skips and node not in self.failures
        ]
        return {
            "initialCollection": self.initial_collection, "collected": self.collected, "passed": passed, "failed": sorted(self.failures),
            "skipped": sorted(self.skips), "collectionErrors": sorted(self.collection_errors),
        }


def _complete_population(result: dict) -> bool:
    if result["failed"] or result["skipped"] or result["collectionErrors"]:
        return False
    nodes = result["collected"]
    if result["initialCollection"] != nodes:
        return False
    if not nodes or len(set(nodes)) != len(nodes) or sorted(nodes) != sorted(result["passed"]):
        return False
    return _matching_population(nodes, result["testTargets"])


def _matching_population(nodes: list[str], targets: list[str]) -> bool:
    return (
        all(any(_selected(node, target) for target in targets) for node in nodes)
        and all(any(_selected(node, target) for node in nodes) for target in targets)
    )


def _selected(node: str, target: str) -> bool:
    return node == target or node.startswith((target + "::", target + "["))


def _run(args: argparse.Namespace, result: dict, capture: _Capture) -> None:
    context, _ = _read_object(args.context)
    if set(context).intersection(result):
        raise ValueError("acceptance context must not override observed runtime fields")
    result.update({key: value for key, value in context.items() if key != "sourceManifestPath"})
    args.source_manifest = Path(context["sourceManifestPath"])
    inventory, _ = _read_object(args.inventory)
    root = _validate_scope(args, context)
    files = _validate_manifest(context, args.inventory)
    suite = _suite(inventory, args.runtime, files)
    result.update(suiteId=suite["suiteId"], testTargets=suite["testTargets"])
    result.update(_execution_posture(args, inventory, root))
    if inventory.get('requiredPlatform', {}).get('networkDisabled') is True:
        from ladon.acceptance_network import observe_network_isolation

        result['networkIsolation'] = observe_network_isolation(context['hostNetworkNamespace'])
    members = _package_members(args.wheel, result["importOrigin"])
    result["installedPackageMembers"] = members
    import pytest

    posture = {key: os.environ.get(key) for key in (
        "PYTEST_ADDOPTS", "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
    )}
    if posture != {"PYTEST_ADDOPTS": None, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}:
        raise ValueError("acceptance requires no pytest environment selection or external plugins")
    result["pytestEnvironment"] = posture
    result["pytestArgv"] = ["-q", "-o", "addopts=", "--rootdir", str(root), *suite["testTargets"]]
    _Capture.pytest_collection_modifyitems = pytest.hookimpl(tryfirst=True)(
        _Capture.pytest_collection_modifyitems
    )
    result["exitCode"] = int(pytest.main(
        result["pytestArgv"],
        plugins=[capture],
    ))
    result.update(capture.result())
    _validate_scope(args, context)
    _validate_manifest(context, args.inventory)
    if _package_members(args.wheel, result["importOrigin"]) != members:
        raise ValueError("installed package identity changed during acceptance")
    if not _complete_population(result):
        result["exitCode"] = result["exitCode"] or 1


def _initial_result(args: argparse.Namespace) -> dict:
    command = [sys.executable, "-I", __file__, *sys.argv[1:]]
    return {
        "schema": "ladon-child-acceptance-result-v1", "schemaVersion": 1,
        "startedAt": datetime.now(UTC).isoformat(),
        "suiteId": None, "runtime": args.runtime,
        "testTargets": [], "exitCode": 2,
        "pythonVersion": list(sys.version_info[:3]), "pythonExecutable": sys.executable,
        "environmentPrefix": sys.prefix, "isolatedPython": bool(sys.flags.isolated),
        "installedPackageMembers": {}, "environmentRequirements": {},
        "commandVector": command, "command": shlex.join(command),
    }


def _write_result(args: argparse.Namespace, result: dict) -> None:
    result['completedAt'] = datetime.now(UTC).isoformat()
    output = args.output.resolve()
    protected = {path.resolve() for path in (args.inventory, args.context, args.wheel, Path(__file__))}
    if hasattr(args, "source_manifest"):
        protected.add(args.source_manifest.resolve())
    if output in protected:
        raise ValueError("result output must not overwrite acceptance inputs")
    if "workingDirectory" in result and output.is_relative_to(Path(result["workingDirectory"])):
        raise ValueError("result output must be outside the candidate source")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=output.parent, delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    try:
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    args = _arguments()
    result, capture = _initial_result(args), _Capture()
    try:
        _run(args, result, capture)
    except (
        OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError, ImportError,
        zipfile.BadZipFile, KeyboardInterrupt, SystemExit,
    ) as error:
        result["exitCode"] = 130 if isinstance(error, KeyboardInterrupt) else 2
        result["qualificationError"] = {
            "kind": type(error).__name__, "message": str(error)[:4000],
        }
    result.update(capture.result())
    try:
        _write_result(args, result)
    except (OSError, ValueError) as error:
        print("cannot write child acceptance result: " + str(error), file=sys.stderr)
        return 2
    return result["exitCode"]


if __name__ == "__main__":
    raise SystemExit(main())
