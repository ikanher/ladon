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
