## ADDED Requirements

### Requirement: Internal missing-import scope
Missing-import classification SHALL use project namespace ownership rather than
restricting candidates to the exact selected owner module.

#### Scenario: Missing sibling module
- **WHEN** module `Pkg.Owner` imports absent module `Pkg.Missing` and `Pkg` is a discovered project namespace
- **THEN** Ladon emits one internal missing-import row with the source import location

#### Scenario: Missing external module
- **WHEN** a source imports an absent module outside every discovered or configured project namespace
- **THEN** Ladon does not label that import as an internal missing import

### Requirement: Truthful fan-in populations
Every fan-in table and finding MUST count exactly the module population named by
its identifier and rendered description.

#### Scenario: Generated importers of handwritten target
- **WHEN** five generated modules and one handwritten module import a handwritten target
- **THEN** the handwritten fan-in count is one and the generic fan-in count may be six

#### Scenario: Generated target exclusion
- **WHEN** a generated target has high fan-in
- **THEN** it is excluded from a handwritten-target table and remains available in an explicitly generated or generic population

### Requirement: Comment-safe text declaration inventory
The text backend SHALL mask comments and string literals while preserving
source offsets before recognizing supported Lean declarations.

#### Scenario: Declaration-like comment
- **WHEN** a comment or string contains text such as `axiom Fake : True`
- **THEN** that text creates no declaration and cannot change facade classification

#### Scenario: Modified declaration forms
- **WHEN** source contains supported forms such as `noncomputable def`, `opaque`, `axiom`, or `constant`
- **THEN** the text inventory records the declaration kind, name, and source location

### Requirement: Honest text-backend limits
Text declaration evidence MUST identify its lexical authority and MUST NOT claim
complete Lean syntax or elaboration coverage.

#### Scenario: Unsupported declaration syntax
- **WHEN** the text scanner cannot classify a declaration form
- **THEN** the report preserves the text-backend limitation without inventing an elaborated declaration fact

### Requirement: Conventional namespace compatibility
Namespace drift SHALL distinguish ordinary parent/module namespace layouts from
unrelated or policy-forbidden namespace placement.

#### Scenario: Parent namespace convention
- **WHEN** module `Pkg.Semantics.Propagation` declares names under namespace `Pkg.Semantics`
- **THEN** Ladon does not emit one namespace-drift finding per declaration

#### Scenario: Unrelated namespace
- **WHEN** the dominant declaration namespace is unrelated to the module path and no policy suppresses it
- **THEN** Ladon emits a source-backed namespace compatibility finding

### Requirement: Concrete evidence for high proof-family similarity
Coarse unresolved-reference classes MUST NOT by themselves produce the highest
proof-family similarity confidence or an uncapped perfect score.

#### Scenario: Same coarse classes without identifier overlap
- **WHEN** two declarations share unresolved classifications but have no resolved-declaration or concrete normalized-identifier overlap
- **THEN** their similarity remains below the high-confidence band and explains the coarse-only evidence

#### Scenario: Concrete dependency overlap
- **WHEN** two declarations share concrete resolved declarations or normalized identifiers
- **THEN** that overlap may contribute to high similarity with its evidence exposed

### Requirement: Deduplicated finding promotion
Semantically equivalent findings over the same evidence and population SHALL
share a stable key and SHALL be promoted at most once.

#### Scenario: Generic and handwritten duplicate
- **WHEN** generic and handwritten fan analysis describe the same target, count, population, and recommendation
- **THEN** the default finding list contains one promoted row while raw metric tables remain inspectable

### Requirement: Authority-labeled trust markers
Text-observed missing imports, `sorry` markers, and axiom declarations SHALL be
raw review evidence with lexical authority; Lean-confirmed footprints SHALL
remain separate elaborated facts.

#### Scenario: Text-only sorry marker
- **WHEN** the text backend observes a non-comment `sorry`
- **THEN** the raw row identifies lexical authority, does not claim a Lean-elaborated dependency or theorem verdict, and is not promoted as a new default finding by this change
