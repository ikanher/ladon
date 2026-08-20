## ADDED Requirements

### Requirement: Audit commands as first-class review surfaces

Ladon SHALL recognize supported `#check` and `#print axioms` commands in Lean
source as audit-command rows with command kind, containing module, source range,
bounded subject text, backend, and authority. A module containing supported
audit commands but no declarations MUST remain an inspectable command-only
review root rather than being reported as an empty declaration surface.

#### Scenario: Command-only audit facade

- **WHEN** a selected root contains imports, `#check` commands, and `#print axioms` commands but declares no constants
- **THEN** Ladon reports a command-only audit surface with all supported commands and does not fabricate root-owned declarations

#### Scenario: Ordinary theorem owner

- **WHEN** a selected root declares a theorem and contains no supported audit command
- **THEN** Ladon reports the declaration surface normally and MUST NOT label the module command-only

#### Scenario: Commented audit syntax

- **WHEN** `#check` or `#print axioms` text occurs only inside comments or string literals
- **THEN** Ladon emits no audit-command row for that text

### Requirement: Check-command intent and resolution

A `#check` row SHALL represent a request to inspect a term or declaration, not
a new declaration, theorem endorsement, or proof result. Text extraction SHALL
preserve lexical intent; when Lean-backed resolution is available, Ladon SHALL
attach the resolved declaration or elaborated term evidence as a separate
authority-bearing result.

#### Scenario: Text-only check command

- **WHEN** the text backend observes `#check` applied to a declaration name
- **THEN** Ladon records the lexical command intent and source location without claiming name resolution or elaboration

#### Scenario: Lean-resolved check command

- **WHEN** the Lean backend resolves a `#check` subject to an imported declaration
- **THEN** Ladon links the command to the imported declaration owner with Lean and toolchain provenance while preserving that the selected root does not own that declaration

#### Scenario: Unresolved check command

- **WHEN** a supported `#check` command cannot be resolved by the selected backend
- **THEN** Ladon retains the command row with unresolved status and a structured reason instead of inventing a declaration edge

### Requirement: Axiom-query intent and trust evidence

A `#print axioms` row SHALL distinguish lexical query intent from any
Lean-supplied axiom result. Ladon MUST NOT infer a transitive axiom footprint
from command text alone, and a captured Lean result MUST retain its exact
backend, toolchain, scope, and completeness boundary.

#### Scenario: Text-only axiom query

- **WHEN** the text backend observes `#print axioms` for a declaration
- **THEN** Ladon records only axiom-query intent and an explicit nonclaim that no axiom set was established

#### Scenario: Lean-backed axiom result

- **WHEN** the Lean backend resolves the queried declaration and supplies its axiom-query result
- **THEN** Ladon records the result as Lean-supplied trust-footprint evidence with toolchain provenance and without claiming independent verification or theorem truth

#### Scenario: Query without captured result

- **WHEN** a Lean-backed run preserves an axiom query but does not capture a complete result
- **THEN** Ladon reports the result state as unavailable or partial and MUST NOT substitute direct dependency traversal as a complete axiom answer

### Requirement: Bounded resource-directive surface

Ladon SHALL report supported numeric `set_option maxHeartbeats` and
`set_option maxRecDepth` directives with their raw value, normalized meaning
when defined by Lean, lexical scope, containing module, and source range.
Resource directives SHALL be cost-risk navigation evidence only and MUST NOT
be treated as measured runtime, proof failure, proof authority, or theorem
truth.

#### Scenario: Scoped finite heartbeat override

- **WHEN** a declaration is wrapped by a numeric `set_option maxHeartbeats` directive with an `in` scope
- **THEN** Ladon records the finite value and declaration-local lexical scope without claiming that the full budget was consumed

#### Scenario: Unlimited heartbeat override

- **WHEN** source contains numeric `set_option maxHeartbeats 0` under Lean semantics where zero disables the limit
- **THEN** Ladon preserves the raw zero, marks the normalized setting as unlimited, and emits only review-oriented resource pressure

#### Scenario: Module-level recursion override

- **WHEN** source contains a module-level numeric `set_option maxRecDepth` directive
- **THEN** Ladon records its module scope and value without attaching it to unrelated modules in the import closure

#### Scenario: Directive-like comment

- **WHEN** a resource directive occurs only in a comment or string literal
- **THEN** Ladon emits no resource-directive row

#### Scenario: Unsupported option expression

- **WHEN** a supported option name is followed by syntax whose numeric value or scope cannot be parsed safely
- **THEN** Ladon preserves bounded lexical evidence with an unparsed diagnostic and MUST NOT guess a normalized value

### Requirement: Audit ownership and nonclaims

Every audit-command and resource-directive row SHALL preserve the difference
between the containing audit module, the referenced declaration owner, the
evidence backend, and any quoted result authority. Renderers and rankings MUST
NOT promote audit presence, repeated checks, axiom-query intent, or raised
resource limits into proof completion, publication readiness, or defect claims.

#### Scenario: Repeated checks of one imported theorem

- **WHEN** several audit facades check the same imported theorem
- **THEN** Ladon preserves each command location while retaining one referenced declaration identity and MUST NOT increase the theorem's proof authority

#### Scenario: Resource-heavy successful theorem

- **WHEN** a theorem is adjacent to a large resource override and Lean-backed declaration extraction succeeds
- **THEN** Ladon keeps resource pressure and declaration authority in separate fields and does not classify the theorem as failed or untrusted solely from the override

### Requirement: Stable bounded audit reporting

Audit-command surfaces SHALL use stable identifiers derived from normalized
module, command kind, source anchor, and subject identity. JSON and text
rendering SHALL consume the same registered report data, preserve total counts
and authority, bound displayed subject text, and order rows deterministically.

#### Scenario: Equivalent repeated audit

- **WHEN** equivalent source and explicit metadata are analyzed twice
- **THEN** audit-command and resource-directive identifiers, ordering, counts, authority fields, and normalized JSON bytes are identical

#### Scenario: Compact text projection

- **WHEN** a command-only facade contains more audit rows than the text display limit
- **THEN** compact text reports complete totals and omitted-row counts while every displayed row matches the canonical JSON identifier and authority

### Requirement: Partial and unavailable audit states

Audit-command extraction SHALL remain schema-valid when text parsing is
partial, Lean resolution times out, or the Lean backend is not selected.
Successful lexical rows MUST remain available alongside structured per-row or
phase diagnostics, and missing Lean evidence MUST NOT be fabricated.

#### Scenario: Lean resolution timeout

- **WHEN** Lean resolution times out after lexical audit commands were extracted
- **THEN** Ladon preserves the lexical rows, marks Lean resolution partial or failed with a structured reason, and emits no invented Lean-owned result

#### Scenario: Text backend selected

- **WHEN** the caller selects text extraction for a command-only audit facade
- **THEN** Ladon completes the lexical audit surface and marks Lean resolution and axiom results unavailable by explicit backend policy

### Requirement: Portable positive and negative audit fixtures

Required regression gates SHALL use tracked portable Lean fixtures that cover
command-only facades, imported subjects, axiom-query intent, finite and
unlimited resource directives, unresolved references, comments, strings, and
ordinary declaration-only modules. Mutable external repositories MUST remain
optional observational evidence.

#### Scenario: Portable positive audit fixture

- **WHEN** a fixture contains a command-only facade with a resolvable `#check`, a resolvable `#print axioms`, a finite heartbeat override, an unlimited heartbeat override, and a recursion-depth override
- **THEN** the required gate verifies source anchors, resolution ownership, separate authority classes, normalized resource meanings, and command-only root preservation

#### Scenario: Portable negative audit fixture

- **WHEN** a fixture contains command and directive syntax only in comments or strings, an unresolved check subject, and an ordinary theorem owner with no audit commands
- **THEN** the required gate verifies comment-safe exclusion, honest unresolved status, no fabricated trust result, and no false command-only classification
