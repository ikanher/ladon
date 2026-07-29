## ADDED Requirements

### Requirement: Valid plan is the sole materialization authority
The materializer SHALL accept a theorem-capsule plan produced by the planning
capability and MUST validate its schema, protocol, guarantee level, target identity,
and bound input fingerprints before creating output. It MUST NOT rediscover or
silently repair dependency closure during materialization.

#### Scenario: Compatible plan is unchanged
- **WHEN** every source, configuration, toolchain, and graph fingerprint still matches a supported plan
- **THEN** materialization proceeds using exactly the plan's target and inclusion set

#### Scenario: Plan or input is stale
- **WHEN** a plan is incompatible or any bound input has changed
- **THEN** materialization fails before publication and directs the caller to replan

### Requirement: Target command prefix preserves source context
The materializer MUST copy the owning Lean source from byte zero through the exact
end of the target theorem command recorded in the plan. It MUST preserve original
bytes, line endings, encoding, and all preceding source context and MUST NOT copy
later commands from that file.

#### Scenario: Target has preceding local context
- **WHEN** a theorem relies on preceding namespace, section, variable, notation, attribute, option, macro, open, or local-instance commands
- **THEN** those original commands are retained byte-for-byte in the target prefix

#### Scenario: File contains later declarations
- **WHEN** declarations follow the theorem command in its owning file
- **THEN** their bytes are absent from the materialized target source

### Requirement: Build closure preserves module resolution
The materializer MUST copy every repository-owned non-target module in the planned
build closure as a whole file, preserve source-root-relative module paths, and
package the pinned toolchain and locked Lake metadata required by the supported
configuration. Generated relocation/control files MUST be identified separately
from copied evidence.

#### Scenario: Project uses multiple source roots
- **WHEN** planned modules come from more than one configured source root
- **THEN** the capsule preserves unambiguous source-root mappings and Lean resolves each module to its planned bytes

#### Scenario: Locked external package is required
- **WHEN** the build frontier includes an external Lake package
- **THEN** the capsule retains its lock and package identity without falsely listing its source as repository-owned or vendored

### Requirement: Path-safe transactional publication
The materializer MUST normalize and validate every input and output path before
copying. It MUST reject absolute/escaping paths, unsafe links, special files,
filesystem collisions, and writes into the target repository. It SHALL construct a
complete staged tree and publish it atomically where the platform supports atomic
rename.

#### Scenario: Plan contains a path escape or collision
- **WHEN** any path escapes a declared root or two logical entries collide under the destination filesystem policy
- **THEN** materialization fails before writing a published capsule

#### Scenario: Copy fails partway
- **WHEN** an I/O, hash, limit, or validation failure occurs in staging
- **THEN** no destination is presented as a complete capsule and the target repository remains unchanged

#### Scenario: Output points inside target repository
- **WHEN** the requested output resolves inside the repository being extracted
- **THEN** Ladon rejects the destination before materialization

### Requirement: Complete manifest file accounting
Every capsule SHALL contain a canonical `capsule.json` that accounts for each
copied or generated file with normalized path, role, inclusion reason, origin,
hash, size, and normalized mode. The manifest MUST link to the source plan,
theorem identity, semantic/build closure identities, source-root mapping, external
frontier, guarantee level, and expected replay checks.

#### Scenario: Reviewer asks why a file exists
- **WHEN** a manifest entry is inspected
- **THEN** it identifies a target-prefix, module-import, configuration, toolchain, lock, resource, generated-control, or other typed inclusion reason

#### Scenario: Unaccounted file appears in staging
- **WHEN** staged output contains a file not represented by the manifest model
- **THEN** publication fails rather than emitting an incompletely inventoried capsule

### Requirement: Deterministic directory and archive output
Canonical manifest serialization and archive creation MUST use deterministic
ordering and normalized metadata. Repeated materialization from the same valid plan
and identical inputs SHALL produce identical logical trees, manifests, and archive
hashes.

#### Scenario: Capsule is materialized twice
- **WHEN** the same plan and bytes are materialized in different host directories
- **THEN** host paths and wall-clock metadata do not change the canonical manifest or archive identity

#### Scenario: Copied mode is unsafe or host-specific
- **WHEN** a source mode is outside the capsule's supported normalized mode set
- **THEN** materialization either normalizes it according to the manifest contract or rejects it explicitly

### Requirement: Locked/rebuildable guarantee is bounded
Materialized output MUST state that v1 is a locked/rebuildable module-prefix
capsule. It MUST NOT claim global or declaration-level minimality, offline
vendoring, system hermeticity, or successful Lean verification until the replay
capability supplies corresponding evidence.

#### Scenario: Materialization succeeds without replay
- **WHEN** a capsule tree and manifest are published but replay has not succeeded
- **THEN** its status is materialized/unverified and its nonclaims remain visible

#### Scenario: Unsupported build facet is present
- **WHEN** the plan marks a facet unsupported for the requested guarantee
- **THEN** materialization refuses that guarantee rather than copying a best-effort package

### Requirement: Caller-neutral materialization CLI
The installed CLI SHALL expose an ordinary theorem materialization operation with
explicit plan and output paths and structured text/JSON outcomes under the existing
stream and exit contract.

#### Scenario: User materializes reviewed plan
- **WHEN** a user invokes the installed materialization command with a valid plan and safe destination
- **THEN** Ladon publishes the capsule and reports its manifest identity and unverified status

#### Scenario: Destination already contains data
- **WHEN** the destination is non-empty and no supported replacement contract was explicitly selected
- **THEN** Ladon refuses to overwrite it
