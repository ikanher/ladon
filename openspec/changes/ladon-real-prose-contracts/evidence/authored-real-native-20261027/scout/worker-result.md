worker_result:
  role: documentation_scout
  status: partial_support
  exact_claim: >
    Mapped the current native contract dispatch, batch-owner validator, report/inspection routes, SQLite projection, and existing semantic profile gates with exact file:line locations. A new authored Real profile requires an explicit validator and exact interpretation/observation/recognition owner recomputation. Existing Nat propagation/probe/uniformity consumers reject non-Nat profiles; the provider route lacks a profile gate and needs caller audit. The selected ~5.4 MB observation cannot be embedded naively because native caps also forbid depth >64, strings >1 MiB and float scalars. Posted a codec artifact-size expansion challenge at board post 1930.
  artifacts: .codex/state/real-prose-native/scout/inventory.md; board posts 1928, 1930
  commands: >
    Read-only cat/rg/nl/find over assigned CONTRACT.md, OpenSpec proposal/design/spec/tasks, native validator/dispatch/payload/report/SQLite and semantic consumers; git rev-parse HEAD => e6479e465d652029502bc19b6a03e90b359bf5b5; git status --short showed shared worktree dirty, including relevant dispatch/SQLite/report sources. No test/build/Lean commands run.
  baseline: >
    HEAD e6479e465d652029502bc19b6a03e90b359bf5b5. Relevant files are already dirty in shared worktree; line map is a current-source snapshot, not a clean revision baseline. No source hashes captured.
  dependencies: none
  assigned_files_edited: .codex/state/real-prose-native/scout/inventory.md; .codex/state/real-prose-native/scout/worker-result.md
  frozen_tests_unchanged: true
  remaining_gate: >
    Root integration must verify each consumer against current edited sources and test actual bounded chunked artifact size, complete owner closure, persistence round trips, rollback and explicit unsupported responses. No implementation or runtime verification performed by this scout.
  trust_notes: >
    Findings are source inspection only. Saved observation/recognition history remains unauthenticated absent fresh checks. Proposed chunk codec must check enclosing canonical artifact bytes, not just raw chunk text, because escaping can increase size.
