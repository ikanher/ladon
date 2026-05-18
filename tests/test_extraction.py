from __future__ import annotations

from pathlib import Path

from ladon.analysis.module_dag import summarize_module_dag
from ladon.extraction import parse_imports, parse_lean_module


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
