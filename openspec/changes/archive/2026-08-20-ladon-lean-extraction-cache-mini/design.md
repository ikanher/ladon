# Design

The cache stores the raw helper JSON payload for each source file under a user
provided directory. Each key includes:

- absolute repo root
- source path relative to repo root
- source file SHA-256
- helper file SHA-256

This makes cache entries content-addressed enough for the current tool without
needing to understand Lake build state. If imports change indirectly but the
target source text does not, the helper payload may still be affected. To avoid
overclaiming, the cache is opt-in and documented as a repeated-run speed tool,
not a sound incremental build system.

Pipeline counters will report:

- `lean_cache_hits`
- `lean_cache_misses`

The cache object stays inside `lean_extraction.py`; the pipeline only passes an
optional cache directory and records counters from the returned bundle metadata.
