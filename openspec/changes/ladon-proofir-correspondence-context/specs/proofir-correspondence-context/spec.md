# Spec Delta

## Purpose

Expose the exact stored source interpretation and formal application context together so readers can inspect the semantic boundary of correspondence evidence.

## ADDED Requirements

### Requirement: Exact correspondence context
Native inspection SHALL return the interpretation record, lowered formula, fidelity, source reference and formal slice associated with the exact correspondence owner. It SHALL resolve interpretations by owner and local identity, never by an unqualified name. Stored evidence SHALL retain its existing authority and dimensions.

#### Scenario: Same local identity under different owners
- **WHEN** two interpretations share a local identity and only one is referenced
- **THEN** inspection returns only the referenced owner's interpretation and the correspondence's actual slice

#### Scenario: Missing stored interpretation
- **WHEN** the referenced interpretation or its projection table is absent
- **THEN** its context is explicitly unavailable and inspection coverage is incomplete

### Requirement: Bounded context delivery
Inspection SHALL bound each context component by a configurable byte allowance, defaulting to 65536 bytes and accepting integers from 1 through 8388608. Oversized components SHALL be omitted whole with their stored byte size and reason. The bound SHALL be checked before transferring the component's text from SQLite into Python. Bounds measure stored UTF-8 text, not the entire output envelope.

#### Scenario: Oversized multibyte source
- **WHEN** stored interpretation text exceeds the byte allowance
- **THEN** inspection reports an omitted component and incomplete coverage without returning a partial interpretation

#### Scenario: Public override and invalid allowance
- **WHEN** the caller supplies a valid larger allowance or an invalid value
- **THEN** the public command delivers newly fitting components or returns an explicit input error respectively

### Requirement: Inspection version and authority
The native context-bearing response SHALL use inspection schema v2. The outer inspection envelope and canonical artifacts SHALL retain their existing schemas. Inspection SHALL identify its authority as stored evidence only, state that source fidelity and live freshness are unverified, and include stable limitation identifiers.

#### Scenario: Fully available context
- **WHEN** all context and child rows are available without omissions
- **THEN** coverage can be complete for stored inspection while source fidelity and current-filesystem freshness remain unestablished

### Requirement: Inspect stored obligation check bindings
Inspection SHALL expose bounded receipt evidence for exact owner-qualified check references and compare stored plan, obligation, goal digest, polarity, status and check operation. It SHALL distinguish matched stored records, mismatches and unavailable evidence without promoting result dimensions or claiming replay. Checks SHALL retain their row limit and share one receipt-payload byte allowance equal to the context allowance.

#### Scenario: Receipt describes a different target
- **WHEN** a receipt names another plan, obligation, goal, mode or status than its stored obligation and check operation
- **THEN** inspection reports a mismatch and incomplete coverage while preserving original labels

#### Scenario: Receipt is absent or discarded
- **WHEN** the exact check or receipt is absent, or the projection retained only its digest
- **THEN** inspection reports unavailable binding evidence and incomplete coverage without using another owner's receipt

#### Scenario: Receipt budget or row limit is exhausted
- **WHEN** selected receipt payloads exceed their shared byte allowance or checks exceed the row limit
- **THEN** omissions remain explicit and inspection coverage remains incomplete

### Requirement: Correspondence slice module capacity
Canonical correspondence envelopes SHALL admit up to 32768 entries at
`payload.slice.observation.importedModules` and
`payload.slice.compiledInventory.modules` for `ladon-proof-slice-v1`. The
allowance SHALL apply only to those paths in a root `proofir.correspondence`
envelope or the corresponding `observation.importedModules` and
`compiledInventory.modules` paths of a standalone `ladon-proof-slice-v1` value
used by projection. Other collections, nested row contents, byte and depth bounds,
slice validation and evidence authority SHALL retain their existing contracts.
Accepted canonical byte encodings and identities SHALL remain unchanged.

The same 32768-entry bound SHALL apply at
`capture.capture.environment.compiledInventory.modules` in generated
correspondence-obligation receipts, including their exact `{planId, receipt}`
identity-hash wrapper. Recognition SHALL require the generated-obligation origin,
capture-result schema and capture operation. Arbitrary enclosing objects and
all other receipt collections SHALL retain generic bounds. This size allowance
SHALL NOT confer receipt validity, replay acceptance or source fidelity.

#### Scenario: Real library closure exceeds generic collection size
- **WHEN** an extracted application has 11034 imported modules within existing artifact byte bounds
- **THEN** correspondence production preserves every module and proceeds to ordinary validation

#### Scenario: Checking receipt carries a large captured closure
- **WHEN** a generated obligation receipt contains more than 10000 but at most 32768 captured modules
- **THEN** both receipt and check-identity hashing preserve the complete canonical bytes without relaxing replay or binding checks

#### Scenario: Module allowance is used elsewhere or exceeded
- **WHEN** a module list exceeds 32768 or an unrelated list exceeds its generic limit
- **THEN** canonical serialization rejects the input without truncation or authority promotion
