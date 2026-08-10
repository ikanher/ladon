# ProofIR v3 publication boundary

The v3 SQLite database is a disposable, project-local projection. Publication
acquires `<database>.lock` beside the destination and records the owner PID.
Live owners fail closed; dead or malformed lock records are recoverable. Builds
use an owner-specific temporary file in the same directory, enable foreign-key
and full synchronous modes, set `max_page_count` from `maxDatabaseBytes`, run
integrity and query-plan gates, fsync the temporary file, atomically replace the
destination, and fsync the containing directory where supported.

Any failure leaves the previous destination untouched and removes only the
temporary file, sidecars, and lock owned by that build. `dbstat` is optional
diagnostic enrichment; portable page-size × page-count accounting remains the
authoritative database-size bound.
