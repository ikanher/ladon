"""Supervised execution and exact compiled-closure binding for proof slices."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from ladon.process_supervisor import run_bounded_target_process
from ladon.scoped_slice import premise_rows, profile_is_scoped, provider_frontiers
from ladon.source_association_inventory import (
    _compiled_roots,
    _inventory,
    _resolve_one_compiled_module,
)
from ladon.source_association_io import MAX_MODULES, _file_identity


@dataclass
class SliceRunner:
    root: Path
    execution: object
    environment: dict
    result: dict

    def run(self, arguments):
        process = run_bounded_target_process(
            [*self.execution.command, *arguments],
            cwd=self.root,
            env=self.environment,
            timeout_seconds=60,
            max_output_bytes=8 * 1024**2,
            max_rss_bytes=32 * 1024**3,
        )
        receipt = asdict(process)
        for stream in ("stdout", "stderr"):
            raw = receipt.pop(stream).encode("utf-8")
            receipt[stream + "Bytes"] = len(raw)
            receipt[stream + "Digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
            if not process.succeeded:
                receipt[stream] = raw[:1048576].decode("utf-8", errors="replace")
        self.result["processReceipts"].append(receipt)
        if not process.succeeded:
            self.result["frontiers"].append(
                {"reason": "bounded-process-failed", "phase": arguments[0]}
            )
        return process


def read_frame(process):
    frames = [
        line.removeprefix("LADON_PROOF_SLICE ")
        for line in process.stdout.splitlines()
        if line.startswith("LADON_PROOF_SLICE ")
    ]
    if len(frames) != 1:
        raise ValueError("expected exactly one bounded proof-slice frame")
    return json.loads(frames[0])


def _closure_rows(frame):
    modules, paths = frame["importedModules"], frame["compiledModulePaths"]
    if not modules or len(modules) > MAX_MODULES or len(set(modules)) != len(modules):
        raise ValueError("invalid bounded compiled import closure")
    if len(paths) != len(modules) or {row["module"] for row in paths} != set(modules):
        raise ValueError("compiled import paths do not bind the complete closure")
    return paths


def compiled_closure(frame, module, output, toolchain):
    paths = _closure_rows(frame)
    roots, files = _compiled_roots(toolchain), {}
    for row in paths:
        expected = (
            output.resolve()
            if row["module"] == module
            else _resolve_one_compiled_module(row["module"], roots)
        )
        if Path(row["path"]).resolve(strict=True) != expected:
            raise ValueError("helper loaded an unexpected compiled module path")
        files[row["module"]] = expected
    if module not in files:
        raise ValueError("selected compiled module absent from loaded closure")
    recorded = [
        {"module": name, "digest": _file_identity(file)[0]} for name, file in sorted(files.items())
    ]
    inventory_environment = {"payload": {"compiledModules": recorded}}
    return files, recorded, inventory_environment


def observe_stable(runner, output, source_file, path, module, toolchain):
    if not runner.run(["-o", str(output), source_file]).succeeded:
        return None
    observed = runner.run([str(path)])
    if not observed.succeeded:
        return None
    frame = read_frame(observed)
    files, recorded, inventory_environment = compiled_closure(frame, module, output, toolchain)
    before = _inventory(files, inventory_environment)
    # The second compilation and observation occur inside the stable interval.
    if not runner.run(["-o", str(output), source_file]).succeeded:
        return None
    replayed = runner.run([str(path)])
    if not replayed.succeeded:
        return None
    if read_frame(replayed) != frame or _inventory(files, inventory_environment) != before:
        raise ValueError("stale compiled environment or application observation")
    frame.pop("compiledModulePaths")
    return frame, {**before, "modules": recorded}


def install_observation(result, frame, inventory, declaration, occurrence, module):
    if frame["declaration"] != declaration or occurrence >= len(frame["applications"]):
        raise ValueError("application selection did not reproduce requested declaration/occurrence")
    row = frame["applications"][occurrence]
    scoped = profile_is_scoped(result)
    premises = premise_rows(row, scoped=scoped)
    node = {
        "id": "application-0",
        "kind": "application",
        "declaration": frame["applicationHead"],
        "arguments": row["arguments"],
        "premises": premises,
        "type": row["applicationType"],
        "expression": row["application"],
        "closedType": row["closedApplicationTypeText"],
        "closedProof": row["closedApplicationProofText"],
    }
    result.update(
        status="extracted",
        complete=True,
        nodes=[node],
        localContext=row["localContext"] if scoped else frame["proofLocalsAndLets"],
        observation=frame,
        compiledInventory=inventory,
    )
    result["source"].update(
        attribution=frame["sourceAttribution"], module=module, declaration=declaration
    )
    result["frontiers"] = provider_frontiers(premises, scoped=scoped)


def stage_namespace_overlay(private, module, toolchain):
    """Lean resolves a namespace directory in its first root as a whole.

    Link canonical sibling artifacts into that private namespace, excluding the
    freshly compiled target. The observed import path still resolves to the
    unique canonical artifact and compiled_closure checks that exact path.
    """
    parts = module.split(".")
    if len(parts) == 1:
        return
    roots = _compiled_roots(toolchain)
    count = 0
    seen = set()
    for root in roots:
        namespace = root / parts[0]
        if not namespace.is_dir():
            continue
        for candidate in sorted(namespace.rglob("*.olean")):
            relative = candidate.relative_to(root)
            name = ".".join(relative.with_suffix("").parts)
            if name == module:
                continue
            if name in seen:
                raise ValueError("ambiguous compiled sibling in private namespace overlay")
            seen.add(name)
            count += 1
            if count > MAX_MODULES:
                raise ValueError("private namespace overlay exceeds compiled module bound")
            canonical = _resolve_one_compiled_module(name, roots)
            output = private / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            output.symlink_to(canonical)
            for sibling, destination in [
                (Path(str(canonical) + ".server"), Path(str(output) + ".server")),
                (Path(str(canonical) + ".private"), Path(str(output) + ".private")),
                (canonical.with_suffix(".ir"), output.with_suffix(".ir")),
            ]:
                if sibling.is_file():
                    destination.symlink_to(sibling)
