## Context

Materialization begins only after the planning packet has produced a complete,
compatible plan. The source bytes, exact theorem-command boundary, module closure,
source-root mapping, package metadata, and input hashes are therefore already
known. This phase must preserve those bytes and paths without allowing a repository
to redirect writes, escape the output root, or change between validation and copy.

The product boundary is a locked/rebuildable capsule. Repository-owned source is
included; external Lake packages remain pinned rather than necessarily vendored.

## Goals / Non-Goals

**Goals:**

- Materialize only a valid, non-stale theorem-capsule plan.
- Preserve the target module prefix through the theorem and all other required
  repository modules byte-for-byte.
- Preserve module/source-root layout, toolchain, and locked package configuration.
- Produce deterministic directories and archives with full file accounting.
- Leave the target repository unchanged and reject unsafe filesystem inputs.

**Non-Goals:**

- No dependency discovery or repair of an incomplete plan.
- No declaration-level slicing inside imported modules.
- No source formatting, namespace rewriting, or generated proof.
- No implicit dependency downloads.
- No offline-vendored or system-hermetic guarantee.

## Decisions

### 1. Materialization consumes a plan, never an ad hoc theorem lookup

`ladon theorem materialize --plan <plan> --output <path>` validates schema,
protocol, guarantee level, target identity, and every bound input before creating
output. The combined extract command passes the same in-memory/serialized contract.
If any input hash or source mapping changed, the caller must replan.

Alternative considered: transparently refresh stale plans. That would make the
output differ from the artifact the caller reviewed.

### 2. Copy an exact prefix for the owner and whole files for imports

The target file is copied from byte zero through the parser command end associated
with the Lean-confirmed theorem. The cut occurs at a byte boundary and retains the
original line endings and encoding. Every other repository module in the build
closure is copied whole. No synthetic namespace wrappers or imports are introduced
into proof sources.

Alternative considered: reconstruct earlier declarations from AST rows. The source
index does not retain every contextual command needed for equivalent elaboration.

### 3. Preserve source-root-relative module identity

The capsule layout records each source root and maps modules to paths beneath it,
including projects with multiple roots. Package configuration is normalized only
where necessary to relocate those roots inside the capsule. Original files and the
generated relocation metadata are separately identified in the manifest.

Alternative considered: flatten all modules into one directory. That creates
collisions and can change Lean module resolution.

### 4. Separate generated control files from copied evidence

`capsule.json` is the canonical manifest. It records plan identity, theorem
identity, guarantee level, file hashes/sizes/modes, inclusion reasons, source-root
mapping, external lock frontier, unsupported/nonclaim fields, and expected replay
checks. Generated Lake wrapper/config files, if required, are marked as generated
with their derivation. Copied inputs retain original hashes.

### 5. Build output through a safe staging transaction

All plan paths are normalized repository-relative paths. The materializer rejects
absolute paths, `..` escapes, NULs, case/Unicode collisions under the target
filesystem policy, unsupported special files, and links whose resolved target is
outside the declared input root. It writes to a sibling staging directory, hashes
the completed tree, then atomically publishes when possible. Existing non-empty
destinations are not overwritten without an explicit future contract.

Alternative considered: copy directly to the destination. A failure would leave an
artifact that looks complete but lacks a final manifest.

### 6. Make archive bytes reproducible

Directory manifests use canonical ordering. Archive entries use normalized
timestamps, owners, modes, separators, and ordering; generated JSON uses canonical
serialization. Repeated materialization of the same plan and inputs produces the
same manifest and archive hash.

## Risks / Trade-offs

- [The owner prefix can include unrelated earlier declarations] → State the
  module-prefix strategy and avoid a minimality claim.
- [Lake configuration relocation can change behavior] → Limit supported config
  forms, record every generated difference, and fail on unknown custom behavior.
- [Filesystem normalization varies by platform] → Preflight both logical and target
  filesystem collision rules before any publication.
- [External packages are not present offline] → Preserve lock metadata and label the
  capsule locked/rebuildable, not offline-vendored.
- [Large closures duplicate many bytes] → Stream hashes/copies and leave content
  addressing as a later optimization that does not change manifest semantics.

## Migration Plan

1. Land manifest/layout models and plan compatibility validation.
2. Land target-prefix and whole-module copy into staging.
3. Land safe publication and reproducible archive support.
4. Gate deterministic output, path attacks, drift, multiple source roots, and
   interrupted publication.
5. Rollback removes only the new materializer; target repositories are never
   migrated.

## Open Questions

- Which archive format should be normative across supported platforms?
- Should an existing empty output directory be accepted or always require a
  nonexistent destination?
