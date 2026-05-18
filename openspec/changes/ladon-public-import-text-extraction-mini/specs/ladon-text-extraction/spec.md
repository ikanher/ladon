## ADDED Requirements

### Requirement: Text Extraction Recognizes Lean Import Modifiers

Ladon SHALL extract module dependencies from the Lean import forms used by
current mathlib without requiring Lean elaboration.

#### Scenario: public imports are dependencies

- GIVEN a Lean source file containing `public import Mathlib.Data.Set.Basic`
- WHEN text extraction parses the file
- THEN the module dependency list SHALL include `Mathlib.Data.Set.Basic`.

#### Scenario: public meta imports are dependencies

- GIVEN a Lean source file containing `public meta import Mathlib.Tactic.Common`
- WHEN text extraction parses the file
- THEN the module dependency list SHALL include `Mathlib.Tactic.Common`.

#### Scenario: import-all syntax is supported

- GIVEN a Lean source file containing `import all Init.Data.Fin.Fold`
- WHEN text extraction parses the file
- THEN the module dependency list SHALL include `Init.Data.Fin.Fold`.

### Requirement: Text Extraction Ignores Documentation Import Examples

Ladon SHALL NOT treat imports inside Lean block comments or module docstrings as
module dependencies.

#### Scenario: docstring imports are not dependencies

- GIVEN a Lean source file containing a block comment with
  `import Mathlib.Tactic.Rify`
- WHEN text extraction parses the file
- THEN the module dependency list SHALL NOT include `Mathlib.Tactic.Rify` from
  that comment.

#### Scenario: docstring self-imports do not create cycles

- GIVEN a module whose only self-import text occurs inside a documentation
  example
- WHEN the module DAG is summarized
- THEN Ladon SHALL NOT report a cyclic component for that documentation
  example.
