## Purpose

Allow lexical search to follow source edits while retained formal evidence remains inspectable under its original identities, without promoting historical results into current guarantees.

## ADDED Requirements

### Requirement: Supported evidence does not block explicit lexical update
An explicit update of a compatible index with recognized retained evidence SHALL refresh lexical search and preserve that evidence under its original ownership. Update SHALL report base and output generations, source changes, extraction reuse and preserved snapshot identities. It SHALL NOT invoke Lean or initiate compilation.

#### Scenario: Add edit remove and rename declarations
- **WHEN** an evidence-bearing index is updated after stable source additions, edits, removals and renames
- **THEN** current lexical declarations, imports, scopes and name/type search match a clean build of those inputs, and historical evidence remains available

#### Scenario: Sources are unchanged
- **WHEN** explicit update finds unchanged supported inputs
- **THEN** it preserves the existing no-op behavior without replacement, extraction, archival duplication or Lean execution

### Requirement: Retained evidence keeps exact original ownership
Preservation SHALL retain original evidence payloads, subject and environment identities, authority, coverage, limitations and source associations. Snapshot identity SHALL distinguish different retained populations even under the same source generation. A historical snapshot SHALL NOT be described as a complete replay environment unless its dependencies are actually included.

#### Scenario: More evidence arrives without a source edit
- **WHEN** two preserved populations share a source generation but contain different acquisitions
- **THEN** they remain distinguishable and neither population silently overwrites the other

#### Scenario: Preserved evidence refers to external files
- **WHEN** retained evidence references files outside the snapshot
- **THEN** those original references remain identifiable and missing dependencies are disclosed rather than reported as preserved bytes

### Requirement: Current search cannot inherit historical authority
Current queries SHALL use the current lexical population. They SHALL NOT obtain current semantic types, proof success, dependency coverage or freshness by joining historical records on names, source paths or lexical identifiers. Semantic data not established for the current selection SHALL remain unavailable or explicitly historical.

#### Scenario: Same name gains a premise
- **WHEN** a theorem keeps its name but gains an assumption after a successful stored check
- **THEN** search shows the new source signature and the old check is not presented as an accepted application of the new statement

#### Scenario: An import changes but the owner file does not
- **WHEN** an imported definition changes under an unchanged theorem owner
- **THEN** unchanged owner bytes do not automatically renew the stored theorem's environment association

### Requirement: Historical inspection is explicit and read only
History inventory SHALL identify snapshots, original generations, bytes and evidence availability with bounded output and disclosed omissions. Explicit historical lineage selection SHALL validate the selected snapshot and use its archived context, preserve original receipt guarantees, and mark current association as not established. Historical selection SHALL reject refresh or other mutations.

#### Scenario: Inspect a removed theorem without the live project
- **WHEN** a reader selects a valid historical snapshot containing lineage for a theorem removed from current sources
- **THEN** the stored graph can be inspected without Lean execution or live-source freshness, with its original identity and historical selection shown

#### Scenario: Selected archive has been substituted
- **WHEN** a registered snapshot is missing, corrupted, replaced or resolves outside its permitted history root
- **THEN** historical inspection fails explicitly and does not select another snapshot or current evidence as fallback

#### Scenario: Historical record was already stale
- **WHEN** a closure did not match the original archived base identities
- **THEN** historical selection retains that limitation instead of manufacturing a matching context from the closure

### Requirement: Freshness and evidence availability stay separate
Status and update results SHALL distinguish current lexical comparison, historical evidence availability and current compiled association. A lexical update or successful external build SHALL NOT renew stored proof or lineage evidence. Existing explicit acquisition checks SHALL govern new evidence selection.

#### Scenario: Lexical refresh precedes compilation
- **WHEN** search has been refreshed but current compiled evidence has not been acquired
- **THEN** output can report fresh lexical data and historical evidence together without reporting current compiled coverage

#### Scenario: New acquisition fails
- **WHEN** an attempt to acquire current lineage fails
- **THEN** previous snapshots remain available and are not silently selected as current evidence

### Requirement: Publication preserves a recoverable complete generation
Update SHALL serialize with supported evidence writers, durably preserve required history before active replacement, and publish a complete validated generation. Failure before replacement SHALL preserve the active base. A failure after replacement with uncertain durability SHALL be reported as uncertain rather than as a completed rollback. Readers SHALL observe a complete generation.

#### Scenario: Competing writer
- **WHEN** a lineage, semantic, ProofIR or lexical publisher owns the same destination
- **THEN** another mutation receives a bounded busy outcome or serialized execution and no committed evidence is lost

#### Scenario: Interrupted archival or replacement
- **WHEN** execution stops during archive creation, after archive publication, or after active replacement
- **THEN** recovery distinguishes complete active state, complete protected orphan history and incomplete temporary state without presenting a mixed generation

### Requirement: Source instability gives actionable bounded diagnostics
Observed source changes during update SHALL prevent publication and report a stable failure reason, bounded available added/changed/removed path details, omissions and guidance to retry after edits settle. Diagnostics SHALL NOT claim complete path knowledge when the available observations are insufficient.

#### Scenario: Another agent adds a Lean owner during update
- **WHEN** the supported source inventory changes before publication
- **THEN** the old active generation remains usable and the result identifies observed changes and the quiet-workspace retry action

### Requirement: Storage and cleanup protect retained history
Inventory SHALL distinguish active, historical and temporary bytes and state whether totals are complete. Update SHALL honor existing active limits and a supplied history limit. Storage failure SHALL NOT cause evidence eviction. Ordinary prune SHALL protect historical snapshots, catalogs and uncertain publication artifacts; age and filename alone SHALL NOT establish disposability.

#### Scenario: History limit or disk write fails
- **WHEN** required preservation exceeds the supplied limit or cannot be written
- **THEN** publication stops with configured and observed resource information while retaining the prior usable state and existing evidence

#### Scenario: History is selected for ordinary prune
- **WHEN** a caller explicitly selects an old retained snapshot or catalog for ordinary cleanup
- **THEN** preview and apply protect it with an evidence-retention reason

### Requirement: Migration and replacement remain explicit
Supported legacy indexes SHALL migrate through explicit update with original evidence preserved. Unsupported schemas or unknown evidence extensions SHALL be refused without destructive changes. New layouts SHALL have an identity that incompatible readers reject. Rebuild at a history-owning path SHALL preserve history or refuse with a new-path instruction.

#### Scenario: Unknown future evidence table
- **WHEN** an otherwise readable index contains unsupported retained evidence
- **THEN** update keeps the base unchanged and explains the supported migration or separate-path fallback

#### Scenario: Rebuild would lose historical references
- **WHEN** a full build targets an active index owning history without a preservation-capable replacement path
- **THEN** it refuses before replacement and directs the caller to a new index path

#### Scenario: Active index is copied without history
- **WHEN** registered snapshots are absent after a partial move
- **THEN** status reports missing history and preservation-requiring mutation refuses rather than treating the index as history-free

#### Scenario: Index and adjacent history move together
- **WHEN** the active index and complete adjacent history are relocated together
- **THEN** historical navigation remains usable through relative references while original repository associations remain unchanged
