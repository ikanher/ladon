## ADDED Requirements

### Requirement: Lean Backend Preserves Text Inventory

The Lean backend SHALL preserve text-discovered module inventory when helper
extraction covers only a subset of files.

#### Scenario: root Lean extraction keeps sibling modules

- GIVEN text discovery finds a root module and imported sibling modules
- AND Lean root extraction returns only the root module
- WHEN the pipeline runs module-DAG analysis
- THEN the module-DAG summary SHALL still include the sibling modules.

#### Scenario: helper module row overrides text row

- GIVEN text discovery and Lean helper extraction both produce a row for the same
  module
- WHEN the pipeline merges module rows
- THEN the Lean helper row SHALL win for that module.

#### Scenario: declaration graph stays helper-scoped

- GIVEN Lean helper extraction returns declarations for selected files
- WHEN module rows are merged with text inventory
- THEN declaration graph analysis SHALL use only helper-provided declaration
  rows.
