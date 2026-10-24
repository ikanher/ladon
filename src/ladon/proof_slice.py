"""Extract actual applications from a privately compiled, source-bound Lean proof."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from importlib import resources
from pathlib import Path

from ladon._proof_slice_runtime import (
    SliceRunner,
    install_observation,
    observe_stable,
    stage_namespace_overlay,
)
from ladon._source_goal_helpers import helper_source
from ladon.lean_toolchain import resolve_toolchain_context, verify_toolchain_identities
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.source_association_io import _read_regular, _source_path

SCHEMA = "ladon-proof-slice-v1"
MAX_SOURCE_BYTES = 8 * 1024**2
_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*\Z")


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def pinned_toolchain(root):
    """Resolve installed pinned binaries explicitly, without downloading or Lake builds."""
    pin = (root / "lean-toolchain").read_text().strip()
    if not re.fullmatch(r"leanprover/lean4:v[0-9.]+(?:-rc[0-9]+)?", pin):
        raise ValueError("extraction requires an installed release toolchain")
    lean = (
        Path.home() / ".elan/toolchains" / pin.replace("/", "--").replace(":", "---") / "bin/lean"
    )
    return resolve_toolchain_context(root, lean_path=lean, lake_path=lean.with_name("lake"))


def _validate_selection(module, declaration, application, occurrence):
    for name in (module, declaration, application):
        if not isinstance(name, str) or not _NAME.fullmatch(name):
            raise ValueError("slice selection requires ordinary qualified names")
    if type(occurrence) is not int or not 0 <= occurrence < 4096:
        raise ValueError("invalid bounded application occurrence")


def extract_proof_slice(repo_root, source_file, module, declaration, application, occurrence=0,
                        *, scoped=False):
    if type(scoped) is not bool:
        raise TypeError("scoped profile selection must be boolean")
    root = Path(repo_root).resolve(strict=True)
    _validate_selection(module, declaration, application, occurrence)
    source = _source_path(root, source_file, module)
    original = _read_regular(source, MAX_SOURCE_BYTES)
    toolchain = pinned_toolchain(root)
    execution = prepare_direct_lean_execution(root, None, toolchain, require_compiled_module=False)
    helper_name = "ladon_scoped_slice_helper.lean" if scoped else "ladon_proof_slice_helper.lean"
    helper = Path(str(resources.files("ladon").joinpath("lean", helper_name)))
    template = helper_source(helper)
    result = {
        "schema": SCHEMA,
        "complete": False,
        "status": "unavailable",
        "nodes": [],
        "frontiers": [],
        "processReceipts": [],
        "selection": {
            "sourceFile": source_file,
            "module": module,
            "declaration": declaration,
            "application": application,
            "occurrence": occurrence,
        },
        "source": {"path": source_file, "sha256": hashlib.sha256(original).hexdigest()},
        "environment": toolchain.context_identity,
        "helper": {
            "sha256": hashlib.sha256(template).hexdigest(),
            "profile": "scoped-identity-transport-v2" if scoped else "declaration-scoped-application-v1",
        },
        "limits": {
            "secondsPerProcess": 60,
            "rssBytes": DEFAULT_MAX_RSS_BYTES,
            "outputBytes": 8 * 1024**2,
            "nodes": 8192,
            "depth": 64,
        },
    }
    with tempfile.TemporaryDirectory(prefix="ladon-proof-slice-") as temporary:
        private = Path(temporary)
        output = private.joinpath(*module.split(".")).with_suffix(".olean")
        output.parent.mkdir(parents=True, exist_ok=True)
        stage_namespace_overlay(private, module, toolchain)
        env = dict(execution.environment)
        env["LEAN_PATH"] = str(private) + ":" + env.get("LEAN_PATH", "")

        runner = SliceRunner(root, execution, env, result)
        code = template.replace(b"-- LADON_TARGET_IMPORT", f"import {module}".encode())
        selected_application = application
        if "." not in application and "." in declaration:
            selected_application = declaration.rsplit(".", 1)[0] + "." + application
        code = code.replace(
            b"-- LADON_SELECTION",
            f"#ladon_proof_slice {declaration} {selected_application}".encode(),
        )
        path = private / "LadonSlice.lean"
        path.write_bytes(code)
        observed = observe_stable(runner, output, source_file, path, module, toolchain)
        if observed is None:
            return result
        frame, inventory = observed
        if _read_regular(source, MAX_SOURCE_BYTES) != original or helper_source(helper) != template:
            raise ValueError("stale source or helper during proof slice extraction")
        verify_toolchain_identities(toolchain)
        install_observation(result, frame, inventory, declaration, occurrence, module)
        # Identity excludes timings and temporary compiler paths. Checking always
        # re-extracts these bound observations; a caller cannot self-sign evidence.
        result["sliceId"] = slice_identity(result)
    return result


def slice_identity(result):
    return digest(
        {
            key: result[key]
            for key in (
                "schema",
                "selection",
                "source",
                "environment",
                "nodes",
                "localContext",
                "observation",
                "helper",
                "compiledInventory",
                "frontiers",
                "limits",
            )
        }
    )
