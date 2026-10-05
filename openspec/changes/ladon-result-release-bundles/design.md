## Context

See proposal.md for the outcome. Existing result manifests and canonical evidence are immutable inputs. `result_dossier.prepare_dossier` owns evidence joins; guide/assessment/lineage companions have strict validators. Existing capsule archive helpers lack aggregate extraction bounds, so they provide design references, not an importer to reuse unchanged. Python 3.11/3.12 and standard-library-only runtime dependencies remain supported.

## Goals / Non-Goals

Core transport must work with ordinary installed result views, without a cache or source checkout. Full research-process records and version-pinned community profile adapters remain subsequent work under the parent graph. Integrity does not establish authenticity, checking, informal correspondence or scholarly approval.

## Decisions

### Explicit selection and immutable payloads

`result export MANIFEST --selection SELECTION --output BUNDLE [--max-bytes N] [--max-members N]` consumes `ladon-result-bundle-selection-v1`. The document has `supplier` (identity/kind), `entries`, `lineageBindings`, `identifiers` and `externalDependencies`. Entry fields are `id`, `role`, `disclosure` (supplied/redacted/unavailable/not-collected), `permission` (include/omit), optional local `path`, omission `reason`, and optional `review` (author identity/kind, subjectRevision, scope). Roles: artifact, guide, assessments, lineage, lineage-database, predecessor, attachment, review, capsule. Guide, assessments and lineage are singleton roles. Review-role attachments require review metadata. Every omitted/non-supplied entry needs a reason; it is never opened or hashed, and its source path is excluded from output. Selection paths resolve relative to the selection document and can be explicit absolute local paths. URLs are inert metadata. Existing immutable payloads may themselves contain producer paths; selected complete files are disclosed as supplied, not silently redacted.

All selected regular files are copied unchanged into a private stage through no-follow file descriptors, with streaming byte accounting. ZIP member names are generated from sorted IDs, not from source paths. The result manifest is `manifest.json`; selected files have deterministic `assets/NNNNN` names. `bundle.json` (ladon-result-bundle-v1, profile core-v1) contains resultId, revision, full payload inventory (id, role, path, bytes, sha256 and optional review), explicit omissions, supplier, identifiers, externalDependencies, lineageBindings and previous revisions. The inventory covers every file except its own index, avoiding self-hash recursion; the terminal result separately hashes the index. It records no source filesystem paths outside immutable supplied content.

Canonical IDs are never rewritten. Inventory SHA-256 hashes raw bytes; ProofIR owners validate detached artifact identities independently. Missing optional canonical evidence stays unresolved. Internal bundle references must resolve exactly.

### Portable lineage without implied disclosure

Each lineage binding names `entryId` and a selected `databaseId`. Export checks the source database path matches that entry in the supplied lineage companion. A store is included only by an explicit permitted `lineage-database` selection; this discloses the whole file, so docs recommend a dedicated evidence store. SQLite WAL/journal sidecars with pending contents are rejected instead of silently copying an inconsistent main file. No automatic snapshot of private cache content is taken.

The original lineage companion remains byte-identical. The bundle loader derives transport database paths from its bindings in memory; an unbound entry maps to an absent reserved path and is reported unavailable. The verifier rejects unused/conflicting bindings and never follows original paths. An optional logical reference prefix in lineage inspection makes database references and cursor bindings independent of temporary extraction directories. Existing explicit-file callers retain their existing outputs.

### Bounded deterministic transport and publication

Use ZIP_STORED for deterministic export with sorted members, fixed timestamps/modes and no comments/extras. Import accepts regular ZIP_STORED/ZIP_DEFLATED entries only, rejecting unsupported/encrypted entries. All names are portable relative POSIX paths: reject absolute/drive/backslash/NUL/dot segments, Unicode NFC/casefold aliases, directory/file conflicts and symlinks. Reject source symlinks, including intermediate path components. Count actual expanded bytes while streaming, bound archive bytes separately, and reject member count above a configured ceiling (default 10,000). Byte ceiling defaults to 256 MiB; existing 16 MiB JSON, canonical artifact and collection limits also apply. Bounds must be positive finite integers.

Export stages beside the destination, validates the complete staged payload, streams the ZIP into a temporary sibling, flushes and atomically replaces the output. Failure/interruption removes staging and preserves previous output. `result verify BUNDLE [--extract-to NEW_DIRECTORY]` validates ZIP or an extracted directory; extraction publishes a private staged directory only after complete verification and refuses an existing destination. Verification does not perform replay. Its result includes integrity status, exact revision, payload/omission counts, explicit missing dependencies, unknown replay coverage and not-run replay. Larger lists use counts and exact index pointers within the compact output limit.

### Ordinary bundle consumers

`result inspect BUNDLE` and `result guide BUNDLE` accept a ZIP or extracted bundle directory and use existing views. Mixed external companion/artifact flags are rejected for bundle input to avoid ambiguous evidence. Archive extraction is private and temporary; neither inspection nor verification refreshes caches or changes inputs. Revision history is preserved as exact predecessor manifest attachments, validated against the selected result's chain; missing predecessors remain explicit. After extraction each historical manifest is inspectable by its inventoried path, with historical reviews retained.

### Module ownership and acceptance

Separate selection/index shape, safe file/archive IO, export assembly, bundle validation/loading and CLI routing. Public Python facade: `export_result_bundle(manifest_path, selection_path, output, *, max_bytes=268435456, max_members=10000)` and `verify_result_bundle(bundle_path, *, extract_to=None, max_bytes=268435456, max_members=10000)`. Both return bounded dictionaries and raise ResultManifestError for invalid input. Low-level archive module exposes `write_bundle_archive(root, output, *, max_bytes, max_members)` and `extract_bundle_archive(archive, destination, *, max_bytes, max_members)`; the latter targets a private empty stage and never publishes it. Public publication is root-owned.

Freeze independent failing tests before production edits; use the canonical engineering board `.codex/state/ultra-result-evidence.sqlite3`, topic bundles-r48. Root integrates. Installed acceptance includes malicious paths/archives, rollback and redaction, altered-content cursors, JSON/text parity, history, schema packaging and a relocated real exposition bundle with network disabled. Record peak RSS, elapsed time, archive and expanded bytes separately. Required upstream receipts must match the final implementation contract and candidate; prior receipts remain historical until compatibility is established.

## Risks / Trade-offs

- A whole selected SQLite file can include unrelated rows → require explicit whole-file permission, document dedicated stores, never auto-select from cache.
- Source changes while exporting → descriptor-based copying with metadata stability checks; hash copied bytes, never reread a different path for validation.
- ZIP expansion and hostile inventories → enforce streamed actual-byte limits and complete validation before publication; never use extractall.
- Temporary extraction can invalidate cursors → stable bundle index identity and logical lineage references, tested across relocations.
- Broad dossier traversal already costs repeated validation → record bundle overhead on a small real first-page/cursor sample before widening field work; if it fails the default 256 MiB bound or detached inspection, diagnose that limit before repeating the full field traversal.

## Migration Plan

Additive CLI/schema installation only. Existing manifests/companions and explicit-file commands remain compatible. No schema reinterpretation or upstream artifact edits. Rollback removes the additive bundle layer while exported immutable files remain accessible as ZIP payloads. Core acceptance enables the parent's qualitative alpha use; it does not complete the full child or archive it.
