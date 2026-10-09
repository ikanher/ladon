## Purpose
Make disposable local index storage visible and reclaimable without deleting an active publication, a protected generation or unrelated files.

## ADDED Requirements

### Requirement: Index inventory is bounded and informative
An index inventory operation SHALL list supported indexes in an explicit directory with path, bytes, readable generation/repository identity, filesystem age basis, publisher state and retention classification. It SHALL identify temporary files and sidecars separately, bound detailed output and report omissions or unreadable entries.

#### Scenario: Many private indexes
- **WHEN** a directory contains the default index, private indexes and orphan candidates
- **THEN** inventory reports aggregate bytes and per-entry classifications without rebuilding, modifying or recursively searching unrelated directories

### Requirement: Cleanup requires an explicit selection
Prune SHALL default to a non-mutating preview. Deletion SHALL require an explicit apply option and selector, display eligible and protected paths with reasons, and revalidate each candidate at execution. The default index, explicitly retained indexes and foreign-repository entries SHALL be protected; age alone SHALL NOT establish disposability.

#### Scenario: Preview private-index cleanup
- **WHEN** a caller previews selected old private indexes
- **THEN** the command reports potential reclaimed bytes and protection reasons while all files remain unchanged

#### Scenario: Selection changes before apply
- **WHEN** a previewed path is replaced, its identity changes or a publisher becomes active
- **THEN** apply skips or rejects that candidate with a specific reason instead of deleting the replacement

### Requirement: Cleanup respects publication and SQLite ownership
Cleanup SHALL use destination ownership checks before deleting a database or its associated temporary files. Persistent lock paths SHALL NOT be deleted merely because their recorded PID is old. Active or ambiguous journals, temporary files, symlinks and unrecognized files SHALL be protected by default.

#### Scenario: Inactive lock file remains
- **WHEN** an inactive publisher lock exists alongside a selected disposable database
- **THEN** its presence is explained as persistent coordination state and cleanup does not unlink the lock inode

#### Scenario: Active publication or uncertain sidecar
- **WHEN** a selected database has an active publisher or sidecar ownership cannot be established
- **THEN** cleanup protects the affected group and records why it could not safely reclaim those bytes

### Requirement: Cleanup results are attributable
Cleanup SHALL report selected, deleted, skipped and failed paths with byte totals and terminal status, including partial failure. A repeated apply SHALL handle already absent files without widening selection. Successful cleanup SHALL NOT imply that remaining indexes are fresh.

#### Scenario: One deletion fails
- **WHEN** deletion succeeds for one eligible file but fails for another
- **THEN** the result preserves both outcomes and accurately reports reclaimed bytes without claiming complete success
