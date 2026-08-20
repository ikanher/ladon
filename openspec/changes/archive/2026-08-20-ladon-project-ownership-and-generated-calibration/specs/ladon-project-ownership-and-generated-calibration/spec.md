## ADDED Requirements

### Requirement: Calibrated project populations

Ladon SHALL assign every included module and declaration with sufficient
evidence to exactly one primary population: `target_owned`, `imported`,
`compiler_generated`, or `project_generated`. Classification SHALL use, in
order, target source-root ownership, explicit project-generated-family policy,
and Lean-supplied compiler-generation evidence. A row with insufficient or
contradictory evidence MUST remain explicitly unclassified and MUST NOT enter a
calibrated ranking.

#### Scenario: Authored target module

- **WHEN** a source module is inside a configured target source root and neither project-generated policy nor Lean compiler-generation evidence applies
- **THEN** Ladon classifies the module and its source declarations as `target_owned`

#### Scenario: Imported declaration

- **WHEN** a resolved declaration belongs to a dependency module outside every configured target source root
- **THEN** Ladon classifies it as `imported` even when the dependency is available in the loaded Lean environment

#### Scenario: Compiler-generated declaration

- **WHEN** the Lean backend supplies compiler-generation evidence for a declaration in an otherwise target-owned source module
- **THEN** Ladon classifies that declaration as `compiler_generated` and records the Lean backend and toolchain as its classification evidence

#### Scenario: Configured generated source

- **WHEN** a target source module matches exactly one configured project-generated family
- **THEN** Ladon classifies the module and its non-compiler-generated declarations as `project_generated` and attaches the configured family identity

#### Scenario: Contradictory classification evidence

- **WHEN** available ownership or generation evidence cannot select one primary population under the documented precedence
- **THEN** Ladon preserves the row as unclassified with a structured diagnostic instead of silently choosing a population

### Requirement: Explicit generated-family provenance

Ladon SHALL accept a repository-relative, versioned policy that assigns stable
family identifiers to project-generated path or module patterns. Each family
MUST preserve the matched rule, policy digest, and any supplied generator name,
generator version, manifest identity, or source anchor. Host-specific absolute
paths and target-specific built-in names MUST NOT be required.

#### Scenario: Manifest-backed generated family

- **WHEN** a portable policy maps several generated source modules to one family and supplies generator and manifest metadata
- **THEN** every matched row carries the same stable family identifier and the quoted generator and manifest provenance

#### Scenario: Pattern-only generated family

- **WHEN** a portable policy maps generated modules to a family without a generator manifest
- **THEN** Ladon records policy-backed family membership and an explicit nonclaim that generator execution or freshness was not verified

#### Scenario: Overlapping family rules

- **WHEN** one source module matches different configured family identifiers without an explicit deterministic resolution
- **THEN** Ladon rejects the ambiguous policy with source-locatable rule diagnostics before promoting generated-family metrics

#### Scenario: Generated-looking authored name

- **WHEN** an authored target module contains a generated-looking token in its path or declaration name but matches no configured family and has no Lean compiler-generation evidence
- **THEN** Ladon keeps it in `target_owned` and MUST NOT promote a filename heuristic to project-generated provenance

### Requirement: Population-calibrated metrics

Every population-sensitive table, ranking, finding, and summary SHALL identify
its population, numerator, denominator, and exclusions. Default owner-focused
rankings SHALL use `target_owned` rows; imported, compiler-generated,
project-generated, unclassified, and unfiltered views SHALL remain separately
inspectable.

#### Scenario: Generated rows dominate raw fan-in

- **WHEN** many project-generated modules and one target-owned module import the same target-owned module
- **THEN** Ladon reports distinct raw and population-calibrated counts so generated importers cannot inflate the target-owned importer ranking

#### Scenario: Imported declarations dominate raw centrality

- **WHEN** imported declarations have higher raw centrality than every target-owned declaration
- **THEN** Ladon preserves imported centrality in its named population while the default owner-focused ranking remains based on target-owned declarations

#### Scenario: Population filter selects no rows

- **WHEN** a requested calibrated population is empty in the selected analysis scope
- **THEN** Ladon emits an explicit zero-row population with its denominator and exclusions rather than falling back to another population

### Requirement: Generated-family aggregation

Project-generated families SHALL be available as deterministic aggregate graph
and metric rows with member counts, source-size totals, declaration totals,
import relationships, and bounded representative members. Family aggregation
MUST preserve access to raw members and MUST NOT claim that repetition or size
proves a generator defect.

#### Scenario: Repetitive generated row family

- **WHEN** a configured family contains a data owner, many row-local proof modules, and an aggregation facade
- **THEN** Ladon emits one inspectable family aggregate while retaining the data, row, and facade members in the raw population

#### Scenario: Large generated family finding

- **WHEN** a generated family crosses a configured review threshold
- **THEN** the finding cites the family evidence and states that it is review pressure rather than proof that the generator or generated proofs are incorrect

### Requirement: Classification authority preservation

Population and family classifications SHALL describe source ownership and
generation provenance only. They MUST NOT upgrade lexical evidence to Lean
authority, downgrade an elaborated dependency, assert proof correctness, or
assert that a configured generator produced the current bytes.

#### Scenario: Lexically discovered configured module

- **WHEN** the text backend classifies a module through project-generated policy
- **THEN** the row retains lexical source authority and policy provenance without acquiring Lean-elaborated or generator-replay authority

#### Scenario: Lean-generated declaration

- **WHEN** the Lean backend identifies a compiler-generated declaration
- **THEN** the report may claim Lean-backed generation classification but MUST NOT infer theorem truth or transitive trust from that classification

### Requirement: Deterministic portable calibration

Ladon SHALL produce identical classifications, family aggregates, stable
identifiers, and ordering for equivalent source inventories, normalized
repository-relative policies, selected scopes, and backend evidence. Required
regression gates MUST use portable fixtures and MUST NOT depend on a mutable
external repository.

#### Scenario: Repeated calibrated analysis

- **WHEN** the same portable fixture and normalized family policy are analyzed twice with equivalent explicit metadata
- **THEN** the population rows, family aggregates, diagnostics, identifiers, and normalized JSON bytes are identical

#### Scenario: Portable four-population fixture

- **WHEN** a fixture contains an authored target module, an imported dependency, a Lean-marked synthetic declaration, and a policy-marked generated family
- **THEN** the required gate observes all four primary populations and verifies that each remains separately queryable

#### Scenario: Portable negative calibration fixture

- **WHEN** a fixture contains generated-looking authored names, unmatched family patterns, and an intentionally ambiguous family policy
- **THEN** the required gate verifies no heuristic promotion, explicit unmatched behavior, and deterministic rejection of the ambiguous policy
