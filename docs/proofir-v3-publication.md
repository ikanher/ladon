# ProofIR v3 publication boundary

The v3 SQLite database is a disposable, project-local projection. Publication
uses the shared SQLite publisher to acquire `<database>.lock` beside the
destination. Kernel descriptor ownership is authoritative; PID text is only
diagnostic, and each owner records an unpredictable token. Live owners fail
closed, while unlocked or malformed metadata is safely reusable. Builds
use an owner-specific temporary file in the same directory, enable foreign-key
and full synchronous modes, set `max_page_count` from `maxDatabaseBytes`, run
integrity and query-plan gates, fsync the temporary file, atomically replace the
destination, and fsync the containing directory where supported.

Any failure leaves the previous destination untouched and removes only the
temporary file and sidecars owned by that build. Lock metadata paths persist so
release cannot unlink a replacement owner's path. The same primitive governs
proof-search builds, ProofIR v3 publication, lineage mutation, and optional
atlas SQLite publication. `dbstat` is optional
diagnostic enrichment; portable page-size × page-count accounting remains the
authoritative database-size bound.

## Local-integrity hardening

Manifest link observations are policy v2 records. A discovered file is reported
under `resolvedFileDigest`; `resolvedArtifactId` is populated only after native
ProofIR envelope validation establishes the detached content identity. Existing
disposable indexes must be rebuilt after this field correction; old observations
are not interpreted heuristically.

Authority-sensitive semantic checks should pass an explicit
`LeanToolchainContext`, which binds absolute Lake/Lean executables, the exact
`lean-toolchain` pin, and a sanitized environment. Explicit selection is
fail-closed; ambient selection is labeled non-authoritative. Candidate
application checks are not declaration-proof replay or theorem-truth claims.

The current Ladon boundary deliberately defers object stores, provenance
lattices, signed anchors, repository-closure policy, Lean trust-core predicates,
and future digest-prefix changes.
