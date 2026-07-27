from __future__ import annotations

import hashlib
from pathlib import Path

import ladon.extraction as extraction
from ladon.analysis.module_dag import summarize_module_dag
from ladon.extraction import (
    discover_modules,
    parse_imports,
    parse_import_sites,
    parse_lean_module,
    parse_text_declarations,
)
from ladon.lexical_declarations import (
    normalize_declaration_block,
    normalize_declaration_source_shape,
)


def test_parse_imports_accepts_public_and_import_all_forms() -> None:
    text = """
public import Mathlib.Data.Set.Basic
public meta import Mathlib.Tactic.Common
import all Init.Data.Fin.Fold
import Plain.Module -- trailing comment
"""

    assert parse_imports(text) == (
        "Mathlib.Data.Set.Basic",
        "Mathlib.Tactic.Common",
        "Init.Data.Fin.Fold",
        "Plain.Module",
    )


def test_parse_import_sites_preserves_line_and_text_evidence() -> None:
    text = """
import Alpha.Core

public import Beta.Core -- trailing comment
"""

    sites = parse_import_sites(text)

    assert [(site.module, site.line, site.text) for site in sites] == [
        ("Alpha.Core", 2, "import Alpha.Core"),
        ("Beta.Core", 4, "public import Beta.Core"),
    ]


def test_parse_imports_ignores_line_comments_and_block_comment_examples() -> None:
    text = """
-- import Not.A.Dependency
/-!
```lean
import Mathlib.Tactic.Rify
```
-/
/- nested comment start
  /- import Also.Not.Dependency -/
-/
public import Real.Dependency
"""

    assert parse_imports(text) == ("Real.Dependency",)


def test_parse_lean_module_ignores_docstring_self_import(tmp_path: Path) -> None:
    module = tmp_path / "Example.lean"
    module.write_text(
        """
/-!
Documentation example:

```lean
import Example
```
-/

def exampleValue : Nat := 1
""",
        encoding="utf-8",
    )

    parsed = parse_lean_module(tmp_path, module)
    summary = summarize_module_dag({parsed.name: parsed}, chosen_roots=(parsed.name,))

    assert parsed.imports == ()
    assert summary["acyclic"] is True
    assert summary["cyclic_component_count"] == 0


def test_parse_lean_module_reads_public_import_dependencies(tmp_path: Path) -> None:
    root = tmp_path / "Root.lean"
    root.write_text(
        """
public import Root.Core
public meta import Root.Meta
import all Root.All
""",
        encoding="utf-8",
    )

    parsed = parse_lean_module(tmp_path, root)

    assert parsed.imports == ("Root.Core", "Root.Meta", "Root.All")
    assert parsed.import_sites[0].line == 2
    assert parsed.line_count == 4


def test_parse_lean_module_masks_source_once(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "Root.lean"
    root.write_text(
        """\
import Root.Core
-- sorry and def fake are comments
theorem kept : True := by trivial
""",
        encoding="utf-8",
    )
    original = extraction.mask_lean_source
    calls = 0

    def counted(text: str) -> extraction.LeanSourceMasks:
        nonlocal calls
        calls += 1
        return original(text)

    monkeypatch.setattr(extraction, "mask_lean_source", counted)

    parsed = parse_lean_module(tmp_path, root)

    assert calls == 1
    assert parsed.imports == ("Root.Core",)
    assert parsed.declarations == ("kept",)


def test_parse_lean_module_tags_generated_files_from_generic_conventions(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "GeneratedRoute.lean"
    handwritten = tmp_path / "Owner.lean"
    generated.write_text("def generatedValue : Nat := 1\n", encoding="utf-8")
    handwritten.write_text(
        "-- owner module\ndef ownerValue : Nat := 1\n", encoding="utf-8"
    )

    generated_module = parse_lean_module(tmp_path, generated)
    handwritten_module = parse_lean_module(tmp_path, handwritten)

    assert generated_module.tags == ("generated",)
    assert handwritten_module.tags == ()


def test_parse_lean_module_records_lexical_markers_without_comment_trust_false_positives(
    tmp_path: Path,
) -> None:
    module = tmp_path / "Owner.lean"
    module.write_text(
        """
-- TODO: refactor this
-- sorry in a comment is not a trust construct
axiom externalFact : True
theorem owner : True := by
  admit
""",
        encoding="utf-8",
    )

    parsed = parse_lean_module(tmp_path, module)

    assert [(marker.kind, marker.line) for marker in parsed.lexical_markers] == [
        ("todo", 2),
        ("axiom", 4),
        ("admit", 6),
    ]


def test_trailing_mask_trim_preserves_final_block_and_comment_markers(
    tmp_path: Path,
) -> None:
    text = """\
import Owner.Core
theorem final_owner : True := by trivial
-- TODO: trailing review note
-- theorem comment_only : False := by contradiction

"""
    path = tmp_path / "Owner.lean"
    path.write_text(text, encoding="utf-8")

    parsed = parse_lean_module(tmp_path, path)
    declaration = parsed.declaration_evidence[0]
    block = text[declaration.block_start_offset :]

    assert parsed.imports == ("Owner.Core",)
    assert parsed.declarations == ("final_owner",)
    assert declaration.block_end_offset == len(text)
    assert declaration.normalized_block_sha256 == hashlib.sha256(
        normalize_declaration_block(block).encode("utf-8")
    ).hexdigest()
    assert declaration.normalized_source_shape_sha256 == hashlib.sha256(
        normalize_declaration_source_shape(block).encode("utf-8")
    ).hexdigest()
    assert [(row.kind, row.line) for row in parsed.lexical_markers] == [
        ("todo", 3)
    ]


def test_text_declarations_mask_comments_strings_and_record_supported_forms(
    tmp_path: Path,
) -> None:
    text = """\
/- axiom BlockFake : True -/
def quoted : String := "constant StringFake : Nat"
-- opaque LineFake : Nat
@[simp] private theorem kept_theorem : True := by trivial
noncomputable def kept_def : Nat := 1
opaque kept_opaque : Nat
axiom kept_axiom : True
constant kept_constant : Nat
syntax "custom" : term
"""
    path = tmp_path / "Owner.lean"
    path.write_text(text, encoding="utf-8")

    rows = parse_text_declarations(text)
    parsed = parse_lean_module(tmp_path, path)

    assert [(row.kind, row.name, row.line) for row in rows] == [
        ("def", "quoted", 2),
        ("theorem", "kept_theorem", 4),
        ("def", "kept_def", 5),
        ("opaque", "kept_opaque", 6),
        ("axiom", "kept_axiom", 7),
        ("constant", "kept_constant", 8),
    ]
    assert parsed.declarations == tuple(row.name for row in rows)
    assert all(row.authority == "lexical_text" for row in rows)
    assert all("not a complete Lean parse" in row.nonclaim for row in rows)
    assert text[rows[0].start_offset : rows[0].end_offset] == "quoted"


def test_discover_modules_accepts_directory_root(tmp_path: Path) -> None:
    package = tmp_path / "Pkg"
    subdir = package / "Sub"
    subdir.mkdir(parents=True)
    (package / "Root.lean").write_text("def root : Nat := 1\n", encoding="utf-8")
    (subdir / "Owner.lean").write_text("import Pkg.Sub.Helper\n", encoding="utf-8")
    (subdir / "Helper.lean").write_text("def helper : Nat := 1\n", encoding="utf-8")

    discovery = discover_modules(tmp_path, "Pkg/Sub")

    assert discovery.analysis_root_module == "Pkg.Sub"
    assert discovery.inventory_root == "Pkg.Sub"
    assert sorted(discovery.modules) == ["Pkg.Sub.Helper", "Pkg.Sub.Owner"]
