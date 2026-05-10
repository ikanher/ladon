# Proposal

Lean-backed extraction currently shells out to `lake env lean --run` for every
selected source file. Root extraction is usable, but repeated root runs and
inventory experiments pay the same parser-helper cost repeatedly.

Add a conservative on-disk cache for parser-helper JSON payloads. The cache must
be opt-in through the existing Ladon CLI surface, deterministic, and invalidated
by file contents plus helper contents.

# Scope

- Add cache plumbing to the Lean extraction backend.
- Preserve the default no-cache behavior.
- Expose cache hit/miss counters through the pipeline timing counters.
- Test that cached extraction avoids rerunning the helper and invalidates when a
  source file changes.

# Non-Goals

- No daemon, database, or parallel scheduler.
- No semantic caching across different repos.
- No change to text extraction or declaration graph analysis.
