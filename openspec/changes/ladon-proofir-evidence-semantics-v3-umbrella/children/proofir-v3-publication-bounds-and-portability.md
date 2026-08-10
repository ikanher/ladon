# proofir-v3-publication-bounds-and-portability

Reuse Ladon's project-local PID lock, page limit, integrity, fsync, and durable replacement boundary; make storage and plan evidence portable across SQLite builds.

Start after cross-artifact/query and SQLite foundations. r03 verified durable publication but reproduced cleanup deleting a competitor lock. Exit only when nonce/file-identity ownership protects cleanup and stale recovery under concurrency, PID-reuse, malformed-lock, crash, page/database/query-bound, `dbstat`-absence, and plan gates.
