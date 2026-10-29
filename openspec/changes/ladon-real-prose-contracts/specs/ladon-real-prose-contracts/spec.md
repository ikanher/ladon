## Purpose

Preserve attributed Real estimate readings and connect their exact typed
propositions to formal evidence without confusing interpretation with truth.

## ADDED Requirements

### Requirement: Elaborate authored propositions without asserting them
The system SHALL consume an existing source-bound interpretation and a pinned Lean context, preserve the attributed formula, and observe its elaborated proposition without introducing a theorem, axiom or proof placeholder. Successful elaboration SHALL NOT grant fidelity review, predicate admission or theorem authority.

#### Scenario: A syntactically valid estimate has no known proof
- **WHEN** an authored Real estimate elaborates as a proposition
- **THEN** observation preserves its typed expression and unresolved proof authority without requiring a proof of the estimate

#### Scenario: Interpretation cannot elaborate
- **WHEN** the exact lowered formula has an ill-typed symbol application
- **THEN** the operation reports an elaboration failure and creates no admitted contract

### Requirement: Preserve global and set-indexed bound scopes
The system SHALL distinguish bounds quantified over their full domain from bounds over an explicit set. It SHALL retain all typed binders, guards, operator parameters, point domains and constant dependencies. It SHALL NOT insert a set binder or discard a parameter merely to match the other statement.

#### Scenario: Bound has no set parameter
- **WHEN** the source uses a predicate with function, order and bound arguments
- **THEN** its global scope is explicit and no synthetic set argument is attributed to the source

#### Scenario: Formalization has an additional parameter domain
- **WHEN** the formal estimate quantifies a parameter absent from the prose
- **THEN** connecting the statements requires an explicit checked specialization and preserves its premises

### Requirement: Preserve exact order and coefficient meanings
The system SHALL retain original order and coefficient expressions. Deriving a literal loss or canonical Real product through aliases SHALL require checked equivalence in the pinned context. Unsupported expressions SHALL remain named obligations. Transport SHALL retain actual factors and their dependency scopes, including order-dependent factors.

#### Scenario: Alias names a derivative shift
- **WHEN** the authored interpretation uses a named shift function
- **THEN** a displayed literal loss requires checked evidence linking that function to the claimed shift

#### Scenario: Coordinate norm conversion rescales a bound
- **WHEN** a bridge changes the bound by an order-dependent factor
- **THEN** the connection retains that factor and cannot report an identity conversion or stronger uniform constant

### Requirement: Separate authored and admitted owners
Authored Real representations SHALL use separately versioned closed schemas and exact native interpretation/source owners. They SHALL retain alternative identities, fidelity qualifications and formula origins. Existing extracted Real and Nat schemas SHALL keep their meanings. Semantic consumers SHALL explicitly reject unsupported authored representations.

#### Scenario: Authored reading is offered to an extracted-contract consumer
- **WHEN** an authored Real reading has no required admission evidence
- **THEN** the consumer reports unsupported or unresolved rather than accepting it as extracted or checked

### Requirement: Check exact connections and preserve unresolved premises
A connection SHALL bind exact ordered source and formal owners, full typed propositions, context identities and bridge evidence. Fresh semantic use SHALL replay the required checks. A checked conditional implication SHALL retain all assumptions; a rejected application SHALL NOT be reported as mathematical falsity.

#### Scenario: Stronger input premise is unavailable
- **WHEN** a selected formal route requires five extra derivative orders and the interpretation supplies four
- **THEN** the connection retains that unresolved premise and does not conclude the interpreted theorem is false

### Requirement: Preserve historical and bounded execution behavior
Observation, admission and connection stages SHALL share declared deadlines and RSS/output caps. Saved receipts remain historical, with source freshness separate. Reject tampered identities, source substitutions and forged owners; preserve old formats. Connection transport preserves v1 bytes when they fit; oversized v1 data MAY use versioned lossless compression. Do not increase existing limits. Bound decompression and validate the canonical graph and digest.

#### Scenario: Source changes after authoring
- **WHEN** a stored reading is inspected against a changed source span or context
- **THEN** current-source verification fails without rewriting the historical receipt

#### Scenario: A worker exhausts its memory cap
- **WHEN** the configured memory allowance is exceeded
- **THEN** dependent work stops and the result instructs the caller to stop progress and report the measured limit to the user

#### Scenario: Canonical result exceeds the wire cap but bounded compression fits
- **WHEN** a complete connection result exceeds the v1 wire limit and its compressed envelope fits the same wire limit
- **THEN** the lossless envelope is transported below the 8 MiB wire cap and decoded under the existing 32 MiB expanded, graph, string and process bounds

#### Scenario: Compressed envelope exceeds its expansion budget
- **WHEN** compressed data is malformed, incomplete, concatenated, trailing, or expands beyond the intermediate/aggregate bounds
- **THEN** the worker rejects it before granting connection authority or allocating an unbounded value tree

#### Scenario: Saved v3 history contains compressed worker output
- **WHEN** a connection v3 snapshot retains compressed stdout in bounded chunks
- **THEN** history validation checks the exact wire digest and decoded result without recompressing with the local zlib implementation

### Requirement: Qualify generality separately from discovery
Qualification SHALL include unrelated global and set-indexed estimates, changed names and literal losses, negative authority/scope controls and the informed source pair. It SHALL record observation, admission and connection outcomes separately. Passing these cases SHALL NOT complete the parent's propagation or unfamiliar-source detection gates.

#### Scenario: Known source pair becomes connected
- **WHEN** the informed pair obtains a source-faithful checked connection result
- **THEN** the result is credited as local integration with its qualifications, not independent discovery
