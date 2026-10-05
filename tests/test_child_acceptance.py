"""Adversarial acceptance bundles with real content-addressed evidence bytes.

Producer and suite records are synthetic fixtures. These tests establish the
local receipt checker contract, not authenticity of a recorded test execution.
"""

from __future__ import annotations

import copy
import io
import json
import shlex
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from ladon.child_acceptance import canonical_digest, content_digest, validate_child_bundle


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _wheel(content: bytes) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("ladon/__init__.py", content)
    return stream.getvalue()


@dataclass
class Bundle:
    root: Path
    inventory: dict[str, Any]
    receipt: dict[str, Any]
    results: list[dict[str, Any]]
    objects: dict[str, dict[str, str]]

    def put(self, data: bytes) -> str:
        identity = content_digest(data)
        relative = "objects/" + identity[7:]
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.objects[identity] = {"digest": identity, "path": relative}
        return identity

    def put_json(self, value: Any) -> str:
        return self.put(_json_bytes(value))

    def refresh(self) -> None:
        refs = [self.put_json(result) for result in self.results]
        self.receipt["resultArtifactRefs"] = refs
        self.receipt["logArtifactRefs"] = [result["logArtifactRef"] for result in self.results]
        self.receipt["commands"] = [
            {"command": result["command"], "status": "passed", "evidenceDigest": ref}
            for result, ref in zip(self.results, refs, strict=True)
        ]
        self.receipt["evidenceFiles"] = [self.objects[key] for key in sorted(self.objects)]
        self.rehash()

    def rehash(self) -> None:
        self.receipt.pop("receiptIdentity", None)
        self.receipt["receiptIdentity"] = canonical_digest(self.receipt)

    def validate(self) -> None:
        validate_child_bundle(self.receipt, bundle_root=self.root, inventory=self.inventory)


def _result(bundle: Bundle, runtime: str, member_digest: str) -> dict[str, Any]:
    version = "3.11" if runtime == "py311" else "3.12"
    prefix = bundle.root / "environments" / runtime
    executable = str(prefix / "bin" / "python")
    targets = bundle.inventory["suites"][0]["testTargets"]
    root = Path(bundle.receipt["workingDirectory"])
    command = [executable, "-I", str(root / bundle.inventory["runnerPath"]),
               "--inventory", str(root / bundle.inventory["inventoryPath"]),
               "--context", str(bundle.root / "context.json"), "--wheel", str(bundle.root / "wheel.whl"),
               "--runtime", runtime, "--output", str(bundle.root / (runtime + ".json"))]
    selected = ["tests/test_alpha.py::test_case", "tests/test_beta.py::test_other[case]"]
    fields = ("candidateIdentity", "sourceTreeIdentity", "wheelDigest", "workingDirectory",
              "producerIdentity", "environmentRef")
    return {
        "schema": "ladon-child-suite-result-v1",
        **{field: bundle.receipt[field] for field in fields},
        "suiteId": "portable-correctness", "runtime": runtime,
        "installedPackageMembers": {"ladon/__init__.py": member_digest},
        "environmentRequirements": copy.deepcopy(bundle.inventory["requiredEnvironment"]),
        "isolatedPython": True, "pythonVersion": [3, int(version.split(".")[1]), 0],
        "pythonExecutable": executable, "environmentPrefix": str(prefix),
        "importOrigin": str(prefix / "lib" / f"python{version}" / "site-packages" / "ladon" / "__init__.py"),
        "commandVector": command, "command": shlex.join(command),
        "pytestArgv": ["-q", "-o", "addopts=", "--rootdir", str(root), *targets],
        "pytestEnvironment": {"PYTEST_ADDOPTS": None, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
        "testTargets": list(targets), "exitCode": 0,
        "initialCollection": list(selected), "collected": selected, "passed": list(selected),
        "failed": [], "skipped": [], "collectionErrors": [],
        "logArtifactRef": bundle.put(f"{runtime}: 2 passed\n".encode()),
    }


@pytest.fixture
def bundle(tmp_path: Path) -> Bundle:
    inventory = {
        "schema": "ladon-child-acceptance-inventory-v1", "exitClass": "correctness",
        "requiredRuntimes": ["py311", "py312"],
        "requiredEnvironment": {"PYTHONPATH": "unset", "PYTHONHOME": "unset"},
        "requiredSourceChecks": [],
        "runnerPath": "scripts/runner.py", "inventoryPath": "inventory.json",
        "suites": [{"suiteId": "portable-correctness", "testTargets": [
            "tests/test_alpha.py::test_case", "tests/test_beta.py",
        ]}],
    }
    value = Bundle(tmp_path, inventory, {}, [], {})
    module = b'"""Synthetic installed module fixture."""\n'
    module_ref = value.put(module)
    producer_ref = value.put(b'"""Synthetic fixture producer; authenticity is not asserted."""\n')
    manifest_ref = value.put_json({"files": {
        "src/ladon/__init__.py": module_ref, inventory["runnerPath"]: producer_ref,
        inventory["inventoryPath"]: value.put_json(inventory),
    }})
    wheel_ref = value.put(_wheel(module))
    candidate = {"sourceTreeIdentity": manifest_ref, "wheelDigest": wheel_ref}
    value.receipt.update({
        "schema": "ladon-child-exit-receipt-v1", "status": "passed",
        "exitClass": "correctness", "analysisCompleteness": "complete", "omissions": [],
        "inventoryArtifactRef": value.put_json(inventory),
        "candidateArtifactRef": value.put_json(candidate),
        "candidateIdentity": canonical_digest(candidate),
        "sourceTreeIdentity": manifest_ref, "wheelDigest": wheel_ref,
        "producerIdentity": producer_ref,
        "environmentRef": value.put_json({
            "schema": "ladon-acceptance-environment-v1", "posture": "trusted-repository-only",
            "procAvailable": True, "runtimes": {
                runtime: {"python": str(tmp_path / "environments" / runtime / "bin" / "python")}
                for runtime in ("py311", "py312")
            },
        }),
        "workingDirectory": str(tmp_path / "candidate"),
        "sourceChecksArtifactRef": value.put_json({
            "requirements": [], "status": "passed", "sourceFileRefs": {},
        }),
    })
    value.results.extend(_result(value, runtime, module_ref) for runtime in ("py311", "py312"))
    value.refresh()
    return value


def test_complete_byte_bound_bundle_is_accepted(bundle: Bundle) -> None:
    bundle.validate()


def test_network_required_profile_rejects_unobserved_isolation(bundle: Bundle) -> None:
    from ladon.child_acceptance import _validate_environment_profile

    profile = json.loads((bundle.root / bundle.objects[bundle.receipt['environmentRef']]['path']).read_bytes())
    profile['hostNetworkNamespace'] = 'net:[12345]'
    evidence = {bundle.receipt['environmentRef']: _json_bytes(profile)}
    inventory = copy.deepcopy(bundle.inventory)
    inventory['requiredPlatform'] = {'executionPosture': 'trusted-repository-only',
                                     'networkDisabled': True}
    with pytest.raises(ValueError, match='network'):
        _validate_environment_profile(bundle.results[0], bundle.receipt, inventory, evidence)


@pytest.mark.parametrize("damage", ["missing", "changed", "symlink", "duplicate-descriptor"])
def test_evidence_files_must_exist_and_match_their_recorded_bytes(
    bundle: Bundle, damage: str,
) -> None:
    ref = bundle.results[0]["logArtifactRef"]
    path = bundle.root / bundle.objects[ref]["path"]
    if damage == "missing":
        path.unlink()
    elif damage == "changed":
        path.write_bytes(b"different captured bytes")
    elif damage == "symlink":
        original = path.read_bytes()
        path.unlink()
        alternate = bundle.root / "alternate-log"
        alternate.write_bytes(original)
        path.symlink_to(alternate)
    else:
        bundle.receipt["evidenceFiles"].append(dict(bundle.objects[ref]))
    # Recomputing the receipt cannot legitimize a missing or changed object.
    bundle.rehash()
    with pytest.raises(ValueError):
        bundle.validate()


@pytest.mark.parametrize("field", [
    "producerIdentity", "environmentRef", "inventoryArtifactRef", "sourceChecksArtifactRef",
])
def test_rehashed_receipt_cannot_name_unavailable_provenance(bundle: Bundle, field: str) -> None:
    bundle.receipt[field] = "sha256:" + "0" * 64
    bundle.rehash()
    with pytest.raises(ValueError):
        bundle.validate()


@pytest.mark.parametrize(("field", "bad_value"), [
    ("installedPackageMembers", {"ladon/__init__.py": "sha256:" + "0" * 64}),
    ("installedPackageMembers", {}),
    ("environmentRequirements", {"PYTHONPATH": "inherited", "PYTHONHOME": "unset"}),
    ("pythonVersion", [3, 10, 0]),
    ("isolatedPython", False),
    ("isolatedPython", "false"),
    ("exitCode", False),
    ("importOrigin", "/different-installation/ladon/__init__.py"),
    ("importOrigin", "relative/site-packages/ladon/__init__.py"),
    ("commandVector", ["python", "-m", "pytest"]),
    ("candidateIdentity", "sha256:" + "0" * 64),
    ("sourceTreeIdentity", "sha256:" + "0" * 64),
    ("wheelDigest", "sha256:" + "0" * 64),
    ("environmentRef", "sha256:" + "0" * 64),
])
def test_rehashed_result_cannot_change_the_selected_execution_scope(
    bundle: Bundle, field: str, bad_value: Any,
) -> None:
    bundle.results[0][field] = copy.deepcopy(bad_value)
    bundle.refresh()
    with pytest.raises(ValueError):
        bundle.validate()


def test_import_origin_inside_candidate_checkout_is_rejected(bundle: Bundle) -> None:
    candidate = Path(bundle.receipt["workingDirectory"])
    bundle.results[0]["environmentPrefix"] = str(candidate)
    bundle.results[0]["importOrigin"] = str(candidate / "src" / "ladon" / "__init__.py")
    bundle.refresh()
    with pytest.raises(ValueError, match="checkout"):
        bundle.validate()


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unexpected-suite", "unexpected-runtime"])
def test_complete_unique_suite_runtime_matrix_is_required(bundle: Bundle, mutation: str) -> None:
    if mutation == "missing":
        bundle.results.pop()
    elif mutation == "duplicate":
        bundle.results.append(copy.deepcopy(bundle.results[0]))
    elif mutation == "unexpected-suite":
        bundle.results[0]["suiteId"] = "unselected-suite"
    else:
        bundle.results[0]["runtime"] = "py310"
    bundle.refresh()
    with pytest.raises(ValueError, match="matrix"):
        bundle.validate()


@pytest.mark.parametrize("mutation", [
    "skip", "failure", "collection-error", "nonzero-exit", "overselection",
    "empty-collected", "missing-target", "duplicate-collected", "missing-passed", "changed-targets",
])
def test_actual_collection_and_outcomes_must_cover_exactly_selected_targets(
    bundle: Bundle, mutation: str,
) -> None:
    row = bundle.results[0]
    defect_fields = {"skip": "skipped", "failure": "failed", "collection-error": "collectionErrors"}
    if mutation in defect_fields:
        row[defect_fields[mutation]] = [row["collected"][0]]
    elif mutation == "nonzero-exit":
        row["exitCode"] = 1
    elif mutation == "overselection":
        row["collected"].append("tests/test_unselected.py::test_other")
        row["passed"] = list(row["collected"])
    elif mutation == "empty-collected":
        row["collected"], row["passed"] = [], []
    elif mutation == "missing-target":
        row["collected"], row["passed"] = row["collected"][:1], row["passed"][:1]
    elif mutation == "duplicate-collected":
        row["collected"].append(row["collected"][0])
        row["passed"] = list(row["collected"])
    elif mutation == "missing-passed":
        row["passed"] = row["passed"][:1]
    else:
        row["testTargets"] = ["tests/test_alpha.py"]
    bundle.refresh()
    with pytest.raises(ValueError, match="suite"):
        bundle.validate()


def test_inventory_is_selected_separately_from_the_receipt(bundle: Bundle) -> None:
    bundle.inventory["suites"][0]["testTargets"] = ["tests/test_another.py"]
    with pytest.raises(ValueError, match="inventory"):
        bundle.validate()


def test_command_evidence_digest_binds_the_actual_result_artifact_bytes(bundle: Bundle) -> None:
    row = bundle.results[0]
    differently_encoded = json.dumps(row, indent=2).encode()
    actual_ref = bundle.put(differently_encoded)
    bundle.receipt["resultArtifactRefs"][0] = actual_ref
    bundle.receipt["evidenceFiles"] = list(bundle.objects.values())
    bundle.rehash()
    with pytest.raises(ValueError, match="command|result"):
        bundle.validate()
    bundle.receipt["commands"][0]["evidenceDigest"] = actual_ref
    bundle.rehash()
    bundle.validate()


def test_coherently_rebound_wheel_still_must_match_the_selected_source_manifest(bundle: Bundle) -> None:
    changed = b'"""Changed package bytes not in the selected source manifest."""\n'
    wheel_ref = bundle.put(_wheel(changed))
    candidate = {"sourceTreeIdentity": bundle.receipt["sourceTreeIdentity"], "wheelDigest": wheel_ref}
    bundle.receipt.update({"wheelDigest": wheel_ref, "candidateIdentity": canonical_digest(candidate),
                           "candidateArtifactRef": bundle.put_json(candidate)})
    for row in bundle.results:
        row["wheelDigest"] = wheel_ref
        row["candidateIdentity"] = bundle.receipt["candidateIdentity"]
        row["installedPackageMembers"] = {"ladon/__init__.py": content_digest(changed)}
    bundle.refresh()
    with pytest.raises(ValueError, match="source|wheel"):
        bundle.validate()


@pytest.mark.parametrize("mutation", ["deselected", "keyword-option", "inline-code", "ambient-options"])
def test_approved_producer_and_complete_collection_are_required(bundle: Bundle, mutation: str) -> None:
    row = bundle.results[0]
    if mutation == "deselected":
        row["initialCollection"].append("tests/test_beta.py::test_omitted")
    elif mutation == "keyword-option":
        row["pytestArgv"].extend(["-k", "test_case"])
    elif mutation == "inline-code":
        row["commandVector"] = [row["pythonExecutable"], "-I", "-c", "pass"]
        row["command"] = shlex.join(row["commandVector"])
    else:
        row["pytestEnvironment"]["PYTEST_ADDOPTS"] = "-k test_case"
    bundle.refresh()
    with pytest.raises(ValueError):
        bundle.validate()


def test_named_pipe_evidence_is_rejected_without_waiting(bundle: Bundle) -> None:
    import os

    ref = bundle.results[0]["logArtifactRef"]
    path = bundle.root / bundle.objects[ref]["path"]
    path.unlink()
    os.mkfifo(path)
    with pytest.raises(ValueError, match="regular"):
        bundle.validate()


@pytest.mark.parametrize("invalid", [b'{"value":NaN}', b'{"value":Infinity}', b'{"value":1,"value":2}'])
def test_nonfinite_or_duplicate_json_evidence_is_rejected(bundle: Bundle, invalid: bytes) -> None:
    bundle.receipt["sourceChecksArtifactRef"] = bundle.put(invalid)
    bundle.refresh()
    with pytest.raises(ValueError):
        bundle.validate()


@pytest.mark.parametrize("damage", ["duplicate-owner", "legacy", "recursion", "quux", "dispatch"])
def test_source_assertions_are_recomputed_from_actual_bytes(bundle: Bundle, damage: str) -> None:
    from ladon._child_acceptance_sources import validate_source_checks

    owner = "src/ladon/_proofir_derivation_slice.py"
    source = "class _Slicer:\n def run(self): self._expand_iterative()\n def _expand_iterative(self): pass\n"
    sources = {owner: source}
    if damage == "duplicate-owner":
        sources["src/ladon/proofir_derivation.py"] = source
    elif damage == "legacy":
        sources[owner] += "def _expand_step(): pass\n"
    elif damage == "recursion":
        sources[owner] += "import sys\nsys.setrecursionlimit(9999)\n"
    elif damage == "quux":
        sources[owner] += "import Quux\n"
    else:
        sources[owner] = source.replace("self._expand_iterative()", "pass")
    refs = {path: bundle.put(text.encode()) for path, text in sources.items()}
    requirement = {"checkId": "single-iterative-slice-owner", "files": list(sources)}
    evidence = {ref: (bundle.root / bundle.objects[ref]["path"]).read_bytes() for ref in refs.values()}
    with pytest.raises(ValueError):
        validate_source_checks({"sourceFileRefs": refs}, {"requiredSourceChecks": [requirement]},
                               evidence, bundle.receipt)



def test_recorded_interpreter_must_match_the_selected_environment_profile(bundle: Bundle) -> None:
    row = bundle.results[0]
    old = row["environmentPrefix"]
    other = str(bundle.root / "other-installation")
    row["environmentPrefix"] = other
    row["importOrigin"] = row["importOrigin"].replace(old, other)
    row["pythonExecutable"] = other + "/bin/python"
    row["commandVector"][0] = row["pythonExecutable"]
    row["command"] = shlex.join(row["commandVector"])
    bundle.refresh()
    with pytest.raises(ValueError, match="environment"):
        bundle.validate()



def test_source_quality_command_uses_a_selected_interpreter(bundle: Bundle) -> None:
    from ladon._child_acceptance_sources import validate_source_checks

    source_ref = bundle.put(b"pass\n")
    log_ref = bundle.put(b"tool output\n")
    requirement = {"checkId": "derivation-owner-quality", "files": ["owner.py"]}
    tail = ["-I", "-m", "ruff", "check", "owner.py"]
    checks = {"sourceFileRefs": {"owner.py": source_ref}, "qualityCommands": [{
        "argv": ["true", *tail], "workingDirectory": bundle.receipt["workingDirectory"],
        "exitCode": 0, "status": "passed", "logArtifactRef": log_ref,
    }]}
    evidence = {ref: (bundle.root / row["path"]).read_bytes() for ref, row in bundle.objects.items()}
    inventory = {"requiredSourceChecks": [requirement], "sourceQualityArgvTails": [tail]}
    with pytest.raises(ValueError, match="interpreter"):
        validate_source_checks(checks, inventory, evidence, bundle.receipt)
