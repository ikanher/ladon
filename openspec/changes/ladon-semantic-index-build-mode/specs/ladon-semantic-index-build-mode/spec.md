## ADDED Requirements

### Requirement: Build mode is explicit
`proof-search index build` SHALL support `lexical`, `semantic`, and `hybrid` modes; omission of the mode SHALL remain lexical during compatibility and SHALL never execute Lean implicitly.

#### Scenario: Mode is omitted
- **WHEN** an existing build command omits `--mode`
- **THEN** it performs the lexical build and reports that no target Lean environment was loaded

### Requirement: Semantic extraction is cacheable and sound
Semantic module cache keys MUST include toolchain, Lean, helper/protocol, source, Lake state, transitive local imports, and compiled-artifact identities until a narrower invalidation proof is implemented.

#### Scenario: Imported source changes
- **WHEN** a transitive local import identity differs
- **THEN** dependent module semantic artifacts are not reused as fresh

### Requirement: Publication is atomic and validated
The builder SHALL assemble a fresh temporary database, validate schema, foreign keys, integrity, coverage, query plans, size, and optimization, then atomically replace the prior generation.

#### Scenario: Build is interrupted
- **WHEN** semantic extraction or validation fails before replacement
- **THEN** the previously published database remains intact and queryable

### Requirement: Source-only modules remain visible
Configured Lean source roots SHALL contribute source-only modules and explicit semantic statuses even when files are untracked, unimported, or lack compiled state.

#### Scenario: Requested untracked owner exists
- **WHEN** a configured source file exists on disk but is not part of compiled imports
- **THEN** status exposes it as source-only or an explicit omission rather than a fresh empty success
