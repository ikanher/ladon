# Proposal

Operationalize Ladon's report atlas so it becomes queryable, diffable, and
reviewer-facing rather than just a static JSON/Markdown summary.

# Why

The literature-backed direction now points to graph-query surfaces, architecture
evolution/diffing, and evidence-aware review outputs. Recent review feedback
also exposed an immediate self-audit issue: many completed OpenSpec changes are
still marked `status: active`, which makes the project metadata misleading even
when the CLI can infer completion.

# Scope

- Add a status-hygiene closeout pass for completed OpenSpec packets.
- Add a SQLite-backed atlas query surface with canned operational queries.
- Add atlas diffing over two report roots.
- Add packet/backlog hygiene analysis so Ladon can audit its own process data.
- Upgrade atlas Markdown into compact reviewer cards per root/report.
- Keep JSON as the stable machine interface.

# Non-Goals

- No web UI in this umbrella.
- No replacement of the existing report-atlas JSON.
- No LLM-only classification pass.
- No broad packet-review schema beyond lightweight hygiene/evidence signals.
- No Rust port or storage-engine rewrite.

# Child Packet Plan

1. `ladon-openspec-status-hygiene-mini`: close completed-vs-active metadata
   drift and add a check that prevents silent recurrence.
2. `ladon-atlas-sqlite-query-mini`: export atlas rows into SQLite and provide
   canned queries for hotspots, recurring declarations, region shifts, and
   proof-family pressure.
3. `ladon-atlas-diff-mini`: compare two atlas/report roots and summarize
   changed findings, changed review regions, new/cleared unresolved-reference
   classes, and root-scope shifts.
4. `ladon-openspec-backlog-analysis-mini`: turn packet evidence/hygiene into a
   small Ladon analysis surface, including active-vs-complete drift.
5. `ladon-atlas-reviewer-cards-mini`: emit compact Markdown cards with root,
   backend, top findings, review regions, strongest evidence, known non-claims,
   and report links.

# Acceptance

- Every child packet has tests or deterministic fixture checks.
- The umbrella stays focused on operational atlas usefulness, not visual polish.
- The resulting atlas supports at least one useful query, one useful diff, and
  one reviewer-facing card without reading raw report JSON by hand.
