from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from ladon.extraction import ModuleDiscovery
from ladon.ir import LeanModule
from ladon.pipeline import RunContext, run_pipeline


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"
REPO_ROOT = Path(__file__).parents[1]

HELPER_PAYLOAD = {
    "version": "1",
    "file": "Tiny.lean",
    "header": {
        "hasModuleDeclaration": False,
        "hasPrelude": False,
        "imports": [
            {"module": "Tiny.Core", "isPublic": False, "isMeta": False, "isAll": False},
            {"module": "Tiny.Helper", "isPublic": False, "isMeta": False, "isAll": False},
        ],
    },
    "commands": [
        {
            "isDeclarationLike": True,
            "declarationName": "localName",
            "declarationFullName": "Tiny.localName",
        },
        {
            "isDeclarationLike": False,
            "declarationName": None,
            "declarationFullName": None,
        },
    ],
}


def test_parser_helper_payload_normalizes_to_lean_module() -> None:
    from ladon.lean_extraction import (
        declarations_from_helper_payload,
        module_from_helper_payload,
        selected_helper_files,
    )

    module = module_from_helper_payload(FIXTURE_ROOT, FIXTURE_ROOT / "Tiny.lean", HELPER_PAYLOAD)
    discovery = ModuleDiscovery(
        repo_root=FIXTURE_ROOT,
        analysis_root_file=FIXTURE_ROOT / "Tiny.lean",
        analysis_root_module="Tiny",
        inventory_root="Tiny",
        modules={"Tiny": module},
    )

    assert module == LeanModule(
        name="Tiny",
        path="Tiny.lean",
        imports=("Tiny.Core", "Tiny.Helper"),
        declarations=("Tiny.localName",),
    )
    assert selected_helper_files(discovery, "root") == [FIXTURE_ROOT / "Tiny.lean"]
    declarations = declarations_from_helper_payload(module, HELPER_PAYLOAD)
    assert declarations["Tiny.localName"].kind is None
    assert declarations["Tiny.localName"].references == ()


def test_parser_helper_payload_emits_declaration_source_evidence_rows() -> None:
    from ladon.analysis.declaration_graph import summarize_declaration_graph
    from ladon.lean_extraction import declarations_from_helper_payload, module_from_helper_payload

    payload = {
        **HELPER_PAYLOAD,
        "version": "42",
        "commands": [
            {
                "isDeclarationLike": True,
                "declarationName": "localName",
                "declarationFullName": "Tiny.localName",
                "declarationKind": "theorem",
                "range": {
                    "start": {"line": 3, "column": 1},
                    "finish": {"line": 5, "column": 7},
                },
                "selectionRange": {
                    "start": {"line": 3, "column": 9},
                    "finish": {"line": 3, "column": 18},
                },
                "referenceCandidates": ["Tiny.helper"],
            }
        ],
    }
    module = module_from_helper_payload(FIXTURE_ROOT, FIXTURE_ROOT / "Tiny.lean", payload)
    declarations = declarations_from_helper_payload(
        module,
        payload,
        source_content_hash="sha256:source",
    )

    rows = summarize_declaration_graph(declarations)["declarations"]

    assert rows == [
        {
            "declaration": "Tiny.localName",
            "module": "Tiny",
            "kind": "theorem",
            "sourcePath": "Tiny.lean",
            "sourceRange": {
                "startLine": 3,
                "startColumn": 1,
                "endLine": 5,
                "endColumn": 7,
            },
            "selectionRange": {
                "startLine": 3,
                "startColumn": 9,
                "endLine": 3,
                "endColumn": 18,
            },
            "contentHash": "sha256:source",
            "extractionBackend": "lean_parser_helper",
            "extractorVersion": "42",
            "nameResolutionMethod": "parser_namespace_stack",
            "confidence": "parser_source_range",
        }
    ]


def test_text_backend_skips_lean_extraction_phase() -> None:
    result = run_pipeline(RunContext(repo_root=FIXTURE_ROOT, requested_root="Tiny.lean"))

    assert result.timing_by_phase()["lean_extraction"].status == "skipped"


def test_lean_backend_records_extraction_phase_with_fake_runner() -> None:
    modules = {
        "Tiny": LeanModule(
            name="Tiny",
            path="Tiny.lean",
            imports=("Tiny.Core",),
            declarations=("Tiny.localName",),
        )
    }
    discovery = ModuleDiscovery(
        repo_root=FIXTURE_ROOT,
        analysis_root_file=FIXTURE_ROOT / "Tiny.lean",
        analysis_root_module="Tiny",
        inventory_root="Tiny",
        modules=modules,
    )

    def fake_runner(context: RunContext, discovered: ModuleDiscovery) -> dict[str, LeanModule]:
        assert discovered.analysis_root_module == "Tiny"
        return modules

    context = RunContext(
        repo_root=FIXTURE_ROOT,
        requested_root="Tiny.lean",
        extraction_backend="lean",
        lean_extractor=fake_runner,
    )

    result = run_pipeline(context)
    timing = result.timing_by_phase()["lean_extraction"]

    assert result.discovery.modules["Tiny"] == modules["Tiny"]
    assert "Tiny.Core" in result.discovery.modules
    assert "Tiny.Helper" in result.discovery.modules
    assert timing.status == "ok"
    assert timing.counters["modules"] == 3
    assert timing.counters["declarations"] == 1


def test_parser_helper_preserves_open_scoped_parser_context(tmp_path: Path) -> None:
    """Regression for scoped syntax such as `𝓝[>]` after `open scoped Topology`."""
    lean = shutil.which("lean")
    if lean is None:
        pytest.skip("lean executable is unavailable")

    scoped_module = tmp_path / "Demo" / "Scoped.lean"
    scoped_module.parent.mkdir(parents=True)
    scoped_module.write_text(
        "\n".join(
            [
                "namespace Demo",
                'scoped syntax "foo!" : term',
                "scoped macro_rules | `(foo!) => `(Nat.zero)",
                "end Demo",
                "",
            ]
        ),
        encoding="utf-8",
    )
    main = tmp_path / "Main.lean"
    main.write_text(
        "\n".join(
            [
                "import Demo.Scoped",
                "open scoped Demo",
                "",
                "def x : Nat := foo!",
                "",
            ]
        ),
        encoding="utf-8",
    )

    subprocess.run(
        [lean, "-R", ".", "Demo/Scoped.lean", "-o", "Demo/Scoped.olean"],
        cwd=tmp_path,
        check=True,
    )
    env = {**os.environ, "LEAN_PATH": str(tmp_path)}
    proc = subprocess.run(
        [
            lean,
            "--run",
            str(REPO_ROOT / "src" / "ladon" / "lean" / "ladon_parser_helper.lean"),
            "--",
            str(main),
        ],
        check=True,
        env=env,
        stdout=subprocess.PIPE,
        text=True,
    )

    payload = json.loads(proc.stdout)
    declarations = [
        command.get("declarationFullName")
        for command in payload["commands"]
        if command.get("declarationFullName")
    ]
    assert declarations == ["x"]


def test_lean_helper_cache_reuses_payload_by_file_content(tmp_path: Path) -> None:
    from ladon.lean_extraction import cached_or_run_helper

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    source = repo_root / "Tiny.lean"
    helper = tmp_path / "helper.lean"
    source.write_text("def x := 1\n", encoding="utf-8")
    helper.write_text("-- helper\n", encoding="utf-8")
    cache_dir = tmp_path / "cache"
    calls = 0

    def runner(_repo_root: Path, _file_path: Path, _helper_path: Path) -> dict:
        nonlocal calls
        calls += 1
        return {"calls": calls}

    counters = {"lean_cache_hits": 0, "lean_cache_misses": 0}
    first = cached_or_run_helper(repo_root, source, helper, cache_dir, counters, runner)
    second = cached_or_run_helper(repo_root, source, helper, cache_dir, counters, runner)

    assert first == second == {"calls": 1}
    assert calls == 1
    assert counters == {"lean_cache_hits": 1, "lean_cache_misses": 1}


def test_lean_helper_cache_invalidates_on_source_change(tmp_path: Path) -> None:
    from ladon.lean_extraction import cached_or_run_helper

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    source = repo_root / "Tiny.lean"
    helper = tmp_path / "helper.lean"
    source.write_text("def x := 1\n", encoding="utf-8")
    helper.write_text("-- helper\n", encoding="utf-8")
    cache_dir = tmp_path / "cache"
    calls = 0

    def runner(_repo_root: Path, _file_path: Path, _helper_path: Path) -> dict:
        nonlocal calls
        calls += 1
        return {"calls": calls}

    counters = {"lean_cache_hits": 0, "lean_cache_misses": 0}
    cached_or_run_helper(repo_root, source, helper, cache_dir, counters, runner)
    source.write_text("def x := 2\n", encoding="utf-8")
    second = cached_or_run_helper(repo_root, source, helper, cache_dir, counters, runner)

    assert second == {"calls": 2}
    assert counters == {"lean_cache_hits": 0, "lean_cache_misses": 2}
