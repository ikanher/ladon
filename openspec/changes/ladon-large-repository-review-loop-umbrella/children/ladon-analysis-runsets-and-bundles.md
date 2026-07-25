# `ladon-analysis-runsets-and-bundles`

Owns a generic versioned plan manifest, one canonical report per root,
deterministic bundle manifests, serial-by-default execution, shared sound reuse,
failure isolation, cancellation cleanup, and fingerprinted resume.

- Dependencies: large-inventory reuse, explicit scope plans, and partial-run
  observability.
- Enables: repeatable report sets and installed atlas/query/diff workflows.
- Excludes: a second analyzer, merged multi-root authority, caller-specific
  defaults, built-in sibling-repository matrices, or automatic git-ref
  orchestration.
- Exit: unchanged resume launches zero analyses, a one-entry change invalidates
  only that entry and declared dependents, one failure preserves other reports,
  bundle backreferences resolve, and cancellation leaves no helpers.
