## Purpose

Generate connecting obligations from actual observed Lean local contexts while preserving binder identity, scope, dependencies, and source provenance.

## ADDED Requirements

### Requirement: Local identity determines transport
Context transport SHALL use exact observed local identities and dependency order rather than display spelling. Supported Unicode, subscript, prime, and quoted names SHALL preserve the same semantics as ordinary names without modifying the primary source.

#### Scenario: Scoped functional objects
- **WHEN** a selected application uses observed local functions A₀ and A₁ with supplied object maps
- **THEN** the original premise-supply and conclusion-transfer obligations can be generated and checked without renaming the source or adding assumptions

#### Scenario: Repeated display names
- **WHEN** distinct observed locals share a display name in nested scopes
- **THEN** they remain distinct and an ambiguous name-only map cannot select one implicitly

### Requirement: Local types and values retain their dependencies
Transport SHALL preserve dependencies in local types, let values, instantiated arguments, and premise providers. Branch-local or later unavailable objects SHALL NOT escape scope. Unsupported dependent structures SHALL produce specific residuals rather than weakened obligations.

#### Scenario: Let-bound dependency
- **WHEN** a local value depends on an earlier mapped object
- **THEN** reconstruction retains that value and dependency in the checked context

#### Scenario: Escaped witness or invented proof premise
- **WHEN** a proposed transport requires a witness outside its branch or adds an unavailable proof assumption
- **THEN** the transport is rejected or remains incomplete without checked support

### Requirement: Source context and map compatibility are explicit
Transport records SHALL bind exact source, module, namespace, application, local identities, map profile, and environment. Existing name-based maps SHALL resolve only when unambiguous. Changed contexts or maps SHALL invalidate dependent checks and reviews.

#### Scenario: Module alias workaround
- **WHEN** a source is compiled under a different module context to work around an unsupported selector
- **THEN** the resulting evidence identifies that context and cannot be attached as an unchanged observation of the original selection

#### Scenario: Existing unique name map
- **WHEN** an old supported map names exactly one observed local
- **THEN** it remains usable with the resolved identity recorded, without changing historical artifact identities on read

### Requirement: Reconstructed links are independently checked
Generated context bindings and connecting implications SHALL be checked in the pinned Lean environment. Successful serialization, alpha-renaming, or conditional replay alone SHALL NOT establish that premise supply or conclusion transfer succeeded.

#### Scenario: Conditional succeeds while a transfer fails
- **WHEN** the selected formal application is valid but a required connecting implication remains unsupported
- **THEN** formal conditional validity is retained and parent correspondence remains incomplete
