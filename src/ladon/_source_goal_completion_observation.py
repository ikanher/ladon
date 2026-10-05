"""Fresh worker and source observation validation for completion."""
from __future__ import annotations

from pathlib import Path

from ladon._source_goal_completion_binding import _fail, _module_name
from ladon._source_goal_protocol import GOAL_FIELDS, _validate_goals
from ladon.source_association_io import _file_identity


def _validate_worker(value, env, toolchain):
    _validate_captured_worker(value, env)
    _validate_live_worker(value, toolchain)


def _validate_captured_worker(value, env):
    if any(value[k] != env[cap] for k, cap in (("leanVersion", "leanVersion"), ("leanCommit", "leanCommit"), ("leanExecutablePath", "leanExecutablePath"))):
        _fail("completion worker differs from captured toolchain identity", "stale", "worker-identity")


def _validate_live_worker(value, toolchain):
    exe = Path(value["leanExecutablePath"])
    if (value["leanVersion"] != toolchain.lean_release
        or (toolchain.lean_commit is not None and value["leanCommit"] != toolchain.lean_commit)
        or not exe.is_absolute() or exe.is_symlink() or exe.resolve(strict=True) != toolchain.lean_path
        or _file_identity(exe)[0] != toolchain.lean_identity):
        _fail("completion helper Lean worker differs from the selected pinned toolchain", "stale", "worker-identity")


def _validate_observation(value, request, capture):
    src, env, goal = capture["source"], capture["environment"], capture["goal"]
    if (src["digest"] != request["sourceDigest"] or src["module"] != request["module"]
        or src["path"] != request["filename"] or src["position"]["line"] != request["line"]
        or src["position"]["column"] != request["column"] or goal["ordinal"] != request["goalOrdinal"]):
        _fail("request does not identify the captured source goal", "stale", "capture-identity")
    selected = value["selectedGoal"]
    if selected is None:
        if value["status"] not in ("unsupported", "rejected") or value["diagnostic"] is None:
            _fail("selected goal may be absent only for a diagnosed unavailable observation")
        return
    _validate_position_scope(value, src, env, capture["helper"]["observation"])
    _validate_selected_goal(value, goal)


def _validate_position_scope(value, src, env, helper_observation):
    integer_fields = ("line", "column", "byteOffset", "rangeStartByte", "rangeEndByte", "selectionEndByte", "goalCount", "goalOrdinal")
    if any(type(value[k]) is not int for k in integer_fields) or type(value["useAfter"]) is not bool:
        _fail("completion position and count fields must be exact integers/booleans")
    pos, syntax, selection = src["position"], src["syntaxRange"], src["selectionRange"]
    observed = (value["byteOffset"], value["rangeStartByte"], value["rangeEndByte"], value["selectionEndByte"], value["useAfter"])
    expected = (pos["byteOffset"], syntax["startByte"], syntax["endByte"], selection["endByteInclusive"], helper_observation["useAfter"])
    if observed != expected:
        _fail("fresh source observation differs from the preserved source capture", "stale", "observation-changed")
    for key, capture_key in (("namespaceName", "namespace"), ("openDeclarationsStructural", "openDeclarationsStructural"), ("optionsStructural", "optionsStructural")):
        if value[key] != env[capture_key]:
            _fail(f"fresh {key} differs from the preserved capture", "stale", "observation-changed")


def _validate_selected_goal(value, goal):
    if value["goalCount"] != goal["goalCount"] or value["goalOrdinal"] >= value["goalCount"]:
        _fail("fresh goal count or selected ordinal differs from capture", "stale", "observation-changed")
    selected = value["selectedGoal"]
    if not isinstance(selected, dict) or set(selected) != GOAL_FIELDS:
        _fail("selected goal row is malformed")
    if selected != {k: goal[k] for k in GOAL_FIELDS}:
        _fail("fresh selected goal differs from preserved capture", "stale", "observation-changed")
    _validate_goals([selected])


def _validate_inventory(value, env):
    inventory = env["compiledInventory"]["modules"]
    paths = value["compiledModulePaths"]
    _validate_paths(paths, inventory)
    _validate_import_order(value["importedModules"], paths)
    _validate_direct_imports(value["directImports"])


def _validate_paths(paths, inventory):
    if not isinstance(paths, list) or any(not isinstance(row, dict) or set(row) != {"module", "path"} for row in paths):
        _fail("fresh compiled module path rows are malformed")
    ordered = [{"module": x["module"], "path": x["path"]} for x in sorted(paths, key=lambda x: x["module"])]
    if ordered != [{"module": x["module"], "path": x["path"]} for x in inventory]:
        _fail("fresh compiled-module paths differ from captured inventory", "stale", "compiled-inventory-changed")


def _validate_import_order(imported, paths):
    if not isinstance(imported, list) or any(not _module_name(x) for x in imported) or imported != [x["module"] for x in paths]:
        _fail("ordered imported module names differ from fresh path rows", "stale", "compiled-inventory-changed")


def _validate_direct_imports(direct):
    if not isinstance(direct, list) or any(not _module_name(x) for x in direct) or len(direct) != len(set(direct)):
        _fail("owner direct-import list is malformed")
