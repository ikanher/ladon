## ADDED Requirements

### Requirement: Opt-In Lean Helper Cache

The Lean extraction backend SHALL support an optional cache directory for helper
JSON payloads.

#### Scenario: default behavior remains uncached

- GIVEN a user runs Ladon without a cache directory
- WHEN the Lean backend extracts a file
- THEN Ladon SHALL invoke the Lean helper normally.

#### Scenario: repeated cached extraction

- GIVEN a user runs Ladon with a cache directory
- AND the same repo root, source file content, and helper content have already
  been extracted
- WHEN the Lean backend extracts the same file again
- THEN Ladon SHALL reuse the cached helper JSON payload.

#### Scenario: source content invalidates cache

- GIVEN a user runs Ladon with a cache directory
- AND the source file content changes
- WHEN the Lean backend extracts the file again
- THEN Ladon SHALL not reuse the old cache entry.

### Requirement: Cache Counters

The report pipeline SHALL expose Lean cache hit and miss counters when the Lean
backend is used.

#### Scenario: cached run reports counters

- GIVEN a user runs Ladon with the Lean backend and a cache directory
- WHEN extraction completes
- THEN the `lean_extraction` timing counters SHALL include cache hit and miss
  counts.
