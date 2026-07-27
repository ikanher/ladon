"""Portable installed-CLI signal fixtures and contract assertions."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Sequence

from ladon.installed_contract import invoke


def assert_installed_text_signal_contract(
    command: Sequence[str],
    tmp_path: Path,
) -> None:
    """Exercise corrected text signals through the installed console."""

    repo_root = build_text_signal_fixture(tmp_path)
    result = invoke(
        command,
        "--repo-root",
        str(repo_root),
        "--root",
        "Pkg.lean",
        "--scope",
        "inventory",
        "--format",
        "json",
        "--output",
        "-",
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert_text_signal_payload(json.loads(result.stdout))
    assert_text_signal_rendering(command, repo_root)


def assert_text_signal_rendering(
    command: Sequence[str],
    repo_root: Path,
) -> None:
    """Assert text output labels exact fan populations and authority."""

    text = invoke(
        command,
        "--repo-root",
        str(repo_root),
        "--root",
        "Pkg.lean",
        "--scope",
        "inventory",
    )
    assert text.returncode == 0
    assert (
        "Top Target-Owned Importer to Target-Owned Target Fan-In"
        in text.stdout
    )
    assert "Top Generated-Importer Fan-In Contributions" in text.stdout
    assert "population=generated_importers_to_all_targets" in text.stdout
    assert "authority=module_import_graph" in text.stdout


def assert_installed_lean_signal_contract(
    command: Sequence[str],
    tmp_path: Path,
) -> None:
    """Exercise declaration-only signals through a fake Lean helper."""

    repo_root, fake_bin = build_lean_signal_fixture(tmp_path)
    result = subprocess.run(
        [
            *command,
            "--repo-root",
            str(repo_root),
            "--root",
            "Pkg/Surface/Deep.lean",
            "--build",
            "--extraction-backend",
            "lean",
            "--format",
            "json",
            "--output",
            "-",
        ],
        text=True,
        capture_output=True,
        check=False,
        env=environment_with_fake_bin(fake_bin),
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert_lean_similarity_signals(payload)
    assert_namespace_drift_signal(payload)


def assert_lean_similarity_signals(payload: dict) -> None:
    """Assert positive and intentionally capped proof-family evidence."""

    declaration_graph = report_section(payload, "declaration_graph")
    candidates = {
        row["suffix"]: row
        for row in declaration_graph["proof_family_similarity_candidates"]
    }
    assert candidates["ge_one"]["similarity_score"] == 0.5
    assert candidates["ge_one"]["coarse_only"] is True
    assert candidates["ge_one"]["promoted"] is False
    assert candidates["eq_zero"]["max_concrete_identifier_overlap"] == 1.0
    assert candidates["eq_zero"]["promoted"] is True


def assert_namespace_drift_signal(payload: dict) -> None:
    """Assert parent compatibility and one aggregated unrelated namespace."""

    module_readiness = report_section(payload, "module_readiness")
    drift = [
        row
        for row in module_readiness["rows"]
        if row["kind"] == "namespace_module_drift"
    ]
    assert len(drift) == 1
    assert drift[0]["module"] == "Pkg.Surface.Deep"
    assert drift[0]["namespace"] == "Other.Space"
    assert drift[0]["declarationCount"] == 2
    assert drift[0]["authority"] == "source_declaration_inventory"


def build_text_signal_fixture(tmp_path: Path) -> Path:
    """Create one portable source tree spanning the repaired text signals."""

    repo_root = tmp_path / "signal-target"
    generated = repo_root / "Pkg" / "Generated"
    generated.mkdir(parents=True)
    owners = [f"Pkg.Owner{index}" for index in range(5)]
    generated_modules = [f"Pkg.Generated.Row{index}" for index in range(5)]
    (repo_root / "Pkg.lean").write_text(
        "\n".join(f"import {module}" for module in [*owners, *generated_modules])
        + "\n",
        encoding="utf-8",
    )
    write_handwritten_importers(repo_root, owners)
    write_generated_importers(generated, generated_modules)
    write_signal_targets(repo_root)
    return repo_root


def write_handwritten_importers(
    repo_root: Path,
    owners: list[str],
) -> None:
    """Write handwritten importers with one internal/external boundary row."""

    for index, _module in enumerate(owners):
        imports = ["import Pkg.CoreShared"]
        if index == 0:
            imports.extend(
                [
                    "import Pkg.CoreMixed",
                    "import Pkg.Missing",
                    "import External.Missing",
                ]
            )
        (repo_root / "Pkg" / f"Owner{index}.lean").write_text(
            "\n".join(imports) + f"\ndef owner{index} : Nat := {index}\n",
            encoding="utf-8",
        )


def write_generated_importers(
    generated: Path,
    modules: list[str],
) -> None:
    """Write generated importers of one handwritten target."""

    for index, _module in enumerate(modules):
        (generated / f"Row{index}.lean").write_text(
            f"import Pkg.CoreMixed\ndef row{index} : Nat := {index}\n",
            encoding="utf-8",
        )


def write_signal_targets(repo_root: Path) -> None:
    """Write declaration masking and lexical-authority target modules."""

    (repo_root / "Pkg" / "CoreMixed.lean").write_text(
        "def mixed : Nat := 1\n",
        encoding="utf-8",
    )
    (repo_root / "Pkg" / "CoreShared.lean").write_text(
        """\
/- axiom BlockFake : True -/
def quoted : String := "constant StringFake : Nat"
-- opaque LineFake : Nat
@[simp] private theorem keptTheorem : True := by trivial
noncomputable def keptDef : Nat := 1
opaque keptOpaque : Nat
axiom keptAxiom : True
constant keptConstant : Nat
theorem trustedMarker : True := by
  sorry
""",
        encoding="utf-8",
    )


def assert_text_signal_payload(payload: dict) -> None:
    """Assert corrected text signals and their intentional negatives."""

    dag = report_section(payload, "module_dag")
    assert_missing_import_signal(dag)
    assert_fan_population_signals(dag)
    assert_declaration_inventory_signal(dag)
    assert_lexical_marker_signals(dag)
    assert_deduplicated_fan_finding(payload)


def assert_missing_import_signal(dag: dict) -> None:
    """Assert project-owned absence without an external false positive."""

    assert [row["targetModule"] for row in dag["missing_internal_imports"]] == [
        "Pkg.Missing"
    ]
    missing = dag["missing_internal_imports"][0]
    assert missing["authority"] == "lexical_text"
    assert "not a Lean resolver" in missing["nonclaim"]


def assert_fan_population_signals(dag: dict) -> None:
    """Assert exact ownership and lexical generated-tag populations."""

    generic = rows_by_module(dag["top_fan_in"])
    target_owned = rows_by_module(dag["top_target_owned_fan_in"])
    generated = rows_by_module(dag["top_generated_importer_fan_in"])
    assert generic["Pkg.CoreMixed"]["fan_in"] == 6
    # A generated-looking path is advisory evidence, not configured generated
    # provenance, so all six source-root members remain target-owned.
    assert target_owned["Pkg.CoreMixed"]["fan_in"] == 6
    assert generated["Pkg.CoreMixed"]["fan_in"] == 5
    assert generic["Pkg.CoreShared"]["fan_in"] == 5
    assert target_owned["Pkg.CoreShared"]["fan_in"] == 5


def assert_declaration_inventory_signal(dag: dict) -> None:
    """Assert bounded declarations and comment/string negatives."""

    metadata = dag["module_metadata"]["Pkg.CoreShared"]
    names = {row["name"] for row in metadata["textDeclarations"]}
    assert {"BlockFake", "StringFake", "LineFake"}.isdisjoint(names)
    assert {
        "quoted",
        "keptTheorem",
        "keptDef",
        "keptOpaque",
        "keptAxiom",
        "keptConstant",
        "trustedMarker",
    } == names
    assert metadata["declarationAuthority"] == "lexical_text"
    assert all(
        "not a complete Lean parse" in row["nonclaim"]
        for row in metadata["textDeclarations"]
    )


def assert_lexical_marker_signals(dag: dict) -> None:
    """Assert lexical trust rows carry bounded authority wording."""

    markers = [
        row
        for row in dag["lexical_markers"]
        if row["module"] == "Pkg.CoreShared"
    ]
    assert {row["kind"] for row in markers} == {"axiom", "sorry"}
    assert all(row["authority"] == "lexical_text" for row in markers)
    assert all("not a Lean-elaborated" in row["nonclaim"] for row in markers)


def assert_deduplicated_fan_finding(payload: dict) -> None:
    """Assert equivalent raw fan tables produce one promoted finding."""

    shared_findings = [
        row
        for row in report_section(payload, "findings")
        if row.get("metric") == "module_fan_in"
        and row["subject"] == "Pkg.CoreShared"
    ]
    assert len(shared_findings) == 1
    finding = shared_findings[0]
    assert finding["kind"] == "target_owned_module_fan_in_hotspot"
    assert finding["promotion_population"] == (
        "target_owned_importers_to_target_owned_targets"
    )
    assert finding["promotion_threshold"] == 5
    assert finding["authority"] == (
        "module_import_graph_and_population_policy"
    )
    assert finding["stable_key"].startswith("module_fan_in:Pkg.CoreShared:5:")


def report_section(payload: dict, name: str):
    """Resolve one canonical v2 or v3 report section for parity assertions."""

    if name in payload:
        return payload[name]
    sections = payload.get("sections", {})
    if isinstance(sections, dict) and name in sections:
        return sections[name]
    raise AssertionError(f"report section is absent: {name}")


def rows_by_module(rows: list[dict]) -> dict[str, dict]:
    """Index report rows by module for compact contract assertions."""

    return {str(row["module"]): row for row in rows}


def build_lean_signal_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Create a fake-helper repository spanning declaration-only signals."""

    repo_root = tmp_path / "lean-signal-target"
    source = repo_root / "Pkg" / "Surface"
    source.mkdir(parents=True)
    (source / "Deep.lean").write_text(
        "namespace Pkg\n theorem placeholder : True := by trivial\nend Pkg\n",
        encoding="utf-8",
    )
    (repo_root / "lakefile.lean").write_text("package Pkg\n", encoding="utf-8")
    fake_bin = tmp_path / "lean-signal-bin"
    fake_bin.mkdir()
    lake = fake_bin / "lake"
    lake.write_text(
        fake_batch_lake_script(lean_signal_payload()),
        encoding="utf-8",
    )
    lake.chmod(lake.stat().st_mode | stat.S_IXUSR)
    return repo_root, fake_bin


def fake_batch_lake_script(payload: dict) -> str:
    """Return a fake Lake that wraps payloads in the framed batch protocol."""

    encoded = json.dumps(payload, sort_keys=True)
    return f"""#!/usr/bin/env python3
import json
import pathlib
import sys

if len(sys.argv) > 1 and sys.argv[1] == "build":
    raise SystemExit(0)
if "--batch" not in sys.argv:
    print(json.dumps({{
        "version": "2",
        "helperVersion": "installed-elaborated-helper-v1",
        "leanVersion": "Lean 4.fixture",
        "declarations": [],
    }}))
    raise SystemExit(0)
request = json.loads(pathlib.Path(sys.argv[-1]).read_text(encoding="utf-8"))
payload = json.loads({encoded!r})
for row in request["modules"]:
    module_payload = dict(payload)
    module_payload["file"] = row["file"]
    print(json.dumps({{
        "frame": "module",
        "protocolVersion": request["protocolVersion"],
        **row,
        "status": "ok",
        "payload": module_payload,
    }}))
print(json.dumps({{
    "frame": "summary",
    "protocolVersion": request["protocolVersion"],
    "helperVersion": "installed-fixture-helper-v2",
    "leanVersion": "Lean 4.fixture",
    "requested": len(request["modules"]),
    "completed": len(request["modules"]),
    "failed": 0,
}}))
"""


def lean_signal_payload() -> dict:
    """Return helper data spanning namespace and similarity boundaries."""

    return {
        "version": "signal-fixture-v1",
        "header": {"imports": []},
        "commands": [
            helper_declaration("Pkg.parentValue", []),
            helper_declaration("Other.Space.first", []),
            helper_declaration("Other.Space.second", []),
            helper_declaration("Pkg.left_ge_one", ["LeftOnly"]),
            helper_declaration("Pkg.right_ge_one", ["RightOnly"]),
            helper_declaration(
                "Pkg.left_eq_zero",
                ["Shared.One", "Shared.Two"],
            ),
            helper_declaration(
                "Pkg.right_eq_zero",
                ["_root_.Shared.One", "Shared.Two"],
            ),
        ],
    }


def helper_declaration(name: str, references: list[str]) -> dict:
    """Return one parser-helper declaration command."""

    return {
        "isDeclarationLike": True,
        "declarationName": name.rsplit(".", 1)[-1],
        "declarationFullName": name,
        "declarationKind": "theorem",
        "referenceCandidates": references,
    }


def environment_with_fake_bin(fake_bin: Path) -> dict[str, str]:
    """Prepend a fake toolchain directory for one installed-process test."""

    environment = dict(os.environ)
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment['PATH']}"
    return environment
