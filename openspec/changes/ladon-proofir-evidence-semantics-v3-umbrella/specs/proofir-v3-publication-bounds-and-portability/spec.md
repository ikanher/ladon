## ADDED Requirements

### Requirement: Project-local publication uses one owned build lock
Each ProofIR SQLite database SHALL remain local to its analyzed project and SHALL use Ladon's shared same-directory build lock with an attributable owner PID.

#### Scenario: Concurrent build
- **WHEN** a second live process attempts to rebuild the same project database
- **THEN** it fails fast with the lock owner PID and does not modify the active database or first builder's files

### Requirement: Database growth is independently bounded
The publisher SHALL enforce a positive `maxDatabaseBytes` through SQLite page limits and prepublication accounting independently of artifact, batch, and query bounds.

#### Scenario: Projection exceeds its page budget
- **WHEN** SQLite cannot allocate a page within `maxDatabaseBytes`
- **THEN** publication fails with a stable resource diagnostic and preserves the prior database

### Requirement: Replacement is durable and failure-safe
The publisher SHALL integrity-check, sync, atomically replace, and durably publish a complete temporary database while cleaning only resources owned by the failed build.

#### Scenario: Integrity check fails
- **WHEN** the temporary projection fails an integrity or foreign-key check
- **THEN** the previous destination remains byte-for-byte unchanged and the failed temporary is removed

### Requirement: Storage accounting tolerates optional SQLite features
Core publication and accounting SHALL NOT require the optional `dbstat` virtual table.

#### Scenario: dbstat is unavailable
- **WHEN** the SQLite build lacks `dbstat`
- **THEN** page size, page count, allocated bytes, and an explicit unavailable per-object breakdown are returned without failing publication

### Requirement: Plan gates assert access semantics portably
Index gates SHALL assert required access-path properties without depending on exact platform-specific `EXPLAIN QUERY PLAN` text.

#### Scenario: SQLite wording changes
- **WHEN** a supported SQLite version expresses the same indexed access with different detail prose
- **THEN** the semantic plan gate passes, while a forbidden full scan still fails

### Requirement: Lock cleanup proves ownership at unlink time
Every acquired lock SHALL carry an unpredictable owner token and stable file identity, and cleanup SHALL remove the path only after proving that the current path still represents that exact acquisition.

#### Scenario: Competitor replaces the lock before cleanup
- **WHEN** another writer owns a new lock at the same path before the first writer's `finally` block runs
- **THEN** the first writer leaves the competitor lock intact

### Requirement: Stale recovery cannot delete a new owner
Stale-lock recovery SHALL use an atomic claim/rename or compare-and-delete operation that cannot unlink a lock acquired after the stale observation.

#### Scenario: PID is reused or lock changes during recovery
- **WHEN** the observed owner state differs from the file/token state at recovery time
- **THEN** recovery retries or fails closed without deleting the current owner's lock
