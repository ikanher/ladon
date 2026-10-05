## ADDED Requirements

### Requirement: Portable bundles retain result identity and source scope
Following [Responsible Release of AI-Generated Mathematics](https://agmai.org/general-sep29/) (2026-09-29), §2.B Step I.2–4, the system SHALL export a selected immutable result revision, claim links, dossiers/guides, selected evidence, disclosure omissions, and optional existing capsule references into a locally inspectable bundle. It SHALL include an inventory of relative paths, byte sizes, and content hashes. Source interpretation SHALL remain traceable through `../../sources.md`.

#### Scenario: A reviewer opens a bundle outside the originating checkout
- **WHEN** all selected local inspection assets are bundled but an optional replay dependency is external
- **THEN** the reviewer can inspect claims and evidence without the original paths or Ladon cache and sees the missing replay dependency explicitly

### Requirement: Export and integrity verification have narrow authority
`ladon result export` SHALL publish atomically to an explicit output destination and produce identical bytes for identical selected inputs/options. `ladon result verify` SHALL verify bundle structure and integrity without claiming theorem correctness, authenticity, peer review, or responsible-release compliance. Neither command SHALL submit to a repository, invoke Lean or a model, or dereference external URLs implicitly.

#### Scenario: A complete bundle has never been replayed
- **WHEN** all inventory hashes and structural checks pass
- **THEN** verification reports integrity success and absent replay evidence separately and does not report the mathematical result as proved

### Requirement: Publication and extraction enforce finite safe boundaries
Exports SHALL enforce a finite configured byte ceiling with a 256 MiB default, reject absolute paths, traversal, symlink escapes, normalized-name collisions, and invalid required references, and leave any previous output intact on failure. Archive inspection/extraction SHALL enforce actual expanded byte and member-count limits before publishing extracted contents, including the manifest collection bounds. Attachments SHALL require explicit selection and disclosure permission.

#### Scenario: An attachment would escape the destination
- **WHEN** an export or imported archive contains a traversal path or symlink to an external file
- **THEN** processing fails before external content is read or written and any existing destination remains unchanged

#### Scenario: An archive exceeds its declared expanded size
- **WHEN** decompression would exceed the configured expanded-byte ceiling
- **THEN** processing terminates with a bounded limit diagnostic and no partial bundle is published

### Requirement: Revisions and scholarly identifiers are distinct
Bundles SHALL preserve predecessor references and exact revision identities. Supplied scholarly repository identifiers SHALL be attributed metadata; local content hashes SHALL NOT be described as minted scholarly identifiers. Reviews and comments imported as attachments SHALL retain author, subject revision, and scope rather than silently applying to newer revisions.

#### Scenario: A deposited result is revised
- **WHEN** a later manifest records a repository identifier and a changed statement
- **THEN** both immutable revisions and their relationship remain inspectable and reviews of the older statement do not approve the newer one

### Requirement: Community profiles are optional and version-pinned
Explicitly selected profile adapters SHALL pin the authoritative upstream contract, supported version, and coverage. Copyright-header, `formalization.yaml`, and comparator-challenge checks SHALL separate presence/schema checks from explicit comparator execution and its exact relation, subjects, and environment. Unsupported versions SHALL return unavailable. Profile results SHALL NOT imply faithful natural-language correspondence or institutional compliance.

#### Scenario: Requested formalization metadata profile is unsupported
- **WHEN** a bundle requests a version for which Ladon has no pinned adapter
- **THEN** profile evaluation reports unavailable with a reason while core bundle inspection remains possible

#### Scenario: A challenge file exists without comparator execution
- **WHEN** the artifact profile finds a valid challenge file but no comparator observation is attached
- **THEN** the profile records artifact presence and not-run comparator status separately

### Requirement: Core and full bundle exits are separate
The core exit SHALL require claim links, dossier/guide export, integrity verification, and installed offline inspection evidence. The full exit SHALL additionally require the research-provenance integration and pinned supported-profile scenarios. A core exit SHALL NOT mark the full child or umbrella complete.

#### Scenario: First qualitative feedback pass uses a core bundle
- **WHEN** core export works but provenance/profile integration is unfinished
- **THEN** usage feedback can consume the explicitly experimental core profile while full release readiness remains incomplete
