## Context

Ladon already preserves an important trust boundary: structural observations,
source-hash/range joins, packet evidence summaries, and optional ProofIR statuses
are review-routing context only. The current bridge can attach compact ProofIR
surfaces to Ladon declarations, preserve quoted external status, and warn about
weak or stale attachment. That foundation is necessary but not sufficient for
the highest-risk process failure reported in review: a public claim says
"closed" or "fully proved" while the actual route is conditional on imported
certificate rows, interval-certified scalar evidence, side-condition packages,
or a theorem surface whose endpoint scope is narrower than the prose claim.

This umbrella makes claim/evidence authority auditing the next serious Ladon
milestone. It should build on the ProofIR bridge, atlas workflow, packet
evidence summaries, and declaration-surface evidence without making Ladon a
proof checker.

## Goals / Non-Goals

**Goals:**

- Add a route-audit model for claim status, claimed authority, endpoint scope,
  primary/supporting theorem surfaces, required evidence authorities, allowed
  external evidence, and nonclaims.
- Emit explicit diagnostics when a claim's advertised authority is stronger than
  its observed evidence route supports.
- Extend compact ProofIR bridge inputs with route/authority metadata while
  keeping raw ProofIR dialects outside Ladon core.
- Build portable fixtures from the b-min-sep-style failure classes so regressions
  target real overclaim patterns.
- Add warning-only theorem signature heuristics for final-sounding names whose
  signatures still expose conditional evidence premises.
- Improve review-packet validation summaries by distinguishing skipped source
  paths from forbidden files actually included in an archive.

**Non-Goals:**

- Ladon does not prove theorem truth, replay Lean proofs, validate witness
  adequacy, or decide mathematical correctness.
- Ladon does not infer arbitrary semantic scope hierarchies without explicit
  route metadata or a small configured taxonomy.
- Signature heuristics do not establish authority mismatches; they only route
  human review.
- This umbrella does not require a graph database, Rust rewrite, LLM explanation
  layer, UI, or full elaborated proof-dependency engine.
- This umbrella does not replace Quux/ProofIR claim-governance ownership; it
  consumes compact route metadata at the bridge boundary.

## Decisions

1. Model route auditing as a pure analysis layer.

   Add a pure route-audit module that consumes already-normalized claim route
   rows, Ladon declaration/source evidence rows, packet evidence rows, and
   optional ProofIR bridge joins. It returns diagnostics and reviewer-card rows.
   It must not shell out to Lean, inspect arbitrary files, or mutate bridge
   input. CLI and bridge code can adapt external artifacts into the route model.

   Alternative considered: embed these checks directly in `proofir_bridge`. That
   would blur input normalization with governance policy and make route-audit
   fixtures harder to run without ProofIR.

2. Treat explicit route metadata as the primary evidence source.

   The route model should prefer explicit fields: `claimedStatus`,
   `claimedAuthority`, `endpointScope`, `primaryTheoremSurfaces`,
   `supportingTheoremSurfaces`, `backgroundTheoremSurfaces`,
   `requiredEvidenceAuthorities`, `allowedExternalEvidence`, and `nonclaims`.
   Ladon declaration joins establish attachment confidence for theorem surfaces,
   not proof truth.

   Alternative considered: infer route authority from theorem names and packet
   prose first. That is useful as a warning, but too weak for the direct
   closed-with-imported-evidence diagnostic.

3. Keep authority vocabulary small and explicit.

   Start with normalized strings such as `lean_proved`, `lean_closed`,
   `lean_checker`, `imported_numeric`, `interval_certified`,
   `imported_interval_certified`, `external_certificate`, `diagnostic`, `smoke`,
   `unchecked`, and `conditional_external_evidence`. Unknown authorities should
   be preserved and diagnosed as unknown, not silently upgraded.

   Alternative considered: one numeric confidence score. That would hide the
   distinction between Lean-owned closure, external certificates, imported
   numeric evidence, and smoke/diagnostic rows.

4. Make endpoint-scope overclaim explicit and conservative.

   A claim row may state `endpointScope`, and theorem surfaces or route rows may
   state observed scopes. Ladon should flag a configured stronger claim such as
   `arbitrary_neighbor_event_dp` when the observed primary theorem route is only
   `sampled_null_event_dp`. If no configured relation is known, Ladon should emit
   a lower-confidence scope mismatch row rather than inventing a semantic order.

   Alternative considered: parse theorem names/prose to infer endpoint scope.
   That can support warnings, but it should not drive high-confidence route
   overclaim diagnostics by itself.

5. Signature-pattern checks remain warning-only.

   Theorem names containing final/production/maintained/closed/eventDP-like
   markers plus signatures containing `EvidenceAt`, `Certificate`, `Package`,
   `falsePkg`, `hForwardCDF`, `hReverseCDF`, `hcountMassEvidence`,
   `haggregateEvidence`, `imported`, or generic row evidence should produce
   `ladon.theorem.final_name_conditional_statement`. These rows help reviewers
   inspect suspicious declarations; they do not determine proof authority.

   Alternative considered: fail packets on those signatures. That would create
   false positives for honestly conditional theorems and would confuse review
   routing with proof policy.

6. Route-audit fixtures come before broad heuristics.

   Freeze small, source-first fixtures for the known failure classes before
   expanding authority rules. The initial fixtures should include overclaiming
   negatives and honest positives so the audit learns boundaries, not just
   examples from one project history.

   Alternative considered: add many new smell classes first. The review feedback
   makes clear that process overclaims are more urgent than additional
   architecture signals.

## Risks / Trade-offs

- [Risk] Authority labels drift across Quux/ProofIR versions. -> Mitigation:
  normalize only the compact route contract, preserve unknown labels, and emit
  an unknown-authority diagnostic instead of upgrading status.
- [Risk] Endpoint-scope taxonomy is incomplete. -> Mitigation: start with a
  small configured table and mark unconfigured mismatches as review warnings.
- [Risk] Honest conditional theorems get noisy final-name warnings. ->
  Mitigation: keep signature heuristics warning-only and suppress them when the
  claim route explicitly labels imported/conditional evidence.
- [Risk] Users read route diagnostics as proof failures. -> Mitigation: every
  report section must state that Ladon audits authority/evidence alignment, not
  theorem truth.
- [Risk] b-min-sep-derived fixtures become private-project overfitting. ->
  Mitigation: reduce fixtures to portable, synthetic route JSON and tiny Lean
  snippets with explicit expected diagnostics.
- [Risk] Packet validation summaries remain noisy. -> Mitigation: separate
  `skippedSourcePaths` from `forbiddenArchiveEntries` and fail only on the
  latter.

## Migration Plan

1. Add compact route/authority fixtures and the pure audit data model.
2. Implement the core route diagnostics:
   `closed_with_imported_evidence`, `endpoint_scope_overclaim`,
   `authority_mismatch`, and `missing_primary_theorem_surface`.
3. Extend ProofIR normalization to preserve route/authority fields into bridge
   report and reviewer-card output.
4. Add signature-pattern heuristics as a separate warning-only pass.
5. Add atlas/reviewer-card summaries for claim authority audit sections.
6. Improve review-packet validation summary naming for skipped versus included
   forbidden paths.
7. Update docs and pro review packet guidance to present claim authority audit
   as Ladon's Priority 1 roadmap item.

All changes should be additive. Existing ProofIR bridge reports remain valid
when route fields are absent; the audit should then emit unavailable or missing
route diagnostics rather than fabricating authority.

## Open Questions

- Which authority labels should be canonical versus preserved as project-local
  extensions?
- Should endpoint-scope relations live in code, config, or compact ProofIR route
  metadata?
- What minimum theorem-surface data is required before a public claim can avoid
  `missing_primary_theorem_surface`?
- Should CI failure rules live in route-audit configuration or in the later
  Review Radar layer?
