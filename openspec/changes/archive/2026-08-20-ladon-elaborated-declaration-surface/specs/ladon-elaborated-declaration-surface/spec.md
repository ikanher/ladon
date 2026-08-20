## ADDED Requirements

### Requirement: Lean-owned declaration surface
For every successfully extracted declaration, Ladon SHALL expose its fully
qualified name, kind, module, source range, source hash, backend/toolchain
identity, and elaborated-type availability.

#### Scenario: Root theorem
- **WHEN** Lean extraction succeeds for a theorem in the selected root
- **THEN** the report contains a source-locatable declaration row with Lean authority and its rendered elaborated type

#### Scenario: Supported declaration kinds
- **WHEN** fixtures contain theorem, definition, axiom, opaque declaration, and unsafe declaration forms
- **THEN** each row preserves its actual declaration kind and relevant status

### Requirement: Structured theorem statement
The Lean backend SHALL decompose leading elaborated binders or premises from the
conclusion and SHALL retain the complete bounded rendered type.

#### Scenario: Implicit and explicit binders
- **WHEN** a theorem type contains implicit parameters, typeclass parameters, and explicit premises
- **THEN** the surface distinguishes those binders and renders the remaining conclusion

#### Scenario: Imported notation
- **WHEN** a statement uses imported notation
- **THEN** the elaborated type remains available with the printer/toolchain provenance needed to interpret it

### Requirement: Separate dependency authorities
Ladon MUST keep parser identifier candidates, elaborated type constants, and
elaborated value/proof constants in separate fields and graph edge kinds.

#### Scenario: Parser and elaborator disagree
- **WHEN** a lexical identifier candidate does not occur as a constant in the elaborated expression
- **THEN** it remains a parser candidate and is not promoted to an elaborated dependency

#### Scenario: Direct proof dependency
- **WHEN** the elaborated value expression directly references another constant
- **THEN** Ladon emits a value-dependency edge with Lean authority

### Requirement: Imported dependency targets
Resolved imported constants SHALL be representable even when their complete
declaration rows were not extracted.

#### Scenario: Root-only imported dependency
- **WHEN** a root declaration references an imported constant outside the extracted declaration inventory
- **THEN** the graph contains a named imported target stub with resolution and provenance rather than an unresolved parser-only row

#### Scenario: Inventory join
- **WHEN** inventory extraction later supplies the imported declaration row
- **THEN** Ladon joins it deterministically by fully qualified name without duplicating the target

### Requirement: Bounded source navigation
Declaration output SHALL include a bounded statement excerpt and proof/body
presence metadata with explicit truncation information.

#### Scenario: Large proof body
- **WHEN** a declaration has a proof body larger than configured report bounds
- **THEN** Ladon includes the statement navigation surface and truncation metadata without serializing the full proof

### Requirement: Bounded body metadata
Body metadata SHALL remain limited to source navigation, proof presence/form,
and truncation state and MUST NOT become tactic or goal-state analysis.

#### Scenario: Tactic proof body
- **WHEN** the parser observes a tactic proof body
- **THEN** Ladon records its range and proof form without emitting tactic heads, a tactic skeleton, InfoTree data, or goal-state claims

### Requirement: Lean trust-footprint facts
Declared axioms, unsafe status, and direct `sorryAx` or axiom references SHALL
be reported with scope and Lean authority.

#### Scenario: Direct sorry exposure
- **WHEN** a declaration's elaborated value directly references `sorryAx`
- **THEN** the declaration has a direct sorry-footprint row with Lean/toolchain provenance

#### Scenario: No transitive evidence
- **WHEN** only direct expression traversal was performed
- **THEN** the report does not claim a complete transitive axiom footprint

### Requirement: Valid unavailable state
Reports MUST remain schema-valid when elaborated declaration data is unavailable
or partially extracted.

#### Scenario: Text backend
- **WHEN** a caller selects the text backend
- **THEN** elaborated declaration surface status is skipped or unavailable with a textual reason and no fabricated Lean fields

### Requirement: No proof-truth claim
Declaration surfaces and dependency facts MUST be described as navigation and
review evidence, not proof correctness or theorem truth.

#### Scenario: Successfully elaborated theorem
- **WHEN** a theorem surface is present
- **THEN** the report states what Lean artifact was observed without asserting that Ladon independently verified the theorem

### Requirement: Non-skippable real-Lean acceptance
The declaration-surface child MUST provide a required real-Lean gate whose
missing toolchain status is a failure rather than a test skip.

#### Scenario: Declaration child closeout
- **WHEN** declaration-surface completion is evaluated
- **THEN** the required gate provisions the fixture's pinned reference toolchain and covers every declared declaration kind, statement decomposition, dependency split, and trust fixture on tracked Lake inputs
