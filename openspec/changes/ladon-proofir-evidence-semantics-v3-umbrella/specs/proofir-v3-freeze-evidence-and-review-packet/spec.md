## ADDED Requirements

### Requirement: Freeze packets contain a durable proof state
Every semantic-freeze packet SHALL contain `proof-state.md` recording completed and open work, exact blockers, Rust hold state, executed commands, limitations, and the next admissible action.

#### Scenario: Reviewer enters through proof state
- **WHEN** the packet README recommends `proof-state.md`
- **THEN** that file exists and its task/blocker state agrees with the machine-readable dependency and release evidence

### Requirement: Every packet file is content inventoried
The packet manifest SHALL record each relative path, role, byte size, SHA-256 digest, and source classification.

#### Scenario: Included source changes
- **WHEN** any included byte changes after manifest creation
- **THEN** packet validation fails before a review result is attributed to that manifest

### Requirement: Source and toolchain state are attributable
The packet SHALL record source commit, dirty-tree and untracked content identities, relevant lock/toolchain hashes, tool versions, packet-builder version, and build timestamp.

#### Scenario: Packet is built from a dirty tree
- **WHEN** uncommitted or untracked files contribute to the packet
- **THEN** their canonical manifest and content digest are recorded rather than presenting HEAD as the complete source identity

### Requirement: Command evidence is reproducible and content addressed
Every claimed validation command SHALL record argv, working directory, bounded environment description, timestamps, exit code, and stdout/stderr paths, sizes, and hashes.

#### Scenario: Quoted full-suite count
- **WHEN** the packet cites a full-suite result
- **THEN** the exact source state, command, exit code, and content-addressed logs supporting that count are included

### Requirement: Advertised packet-local commands have a complete closure
The packet SHALL include every CLI source, support module, fixture, schema, OpenSpec child, and other repository artifact read or imported by its advertised packet-local commands.

#### Scenario: A required fixture is omitted
- **WHEN** a clean extracted replay cannot find the fixture
- **THEN** packet construction fails and no reproducibility claim is emitted

### Requirement: Expert disposition gates semantic freeze and Rust
The Rust hold SHALL remain until every pre-freeze child is green and an expert review dispositions every original blocker against the content-addressed packet.

#### Scenario: One integration blocker remains
- **WHEN** incremental worker evidence still cannot be projected and queried end to end
- **THEN** the semantic contract remains unfrozen and Rust implementation is not an admissible next task

### Requirement: Manifest validation is closed and nonvacuous
Packet verification SHALL require the exact supported manifest format, required top-level source/toolchain state, a non-empty typed file inventory, and exact inventory closure before checking file hashes.

#### Scenario: Old path-only manifest is supplied
- **WHEN** a manifest contains `includedArtifacts` but no supported `format` or `files` collection
- **THEN** verification rejects the manifest instead of succeeding after checking zero files

### Requirement: Packet-owned metadata is inventoried
README, manifest metadata, source map, validation summary, command records, logs, sources, tests, and fixtures SHALL all be covered by an explicit self-manifest or detached root-hash rule.

#### Scenario: Unadvertised regular file exists
- **WHEN** the extracted archive contains a file outside the declared self-manifest exception
- **THEN** packet validation fails and no review result is attributed to that packet

### Requirement: Manifest identity separates deterministic content from observation time
The packet SHALL define which generation observations are excluded from deterministic content identity and SHALL hash both paths and bytes of untracked source inputs.

#### Scenario: Untracked file content changes
- **WHEN** an untracked file retains its path but changes bytes
- **THEN** the source-state identity changes and prior command evidence cannot be reused
