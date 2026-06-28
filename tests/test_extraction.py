from __future__ import annotations

from pathlib import Path

from ladon.analysis.module_dag import summarize_module_dag
from ladon.extraction import (
    discover_modules,
    parse_imports,
    parse_import_sites,
    parse_lean_module,
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


def test_parse_lean_module_tags_generated_files_from_generic_conventions(tmp_path: Path) -> None:
    generated = tmp_path / "GeneratedRoute.lean"
    handwritten = tmp_path / "Owner.lean"
    generated.write_text("def generatedValue : Nat := 1\n", encoding="utf-8")
    handwritten.write_text("-- owner module\ndef ownerValue : Nat := 1\n", encoding="utf-8")

    generated_module = parse_lean_module(tmp_path, generated)
    handwritten_module = parse_lean_module(tmp_path, handwritten)

    assert generated_module.tags == ("generated",)
    assert handwritten_module.tags == ()


def test_parse_lean_module_records_lexical_markers_without_comment_trust_false_positives(tmp_path: Path) -> None:
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
