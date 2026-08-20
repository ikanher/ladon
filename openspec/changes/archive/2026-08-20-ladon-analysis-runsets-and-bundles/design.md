## Context

Large Lean projects have several useful review roots. Repeating independent
commands discards reusable discovery work and makes interrupted reviews hard to
resume. This child orchestrates ordinary analyses without inventing a merged
authority surface.

## Decisions

### A runset is a versioned generic manifest

Each entry names a repository-relative root, scope, backend, projection,
documented analysis options, output identity, and required/advisory status.
The complete manifest is validated before any target process starts.

### Reports remain independent

Every entry runs the ordinary one-root analysis and writes one canonical
report. The bundle manifest references those reports by relative path and
records terminal state, hashes, scope identity, phase summary, and resource
counters.

### Execution is serial and resumable

Serial execution is the default. Source indexes and Lean caches are reused only
when full validity fingerprints agree. Atomic state after every terminal entry
permits zero-launch resume hits and selective invalidation.

## Existing Owners And Exclusions

CLI status/streams, report schemas, source indexes, caches, and process
supervision retain their existing owners. This child does not merge reports,
change analyzer thresholds, execute VCS, or add repository-specific manifests.

## Risks

A corrupt or manually edited report could be accepted during resume. Entry
fingerprints, report versions, content hashes, and completion state all must
validate before reuse.
